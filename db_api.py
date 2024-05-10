import datetime
from abc import abstractmethod
from typing import *

import psycopg2
from psycopg2 import errors as pgerr


class ToDict:
    @abstractmethod
    def serialize(self):
        pass


class Chat:
    def __init__(self, chat_id: int, creation_time: int):
        self.chat_id = chat_id
        self.creation_time = creation_time

    @classmethod
    def from_tuple(cls, tup: tuple):
        return cls(*tup)


class DisplayChat(ToDict):
    def __init__(
            self,
            chat_id: int,
            name: str,
            unreads: int,
            last_message: int,
            last_msg_preview: str,
            time_last_msg: int
    ):
        self.chat_id = chat_id
        self.name = name
        self.unreads = unreads
        self.last_message = last_message
        self.last_msg_preview = last_msg_preview
        self.time_last_msg = time_last_msg

    def serialize(self):
        return {
            "chat_id": self.chat_id,
            "name": self.name,
            "unreads": self.unreads,
            "last_message": self.last_message,
            "last_msg_preview": self.last_msg_preview,
            "time_last_msg": self.time_last_msg
        }


class User:

    def __init__(self,
                 user_id: int,
                 firebase_id: str,
                 user_tag: str,
                 user_name: str
                 ):
        self.user_id = user_id
        self.firebase_id = firebase_id
        self.user_tag = user_tag
        self.user_name = user_name

    @classmethod
    def from_tuple(cls, tup: Tuple):
        return cls(*tup)






class Database:
    def __init__(self):
        self.connection = psycopg2.connect(
            dbname="twaddle_db",
            user="twaddle_gateway",
            password="password",
            host="localhost",
            port=5432
        )   

    def register_user(self, firebase_id: str, user_tag: str, user_name: str) -> User | None:
        try:
            with self.connection.cursor() as crsr:
                crsr.execute("INSERT INTO users (firebase_id, user_tag, user_name) VALUES (%s, %s, %s)",
                             (firebase_id, user_tag, user_name))
            self.connection.commit()

        except pgerr.UniqueViolation:
            return None

        return self.get_user_by_fuid(firebase_id)

    def get_user_by_fuid(self, fuid: str):
        with self.connection.cursor() as crsr:
            crsr.execute("SELECT * FROM users WHERE firebase_id = %s", (fuid,))
            res = crsr.fetchone()
        return User.from_tuple(res)

    def get_user_by_tag(self, usertag: str):
        with self.connection.cursor() as crsr:
            crsr.execute("SELECT * FROM users WHERE user_tag = %s", (usertag,))
            res = crsr.fetchone()
        return User.from_tuple(res)

    def create_user_chat(self, user_id_1: int, user_id_2: int) -> Chat | None:
        try:
            with self.connection.cursor() as crsr:
                crsr.execute("INSERT INTO chats (creation_time) VALUES (%s)", (datetime.datetime.now().timestamp(),))
                chat_id = crsr.fetchone()[0]

                now = datetime.datetime.now()
                crsr.execute("INSERT INTO chats_users (chat_id, user_id, join_time) VALUES (%s, %s, %s)",
                             (chat_id, user_id_1, now))
                crsr.execute("INSERT INTO chats_users (chat_id, user_id, join_time) VALUES (%s, %s, %s)",
                             (chat_id, user_id_2, now))

                self.connection.commit()

        except pgerr.UniqueViolation:
            return None

        with self.connection.cursor() as crsr:
            crsr.execute("SELECT * FROM chats WHERE chat_id = %s", (chat_id,))
            res = Chat.from_tuple(crsr.fetchone())

        return res

    def get_user_chats(self, user_id: int):
        with self.connection.cursor() as crsr:
            crsr.execute("SELECT * FROM chats_users WHERE user_id = %s", (user_id,))
            res = crsr.fetchall()
        return res


    def load_user_chats(self, user_id: int):
        chats = self.get_user_chats(user_id)


db = Database()