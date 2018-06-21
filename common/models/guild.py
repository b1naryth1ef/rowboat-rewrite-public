import peewee
import uuid
import operator
import json

from redis import Redis
from playhouse.postgres_ext import BinaryJSONField, ArrayField

from common.models import BaseModel


class Guild(BaseModel):
    class Meta:
        db_table = 'guilds'

    guild_id = peewee.BigIntegerField(primary_key=True)
    owner_id = peewee.BigIntegerField()
    config_id = peewee.UUIDField(null=True)
    name = peewee.TextField()

    member_count = peewee.IntegerField()
    channel_count = peewee.IntegerField()
    role_count = peewee.IntegerField()
    emoji_count = peewee.IntegerField()

    web_viewers = ArrayField(peewee.BigIntegerField, default=[])
    web_editors = ArrayField(peewee.BigIntegerField, default=[])
    web_admins = ArrayField(peewee.BigIntegerField, default=[])

    @classmethod
    def with_id(cls, guild_id):
        try:
            return cls.get(guild_id=guild_id)
        except cls.DoesNotExist:
            return None

    def to_dict(self):
        return {
            'guild_id': str(self.guild_id),
            'owner_id': str(self.owner_id),
            'config_id': str(self.config_id),
            'name': self.name,
            'web': {
                'viewers': map(str, self.web_viewers),
                'editors': map(str, self.web_editors),
                'admins': map(str, self.web_admins),
            },
            'stats': {
                'member_count': self.member_count,
                'channel_count': self.channel_count,
                'role_count': self.role_count,
                'emoji_count': self.emoji_count,
            }
        }

    def dispatch(self, action_name, payload):
        rdb = Redis(db=6)
        rdb.publish('actions', json.dumps({
            'guild_id': self.guild_id,
            'action': action_name,
            'payload': payload,
        }))

    def update_config(self, config_obj, previous_config_id=None):
        new_config = GuildConfig.create(
            guild_id=self.guild_id,
            raw_content=config_obj.raw,
            config=config_obj.to_dict(),
        )

        clauses = [
            (Guild.guild_id == self.guild_id)
        ]

        if previous_config_id:
            clauses.append(
                (Guild.config_id == previous_config_id)
            )

        success = Guild.update(config_id=new_config.config_id).where(
            reduce(operator.and_, clauses)
        ).execute() == 1

        if success:
            self.dispatch('CONFIG_UPDATE', config_obj.to_dict())

        return success, new_config


class GuildConfig(BaseModel):
    class Meta:
        db_table = 'guild_configs'
        primary_key = peewee.CompositeKey('guild_id', 'config_id')

    config_id = peewee.UUIDField(default=uuid.uuid4)
    guild_id = peewee.BigIntegerField()

    raw_content = peewee.TextField(default='')
    config = BinaryJSONField(default={})

    @classmethod
    def with_id(cls, config_id):
        try:
            return cls.get(config_id=config_id)
        except GuildConfig.DoesNotExist:
            return None

    @classmethod
    def latest_for_guild(cls, guild_id):
        try:
            return GuildConfig.select(GuildConfig).join(Guild, on=(
                (Guild.guild_id == GuildConfig.guild_id) &
                (Guild.config_id == GuildConfig.config_id)
            )).where(
                (Guild.guild_id == guild_id)
            ).get()
        except GuildConfig.DoesNotExist:
            return None

    def to_dict(self):
        return {
            'config_id': str(self.config_id),
            'guild_id': str(self.guild_id),
            'contents': self.raw_content,
            'config': self.config,
        }
