import yaml

from disco.types.base import Model, Field, ListField, DictField, text, snowflake


class BotConfig(Model):
    nickname = Field(text)
    enabled = Field(bool)


class WebConfig(Model):
    viewers = ListField(snowflake)
    editors = ListField(snowflake)
    admins = ListField(snowflake)


class GuildConfigObject(Model):
    bot = Field(BotConfig)
    web = Field(WebConfig)
    # permissions = Field(PermissionsConfig)
    # plugins = RawField()

    def __init__(self, raw_data):
        self.raw = raw_data
        obj = yaml.load(raw_data)
        super(GuildConfigObject, self).__init__(obj)
