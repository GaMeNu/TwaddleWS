import json
import logging
from tornado import httputil
from typing import *

import tornado
import tornado.websocket

from db_api import Message
from sse_handling import ServerSideEventHandler, Events

"""
OPCODES GUIDE
-------------

"""
stream_handler = logging.StreamHandler()
LOGGER = logging.Logger('TwaddleLogger')
LOGGER.addHandler(stream_handler)
app_log = logging.getLogger('tornado.application')
logging.getLogger('tornado.application').addHandler(stream_handler)


class WSEvents:
    registry = Events.Registry

    @staticmethod
    def _prepare_event_resp(event: str,
                            success: bool,
                            data: dict | None = None
                            ):
        resp = {
            "op": 1,
            "data": {
                "e": event,
                "s": success,
            }
        }
        if data is not None:
            resp_data: dict = resp["data"]
            resp_data["data"] = data

        return resp

    def __init__(self, ws):
        self.ws: TwaddleWSServer = ws
        self.db = self.ws.handler.events.db

    @registry.register("LOGIN_USER")
    async def login_set_active(self, event: str, data: dict):
        user = self.db.get_user_by_fuid(data.get("firebase_id"))
        self.ws.set_active(user.user_id)
        print(TwaddleWSServer.active_sockets)

    @registry.register("LOAD_SINGLE_CHAT")
    async def sc_mark_read(self, event: str, data: dict):
        chat_id = data.get("chat_id")
        self.db.mark_chat_as_read(chat_id, self.ws.user_id)

    @registry.register("SEND_CHAT_MESSAGE")
    async def send_chat_message(self, event: str, data: dict):
        chat_id = int(data.get("chat_id"))
        user_id = self.ws.user_id
        content = data.get("content")
        msg = self.db.create_new_message(chat_id, user_id, content)
        if msg is None:
            return self._prepare_event_resp(event, False)
        users = self.db.get_chat_user_ids(chat_id)
        users.remove(user_id)

        await self.ws.send_new_message(msg, tuple(users))

        self.db.mark_chat_as_read(chat_id, user_id)

        return self._prepare_event_resp(event, True, msg.serialize())


class TwaddleWSServer(tornado.websocket.WebSocketHandler):

    # key = userID, value = Server instance.
    active_sockets: dict[str, 'TwaddleWSServer'] = {}

    def set_active(self, user_id: int) -> None:
        self.active_sockets[str(user_id)] = self
        self.user_id = user_id

    def remove_active(self, user_id: int) -> None:
        self.active_sockets.pop(str(user_id))

    @classmethod
    def get_active_socket(cls, user_id: int) -> 'TwaddleWSServer':
        return cls.active_sockets.get(str(user_id))

    def __init__(self, application: tornado.web.Application, request: httputil.HTTPServerRequest, **kwargs: Any):
        super().__init__(application, request, **kwargs)
        self.handler = ServerSideEventHandler(self)
        self.events = WSEvents(self)
        self.user_id: int = 0

    @property
    def active_sockets_key(self) -> str:
        if self.user_id == 0:
            return ""
        return str(self.user_id)

    def open(self, *args: str, **kwargs: str):
        LOGGER.info("New connection established!")

    async def on_message(self, message: Union[str, bytes]):
        print(f"Received data:\n{message}")

        data = json.loads(message)
        if data.get("op") == 1:
            res_ls = await self.handler.handle(data)
            for res in res_ls:
                if res is None:
                    continue

                print("SENDING")
                print(res)
                await self.write_message(json.dumps(res))

    @staticmethod
    async def send_new_message(msg: Message, users: tuple[int]):
        msg_srz = msg.serialize()
        for user in users:
            instance = TwaddleWSServer.get_active_socket(user)
            if instance is None:
                continue
            await instance.write_message(json.dumps({
                "op": 2,
                "data": msg_srz
            }))

    def on_close(self) -> None:
        if self.active_sockets_key is not None and self.active_sockets.get(self.active_sockets_key) is not None:
            self.active_sockets.pop(self.active_sockets_key, None)
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
    app.listen(port=port, address=ip)

    LOGGER.info(f"Started server! Listening on\nws://{ip}:{port}/")
    LOGGER.info(f"Loaded EVENTS: {Events.get_events()}")

    ioloop = tornado.ioloop.IOLoop.current()
    ioloop.start()

    return app

