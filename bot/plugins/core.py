import pprint

from disco.api.http import APIException

from bot.plugins import command, listener

PY_CODE_BLOCK = u'```py\n{}\n```'


@command('ping', admin=True)
def cmd_ping(inst, event):
    event.msg.reply('Pong!')


@command('eval', admin=True)
def command_eval(inst, event):
    ctx = {
        'bot': inst.bot,
        'client': inst.bot.client,
        'state': inst.bot.state,
        'event': event,
        'inst': inst,
        'msg': event.msg,
        'guild': event.msg.guild,
        'channel': event.msg.channel,
        'author': event.msg.author
    }

    # Mulitline eval
    src = event.codeblock
    if src.count('\n'):
        lines = filter(bool, src.split('\n'))
        if lines[-1] and 'return' not in lines[-1]:
            lines[-1] = 'return ' + lines[-1]
        lines = '\n'.join('    ' + i for i in lines)
        code = 'def f():\n{}\nx = f()'.format(lines)
        local = {}

        try:
            exec compile(code, '<eval>', 'exec') in ctx, local
        except Exception as e:
            event.msg.reply(PY_CODE_BLOCK.format(type(e).__name__ + ': ' + str(e)))
            return

        result = pprint.pformat(local['x'])
    else:
        try:
            result = str(eval(src, ctx))
        except Exception as e:
            event.msg.reply(PY_CODE_BLOCK.format(type(e).__name__ + ': ' + str(e)))
            return

    if len(result) > 1990:
        event.msg.reply('', attachments=[('result.txt', result)])
    else:
        event.msg.reply(PY_CODE_BLOCK.format(result))


@command('status', group='carousel', admin=True)
def carousel_status(inst, event):
    event.msg.reply('Nodes: `{}`'.format(','.join(inst.bot.pool.nodes)))


@command('config', group='dbg', admin=True)
def dbg_config(inst, event):
    event.msg.reply('Config: ```{}```'.format(inst.config))


@listener('GuildConfigUpdate')
def on_config_update(inst, event):
    if inst.state.me.id not in inst.guild.members:
        print inst.state.me.id
        print inst.guild.members
        raise Exception('wot?')
    member = inst.guild.members[inst.state.me.id]
    if member and member.nick != inst.config['bot']['nickname']:
        try:
            member.set_nickname(inst.config['bot']['nickname'])
        except APIException:
            inst.log.exception('Failed to set nickname for guild')
