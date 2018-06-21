
class GuildConfigUpdate(object):
    def __init__(self, guild_id, old_config):
        self.guild_id = guild_id
        self.old_config = old_config
