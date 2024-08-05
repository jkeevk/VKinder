import requests
import json
from pprint import pprint


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


class VkApi(ApiBasic):
    host = 'https://api.vk.com/'

    def __init__(self, token):
        self.params = {
                        'access_token': token,
                        'v': '5.131'
                        }

    def get_user(self, user_id):
        """Получаем пользователя, используя унаследованный метод _send_request"""

        return self._send_request(http_method='GET',
                                  uri_path='method/users.get',
                                  params={'user_id': user_id,
                                          'name_case': 'gen',
                                          **self.params
                                          },
                                  response_type='json'
                                  )

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

        if len(all_foto) == 0:
            return "фотографии нет"
        elif len(all_foto) < 3:
            foto_count = len(all_foto)

        for i in all_foto['response']['items']:
            list_foto[i['id']] = {"url": i['sizes'][-1]['url'], "likes": i['likes']['count']}

        return sorted(list_foto.items(), key=lambda x: x[1]['likes'], reverse=True)[:foto_count]

if __name__ == '__main__':

    with open('token.json', 'r') as file:
        data_json = json.load(file)
        access_token = data_json["access_token"]
        user_id = data_json["user_id"]

    vk = VkApi(access_token)
    print(vk.get_user(user_id))

    all_foto = dict(vk.get_user_photos(user_id))
    pprint(vk.get_top3_likes(all_foto))
