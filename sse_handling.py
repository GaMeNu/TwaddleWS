import logging
from typing import *

from db_api import Database, User
from utils import is_valid_tag


class BaseSSEException(Exception):
    pass


class EventNotFoundException(BaseSSEException):
    pass

class Events:

    class Registry:
        events: dict[str, list[Callable]] = {}

        @classmethod
        def register(cls, name: str):
            def wrapper(coro: Callable):
                cls.add_handler(name, coro)
                return coro

            return wrapper

        @classmethod
        def add_handler(cls, name: str, coro: Callable):
            if cls.events.get(name) is None:
                cls.events[name] = []
            cls.events[name].append(coro)

        @classmethod
        def get(cls, name: str, index: int) -> Callable:
            return cls.events.get(name)[index]

        @classmethod
        def get_all(cls, name: str) -> list[Callable]:
            return cls.events.get(name)

    @classmethod
    def get_events(cls):
        return list(Events.Registry.events.keys())

    def __init__(self, ws):
        self.db = Database()
        self.ws: 'TwaddleWSServer' = ws

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

    @Registry.register("CREATE_USER")
    async def create_user(self, event: str, data: dict):
        if not is_valid_tag(data.get("usertag")):
            return Events._prepare_event_resp(event, False)

        res = self.db.register_user(
            data.get("firebase_uid"),
            data.get("usertag"),
            data.get("username")
        )

        if res is None:
            return Events._prepare_event_resp(event, False)
        return Events._prepare_event_resp(event, True, vars(res))

    @Registry.register("LOGIN_USER")
    async def login_user(self, event: str, data: dict):
        res = self.db.get_user_by_fuid(
            data.get("firebase_id")
        )

        if res is None:
            return Events._prepare_event_resp(event, False)
        return Events._prepare_event_resp(event, True, vars(res))

    @Registry.register("CREATE_USER_CHAT")
    async def create_user_chat(self, event: str, data: dict):
        user_tag = data.get("recv_user_tag")
        orig_user_id: int = data.get("orig_user_id")

        user: User = self.db.get_user_by_tag(user_tag)
        if user is None:
            return Events._prepare_event_resp(event, False)

        if user.user_id == orig_user_id:
            return Events._prepare_event_resp(event, False)

        if self.db.get_chat_by_users((orig_user_id, user.user_id)) is not None:
            return Events._prepare_event_resp(event, False)

        res = self.db.create_user_chat(orig_user_id, user.user_id)

        if res is None:
            return Events._prepare_event_resp(event, False)

        return self._prepare_event_resp(event, True, {
            "chat_id": res.chat_id,
            "name": res.name
        })

    @Registry.register("LOAD_USER_CHATS")
    async def load_user_chats(self, event: str, data: dict):
        user_id = data.get("user_id")

        res = self.db.load_user_chats(user_id)
        res.sort(key=lambda x: x.time_last_msg, reverse=True)
        print(res)
        res_srz = [chat.serialize() for chat in res]
        return self._prepare_event_resp(event, True, {
            "chats": res_srz
        })

    @Registry.register("LOAD_SINGLE_CHAT")
    async def load_single_chat(self, event: str, data: dict):
        chat_id = data.get("chat_id")

        msgs = self.db.get_chat_messages(chat_id)
        users = self.db.get_chat_users(chat_id)

        msgs_ls = [msg.serialize() for msg in msgs]
        users_ls = [user.serialize() for user in users]

        return self._prepare_event_resp(event, True, {
            "users": users_ls,
            "messages": msgs_ls
        })

    @Registry.register("UPDATE_DETAILS")
    async def update_details(self, event: str, data: dict):
        user_id = data.get("user_id")
        firebase_id = data.get("firebase_id")
        username = data.get("user_name")
        user_tag = data.get("user_tag")

        if not is_valid_tag(user_tag):
            return Events._prepare_event_resp(event, False)

        old_user = self.db.get_user(user_id)
        if old_user.user_tag != user_tag \
                and self.db.get_user_by_tag(user_tag) is not None:
            return self._prepare_event_resp(event, False)

        user_obj = User(
            user_id,
            firebase_id,
            user_tag,
            username
        )

        res = self.db.update_user(user_obj)

        return self._prepare_event_resp(event, res, user_obj.serialize())




class ServerSideEventHandler:

    def __init__(self, ws, handler: logging.Handler = None):
        self.log = logging.Logger("SSEH")
        if handler is not None:
            self.log.addHandler(handler)
        self.events = Events(ws)

    async def handle(self, received_data: dict):
        event = received_data.get("data").get("event")

        handler_ls: list[Callable] = self.events.Registry.get_all(event)
        print(handler_ls)

        self.log.info(f"Now handling event {event}")
        res_ls: list[dict] = []
        if handler_ls:
            for handler in handler_ls:
                res_ls.append(await handler(self=self.events, event=event, data=received_data.get("data").get("data")))
        else:
            raise EventNotFoundException(f"No handlers found for event {event}")

        if res_ls is not None:
            self.log.info("Sending response")
            return res_ls
