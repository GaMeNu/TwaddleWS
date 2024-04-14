import psycopg2
from psycopg2 import errors as pgerr
class Database:
    def __init__(self):
        self.connection = psycopg2.connect(
            dbname="twaddle_db",
            user="twaddle_gateway",
            password="password",
            host="localhost",
            port=5432
        )   

    def register_user(self, firebase_id: str, user_tag: str, user_name: str):
        try:
            with self.connection.cursor() as crsr:
                crsr.execute("INSERT INTO users (firebase_id, user_tag, user_name) VALUES (%s, %s, %s)",
                             (firebase_id, user_tag, user_name))
            self.connection.commit()
        except pgerr.UniqueViolation:
            raise


db = Database()