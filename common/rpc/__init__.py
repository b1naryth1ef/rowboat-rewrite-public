import socket
import struct

from .msgpack import unpack

HEADER_SIZE = struct.calcsize('!I')


class BaseRPC(object):
    def _on_socket_close(self, sock):
        raise NotImplementedError

    def _handle_socket(self, sock):
        buff = ''

        while True:
            try:
                payload = sock.recv(4096)
                if not payload:
                    self._on_socket_close(sock)
                    return
            except socket.error:
                self._on_socket_close(sock)
                return

            buff += payload

            if len(buff) < HEADER_SIZE:
                continue

            size = struct.unpack('!I', buff[:HEADER_SIZE])[0]
            if len(buff[HEADER_SIZE:]) < size:
                continue

            self._on_payload(sock, *unpack(buff[HEADER_SIZE:HEADER_SIZE + size]))
            buff = buff[HEADER_SIZE + size:]
