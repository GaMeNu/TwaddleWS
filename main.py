import asyncio
import json
import logging
import socket
import websockets
from websockets import server
from typing import *

import tornado
import tornado.websocket

from sse_handling import ServerSideEventHandler

from db_api import Database

##########
# CONFIG #
##########
IP = socket.gethostbyname(socket.gethostname())
PORT = 8888


"""
OPCODES GUIDE
-------------

"""
stream_handler = logging.StreamHandler()
LOGGER = logging.Logger('TwaddleLogger')
LOGGER.addHandler(stream_handler)
app_log = logging.getLogger('tornado.application')
logging.getLogger('tornado.application').addHandler(stream_handler)


class Events:

    handler = ServerSideEventHandler()

    def __init__(self):
        self.db = Database()
        print(self.handler.handlers)

    @handler.event("CREATE_USER")
    async def create_user(self, data: dict):
        self.db.register_user(
            data.get("firebase_uid"),
            data.get("usertag"),
            data.get("username")
        )


class TwaddleWSServer(tornado.websocket.WebSocketHandler):

    # key = userID, value = Server instance.
    active_sockets = {}
    events = Events()

    def open(self, *args: str, **kwargs: str):
        LOGGER.info("New connection established!")

    async def on_message(self, message: Union[str, bytes]):
        print(f"Received data:\n{message}")
        await self.write_message(f"Confirmed.\n{message}")

        data = json.loads(message)
        if data.get("op") == 1:
            await self.events.handler.handle(cname=self.events, received_data=data)

    def on_close(self) -> None:
        print("Web socket closed.")

    def on_ping(self, data: bytes) -> None:
        print(f"Ping called: {data.decode()}")

    def on_pong(self, data: bytes) -> None:
        print(f"Ping response received: {data.decode()}")


def main(port: int, ip: str):
    app = tornado.web.Application(
        [
            ("/", TwaddleWSServer)
        ],
        websocket_ping_interval=20,
        websocket_ping_timeout=120
    )
    app.listen(port=PORT, address=IP)

    print(f"{ip}:{port}")

    LOGGER.debug(f"Started server! Listening on ws://{ip}:{port}/")

    ioloop = tornado.ioloop.IOLoop.current()
    ioloop.start()


# def create_socket_server(ip, port) -> socket.socket:
#     server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     try:
#         server_socket.bind((ip, port))
#         server_socket.listen()
#     except socket.error:
#         server_socket.close()
#         server_socket = None
#         raise
#
#     print(f"Server socket created! {server_socket.getsockname()[0]}:{server_socket.getsockname()[1]}")
#     return server_socket
#
#
# async def recv_listener():
#     print(f"Connecting on {IP}:{PORT}")
#     server_socket = create_socket_server(IP, PORT)
#     client_socket, address = server_socket.accept()
#     print(f"Connected! Client: {address[0]}:{address[1]}")
#     while True:
#         data = client_socket.recv(4096)
#         if data:
#             print("data: " + data.decode('utf_8'))

# async def handler(ws: server.WebSocketServerProtocol):
#     print(f"Connected! Client: {ws.local_address[0]}:{ws.local_address[1]}")
#     while True:
#         msg = await ws.recv()
#         print(msg)
#
#
# async def main():
#     async with server.serve(handler, IP, PORT) as srvr:
#         print(f"Started server on {srvr.sockets[0].getsockname()[0]}:{srvr.sockets[0].getsockname()[1]}")
#         await asyncio.Future()

if __name__ == "__main__":
    main(PORT, IP)
