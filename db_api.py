import datetime
import math
import os
from abc import abstractmethod
from typing import *
import psycopg2
from psycopg2 import errors as pgerr
from dotenv import load_dotenv


load_dotenv()

USERNAME = os.getenv("DB_USERNAME")
PASSWORD = os.getenv("DB_PASSWORD")


class ToDict:
    @abstractmethod
    def serialize(self):
        pass


class Chat:
    def __init__(self, chat_id: int, creation_time: int | datetime.datetime, name: str | None = None):
        self.chat_id = chat_id
        if isinstance(creation_time, datetime.datetime):
            self.creation_time = math.floor(creation_time.timestamp())
        else:
            self.creation_time = creation_time
        self.name = name

    @classmethod
    def from_tuple(cls, tup: tuple):
        return cls(*tup)


class Message(ToDict):
    def __init__(self,
                 message_id: int,
                 chat_id: int,
                 author_id: int,
                 time_sent: int,
                 content: str):
        self.message_id = message_id
        self.chat_id = chat_id
        self.author_id = author_id
        if isinstance(time_sent, datetime.datetime):
            self.time_sent = math.floor(time_sent.timestamp())
        else:
            self.time_sent = time_sent
        self.content = content

    @classmethod
    def from_tuple(cls, tup: tuple):
        return cls(*tup)

    def serialize(self):
        return self.__dict__


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
        if isinstance(time_last_msg, datetime.datetime):
            self.time_last_msg = math.floor(time_last_msg.timestamp())
        else:
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


class User(ToDict):

    def __init__(self,
                 user_id: int,
                 firebase_id: str,
                 user_tag: str,
                 user_name: str
                 ):
        self.user_id: int = user_id
        self.firebase_id: str = firebase_id
        self.user_tag: str = user_tag
        self.user_name: str = user_name

    @classmethod
    def from_tuple(cls, tup: Tuple):
        return cls(*tup)

    def serialize(self):
        return {
            "user_id": self.user_id,
            "firebase_id": self.firebase_id,
            "user_name": self.user_name,
            "user_tag": self.user_tag
        }


