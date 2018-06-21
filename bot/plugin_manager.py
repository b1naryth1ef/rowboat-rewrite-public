import os
import importlib
import re
import logging
import gevent
import functools

from disco.bot.command import CommandEvent

from common.models.user import User

log = logging.getLogger(__name__)


class PluginManager(object):
    def __init__(self, bot):
        self.bot = bot
        self.commands = []
        self.listeners = []
        self.tasks = []
        self.group_abbrev = {}

        self.command_matches_re = None

        self._load()

    def on_message_create(self, event):
        if event.author.id == self.bot.client.state.me.id:
            return

        guild_state = self.bot.guild_state.get(event.guild.id)
        if not guild_state:
            return

        content = event.content

        # TODO: pull from config
        prefix = '!'
        if prefix and not content.startswith(prefix):
            return []
        else:
            content = content[len(prefix):]

        if not self.command_matches_re.match(content):
            return []

        options = []
        for command in self.commands:
            match = command.compiled_regex(self.group_abbrev).match(content)
            if match:
                options.append((command, match))
        options = sorted(options, key=lambda obj: obj[0].group is None)
        if not options:
            return

        user = None
        for command, match in options:
            # If this is an admin command, check if the user is an admin
            if command.level == -1:
                if not user:
                    user = User.with_id(event.author.id)

                if not user or not user.admin:
                    log.warning('User attempted to execute admin-only command %s (%s)', command.name, event.author.id)
                    continue

            # TODO: permissions
            (command_event, kwargs) = command.execute(CommandEvent(command, event.message, match))
            gevent.spawn(command.func, guild_state, command_event, **kwargs)

    def init(self):
        self.bot.client.events.on('MessageCreate', self.on_message_create)

        self._load_commands()
        self._load_listeners()

        # TODO: load tasks

    def _load_commands(self):
        re_str = ''
        for command in self.commands:
            re_str += '|' + command.regex(self.group_abbrev, grouped=False)
        self.command_matches_re = re.compile(re_str, re.I)

    def _load_listeners(self):
        def fn(func, event):
            if hasattr(event, 'guild_id'):
                guild_state = self.bot.guild_state.get(event.guild_id)
            elif hasattr(event, 'guild') and event.guild:
                guild_state = self.bot.guild_state.get(event.guild.id)
            else:
                log.warning('Unhandled event due to lack of Guild metadata: %s', event)
                return

            # TODO: plugin limiting

            return func(guild_state, event)

        for (func, event) in self.listeners:
            self.bot.client.events.on(
                event, functools.partial(fn, func)
            )

    def _load(self):
        plugin_names = []
        for root, dirs, files in os.walk('bot/plugins/'):
            for file_name in files:
                if file_name.startswith('_'):
                        continue
                plugin_names.append(file_name.rsplit('.', 1)[0])

        for module_name in plugin_names:
            log.info('Loading plugin %s', module_name)
            module = importlib.import_module('bot.plugins.{}'.format(
                module_name
            ))

            for variable in map(lambda i: getattr(module, i), dir(module)):
                if hasattr(variable, '_cmd_obj'):
                    self.commands.append(variable._cmd_obj)
                elif hasattr(variable, '_task_obj'):
                    self.tasks.append(variable._task_obj)
                elif hasattr(variable, '_listener_data'):
                    self.listeners.append(variable._listener_data)
