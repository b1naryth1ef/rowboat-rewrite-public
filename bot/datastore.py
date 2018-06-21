import logging
from holster.emitter import Priority

from common.models.message import Message, Reaction

log = logging.getLogger(__name__)


class Datastore(object):
    def __init__(self, bot):
        self.bot = bot

    def init(self):
        events = self.bot.client.events

        events.on('MessageCreate', self.on_message_create, priority=Priority.BEFORE)
        events.on('MessageDelete', self.on_message_delete, priority=Priority.BEFORE)
        events.on('MessageUpdate', self.on_message_update, priority=Priority.BEFORE)
        events.on('MessageDeleteBulk', self.on_message_delete_bulk, priority=Priority.BEFORE)
        events.on('MessageReactionAdd', self.on_message_reaction_add, priority=Priority.BEFORE)
        events.on('MessageReactionRemove', self.on_message_reaction_remove, priority=Priority.BEFORE)
        events.on('MessageReactionRemoveAll', self.on_message_reaction_remove_all, priority=Priority.BEFORE)

    def on_message_create(self, event):
        try:
            Message.ensure_from_disco_message(event.message)
        except Exception:
            log.exception('Failed to insert disco message:')

    def on_message_update(self, event):
        Message.update_from_disco_message(event.message)

    def on_message_delete(self, event):
        Message.update(deleted=True).where(
            (Message.channel_id == event.channel_id) &
            (Message.message_id == event.id)
        ).execute()

    def on_message_delete_bulk(self, event):
        Message.update(deleted=True).where(
            (Message.channel_id == event.channel_id) &
            (Message.id << event.ids)
        ).execute()

    def on_message_reaction_add(self, event):
        Reaction.ensure_from_disco_reaction(event)

    def on_message_reaction_remove(self, event):
        Reaction.delete().where(
            (Reaction.message_id == event.message_id) &
            (Reaction.channel_id == event.channel_id) &
            (Reaction.user_id == event.user_id) &
            (Reaction.emoji_id == (event.emoji.id or None)) &
            (Reaction.emoji_name == event.emoji.name)
        ).execute()

    def on_message_reaction_remove_all(self, event):
        Reaction.delete().where(
            (Reaction.message_id == event.message_id) &
            (Reaction.channel_id == event.channel_id)
        ).execute()
