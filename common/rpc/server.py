import struct
import gevent

from gevent.server import StreamServer
from . import BaseRPC
from .msgpack import pack


class RPCServer(BaseRPC):
    def __init__(self, on_payload, on_close=None, host='localhost'):
        self.server = StreamServer((host, 0), self._handle_connection)
        self.server.start()
        gevent.spawn(self.server.serve_forever)

        self.on_payload = on_payload
        self.on_close = on_close

    def _on_payload(self, *args, **kwargs):
        gevent.spawn(self.on_payload, *args, **kwargs)

    def _handle_connection(self, sock, addr):
        self._handle_socket(sock)

    def _on_socket_close(self, sock):
        if self.on_close:
            self.on_close(sock)

    def send_to(self, socket, op, data):
        packed = pack((op, data))
        socket.send(struct.pack('!I', len(packed)) + packed)

    @property
    def port(self):
        return self.server.socket.getsockname()[1]
