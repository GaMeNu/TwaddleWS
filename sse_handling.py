from typing import *


class BaseSSEException(Exception):
    pass


class EventNotFoundException(BaseSSEException):
    pass


class ServerSideEventHandler:

    def __init__(self):
        self.handlers = {}

    def event(self, name: str) -> callable:
        def wrapper(coro: Coroutine):
            self.handlers[name] = coro
            return coro
        return wrapper

    def set_handler(self, name: str, coro: Coroutine):
        self.handlers[name] = coro

    async def handle(self, cname, received_data: dict):
        event = received_data.get("data").get("event")

        handler: Callable = self.handlers.get(event)


        print(received_data.get("data").get("data"))
        print(handler.__name__)

        if handler:
            print(received_data)
            await handler(self=cname, data=received_data.get("data").get("data"))
        else:
            raise EventNotFoundException(f"No handler found for event {event}")
