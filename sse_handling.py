import logging
from typing import *

from db_api import Database


class BaseSSEException(Exception):
    pass


class EventNotFoundException(BaseSSEException):
    pass


class Events:

    class Registry:
        events = {}

        @classmethod
        def register(cls, name: str):
            def wrapper(coro: Callable):
                cls.events[name] = coro
                return coro

            return wrapper

        @classmethod
        def get(cls, name: str) -> Callable:
            return cls.events.get(name)

    @classmethod
    def get_events(cls):
        return list(Events.Registry.events.keys())

    def __init__(self):
        self.db = Database()

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
        orig_user_id = data.get("orig_user_id")

        user = self.db.get_user_by_tag(user_tag)
        print(user)
        if user is None:
            return Events._prepare_event_resp(event, False)

        if self.db.get_chat_by_users((orig_user_id, user.user_id)) is not None:
            return Events._prepare_event_resp(event, False)

        res = self.db.create_user_chat(orig_user_id, user.user_id)
        print(res)

        if res is None:
            return Events._prepare_event_resp(event, False)

        return self._prepare_event_resp(event, True, {
            "chat_id": res.chat_id,
            "name": res.name
        })

    @Registry.register("LOAD_USER_CHATS")
    async def load_user_chats(self, event: str, data: dict):
        user_id = data.get("user_id")
        print("data")

        res = self.db.load_user_chats(user_id)
        res_srz = [chat.serialize() for chat in res]
        return self._prepare_event_resp(event, True, {
            "chats": res_srz
        })


class ServerSideEventHandler:

    def __init__(self, handler: logging.Handler = None):
        self.log = logging.Logger("SSEH")
        if handler is not None:
            self.log.addHandler(handler)
        self.events = Events()

    async def handle(self, received_data: dict):
        event = received_data.get("data").get("event")

        handler: Callable = self.events.Registry.get(event)

        self.log.info(f"Now handling event {event}")

        if handler:
            res = await handler(self=self.events, event=event, data=received_data.get("data").get("data"))
        else:
            raise EventNotFoundException(f"No handler found for event {event}")

        if res is not None:
            self.log.info("Sending response")
            return res
