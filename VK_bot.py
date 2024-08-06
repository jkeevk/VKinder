import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from VK_class import My_VkApi
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import json

def write_msg(user_id, message, keyboard=None):
    # Отправляем сообщение с опциональной клавиатурой
    vk.method('messages.send', {
        'user_id': user_id,
        'message': message,
        'random_id': 0,
        'keyboard': keyboard
    })

# Авторизуемся как сообщество
with open('token.json', 'r') as file:
    data_json = json.load(file)
    group_access_token = data_json["group_access_token"]

vk = vk_api.VkApi(token=group_access_token)

# Работа с сообщениями
longpoll = VkLongPoll(vk)

# Стартовая клавиатура
def start_buttons():
    keyboard = VkKeyboard(one_time=True)  # Создаем клавиатуру
    keyboard.add_button('Поиск пары', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('Правила', color=VkKeyboardColor.NEGATIVE)
    return keyboard.get_keyboard()

# Клавиатура во время поиска пары
def create_keyboard():
    keyboard = VkKeyboard(one_time=True)  # Создаем клавиатуру
    keyboard.add_button('Добавить в избранное', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('Пропустить', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()  
    keyboard.add_button('Добавить в Чёрный список', color=VkKeyboardColor.SECONDARY)
    keyboard.add_button('Просмотреть избранное', color=VkKeyboardColor.PRIMARY)
    return keyboard.get_keyboard()

# Основной цикл
for event in longpoll.listen():

    # Если пришло новое сообщение
    if event.type == VkEventType.MESSAGE_NEW:

        # Если оно имеет метку для меня (то есть бота)
        if event.to_me:
            vk_user = My_VkApi(group_access_token).get_user(event.user_id)
            print(vk_user, event.text)
            # Сообщение от пользователя
            request = event.text

            # Логика ответа
            if request.lower() == "поиск пары":
                write_msg(event.user_id, "Хай! Выбери одну из кнопок:", create_keyboard())
            elif request.lower() == "правила":
                write_msg(event.user_id, "Правила находятся в стадии разработки (Позже допишу инструкцию)", start_buttons())
            elif request.lower() == "пропустить":
                write_msg(event.user_id, "Вы пропустили эту запись (Придумать как скипнуть)", create_keyboard())
            elif request.lower() == "добавить в избранное":
                write_msg(event.user_id, "Запись добавлена в избранное (DB_editor.add_to_favourites)", create_keyboard())
            elif request.lower() == "добавить в чёрный список":
                write_msg(event.user_id, "Запись добавлена в чёрный список (DB_editor.add_to_black_list)", create_keyboard())
            elif request.lower() == "просмотреть избранное":
                write_msg(event.user_id, "Вот ваше избранное: [...] (DB_editor.get_favourites)", create_keyboard())
            else:
                write_msg(event.user_id, "Не поняла вашего ответа... Выбери одну из кнопок:", start_buttons())