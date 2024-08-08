import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from VK_class import My_VkApi
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import json
from db_tools import DB_creator, DB_editor


def write_msg(user_id, message, keyboard=None, attachment=None):
    # Отправляем сообщение с опциональной клавиатурой
    vk.method('messages.send', {
        'user_id': user_id,
        'message': message,
        'random_id': 0,
        'keyboard': keyboard,
        'attachment': attachment
    })


# Авторизуемся как сообщество
with open('token.json', 'r') as file:
    data_json = json.load(file)
    group_access_token = data_json["group_access_token"]
    user_token = data_json["access_token"]

    

vk = vk_api.VkApi(token=group_access_token)

# Работа с сообщениями
longpoll = VkLongPoll(vk)
print('Bot is running')


# Стартовая клавиатура
def start_buttons():
    keyboard = VkKeyboard(one_time=True)  # Создаем клавиатуру
    keyboard.add_button('Поиск пары', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('Правила', color=VkKeyboardColor.PRIMARY)
    return keyboard.get_keyboard()


# Клавиатура во время поиска пары
def create_keyboard():
    keyboard = VkKeyboard(one_time=True)  # Создаем клавиатуру
    keyboard.add_button('Добавить в избранное', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('Пропустить', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()  
    keyboard.add_button('Добавить в Чёрный список', color=VkKeyboardColor.SECONDARY)
    keyboard.add_button('Просмотреть избранное', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('Вернуться в главное меню', color=VkKeyboardColor.PRIMARY)

    return keyboard.get_keyboard()

# Основной цикл
for event in longpoll.listen():    

    # Если пришло новое сообщение
    if event.type == VkEventType.MESSAGE_NEW:

        # Если оно имеет метку для меня (то есть бота)
        if event.to_me:
            vk_user = My_VkApi(group_access_token).get_user_info(event.user_id)
            sex_user = vk_user[event.user_id]['sex']
            age_user = vk_user[event.user_id]['age']
            sex = 2 if sex_user == 'Женский' else 1  # выбираем противоположный пол
            age_from = age_user - 10
            age_to = age_user + 5
            city = vk_user[event.user_id]['city']

            # создаём запись в базе данных
            vk_user_id = next(iter(vk_user))
            vk_user_sex = 2 if sex_user == 'Женский' else 1
            vk_user_db = DB_editor()
            vk_user_db.register_user(vk_user_id, age_user, vk_user_sex, city)
            
            # Сообщение от пользователя
            request = event.text

            # Поиск людей
            find_users = My_VkApi(user_token).search_users(sex, age_from, age_to, city)
            find_photos = My_VkApi(user_token).find_users_photos(find_users)
            target_name = find_photos[0][0]
            target_last_name = find_photos[0][1]
            target_url = find_photos[0][2]
            target_attachments = [item for item in find_photos[0][3]]

            # Логика ответа
            if request.lower() == "поиск пары":
                write_msg(event.user_id, f'{target_name} {target_last_name}')
                write_msg(event.user_id, target_url)
                write_msg(event.user_id, '',attachment=f'{",".join(target_attachments)}')
                write_msg(event.user_id, "Выбери одну из кнопок:", create_keyboard())
            elif request.lower() == "правила":
                instructions = (
                            "Привет! Я бот, который поможет вам найти людей для знакомства в социальной сети ВКонтакте 🥰\n\n"
                            "1. **Поиск пары**: Нажмите на кнопку «Поиск пары», чтобы начать поиск 👤. Я постараюсь помочь вам найти интересных людей для общения!\n\n"
                            "2. **Добавить в избранное**: Если вам понравился кто-то, просто нажмите «Добавить в избранное» 💖, чтобы сохранить этот профиль.\n\n"
                            "3. **Добавить в чёрный список**: Если вы встретили пользователя, с которым не хотите общаться, нажмите «Добавить в чёрный список» 🚫, чтобы прекратить взаимодействие.\n\n"
                            "4. **Просмотреть избранное**: Вы можете просмотреть всех, кого вы добавили в избранное, нажав на кнопку «Просмотреть избранное» 🔍.\n\n"
                            "5. **Пропустить**: Если вы не хотите взаимодействовать с текущим пользователем, просто нажмите кнопку «Пропустить» ⏭️.\n\n"
                            "✨ **Нажмите на кнопку, чтобы продолжить!** 😊"
                        )
                write_msg(event.user_id, instructions, start_buttons())
            elif request.lower() == "пропустить":
                write_msg(event.user_id, "Вы пропустили эту запись (Придумать как скипнуть)", create_keyboard())
            elif request.lower() == "добавить в избранное":
                target_user_id = find_photos[0][2].replace('https://vk.com/id', '')
                add_to_favourites = vk_user_db.add_to_favourites(vk_user_id, target_name, target_last_name, target_url, target_attachments)
                write_msg(event.user_id, find_photos[0][2])
                write_msg(event.user_id, "Запись добавлена в избранное", create_keyboard())
            elif request.lower() == "добавить в чёрный список":
                target_user_id = find_photos[0][2].replace('https://vk.com/id', '')
                add_to_black_list = vk_user_db.add_to_black_list(vk_user_id, target_user_id)
                write_msg(event.user_id, find_photos[0][2])
                write_msg(event.user_id, "Запись добавлена в чёрный список", create_keyboard())
            elif request.lower() == "просмотреть избранное":
                user_get_favourites = vk_user_db.get_favourites(vk_user_id) 
                write_msg(event.user_id, "Вот ваше избранное:", create_keyboard())
                for favourite in user_get_favourites:
                    write_msg(event.user_id, f"{favourite['name']} {favourite['last_name']}: {favourite['url']}")

            elif request.lower() == "вернуться в главное меню":
                write_msg(event.user_id, "Возвращаемся в главное меню", start_buttons())

            else:
                write_msg(event.user_id, "Не поняла вашего ответа... Выбери одну из кнопок:", start_buttons())
