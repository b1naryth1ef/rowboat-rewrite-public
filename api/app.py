from flask import Flask, g, session
from holster.flask_ext import Holster
from common.models.user import User
from api.lib.responses import APIError

rowboat = Holster(Flask(__name__))


def initialize(config):
    rowboat.app.secret_key = config.api.pop('SECRET_KEY', None)
    rowboat.app.config.update(config.api)


@rowboat.app.route('/api/ping')
def route_ping():
    return 'PONG'


@rowboat.app.before_request
def check_auth():
    g.user = None
    if 'user_id' in session:
        g.user = User.with_id(session['user_id'])


@rowboat.app.after_request
def save_auth(response):
    if g.user:
        session['user_id'] = g.user.user_id
    elif 'user_id' in session:
        del session['user_id']

    response.headers['Access-Control-Allow-Origin'] = '*'

    return response


@rowboat.app.errorhandler(APIError)
def on_api_error(inst):
    return inst.response
