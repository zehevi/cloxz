import psycopg
import logging

LOGGER = logging.Logger()


class Database:
    """
    A class to interact with a PostgreSQL database.

    Attributes:
        host (str): The hostname or IP address of the PostgreSQL server.
        database (str): The name of the database to connect to.
        user (str): The username to use for the database connection.
        password (str): The password to use for the database connection.
        conn (psycopg.Connection): The connection to the PostgreSQL database.
    """

    def __init__(self, host: str = 'localhost', database: str = 'mydb', user: str = 'admin', password: str = 'password') -> None:
        """
        Initializes a new instance of the PostgresDB class.

        Args:
            host (str, optional): The hostname or IP address of the PostgreSQL server. Defaults to 'localhost'.
            database (str, optional): The name of the database to connect to. Defaults to 'mydb'.
            user (str, optional): The username to use for the database connection. Defaults to 'admin'.
            password (str, optional): The password to use for the database connection. Defaults to 'password'.
        """
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.conn = None

    def __enter__(self):
        """
        Enters the context manager, connecting to the PostgreSQL database.

        Returns:
            PostgresDB: The current instance of the PostgresDB class.
        """
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Exits the context manager, closing the connection to the PostgreSQL database.

        Args:
            exc_type (type): The type of the exception, if any.
            exc_value (Exception): The exception instance, if any.
            traceback (TracebackType): The traceback of the exception, if any.
        """
        self.close_connection()

    def connect(self):
        """
        Connects to the PostgreSQL database.
        """
        try:
            self.conn = psycopg.connect(
                host=self.host, database=self.database, user=self.user, password=self.password)
            LOGGER.info("Connected to database")
        except (psycopg.errors.ConnectionException, psycopg.errors.ConnectionFailure, psycopg.errors.ConnectionTimeout) as e:
            LOGGER.critical(f'Connection failed with error: {e}')

    def execute_query(self, query, params=None):
        """
        Executes a SQL query and returns the results.

        Args:
            query (str): The SQL query to execute.
            params (tuple, optional): The parameters to pass to the query.

        Returns:
            list of tuples: The results of the SQL query.
        """
        try:
            with self.conn.cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                return cursor.fetchall()
        except (Exception, psycopg.Error) as error:
            LOGGER.error("Error executing the query:", error)
            return None

    def commit_changes(self):
        """
        Commits any changes made to the database.
        """
        try:
            self.conn.commit()
        except (Exception, psycopg.Error) as error:
            LOGGER.error("Error committing the changes:", error)

    def close_connection(self):
        """
        Closes the connection to the PostgreSQL database.
        """
        try:
            if self.conn is not None:
                self.conn.close()
            LOGGER.info("PostgreSQL connection is closed.")
        except (Exception, psycopg.Error) as error:
            LOGGER.error("Error closing the PostgreSQL connection:", error)

    def create_database(self, database_name):
        """
        Creates a new PostgreSQL database if it doesn't already exist.

        Args:
            database_name (str): The name of the database to create.
        """
        try:
            with psycopg.connect(
                host=self.host, database='postgres', user=self.user, password=self.password
            ) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT 1 FROM pg_database WHERE datname = %s", (database_name,))
                    if not cursor.fetchone():
                        cursor.execute(f"CREATE DATABASE {database_name}")
                        conn.commit()
                        LOGGER.info(
                            f"Database '{database_name}' created successfully.")
                    else:
                        LOGGER.warning(
                            f"Database '{database_name}' already exists.")
        except (Exception, psycopg.Error) as error:
            LOGGER.error("Error creating the database:", error)

    def create_table(self, table_name, columns):
        """
        Creates a new PostgreSQL table if it doesn't already exist.

        Args:
            table_name (str): The name of the table to create.
            columns (list of str): A list of column definitions for the table.
        """
        try:
            with self:
                with self.conn.cursor() as cursor:
                    query = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"
                    cursor.execute(query)
                    self.conn.commit()
                    LOGGER.info(f"Table '{table_name}' created successfully.")
        except (Exception, psycopg.Error) as error:
            LOGGER.error("Error creating the table:", error)
