import sqlite3
import logging

LOGGER = logging.Logger(__name__)
LOGGER.setLevel(logging.CRITICAL)


class Database:
    def __init__(self, database_file: str = "database.db") -> None:
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
            LOGGER.critical(f"Connection failed with error: {e}")

    def execute_query(self, query: str, params: tuple = None):
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
            LOGGER.info(f"Database '{self.database_file}' created successfully.")
        except sqlite3.Error as e:
            LOGGER.error("Error creating the database:", e)

    def create_table(self, table_name: str, columns: list) -> bool:
        try:
            self.connect()
            query = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"
            self.cursor.execute(query)
            self.conn.commit()
            LOGGER.info(f"Table '{table_name}' created successfully.")
            return True
        except sqlite3.Error as e:
            LOGGER.error("Error creating the table:", e)
            return False

    def delete_table(self, table_name: str) -> bool:
        try:
            self.connect()
            query = f"DROP TABLE {table_name}"
            self.cursor.execute(query)
            self.conn.commit()
            LOGGER.info(f"Table [{table_name}] dropped")
            return True
        except sqlite3.Error as e:
            LOGGER.error("Error dropping the table:", e)
            return False

    def insert_row(self, table_name: str, data: list | tuple) -> None:
        try:
            self.connect()
            query = f"INSERT INTO {table_name} VALUES ({','.join(['?'] * len(data))})"
            self.cursor.execute(query, data)
            self.conn.commit()
            LOGGER.info(f"Row inserted into table '{table_name}'")
        except sqlite3.Error as e:
            LOGGER.error(f"Error inserting row into table '{table_name}': {e}")

    def delete_row(self, table_name: str, where_clause: str, params: tuple = ()) -> None:
        try:
            self.connect()
            query = f"DELETE FROM {table_name} WHERE {where_clause}"
            self.cursor.execute(query, params)
            self.conn.commit()
            LOGGER.info(f"Row deleted from table '{table_name}'")
        except sqlite3.Error as e:
            LOGGER.error(f"Error deleting row from table '{table_name}': {e}")

    def read_all_rows(self, table_name: str) -> list | None:
        try:
            self.connect()
            query = f"SELECT * FROM {table_name} ORDER BY date, time"
            self.cursor.execute(query)
            rows = self.cursor.fetchall()
            LOGGER.info(f"Read {len(rows)} rows from table '{table_name}'")
            return rows
        except sqlite3.Error as e:
            LOGGER.error(f"Error reading rows from table '{table_name}': {e}")
            return None

    def get_all_tables(self) -> list:
        try:
            self.connect()
            query = "SELECT name FROM sqlite_master WHERE type='table';"
            self.cursor.execute(query)
            rows = self.cursor.fetchall()
            LOGGER.info(f"Read {len(rows)} tables from database")
            return rows
        except sqlite3.Error as e:
            LOGGER.error(f"Error reading from sqlite_master", e)
            return []
