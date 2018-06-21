import gevent

# from disco.bot.bot import Bot
from disco.bot.command import Command


def command(*args, **kwargs):
    def deco(func):
        if kwargs.pop('admin', False) is True:
            kwargs['level'] = -1
        func._cmd_obj = Command(func, *args, **kwargs)
        return func
    return deco


def listener(event):
    def deco(func):
        func._listener_data = (func, event)
        return func
    return deco


class FakeBot(object):
    def dispatch(self, _, command, event, **kwargs):
        command(event, **kwargs)

    @property
    def bot(self):
        return self

    def __init__(self):
        self.group_abbrev = {}


class Task(object):
    def __init__(self, func, restart=True, args=None, kwargs=None):
        self.func = func
        self.restart = restart

        self.args = args or tuple()
        self.kwargs = kwargs or dict()

        self._greenlet = None

    def on_exception(self, greenlet):
        try:
            self._greenlet.get()
        except Exception:
            self.log.exception('%s raised an exception:', self.func.__name__)

        if self.restart:
            self.run()

    def run(self):
        self._greenlet = gevent.spawn(self.func, *self.args, **self.kwargs)


def task(*args, **kwargs):
    def deco(func):
        func._task_obj = Task(func, *args, **kwargs)
        return func
    return deco
