import psycopg2
import configparser
from typing import List, Optional


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
        Настройки подключения хранятся в файле settings.ini
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

    def create_database(database: str = "vkinder") -> None:
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
                    user_id INT PRIMARY KEY,
                    age INTEGER NOT NULL,
                    CONSTRAINT age_limit CHECK (age < 100),
                    sex VARCHAR(1) CHECK (sex IN ('1', '2')) NOT NULL,
                    city TEXT NOT NULL
                );
                """
            )

            self.cur.execute(
                """
                CREATE TABLE IF NOT EXISTS black_list (
                    black_list_id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(user_id),
                    black_list_user_id INTEGER NOT NULL,
                    UNIQUE (user_id, black_list_user_id) 
                );
                """
            )

            self.cur.execute(
                """
                CREATE TABLE IF NOT EXISTS favourite_users (
                    favourite_user_id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    last_name VARCHAR(255) NOT NULL,
                    url TEXT NOT NULL UNIQUE,
                    attachments TEXT[]
                );
                """
            )

            self.cur.execute(
                """
                CREATE TABLE IF NOT EXISTS favourites (
                    favourite_id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(user_id),
                    favourite_user_id INTEGER NOT NULL REFERENCES favourite_users(favourite_user_id),
                    UNIQUE (user_id, favourite_user_id) 
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


class DB_editor:
    """Класс для работы с базой данных.

    Этот класс предназначен для работы с базой данных. Он
    предоставляет методы для регистрации пользователей, управления
    черными списками и избранными пользователями.

    Методы:
        register_user: Создает запись о пользователе в таблице users.
        add_to_black_list: Добавляет пользователя в черный список.
        add_to_favourites: Добавляет пользователя в избранное.
        get_favourites: Возвращает список избранных пользователей для указанного пользователя.
        get_black_list_user_id: Получает список идентификаторов пользователей из черного списка для данного пользователя.
        get_user_city: Получает город пользователя.
        update_user_city: Обновляет город пользователя.

    Примечания:
        Настройки подключения хранятся в файле settings.ini
    """

    def __init__(self, database: str = "vkinder") -> None:
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

    def register_user(self, user_id: int, age: int, sex: int, city: str) -> None:
        """
        Создает запись о пользователе в таблице users.

        Параметры:
            user_id (int): Уникальный идентификатор пользователя в VK.
            age (int): Возраст пользователя.
            sex (int): Пол пользователя (1 или 2).
            city (str): Город пользователя.
        """
        try:
            self.cur.execute(
                """
            INSERT INTO users(user_id, age, sex, city) 
            VALUES(%s, %s, %s, %s)
            ON CONFLICT (user_id) DO NOTHING;
            """,
                (user_id, age, sex, city),
            )
        except Exception as e:
            print(e)

    def add_to_black_list(self, user_id: int, black_list_user_id: int) -> None:
        """
        Добавляет пользователя в черный список.

        Параметры:
            user_id (int): Уникальный идентификатор основного пользователя.
            black_list_user_id (int): Уникальный идентификатор пользователя,
            которого необходимо добавить в черный список.
        """
        try:
            self.cur.execute(
                """
            INSERT INTO black_list(user_id, black_list_user_id) 
            VALUES(%s, %s)
            ON CONFLICT (user_id, black_list_user_id) DO NOTHING;
            """,
                (user_id, black_list_user_id),
            )
        except Exception as e:
            print(e)

    def add_to_favourites(
        self,
        user_id: int,
        name: str,
        last_name: str,
        url: str,
        attachments: Optional[List[str]],
    ) -> None:
        """
        Добавляет пользователя в избранное.

        Параметры:
            user_id (int): Уникальный идентификатор основного пользователя.
            name (str): Имя избранного пользователя.
            last_name (str): Фамилия избранного пользователя.
            url (str): URL профиля избранного пользователя.
            attachments (Optional[List[str]]): Список вложений (3 ссылки на фотографии).
        """
        try:
            self.cur.execute(
                """
            INSERT INTO favourite_users(name, last_name, url, attachments) 
            VALUES(%s, %s, %s, %s)
            ON CONFLICT (url) DO NOTHING;
            """,
                (name, last_name, str(url), attachments if attachments else None),
            )

            # Получаем id последнего добавленного или существующего.favorite_user_id
            self.cur.execute(
                "SELECT favourite_user_id FROM favourite_users WHERE url = %s",
                (str(url),),
            )

            favourite_user_id = self.cur.fetchone()

            if (
                favourite_user_id
            ):  # Если пользователь был успешно добавлен или уже существует
                favourite_user_id = favourite_user_id[0]  # Извлекаем id
                # Теперь добавляем запись в таблицу favourites
                self.cur.execute(
                    """
                INSERT INTO favourites(user_id, favourite_user_id) 
                VALUES(%s, %s)
                ON CONFLICT (user_id, favourite_user_id) DO NOTHING;
                """,
                    (user_id, str(favourite_user_id)),
                )
            else:
                print("Error fetching favourite user ID.")

        except Exception as e:
            print(e)

    def get_favourites(self, user_id: int) -> Optional[List[dict]]:
        """
        Возвращает список избранных пользователей для указанного пользователя.

        Параметры:
            user_id (int): Уникальный идентификатор пользователя, для которого требуется получить список избранных.

        Возвращаемое значение:
            Optional[List[dict]]: Список словарей, каждый из которых содержит
            имя (`name`), фамилию (`last_name`) и URL (`url`) избранного пользователя,
            или None в случае ошибки.
        """
        try:
            self.cur.execute(
                """
            SELECT name, last_name, url
            FROM favourite_users
            JOIN favourites ON favourite_users.favourite_user_id = favourites.favourite_user_id
            WHERE user_id = %s
            """,
                (user_id,),
            )

            # Преобразуем результат в список словарей для удобства
            result = self.cur.fetchall()
            return [
                {"name": row[0], "last_name": row[1], "url": str(row[2])}
                for row in result
            ]

        except Exception as e:
            print(f"Error fetching favourites: {e}")
            return None

    def get_user_city(self, user_id: int) -> str:
        """
        Получает город пользователя.

        Параметры:
            user_id (int): Идентификатор пользователя.

        Возвращаемое значение:
            Название города пользователя или None в случае ошибки.
        """
        try:
            self.cur.execute(
                """
                SELECT city
                FROM users
                WHERE user_id = %s
                """,
                (user_id,),
            )
            result = self.cur.fetchone()
            return result[0] if result else None  # Проверка на наличие результата
        except Exception as e:
            print(f"Error fetching user city: {e}")
            return None

    def update_user_city(self, user_id: int, city: str) -> None:
        """
        Обновляет город пользователя.

        Параметры:
            user_id (int): Идентификатор пользователя.

        Возвращаемое значение:
            Новое название города, которое будет сохранено.
        """
        try:
            self.cur.execute(
                """
            UPDATE users
            SET city = %s
            WHERE user_id = %s;
            """,
                (city, user_id),
            )
            self.cur.connection.commit()
        except Exception as e:
            print(f"Error updating user city: {e}")

    def get_black_list_user_id(self, user_id: int) -> list[int] | None:
        """
        Получает список идентификаторов пользователей из черного списка для данного пользователя.

        Параметры:
            user_id (int): Идентификатор пользователя.

        Возвращаемое значение:
            Список идентификаторов черного списка или None в случае ошибки.
        """
        try:
            self.cur.execute(
                """
            SELECT black_list_user_id
            FROM black_list
            WHERE user_id = %s
            """,
                (user_id,),
            )
            # Преобразуем результат в список
            return [row[0] for row in self.cur.fetchall()]

        except Exception as e:
            print(f"Error fetching black list: {e}")
            return None


def test_create_db():
    """
    Для отлатки класса DB_creator
    """
    DB_creator.create_database(database)  # создаём базу данных
    with DB_creator(database) as db:
        print("Status OK" if db.conn.closed == 0 else "Connection is closed")
        db.del_table()  # удаляем таблицы
        db.create_tables()  # создаём таблицы

        print("Completed!")
    print("Connection is closed" if db.conn.closed == 1 else "Close connection!")


def test_edit_db():
    """
    Для отлатки класса DB_editor
    """
    # данные нашего пользователя (получает бот)
    vk_id = 1
    vk_user_city = "Санкт-Петербург"
    vk_user_sex = 2
    vk_user_age = 32
    vk_user = DB_editor(database)

    # создаём запись в базе данных
    vk_user.register_user(vk_id, vk_user_age, vk_user_sex, vk_user_city)

    # добавляем в черный список id пользователя
    black_list_user_id = 999
    vk_user.add_to_black_list(vk_id, black_list_user_id)
    black_list_user_id = 1337
    vk_user.add_to_black_list(vk_id, black_list_user_id)
    # добавляем в избранное
    name = "Понравившаяся"
    last_name = "Персона"
    url = "vk.com/id777777"
    attachments = ["url_1, url_2, url_3"]
    vk_user.add_to_favourites(vk_id, name, last_name, url, attachments)

    name = "Другая"
    last_name = "Персона"
    url = "vk.com/id88888"
    attachments = ["url_1, url_2, url_3"]
    vk_user.add_to_favourites(vk_id, name, last_name, url, attachments)

    name = "Третья"
    last_name = "Персона"
    url = "vk.com/id999"
    attachments = ["url_1, url_2, url_3"]
    vk_user.add_to_favourites(vk_id, name, last_name, url, attachments)

    print(vk_user.get_favourites(vk_id))


if __name__ == "__main__":
    database = "vkinder"
    test_create_db()
    test_edit_db()
    
