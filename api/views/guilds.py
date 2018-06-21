import functools

from flask import Blueprint, g, request
from common.models.guild import Guild, GuildConfig
from common.config.guild import GuildConfigObject
from api.lib.decorators import authed
from api.lib.responses import APIResponse, APIError

guilds = Blueprint('guilds', __name__, url_prefix='/api/guilds')


def guild_route(edit=False, admin=False):
    def deco(f):
        @authed
        @functools.wraps(f)
        def func(*args, **kwargs):
            guild = Guild.with_id(kwargs.pop('guild_id'))
            if not guild:
                return APIError('Unknown Guild', 404)

            if g.user.admin or g.user.user_id == guild.owner_id:
                return f(guild)

            is_viewer = g.user.user_id in guild.web_viewers
            is_editor = g.user.user_id in guild.web_editors
            is_admin = g.user.user_id in guild.web_admins

            if not is_viewer and not is_editor and not is_admin:
                return APIError('Unknown Guild', 404)

            return f(guild)
        return func
    return deco


@guilds.route('/')
@authed
def guilds_list():
    if g.user.admin:
        return APIResponse([i.to_dict() for i in Guild.select()])

    return APIResponse([
        i.to_dict() for i in Guild.select().where(
            (Guild.web_viewers.contains(g.user.user_id)) |
            (Guild.web_editors.contains(g.user.user_id)) |
            (Guild.web_admins.contains(g.user.user_id))
        )
    ])


@guilds.route('/<guild_id>')
@guild_route()
def guilds_get(guild):
    return APIResponse(guild)


@guilds.route('/<guild_id>/config', methods=['GET'])
@guild_route()
def guilds_get_config(guild):
    config = GuildConfig.with_id(guild.config_id)
    if not config:
        return APIResponse({})
    return APIResponse(config)


@guilds.route('/<guild_id>/config', methods=['POST'])
@guild_route(edit=True)
def guilds_update_config(guild):
    previous_config_id = request.json.get('previous_config_id', None)

    try:
        contents = request.json['contents']
        config = GuildConfigObject(contents)
    except Exception as e:
        raise APIError('Configuration Error: {}'.format(e))

    can_edit_users = (
        g.user.admin or
        g.user.user_id == guild.owner_id or
        g.user.user_id in guild.web_admins
    )

    users_changed = (
        set(guild.web_viewers) != set(config.web.viewers) or
        set(guild.web_editors) != set(config.web.editors) or
        set(guild.web_admins) != set(config.web.admins)
    )

    if not can_edit_users and users_changed:
        raise APIError('Invalid Permissions')

    # non admins / guild owners cannot remove themselves from the config
    if not g.user.admin and not g.user.user_id == guild.owner_id:
        if g.user.user_id in guild.web_admins and g.user.user_id not in config.web.admins:
            raise APIError('You cannot remove yourself')

    success, new_config = guild.update_config(config, previous_config_id)
    if not success:
        raise APIError('Invalid previous config, is someone else editing the config?')

    if users_changed:
        Guild.update(
            web_viewers=list(set(config.web.viewers)),
            web_editors=list(set(config.web.editors)),
            web_admins=list(set(config.web.admins)),
        ).where(
            (Guild.guild_id == guild.guild_id)
        ).execute()

    return APIResponse(new_config)
