import requests
import json
from pprint import pprint
import datetime
import time
import random


class HttpException(Exception):
    """Класс исключения, выбрасываем, когда API возвращает ошибку."""

    def __init__(self, status: int, message: str = ""):
        self.status = status
        self.message = message

    def __str__(self) -> str:
        return f"http error: {self.status}\n{self.message}"


class ApiBasic:
    """Базовый класс API, от него будут наследоваться Клиент VK."""

    host = ""

    def _send_request(
        self,
        http_method: str,
        uri_path: str,
        params: dict = None,
        json: dict = None,
        response_type: str = None
    ) -> dict | Exception:
        """
        Метод для отправки всех запросов к API.

        Обрабатывает исключения, логирует запросы и т.д.

        Параметры:
            http_method (str): Метод запроса (GET/POST/PUT/PATCH/DELETE).
            uri_path (str): URI API, например, method/users.get.
            params (dict): Параметры запроса.
            json (dict): Данные в формате JSON для отправки.
            response_type (dict): Тип ответа (например, json).

        Возвращаемое значение:
            Ответ от API в формате словаря или Exception в случае ошибки.
        """
        response = requests.request(
            http_method,
            f"{self.host}/{uri_path}",
            params=params,
            json=json
        )  # отправляем запрос
        if response.status_code >= 400:
            # если с сервера приходит ошибка, выбрасываем исключение
            raise HttpException(response.status_code, response.text)
        if response_type == "json":
            response = response.json()
            return response


class My_VkApi(ApiBasic):
    host = "https://api.vk.com/"

    def __init__(self, token: str):
        """
        Инициализация клиента VK с токеном доступа.

        Параметры:
            token: Токен доступа для авторизации в API.
        """
        self.params = {"access_token": token, "v": "5.199"}
        self.user_token = token

    def get_user_info(self, user_id: int) -> dict:
        """
        Получает полную информацию о пользователе по его идентификатору.

        Параметры:
            user_id (int): Идентификатор пользователя.

        Возвращаемое значение:
            Словарь с информацией о пользователе (имя, фамилия, город, возраст, пол).
        """
        user_info = dict()
        user_info_resp = self._send_request(
            http_method="GET",
            uri_path="method/users.get",
            params={"user_id": user_id, "fields": "city, sex, bdate", **self.params},
            response_type="json",
        )

        # Если у пользователя скрыт возраст или год рождения, то берем его по умолчанию
        try:
            user_city = user_info_resp["response"][0]["city"]["title"]
            user_city_id = user_info_resp["response"][0]["city"]["id"]
        except:
            print("Город неизвестен")
            user_city = "Неизвестен"
            user_city_id = 0
        try:
            age_user = datetime.datetime.now().year - int(
                user_info_resp["response"][0]["bdate"].split(".")[2]
            )
        except:
            print("Возраст неизвестен, по умолчанию 18")
            age_user = 18

        user_info[user_id] = {
            "name": user_info_resp["response"][0]["first_name"],
            "lastname": user_info_resp["response"][0]["last_name"],
            "city": user_city,
            "city_id": user_city_id,
            "age": age_user,
            "sex": "Женский" if user_info_resp["response"][0]["sex"] == 1 else "Мужской"
                   if user_info_resp["response"][0]["sex"] == 2 else "Неизвестный",
        }
        return user_info

    def get_short_user_info(self, user_id: int) -> str:
        """
        Получает короткую информацию о пользователе.

        Параметры:
            user_id (int): Идентификатор пользователя.

        Возвращаемое значение:
            Строка, содержащая имя и фамилию пользователя.
        """
        response = self._send_request(
            http_method="GET",
            uri_path="method/users.get",
            params={"user_id": user_id, **self.params},
            response_type="json",
        )
        return f"{response['response'][0]['first_name']} {response['response'][0]['last_name']}"

    def get_user_photos(self, user_id: int) -> dict:
        """
        Получает все фотографии пользователя.

        Параметры:
            user_id (int): Идентификатор пользователя.

        Возвращаемое значение:
            Словарь с информацией о фотографиях пользователя.
        """
        return self._send_request(
            http_method="GET",
            uri_path="method/photos.get",
            params={
                "owner_id": user_id,
                "album_id": "profile",
                "extended": "1",
                **self.params,
            },
            response_type="json",
        )
    # Поиск пользователей по параметрам на выходе список идентификаторов пользователей
    def search_users(self, sex: int, age_from: int, age_to: int, city_id: int) -> list:
        """Получает список идентификаторов пользователей в зависимости от заданных параметров.

        Параметры:
            sex (int): Пол искомых пользователей (1 - женский, 2 - мужской, 0 - не указывать).
            age_from (int): Минимальный возраст пользователей.
            age_to (int): Максимальный возраст пользователей.
            city (str): Город, в котором должны находиться искомые пользователи.

        Возвращаемое значение:
            Список идентификаторов найденных пользователей.
        """
        all_fined_users_id = []
        all_fined_users = self._send_request(
            http_method="GET",
            uri_path="method/users.search",
            params={
                "sort": 1,  # Параметр, отвечающий за сортировку результатов. Значение `1` означает, что результаты сортируются по релевантности.
                "sex": sex,  # Пол искомых пользователей. `1` — женский, `2` — мужской, `0` — не указывать пол.
                "status": 1,  # Семейное положение. Значение `1` означает, что пользователи должны быть "неженаты" (то есть, ищем тех, кто свободен)
                "age_from": age_from,  # Минимальный возраст пользователей (например, `18`).
                "age_to": age_to,  # Максимальный возраст пользователей (например, `30`).
                "has_photo": 1,  # Указывает, должны ли искомые пользователи иметь фотографии.
                "count": 100,  # Количество возвращаемых результатов.
                "online": 1,  # Указывает, должны ли пользователи быть онлайн.
                "city": city_id,  # id города, в котором должны находиться искомые пользователи.
                **self.params,
            },
            response_type="json",
        )
        for user in all_fined_users["response"]["items"]:
            all_fined_users_id.append(user["id"])
        random.shuffle(all_fined_users_id)

        return all_fined_users_id

    def find_users_photos(self, find_users: dict) -> list[list[str]]:
        """Получает топ 3 фото пользователей по количеству лайков.

        Параметры:
            find_users (dict): Словарь с информацией о найденных пользователях.

        Возвращаемое значение:
            Список, где каждый элемент - информация о пользователе (имя, фамилия, ссылка, топ 3 фото).
        """

        all_persons = []

        for element in find_users["response"]["items"]:
            time.sleep(0.2)
            all_foto = dict(
                self.get_user_photos(element["id"])
            )  # Получаем все фото пользователя

            person = [
                element["first_name"],
                element["last_name"],
                "https://vk.com/id" + str(element["id"]),
                get_top3_likes(all_foto),  # Получаем топ 3 фото по количеству лайков
            ]
            all_persons.append(person)

        return all_persons

    # функция поиска города
    def search_city(self, city: str) -> str:
        """
        Ищет город по названию.

        Параметры:
            city (str): Название города для поиска.

        Возвращаемое значение:
            Название найденного города или сообщение о том, что город не найден.
        """
        found_city = self._send_request(
            http_method="GET",
            uri_path="method/database.getCities",
            params={"q": city, "need_all": 0, "count": 1, **self.params},
            response_type="json",
        )
        if found_city["response"]["count"] == 0:
            return "Город не найден"
        else:
            return found_city["response"]["items"][0]["title"]

    def search_city_by_id(self, city_id: int) -> str:
        """
        Ищет город по id.

        Параметры:
            city_id (int): id города для поиска.

        Возвращаемое значение:
            Название найденного города или сообщение о том, что город не найден.
        """
        found_city = self._send_request(
            http_method="GET",
            uri_path="method/database.getCitiesById",
            params={"city_ids": city_id, **self.params},
            response_type="json",
        )

        if not found_city["response"][0]["title"]:
            return "Город не найден"
        else:
            return found_city["response"][0]["title"]