class Database:
    def __init__(self):
        self.connection = psycopg2.connect(
            dbname="twaddle_db",
            user=USERNAME,
            password=PASSWORD,
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

    def get_user(self, user_id: int):
        with self.connection.cursor() as crsr:
            crsr.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
            res = crsr.fetchone()
        return User.from_tuple(res)

    def get_chat(self, chat_id: int):
        with self.connection.cursor() as crsr:
            crsr.execute("SELECT * FROM chats WHERE chat_id = %s", (chat_id,))
            res = crsr.fetchone()
        return Chat.from_tuple(res)

    def get_user_by_fuid(self, fuid: str):
        with self.connection.cursor() as crsr:
            crsr.execute("SELECT * FROM users WHERE firebase_id = %s", (fuid,))
            res = crsr.fetchone()
        return User.from_tuple(res)

    def get_user_by_tag(self, usertag: str):
        with self.connection.cursor() as crsr:
            crsr.execute("SELECT * FROM users WHERE user_tag = %s;", (usertag,))
            print(crsr.query)
            res = crsr.fetchone()
        if res is None:
            return None

        print(res)

        return User.from_tuple(res)

    def get_chat_by_users(self, users: tuple[int, ...]) -> Chat | None:
        with self.connection.cursor() as crsr:
            crsr.execute("""SELECT chat_id
FROM chats_users
WHERE user_id IN %s
GROUP BY chat_id
HAVING COUNT(DISTINCT user_id) = %s;""", (users, len(users)))
            chat_id = crsr.fetchone()

            if chat_id is None:
                return None

            crsr.execute("SELECT * FROM chats WHERE chat_id = %s", (chat_id,))
            res = crsr.fetchone()

            return Chat.from_tuple(res)

    def get_chat_messages_tuples(self, chat_id: int) -> list[tuple]:
        with self.connection.cursor() as crsr:
            crsr.execute("""SELECT * 
FROM messages 
WHERE chat_id = %s 
ORDER BY time_sent DESC""",
                         (chat_id,))
            res = crsr.fetchall()
        return res

    def get_last_read_message_id(self, chat_id: int, user_id: int) -> int:
        with self.connection.cursor() as crsr:
            crsr.execute("""SELECT last_read_message 
FROM chats_users 
WHERE chat_id = %s 
AND user_id = %s""",
                         (chat_id, user_id))
            res = crsr.fetchone()

        if res is None:
            return 0
        return res[0]

    def get_display_chat(self, chat_id: int, user_id: int):
        """
        Prepare and return a DisplayChat for a chat ID, user ID
        :param chat_id: chat to prepare
        :param user_id: user to get POV of
        :return: prepared DisplayChat
        """

        # Get the name for the chat
        chat = self.get_chat(chat_id)

        name = chat.name

        # Get username of other user of chat, if chat is None.
        # Should only happen in userchats, where there are 2 users.
        if name is None:
            uids = self.get_chat_user_ids(chat_id)

            # We need to pop out the uids that aren't ours, should only occur once exactly but meh
            uids_new = [uid for uid in uids if uid != user_id]

            # aand set the name!
            name = self.get_user(uids_new[0]).user_name

        # We want to get the last message in the chat now, so we can get its data for the preview
        last_msg = self.get_last_message_in_chat(chat_id)

        # Set defaults if we failed to get our last message (non-existent, probably. Is a new chat?)
        if last_msg is None:
            message_id = 0
            content = ""
            time_sent = chat.creation_time
        else:
            message_id = last_msg.message_id
            content = last_msg.content[:64]  # I don't want huge previews.
            time_sent = last_msg.time_sent

        # Get last read ID
        lrm_id = self.get_last_read_message_id(chat_id, user_id)

        # Count unreads until the last READ message.
        unreads: int = 0
        if lrm_id != 0:
            msg_tups = self.get_chat_messages_tuples(chat_id)
            for tup in msg_tups:
                msg = Message.from_tuple(tup)
                if msg.message_id == lrm_id:
                    break
                unreads += 1

        return DisplayChat(chat_id, name, unreads, message_id, content, time_sent)

    def create_user_chat(self, user_id_1: int, user_id_2: int) -> Chat | None:
        try:
            with self.connection.cursor() as crsr:
                now = datetime.datetime.now(datetime.timezone.utc)

                crsr.execute("INSERT INTO chats (creation_time) VALUES (%s); "
                             "SELECT currval(pg_get_serial_sequence('chats', 'chat_id'));", (now,))

                chat_id = crsr.fetchone()

                crsr.execute("INSERT INTO chats_users (chat_id, user_id, join_time) VALUES (%s, %s, %s)",
                             (chat_id, user_id_1, now))
                crsr.execute("INSERT INTO chats_users (chat_id, user_id, join_time) VALUES (%s, %s, %s)",
                             (chat_id, user_id_2, now))

                self.connection.commit()

        except pgerr.UniqueViolation:
            return None

        with self.connection.cursor() as crsr:
            crsr.execute("SELECT * FROM chats WHERE chat_id = %s", (chat_id,))
            tup = crsr.fetchone()
            print(tup)
            res = Chat.from_tuple(tup)

        return res

    def get_user_chats(self, user_id: int):
        with self.connection.cursor() as crsr:
            crsr.execute("SELECT * FROM chats_users WHERE user_id = %s", (user_id,))
            res = crsr.fetchall()
        return res

    def get_chat_user_ids(self, chat_id: int) -> list[int]:
        with self.connection.cursor() as crsr:
            crsr.execute("SELECT user_id FROM chats_users WHERE chat_id = %s", (chat_id,))
            res = crsr.fetchall()

        return [val[0] for val in res]

    def get_last_message_in_chat(self, chat_id) -> Message | None:
        with self.connection.cursor() as crsr:
            crsr.execute("SELECT * "
                         "FROM messages "
                         "WHERE chat_id = %s "
                         "ORDER BY time_sent DESC "
                         "LIMIT 1",
                         (chat_id,))
            res = crsr.fetchone()

        if res is None:
            return None

        return Message.from_tuple(res)

    def get_group_name(self, chat_id: int):
        with self.connection.cursor() as crsr:
            crsr.execute("SELECT name FROM groupchats WHERE chat_id = %s", (chat_id,))
            res = crsr.fetchone()
        return res

    def load_user_chats(self, user_id: int):
        chats = self.get_user_chats(user_id)
        res = []
        for chat_tup in chats:
            res.append(self.get_display_chat(chat_tup[0], user_id))
        return res

    def get_chat_users(self, chat_id: int) -> list[User]:
        user_ids = self.get_chat_user_ids(chat_id)
        return [self.get_user(user_id) for user_id in user_ids]

    def get_chat_messages(self, chat_id: int) -> list[Message]:
        msgs = self.get_chat_messages_tuples(chat_id)
        return [Message.from_tuple(msg) for msg in msgs]

    def mark_chat_as_read(self, chat_id: int, user_id: int):
        msg = self.get_last_message_in_chat(chat_id)

        if msg is None:
            return

        with self.connection.cursor() as crsr:
            crsr.execute("""UPDATE chats_users 
SET last_read_message = %s 
WHERE chat_id = %s 
AND user_id = %s""",
                         (msg.message_id, chat_id, user_id))

        self.connection.commit()

    def create_new_message(self, chat_id: int, user_id: int, content: str):
        now = datetime.datetime.now()
        with self.connection.cursor() as crsr:
            crsr.execute("""INSERT INTO messages 
(chat_id, author_id, time_sent, content) 
VALUES (%s, %s, %s, %s);
SELECT currval(pg_get_serial_sequence('messages', 'message_id'));""",
                         (chat_id, user_id, now, content))
            res = crsr.fetchone()
            self.connection.commit()
        if res is None:
            return None
        return Message(
            res[0],
            chat_id,
            user_id,
            math.floor(now.timestamp()),
            content
        )


db = Database()
