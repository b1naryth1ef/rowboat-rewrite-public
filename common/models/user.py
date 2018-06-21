import peewee
from common.models import BaseModel


class User(BaseModel):
    class Meta:
        db_table = 'users'

    user_id = peewee.BigIntegerField(primary_key=True)
    username = peewee.TextField()
    discriminator = peewee.SmallIntegerField()
    avatar = peewee.TextField(null=True)
    bot = peewee.BooleanField()

    admin = peewee.BooleanField(default=False)

    @classmethod
    def with_id(cls, user_id):
        try:
            return cls.select().where(cls.user_id == user_id).get()
        except cls.DoesNotExist:
            return None

    @classmethod
    def ensure_from_disco_user(cls, user):
        try:
            User.create(
                user_id=user.id,
                username=user.username,
                discriminator=user.discriminator,
                avatar=user.avatar,
                bot=user.bot,
            )
        except Exception:
            # TODO(az) scope this ^
            User.update(
                username=user.username,
                discriminator=user.discriminator,
                avatar=user.avatar,
                bot=user.bot
            ).where(
                (User.user_id == user.id)
            ).execute()

    def to_dict(self, me=True):
        obj = {
            'id': str(self.user_id),
            'username': self.username,
            'discriminator': self.discriminator,
            'avatar': self.avatar,
            'bot': self.bot,
        }

        if me:
            obj['admin'] = self.admin

        return obj
