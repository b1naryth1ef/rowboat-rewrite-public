import os
import json

from kazoo.client import KazooClient
from kazoo.handlers.gevent import SequentialGeventHandler
from kazoo.exceptions import NodeExistsError, NoNodeError
from kazoo.recipe.watchers import ChildrenWatch

from .node import Node


class PoolException(Exception):
    pass


class Pool(object):
    """
    A pool represents a set of resources and nodes that own/manage those resources.
    The pool class is responsible for tracking state of all nodes and resources
    within the entire pool.
    """
    def __init__(self, name, hosts='127.0.0.1:2181'):
        self.name = name
        self.path = '/carousel/{}'.format(name)
        self.hosts = hosts

        # Generic metadata tracked for the entire pool
        self.nodes = set()
        self.resources = set()

        self.zk = None

        if hosts:
            self.connect(hosts)

    def _on_resources_change(self, res):
        self.resources = set(res)

    def _on_nodes_change(self, res):
        self.nodes = set(res)

    @property
    def healthy(self):
        resources_with_leaders = set(self.zk.get_children(os.path.join(self.path, 'leaders')))
        resources_without_leaders = self.resources - resources_with_leaders
        return not len(resources_without_leaders)

    def create(self, metadata={}):
        # Create the base pool path with metadata
        self.zk.create(self.path, str.encode(json.dumps(metadata)), makepath=True)

        for path in ['resources', 'nodes', 'leaders']:
            self.zk.create(os.path.join(self.path, path))

        self.load()

    def load(self):
        # Check whether the pool exists
        if not self.zk.exists(self.path):
            raise PoolException("Pool with name {} does not exist!".format(self.name))

        # Next load the pool meta-data
        self.meta, self.meta_stat = self.zk.get(self.path)
        self.meta = json.loads(self.meta.decode())

        # Finally, we need to keep track of resources and nodes
        ChildrenWatch(self.zk, os.path.join(self.path, 'resources'), self._on_resources_change)
        ChildrenWatch(self.zk, os.path.join(self.path, 'nodes'), self._on_nodes_change)

    def connect(self, hosts, timeout=4):
        self.zk = KazooClient(hosts, timeout=timeout, handler=SequentialGeventHandler())
        self.zk.start_async().wait(timeout=5)

        if not self.zk.connected:
            self.zk.stop()
            raise Exception('Failed to reach zookeeper')

        try:
            self.load()
        except PoolException:
            self.create()

    def disconnect(self):
        self.zk.stop()

    def ensure_resources(self, *resources):
        for resource in resources:
            self.ensure_resource(resource)

    def ensure_resource(self, name, metadata=None):
        try:
            self.zk.create(os.path.join(self.path, 'resources', name), json.dumps(metadata or {}))
        except NodeExistsError:
            pass

    def delete_resource(self, name):
        assert name in self.resources

        self.zk.delete(os.path.join(self.path, 'resources', name))

        try:
            self.zk.delete(os.path.join(self.path, 'leaders', name))
        except NoNodeError:
            pass

    def create_node(self, metadata=None):
        return Node(self, metadata or {})

    def get_leader(self, resource):
        result, _ = self.zk.get(os.path.join(self.path, 'leaders', resource))
        return result
