import re
import peewee

from playhouse.postgres_ext import ArrayField, BinaryJSONField
from disco.types.base import UNSET

from common.models import BaseModel
from common.models.user import User
from common.json import json_dumps

EMOJI_RE = re.compile(r'<:.+:([0-9]+)>')


class Message(BaseModel):
    class Meta:
        db_table = 'messages'

    message_id = peewee.BigIntegerField(primary_key=True)
    guild_id = peewee.BigIntegerField()
    channel_id = peewee.BigIntegerField()
    author_id = peewee.BigIntegerField()

    content = peewee.TextField()
    timestamp = peewee.DateTimeField()
    edited_timestamp = peewee.DateTimeField()
    edit_count = peewee.IntegerField(default=0)
    deleted = peewee.BooleanField(default=False)

    mentions = ArrayField(peewee.BigIntegerField, default=[], null=True)
    emojis = ArrayField(peewee.BigIntegerField, default=[], null=True)
    attachments = ArrayField(peewee.TextField, default=[], null=True)
    embeds = BinaryJSONField(default=[], null=True)
    metadata = BinaryJSONField(default={}, null=True)

    @classmethod
    def ensure_from_disco_message(cls, message):
        obj = Message.create(
            message_id=message.id,
            guild_id=(message.guild and message.guild.id),
            channel_id=message.channel_id,
            author_id=message.author.id,
            content=message.content,
            timestamp=message.timestamp,
            edited_timestamp=message.edited_timestamp,
            edit_count=(0 if not message.edited_timestamp else 1),
            mentions=list(message.mentions.keys()),
            emojis=[int(i) for i in EMOJI_RE.findall(message.content)],
            attachments=[i.url for i in message.attachments.values()],
            embeds=[json_dumps(i.to_dict()) for i in message.embeds],
        )

        User.ensure_from_disco_user(message.author)

        for user in message.mentions.values():
            User.ensure_from_disco_user(user)

        return obj

    @classmethod
    def update_from_disco_message(cls, message):
        to_update = {
            'edited_timestamp': message.edited_timestamp,
            'edit_count': cls.edit_count + 1,
            'mentions': list(message.mentions.keys()),
        }

        if message.content is not UNSET:
            to_update['content'] = message.content
            to_update['emojis'] = [int(i) for i in EMOJI_RE.findall(message.content)]

        if message.attachments is not UNSET:
            to_update['attachments'] = [i.url for i in message.attachments.values()]

        if message.embeds is not UNSET:
            to_update['embeds'] = [json_dumps(i.to_dict()) for i in message.embeds]

        cls.update(**to_update).where(cls.message_id == message.id).execute()


class Reaction(BaseModel):
    class Meta:
        db_table = 'reactions'

        primary_key = peewee.CompositeKey('message_id', 'channel_id', 'user_id', 'emoji_id', 'emoji_name')

    message_id = peewee.BigIntegerField()
    channel_id = peewee.BigIntegerField()
    user_id = peewee.BigIntegerField()
    emoji_id = peewee.BigIntegerField(null=True)
    emoji_name = peewee.TextField()

    @classmethod
    def ensure_from_disco_reaction(cls, reaction):
        return cls.create(
            message_id=reaction.message_id,
            channel_id=reaction.channel_id,
            user_id=reaction.user_id,
            emoji_id=reaction.emoji.id or None,
            emoji_name=reaction.emoji.name,
        )
