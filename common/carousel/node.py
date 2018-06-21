import os
import time
import gevent
import random
import math

from kazoo.client import KazooClient
from kazoo.handlers.gevent import SequentialGeventHandler
from kazoo.recipe.watchers import DataWatch, ChildrenWatch
from kazoo.exceptions import NodeExistsError


class Node(object):
    def __init__(self, pool, metadata=None, max_inflight_acquires=1, auto_acquire=True):
        self.pool = pool
        self.zk = KazooClient(pool.hosts, timeout=5, handler=SequentialGeventHandler())
        event = self.zk.start_async()
        event.wait(timeout=5)
        if not self.zk.connected:
            self.zk.stop()
            raise Exception('Failed to reach zookeeper')

        self.metadata = metadata or {}

        self.id = None
        self.path = None
        self.auto_acquire = auto_acquire
        self.max_resources = 0

        # Set of resources we own
        self.resources = set()
        self._resource_backoff = {}
        self._resources_acquiring = gevent.lock.Semaphore(max_inflight_acquires)

        # Callbacks
        self.on_acquire_resource = None
        self.on_release_resource = None

        self._anti_entropy_greenlet = gevent.spawn(self._anti_entropy)

    def disconnect(self):
        self.zk.disconnect()

    def acquire(self, resource):
        assert resource in self.pool.resources
        return self._try_takeover(resource, force=True)

    def release(self, resource):
        assert resource in self.resources

        # TODO: transaction here
        self.zk.delete(os.path.join(self.pool.path, 'leaders', resource))

    def leave(self):
        for resource in list(self.resources):
            self.release(resource)

    def join(self):
        path = self.zk.create(os.path.join(self.pool.path, 'nodes', ''), ephemeral=True, sequence=True)
        self.path = path
        self.id = path.rsplit('/', 1)[-1]

        # Watch for leadership changes so we can possibly take over
        ChildrenWatch(self.zk, os.path.join(self.pool.path, 'leaders'), self._on_leaders_change)

        # Now that we've joined, lets see if there are any dangling resources we
        #  can take ownership of
        gevent.spawn(self._check_for_takeover, delay=0)

    def _on_leaders_change(self, data):
        # TODO: debounce this instead of just sleeping
        gevent.spawn(self._check_for_takeover, delay=5)

    def _on_resource_leader_change(self, data, stat, event):
        if not event:
            return

        resource_name = event.path.split('/')[-1]
        if resource_name not in self.pool.resources:
            return

        if resource_name in self.resources:
            if event.type == 'DELETED' or data != self.id:
                self._resource_backoff[resource_name] = time.time()
                self.resources.remove(resource_name)
                if callable(self.on_release_resource):
                    self.on_release_resource(self, resource_name)
                return False

        if event.type == 'DELETED':
            self._try_takeover(resource_name)

    def _check_for_takeover(self, delay=5):
        if not self.auto_acquire:
            return
        time.sleep(delay)

        resources_with_leaders = set(self.zk.get_children(os.path.join(self.pool.path, 'leaders')))
        resources_without_leaders = self.pool.resources - resources_with_leaders

        for resource in resources_without_leaders:
            self._try_takeover(resource)

            # If we have more than the even-split number of resources, backoff a bit
            if len(self.resources) > len(self.pool.resources) / len(self.pool.nodes):
                time.sleep(1)

    def _try_takeover(self, resource, force=False):
        if self.max_resources and len(self.resources) >= self.max_resources:
            return False

        if not force and resource in self._resource_backoff:
            if time.time() - self._resource_backoff[resource] < 10:
                return False
            del self._resource_backoff[resource]

        if self._resources_acquiring.locked():
            return False

        with self._resources_acquiring:
            path = os.path.join(self.pool.path, 'leaders', resource)

            try:
                self.zk.create(path, unicode.encode(self.id), ephemeral=True)
            except NodeExistsError:
                if not force:
                    return False

                _, metadata = self.zk.get(path)
                transaction = self.zk.transaction()
                transaction.delete(path, version=metadata.version)
                transaction.create(path, unicode.encode(self.id), ephemeral=True)
                result = transaction.commit()
                if result[0] is not True or result[1] != path:
                    return False

            DataWatch(self.zk, path, self._on_resource_leader_change)
            self.resources.add(resource)
            if callable(self.on_acquire_resource):
                self.on_acquire_resource(self, resource)
            return True

    def balance(self):
        threshold = math.ceil(len(self.pool.resources) / (len(self.pool.nodes) * 1.0))
        our_value = len(self.resources)

        if our_value > threshold + 1:
            resource = random.choice(list(self.resources))
            self._resource_backoff[resource] = time.time()
            self.release(resource)

    def _anti_entropy(self):
        while True:
            time.sleep(10)
            self.balance()
