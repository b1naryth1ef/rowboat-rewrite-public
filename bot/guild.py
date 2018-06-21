from __future__ import absolute_import

import logging

from common.models.guild import Guild, GuildConfig
from bot.events import GuildConfigUpdate

log = logging.getLogger(__name__)


class GuildState(object):
    def __init__(self, guild, bot):
        self.guild = guild
        self.config = {}
        self.bot = bot
        self.state = self.bot.client.state

        # TODO: scope to GuildState
        self.log = log

        self._ensure_created()
        gc = GuildConfig.latest_for_guild(guild.id)
        if gc:
            self.config = gc.config

    def _ensure_created(self):
        exists = Guild.select().where(
            (Guild.guild_id == self.guild.id)
        ).exists()

        if not exists:
            Guild.insert(
                guild_id=self.guild.id,
                owner_id=self.guild.owner_id,
                name=self.guild.name,
                member_count=len(self.guild.members),
                channel_count=len(self.guild.channels),
                role_count=len(self.guild.roles),
                emoji_count=len(self.guild.emojis),
            ).execute()
        else:
            Guild.update(
                owner_id=self.guild.owner_id,
                name=self.guild.name,
                member_count=len(self.guild.members),
                channel_count=len(self.guild.channels),
                role_count=len(self.guild.roles),
                emoji_count=len(self.guild.emojis),
            ).where(Guild.guild_id == self.guild.id).execute()

    def handle_action(self, name, payload):
        if name == 'CONFIG_UPDATE':
            old_config = self.config
            self.config = payload
            self.bot.client.events.emit('GuildConfigUpdate', GuildConfigUpdate(
                self.guild.id,
                old_config,
            ))
