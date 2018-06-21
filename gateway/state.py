import copy

"""
EVENTS TODO:
    - GuildDelete ?
    - GuildMembersChunk ?
    - PresenceUpdate ?
    - VoiceStateUpdate ?
"""


class State(object):
    def __init__(self):
        self.guilds = {}
        self.guild_channels = {}
        self.guild_members = {}
        self.guild_roles = {}

        self.ready = {}

        self.channel_ids_to_guild_ids = {}

    def prepare_guild(self, guild_id):
        if guild_id not in self.guilds:
            return None

        guild = copy.deepcopy(self.guilds[guild_id])
        guild['channels'] = self.guild_channels[guild_id].values()
        guild['members'] = self.guild_members[guild_id].values()
        guild['roles'] = self.guild_roles[guild_id].values()
        return guild

    def handle_gateway_event(self, event, data):
        method = getattr(self, 'handle_{}'.format(event.lower()), None)
        if method:
            method(data)

    def handle_ready(self, data):
        self.ready = {
            'user': data['user']
        }

    def handle_guild_create(self, data):
        self.guilds[data['id']] = data
        self.guild_channels[data['id']] = {
            i['id']: i for i in data['channels']
        }
        del self.guilds[data['id']]['channels']
        self.guild_members[data['id']] = {
            i['user']['id']: i for i in data['members']
        }
        del self.guilds[data['id']]['members']
        self.guild_roles[data['id']] = {
            i['id']: i for i in data['roles']
        }
        del self.guilds[data['id']]['roles']

        for channel_id in self.guild_channels[data['id']].keys():
            self.channel_ids_to_guild_ids[channel_id] = data['id']

    def handle_guild_update(self, data):
        self.guilds[data['id']].update(data)

    def handle_guild_delete(self, data):
        del self.guilds[data['id']]
        del self.guild_members[data['id']]
        del self.guild_roles[data['id']]

        for channel_id in self.guild_channels[data['id']].keys():
            del self.channel_ids_to_guild_ids[channel_id]

        del self.guild_channels[data['id']]

    def handle_channel_create(self, data):
        if data.get('guild_id'):
            self.guild_channels[data['guild_id']][data['id']] = data
            self.channel_ids_to_guild_ids[data['id']] = data['guild_id']

    def handle_channel_update(self, data):
        if data.get('guild_id'):
            self.guild_channels[data['guild_id']][data['id']].update(data)

    def handle_channel_delete(self, data):
        if data.get('guild_id'):
            del self.guild_channels[data['guild_id']][data['id']]
            del self.channel_ids_to_guild_ids[data['id']]

    def handle_guild_emojis_update(self, data):
        self.guilds[data['guild_id']]['emojis'] = data['emojis']

    def handle_guild_member_add(self, data):
        self.guild_members[data['guild_id']][data['user']['id']] = data

    def handle_guild_member_update(self, data):
        self.guild_members[data['guild_id']][data['user']['id']].update(data)

    def handle_guild_member_remove(self, data):
        del self.guild_members[data['guild_id']][data['user']['id']]

    def handle_guild_role_add(self, data):
        self.guild_roles[data['guild_id']][data['role']['id']] = data['role']

    def handle_guild_role_update(self, data):
        self.guild_roles[data['guild_id']][data['role']['id']].update(data['role'])

    def handle_guild_role_remove(self, data):
        del self.guild_roles[data['guild_id']][data['role_id']]
