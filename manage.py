#!/usr/bin/env python
from gevent import monkey

monkey.patch_all()  # noqa: E402

import logging
import click

from tabulate import tabulate


def _tabulate_model(rows, *fields):
    extracted_rows = []

    for row in rows:
        extracted_rows.append([getattr(row, field.lower().replace(' ', '_')) for field in fields])

    return tabulate(extracted_rows, headers=fields, tablefmt='psql')


@click.group()
@click.option('--env', default='dev')
@click.option('--config', default='config/rowboat.{env}.yaml')
@click.pass_context
def cli(ctx, env, config):
    from common.app_config import RowboatConfig
    from disco.util.logging import setup_logging
    setup_logging(level=logging.INFO)

    ctx.obj['config'] = RowboatConfig.from_file(config.format(env=env))
    ctx.obj['env'] = env


@cli.group()
def gateway():
    pass


@gateway.command('run')
@click.option('--shard-id', default=0)
@click.pass_context
def gateway_run(ctx, shard_id):
    from gateway.gateway import Gateway
    gateway = Gateway(ctx.obj['config'], shard_id)
    gateway.run()


@cli.group()
def bot():
    pass


@bot.command('run')
@click.option('--shard-count', default=1)
@click.option('--no-auto-acquire', is_flag=True)
@click.option('--max-resources', default=100)
@click.pass_context
def bot_run(ctx, shard_count, no_auto_acquire, max_resources):
    from bot.bot import Bot
    try:
        bot = Bot(shard_count, not no_auto_acquire, max_resources)
        bot.run(ctx.obj['config'])
    except KeyboardInterrupt:
        del bot


@cli.group()
def ctl():
    pass


@ctl.group()
def admins():
    pass


@admins.command('add')
@click.argument('user-id')
def ctl_admins_add(user_id):
    from common.models.user import User
    User.update(admin=True).where(
        (User.user_id == user_id)
    ).execute()


@admins.command('remove')
@click.argument('user-id')
def ctl_admins_remove(user_id):
    from common.models.user import User
    User.update(admin=False).where(
        (User.user_id == user_id)
    ).execute()


@admins.command('list')
def ctl_admins_list():
    from common.models.user import User
    users = list(User.select().where(
        (User.admin >> True)
    ))

    print _tabulate_model(users, 'User ID', 'Username', 'Discriminator')


@cli.group()
def web():
    pass


@web.command('run')
@click.option('--reloader/--no-reloader', '-r', default=False)
@click.pass_context
def web_run(ctx, reloader):
    import os
    from werkzeug.serving import run_with_reloader
    from gevent import wsgi
    from api.app import rowboat, initialize

    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    initialize(ctx.obj['config'])

    def run():
        wsgi.WSGIServer(('0.0.0.0', 45000), rowboat.app).serve_forever()

    if reloader:
        run_with_reloader(run)
    else:
        run()


@cli.command()
def shell():
    from api.app import rowboat

    namespace = {}

    try:
        from IPython.terminal.interactiveshell import TerminalInteractiveShell
        console = TerminalInteractiveShell(user_ns=namespace)
        print 'Starting iPython Shell'
    except ImportError:
        import code
        import rlcompleter
        c = rlcompleter.Completer(namespace)

        # Setup readline for autocomplete.
        try:
            # noinspection PyUnresolvedReferences
            import readline
            readline.set_completer(c.complete)
            readline.parse_and_bind('tab: complete')
            readline.parse_and_bind('set show-all-if-ambiguous on')
            readline.parse_and_bind('"\C-r": reverse-search-history')
            readline.parse_and_bind('"\C-s": forward-search-history')

        except ImportError:
            pass

        console = code.InteractiveConsole(namespace)
        print 'Starting Poverty Shell (install IPython to use improved shell)'

    with rowboat.app.app_context():
        console.interact()


if __name__ == '__main__':
    cli(obj={})
