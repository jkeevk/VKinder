import psycopg2
import configparser


class DB_creator:
    """Класс для создания БД.

    Этот класс предназначен для работы с базой данных, включая
    создание ее схемы. Он обеспечивает методы для создания как
    самой базы данных, так и таблиц.

    Методы:
        get_settings: Читает данные из конфигурационного файла.
        create_database: Создает базу данных, если она не существует.
        create_tables: Создает необходимые таблицы для хранения данных.
        del_table: Удаление таблиц (для отладки)

    Примечания:
        Ключи хранятся в файле настроек settings.ini
    """

    def __init__(self, database: str) -> None:
        """
        Инициализация соединения с базой данных PostgreSQL.

        Параметры:
            database (str): Имя Базы Данных.

        Создает соединение с базой данных, настраивает курсор и
        устанавливает режим автокоммита для всех транзакций.
        """
        self.database = database
        database, user, password, host, port = DB_creator.get_settings()
        self.conn = psycopg2.connect(
            database=self.database, user=user, password=password, host=host, port=port
        )
        self.cur = self.conn.cursor()
        self.conn.autocommit = True

    def __enter__(self) -> None:
        """
        Позволяет использовать класс в качестве контекстного менеджера.

        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Закрывает курсор и соединение при выходе из контекстного менеджера.

        Параметры:
            exc_type (type): Тип исключения, возникшего в блоке with.
            exc_val (Exception): Значение исключения.
            exc_tb (traceback): Объект трассировки.
        """
        self.cur.close()
        self.conn.close()

    def get_settings(file_name: str = "settings.ini") -> tuple:
        """
        Читает данные из конфигурационного файла.

        Параметры:
            file_name (str): Имя файла конфигурации.

        Возвращает:
            tuple: Данные для подключения к БД
        """
        config = configparser.ConfigParser()
        config.read(file_name)
        database = config["SETTINGS"]["database"]
        user = config["SETTINGS"]["user"]
        password = config["SETTINGS"]["password"]
        host = config["SETTINGS"]["host"]
        port = config["SETTINGS"]["port"]
        return database, user, password, host, port

    def create_database(database: str) -> None:
        """
        Создает новую базу данных.

        Метод соединяется с базой данных 'postgres', создает новую базу данных и
        выводит сообщение об успешном создании. Если произошла ошибка, она будет выведена.
        """
        db, user, password, host, port = DB_creator.get_settings()
        try:
            conn = psycopg2.connect(
                database=db, user=user, password=password, host=host, port=port
            )
            cursor = conn.cursor()
            conn.autocommit = True

            cursor.execute(f"CREATE DATABASE {database};")
            print("Database has been created successfully")
            conn.close()
        except Exception as e:
            print(e)

    def create_tables(self) -> None:
        """
        Создает таблицы в базе данных, если они не существуют.
        Создает 4 таблицы: 'users', 'black_list', 'favourite_users' и 'favourites'. Метод выводит
        сообщение об успешном создании таблиц.
        """
        try:
            self.cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id SERIAL PRIMARY KEY,
                    age INTEGER NOT NULL,
                    CONSTRAINT age_limit CHECK (age < 100),
                    sex VARCHAR(1) CHECK (sex IN ('F', 'M')) NOT NULL,
                    city TEXT NOT NULL
                );
                """
            )

            self.cur.execute(
                """
                CREATE TABLE IF NOT EXISTS black_list (
                    black_list_id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(user_id),
                    black_list_user_id INTEGER NOT NULL
                );
                """
            )

            self.cur.execute(
                """
                CREATE TABLE IF NOT EXISTS favourite_users (
                    favourite_user_id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    last_name VARCHAR(255) NOT NULL,
                    url TEXT NOT NULL,
                    attachments TEXT[]
                );
                """
            )

            self.cur.execute(
                """
                CREATE TABLE IF NOT EXISTS favourites (
                    favourite_id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(user_id),
                    favourite_user_id INTEGER NOT NULL REFERENCES favourite_users(favourite_user_id)
                );
                """
            )

            print("Tables have been created successfully")

        except Exception as e:
            print(f"Error creating tables: {e}")

    def del_table(self) -> None:
        """
        Удаляет таблицы из базы данных.

        Этот метод в первую очередь удаляет таблицы в следующем порядке:
        favourites, favourite_users, black_list, users.
        Это необходимо для того, чтобы избежать ошибок внешнего ключа.
        """
        try:
            self.cur.execute(
                """
                DROP TABLE IF EXISTS favourites CASCADE;
                DROP TABLE IF EXISTS favourite_users CASCADE;
                DROP TABLE IF EXISTS black_list CASCADE;
                DROP TABLE IF EXISTS users CASCADE;
                """
            )
            self.conn.commit()  # Применить изменения
            print("Tables have been deleted successfully")
        except Exception as e:
            print(f"Error deleting tables: {e}")


if __name__ == "__main__":
    database = "vkinder"
    DB_creator.create_database(database)  # создаём базу данных
    with DB_creator(database) as db:
        print(
            "Status OK" if db.conn.closed == 0 else "Connection is closed"
        )
        db.del_table()  # удаляем таблицы
        db.create_tables()  # создаём таблицы

        print("Completed!")
    print(
        "Connection is closed"
        if db.conn.closed == 1
        else "Close connection!"
    )