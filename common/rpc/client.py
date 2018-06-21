import gevent
import socket
import struct
import logging

from . import BaseRPC
from .msgpack import pack

log = logging.getLogger(__name__)


class RPCClient(BaseRPC):
    def __init__(self, on_payload, host, port):
        self.on_payload = on_payload
        self.host = host
        self.port = port

        self._connect()

    def _connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        gevent.spawn(self._handle_socket, self.socket)

    def _on_payload(self, sock, *args, **kwargs):
        try:
            self.on_payload(*args, **kwargs)
        except Exception:
            log.exception('Error when handling payload: ')

    def _on_socket_close(self, sock):
        self.socket = None
        self._connect()

    def send(self, op, data):
        packed = pack((op, data))
        self.socket.send(struct.pack('!I', len(packed)) + packed)
