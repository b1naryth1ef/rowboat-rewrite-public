from __future__ import absolute_import

import logging

from redis import Redis
from disco.gateway.events import GatewayEvent
from disco.gateway.client import GatewayClient

from gateway.state import State
from common.rpc.server import RPCServer
from common.carousel.pool import Pool

log = logging.getLogger(__name__)


class RowboatGatewayClient(GatewayClient):
    def handle_dispatch(self, packet):
        if packet['t'] in ['READY', 'RESUMED']:
            obj = GatewayEvent.from_dispatch(None, packet)
            self.events.emit(obj.__class__.__name__, obj)

        self.on_packet(packet)


class Gateway(object):
    def __init__(self, config, shard_id):
        self.token = config.gateway['token']
        self.shard_count = config.gateway['shard_count']
        self.shard_id = shard_id

        self.gw = RowboatGatewayClient(self.token, self.shard_id, self.shard_count, max_reconnects=0)
        self.gw.on_packet = self.on_packet
        self.pool = Pool('guilds')

        self.state = State()

        self._guilds = {}
        self._clients = []

        # Start up loqui
        self.rpc = RPCServer(self._on_rpc_request, self._on_rpc_close)

        self.rdb = Redis(db=6)
        self.pubsub = self.rdb.pubsub()

    def _on_rpc_request(self, socket, op, data):
        log.debug('RPC REQUEST: %s', op)

        if op == 'SYNC_GUILD':
            self._guilds[data] = socket

            if socket not in self._clients:
                self.rpc.send_to(socket, 'INIT', {
                    'token': self.token,
                })
                # TODO: leak
                self._clients.append(socket)

                # Dispatch Ready
                self.dispatch(data, 'READY', self.state.ready)

            guild_data = self.state.prepare_guild(data)
            if guild_data:
                self.dispatch(data, 'GUILD_CREATE', guild_data)

    def _on_rpc_close(self, closed_socket):
        for guild, sock in self._guilds.items():
            if sock == closed_socket:
                del self._guilds[guild]

        self._clients.remove(closed_socket)

    def run(self):
        self.rdb.set('shard:{}'.format(self.shard_id), 'localhost:{}'.format(self.rpc.port))

        self.gw.run(gateway_url='wss://gateway.discord.gg/')

    def forward(self, guild_id, event):
        self.dispatch(guild_id, event['t'], event['d'])

    def dispatch(self, guild_id, packet_type, packet_data):
        if guild_id not in self._guilds:
            return

        if self._guilds[guild_id].closed:
            return

        self.rpc.send_to(self._guilds[guild_id], 'DISPATCH', (packet_type, packet_data))

    def on_packet(self, packet):
        self.state.handle_gateway_event(packet['t'], packet['d'])

        method = getattr(self, 'on_{}'.format(packet['t'].lower()), None)
        if method:
            method(packet)

    def on_ready(self, packet):
        for guild in list(packet['d']['guilds']):
            self.pool.ensure_resource(guild['id'])

    def on_guild_create(self, packet):
        print 'GUILD_CREATE %s' % packet['d']['id']
        # Case 1: We are starting up fresh, no bots exist and this is thrown away
        # Case 2: Bot has been running but gateway was restarted, in this case
        #  we want the bot to entirely replace its guild (since its possible it
        #  has a stale version in memory.
        # Case 3: Discord died and we're just reconnceting. Same as above, we
        #  want to refresh the downstream guild.
        # TODO: guild_replace
        self.dispatch(packet['d']['id'], 'GUILD_CREATE', packet['d'])

        # TODO: check if new
        self.pool.ensure_resource(packet['d']['id'])

    def on_guild_update(self, packet):
        self.forward(packet['d']['id'], packet)

    def on_guild_delete(self, packet):
        # We want to destroy the carousel resource, which will terminate the
        #  downstream bot stuff.
        self.forward(packet['d']['id'], packet)
        self.pool.delete_resource(packet['d']['id'])

    def _message_forward(self, packet):
        guild_id = self.state.channel_ids_to_guild_ids.get(packet['d']['channel_id'])
        if not guild_id:
            return

        self.forward(guild_id, packet)

    on_message_create = _message_forward
    on_message_update = _message_forward
    on_message_delete = _message_forward
    on_message_delete_bulk = _message_forward
    on_typing_start = _message_forward
    on_message_reaction_add = _message_forward
    on_message_reaction_remove = _message_forward
    on_message_reaction_remove_all = _message_forward

    def _easy_forward(self, packet):
        self.forward(packet['d']['guild_id'], packet)

    on_channel_create = _easy_forward
    on_channel_update = _easy_forward
    on_channel_delete = _easy_forward
    on_guild_emojis_update = _easy_forward
    on_guild_member_add = _easy_forward
    on_guild_member_update = _easy_forward
    on_guild_member_remove = _easy_forward
    on_guild_role_create = _easy_forward
    on_guild_role_update = _easy_forward
    on_guild_role_delete = _easy_forward
    on_presence_update = _easy_forward