def get_top3_likes(all_foto: dict) -> str:
    """
    Возвращает топ 3 фото по количеству лайков из списка всех фото пользователя.

    Параметры:
        all_foto (dict): Словарь с информацией о всех фотографиях пользователя.

    Возвращаемое значение:
        Строка с идентификаторами топ 3 фото или сообщение о том, что фотографии отсутствуют.
    """
    foto_count = 3
    list_foto = list()

    if all_foto["response"]["count"] == 0:
        return "фотографии нет"
    elif all_foto["response"]["count"] < 3:
        foto_count = all_foto["response"]["count"]

    for i in all_foto["response"]["items"]:
        list_foto.append(f'photo{i["owner_id"]}_{i["id"]}')

    return " ,".join(sorted(list_foto, key=lambda x: x[1], reverse=True)[:foto_count])


if __name__ == '__main__':

    with open('token.json', 'r') as file:
        data_json = json.load(file)
        group_access_token = data_json["access_token"]
        user_id = data_json["user_id"]
        user_token = data_json["access_token"]

    # search_city = 'Ярославль'
    # found_city = My_VkApi(group_access_token).search_city(search_city)
    # print(found_city)

    vk_user_info = My_VkApi(user_token).get_user_info(user_id)
    pprint(vk_user_info)
    sex = 1 if vk_user_info[user_id]['sex'] == 'Женский' else 2
    age_from = vk_user_info[user_id]["age"] - 5
    age_to = vk_user_info[user_id]["age"] + 5
    city_id = vk_user_info[user_id]['city_id']
    pprint(My_VkApi(user_token).search_users(sex, age_from, age_to, city_id))
