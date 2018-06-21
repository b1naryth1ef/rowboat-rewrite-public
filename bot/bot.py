import gevent
import json
import logging

from redis import Redis
from disco.gateway.events import GatewayEvent
from disco.client import Client, ClientConfig

from .datastore import Datastore
from .plugin_manager import PluginManager
from .guild import GuildState

from common.rpc.client import RPCClient
from common.carousel.pool import Pool

log = logging.getLogger(__name__)


class Bot(object):
    def __init__(self, shard_count, auto_acquire, max_resources):
        self.shard_count = shard_count

        # Carousel Stuff
        self.pool = Pool('guilds')
        self.node = self.pool.create_node()
        self.node.max_resources = max_resources
        self.node.auto_acquire = auto_acquire
        self.node.on_acquire_resource = self.on_acquire_resource
        self.node.on_release_resource = self.on_release_resource
        self.node.join()

        # Redis instance
        self.rdb = Redis(db=6)

        # Plugin Manager
        self.plugin_manager = PluginManager(self)

        # Data store, manages writing events to database
        self.datastore = Datastore(self)

        self.client = None
        self.state = None

        self.shard_clients = {}
        self.guild_clients = {}
        self.guild_state = {}

        # Bot Stuff
        self.command_matches_re = None
        self.commands = []

    def _bind_events(self):
        self.datastore.init()
        self.plugin_manager.init()
        self.client.events.on('GuildCreate', self._on_guild_create)
        gevent.spawn(self._pubsub)

    def _pubsub(self):
        ps = self.rdb.pubsub()
        ps.subscribe('actions')

        for item in ps.listen():
            if item['type'] != 'message':
                continue

            try:
                data = json.loads(item['data'])
                if data['guild_id'] not in self.guild_state:
                    continue

                self.guild_state[data['guild_id']].handle_action(data['action'], data['payload'])
            except Exception:
                log.exception('Failed to handle action:')

    def _on_guild_create(self, event):
        self.guild_state[event.guild.id] = GuildState(event.guild, self)

    def _on_rpc_request(self, op, data):
        log.info('RPC REQUEST: %s', op)

        if op == 'INIT' and not self.client:
            config = ClientConfig()
            config.token = data['token']
            config.state = {'sync_guild_members': False, 'track_messages': False}
            self.client = Client(config)
            self.state = self.client.state
            self._bind_events()
        elif op == 'DISPATCH':
            self._on_dispatch(*data)

    def _on_dispatch(self, packet_type, packet_data):
        log.info('Dispatch: %s', packet_type)
        event = GatewayEvent.from_dispatch(self.client, {
            't': packet_type,
            'd': packet_data,
        })
        self.client.events.emit(event.__class__.__name__, event)

    def on_acquire_resource(self, node, resource):
        log.info('[G:%s] Carousel requested we acquire this Guild', resource)
        guild_id = int(resource)
        shard_id = (guild_id >> 22) % self.shard_count

        if shard_id not in self.shard_clients:
            shard_endpoint = self.rdb.get('shard:{}'.format(shard_id))
            self.shard_clients[shard_id] = RPCClient(self._on_rpc_request, *shard_endpoint.split(':'))

        self.guild_clients[guild_id] = self.shard_clients[shard_id]
        self.shard_clients[shard_id].send('SYNC_GUILD', str(guild_id))

    def on_release_resource(self, node, resource):
        log.info('[G:%s] Carousel asked us to release this Guild', resource)

    def run(self, config):
        self.config = config

        while True:
            gevent.sleep(1)

    def __del__(self):
        self.node.leave()
        self.node.disconnect()
        self.pool.disconnect()
