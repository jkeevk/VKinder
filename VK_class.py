import requests
import json
from pprint import pprint

import vk_api


class HttpException(Exception):
    """Класс исключения, выбрасываем, когда API возвращает ошибку"""

    def __init__(self, status, message=''):
        self.status = status
        self.message = message

    def __str__(self):
        return f'http error: {self.status}\n{self.message}'


class ApiBasic:
    """Базовый класс API от него будут наследоваться Клиент VK"""

    host = ''

    def _send_request(self, http_method, uri_path, params=None, json=None, response_type=None):

        """Через этот метод будут отправляться все запросы ко всем API.
          Здесь мы можем обратывать любые исключения, логирвать запросы и т.п.

          :param http_method: GET/POST/PUT/PATCH/DELETE
          :param uri_path: uri API, например method/users.get
          :param params:
          :param json:
          :param response_type: тип ответа, например json
          :return:
        """

        response = requests.request(http_method, f'{self.host}/{uri_path}', params=params, json=json)  # отправляем запрос
        if response.status_code >= 400:
        # если с сервера приходит ошибка выбрасываем исключение
            raise HttpException(response.status_code, response.text)
        if response_type == 'json':
            response = response.json()
            return response


class My_VkApi(ApiBasic):
    host = 'https://api.vk.com/'

    def __init__(self, token):
        self.params = {
                        'access_token': token,
                        'v': '5.199'
                        }

    def get_user(self, user_id):
        """Получаем пользователя, используя унаследованный метод _send_request"""
        user_info = dict()
        user_info_resp = self._send_request(http_method='GET',
                                  uri_path='method/users.get',
                                  params={'user_id': user_id,
                                          'fields': 'city, sex, bdate',
                                          **self.params
                                          },
                                  response_type='json'
                                  )
        user_info[user_id] = {"name": user_info_resp['response'][0]['first_name'],
                              "lastname": user_info_resp['response'][0]['last_name'],
                              "city": user_info_resp['response'][0]['city']['title'],
                              "bdate": user_info_resp['response'][0]['bdate'],
                              "sex": 'Женский' if user_info_resp['response'][0]['sex'] == 1 else 'Мужской'
                              if user_info_resp['response'][0]['sex'] == 2 else 'Неизвестный'
                              }
        return user_info

    def get_user_photos(self, user_id):
        return self._send_request(http_method='GET',
                                  uri_path='method/photos.get',
                                  params={'owner_id': user_id,
                                          'album_id': 'profile',
                                          'extended': '1',
                                          **self.params
                                          },
                                  response_type='json'
                                  )

    def get_top3_likes(self, all_foto: dict):
        foto_count = 3
        list_foto = dict()

        if all_foto['response']['count'] == 0:
            return "фотографии нет"
        elif all_foto['response']['count'] < 3:
            foto_count = all_foto['response']['count']

        for i in all_foto['response']['items']:
            list_foto[i['id']] = {"url": i['sizes'][-1]['url'], "likes": i['likes']['count']}

        return sorted(list_foto.items(), key=lambda x: x[1]['likes'], reverse=True)[:foto_count]
    
    def search_users(self, sex, age_from, age_to, city):
        all_persons = []
        link_profile = 'https://vk.com/id'
        vk_ = vk_api.VkApi(token=user_token)
        response = vk_.method('users.search',
                            {'sort': 1, # Параметр, отвечающий за сортировку результатов. Значение `1` означает, что результаты сортируются по релевантности.
                            'sex': sex, # Пол искомых пользователей. `1` — женский, `2` — мужской, `0` — не указывать пол.
                            'status': 1, # Семейное положение. Значение `1` означает, что пользователи должны быть "неженаты" (то есть, ищем тех, кто свободен)
                            'age_from': age_from, # Минимальный возраст пользователей (например, `18`).
                            'age_to': age_to, # Максимальный возраст пользователей (например, `30`).
                            'has_photo': 1, # Указывает, должны ли искомые пользователи иметь фотографии. Значение `1` ищет пользователей с фото.
                            'count': 3, # Количество возвращаемых результатов (например, `3` — возвращать 3 пользователей).
                            'online': 1, # Указывает, должны ли пользователи быть онлайн в данный момент. Значение `1` ищет только тех, кто в сети.
                            'hometown': city # Город, в котором должны находиться искомые пользователи (например, название города).
                            })
        for element in response['items']:
            all_foto = dict(vk.get_user_photos(element['id'])) # Получаем все фото пользователя
            person = [
                element['first_name'],
                element['last_name'],
                link_profile + str(element['id']),
                vk.get_top3_likes(all_foto) # Получаем топ 3 фото по количеству лайков
            ]
            all_persons.append(person)
        return all_persons

if __name__ == '__main__':

    with open('token.json', 'r') as file:
        data_json = json.load(file)
        group_access_token = data_json["access_token"]
        user_id = data_json["user_id"]
        user_token = data_json["access_token"]

    vk = My_VkApi(group_access_token)
    vk_user = vk.get_user(user_id)
    pprint(vk_user)

    # all_foto = dict(vk.get_user_photos(user_id))
    # pprint(vk.get_top3_likes(all_foto))
    # pprint(all_foto)


    sex = 1 # женский
    age_from = 18
    age_to = 50
    city = vk_user[user_id]['city'] # город нашего пользователя

    pprint(vk.search_users(sex, age_from, age_to, city))