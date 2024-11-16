import sqlite3
import logging

LOGGER = logging.Logger(__name__)
LOGGER.setLevel(logging.INFO)


class Database:
    def __init__(self, database_file: str = 'database.db') -> None:
        self.database_file = database_file
        self.conn = None
        self.cursor = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close_connection()

    def connect(self):
        try:
            self.conn = sqlite3.connect(self.database_file)
            self.cursor = self.conn.cursor()
            LOGGER.info("Connected to database")
        except sqlite3.Error as e:
            LOGGER.critical(f'Connection failed with error: {e}')

    def execute_query(self, query, params=None):
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchall()
        except sqlite3.Error as error:
            LOGGER.error("Error executing the query:", error)
            return None

    def commit_changes(self):
        try:
            self.conn.commit()
        except sqlite3.Error as error:
            LOGGER.error("Error committing the changes:", error)

    def close_connection(self):
        try:
            if self.cursor is not None:
                self.cursor.close()
            if self.conn is not None:
                self.conn.close()
            LOGGER.info("SQLite connection is closed.")
        except sqlite3.Error as error:
            LOGGER.error("Error closing the SQLite connection:", error)

    def close_connection(self):
        try:
            if self.cursor is not None:
                self.cursor.close()
            if self.conn is not None:
                self.conn.close()
            LOGGER.info("SQLite connection is closed.")
        except sqlite3.Error as error:
            LOGGER.error("Error closing the SQLite connection:", error)

    def create_database(self):
        try:
            self.connect()
            LOGGER.info(
                f"Database '{self.database_file}' created successfully.")
        except sqlite3.Error as e:
            LOGGER.error("Error creating the database:", e)

    def create_table(self, table_name, columns):
        try:
            self.connect()
            query = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"
            self.cursor.execute(query)
            self.conn.commit()
            LOGGER.info(f"Table '{table_name}' created successfully.")
        except sqlite3.Error as e:
            LOGGER.error("Error creating the table:", e)
