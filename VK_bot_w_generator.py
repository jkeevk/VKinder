import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from VK_class import My_VkApi
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import json
from db_tools import DB_editor
from VK_class import get_top3_likes


def write_msg(user_id: int, message: str, keyboard=None, attachment=None):
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
    access_token = data_json["access_token"]
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


# Функция для генерации нового пользователя
def photo_generator(user_list: list):
    for user_id in user_list:
        yield user_id  # берем пользователя из списка найденых


# Функция для генерации нового пользователя
def next_found_user_message(user_id: int):
    # Проверяем что пользователь не находится в black list
    blocked_list = user_database.get_black_list(user_vk_id)
    try:
        if user_id not in blocked_list['blocked']:
            found_user_fio = My_VkApi(access_token).get_short_user_info(user_id)
            # Получаем все фотографии пользователя
            found_user_photos = My_VkApi(access_token).get_user_photos(user_id)
            # Выбираем топ 3 лайкнувших фотографии
            top3_user_photos = get_top3_likes(found_user_photos)
            write_msg(event.user_id,
                    f"{str(found_user_fio)}\nhttps://vk.com/id{user_id}",
                    create_keyboard(),
                    attachment=f"{top3_user_photos}")
            return user_id, found_user_fio, top3_user_photos
        else:
            next_found_user_message(next(all_found_users_generator))
    except Exception as e:
            write_msg(event.user_id, f"Error fetching new user: {e}")
            return None



# Основной цикл
for event in longpoll.listen():
    # Если пришло новое сообщение
    if event.type == VkEventType.MESSAGE_NEW:
        # Если оно имеет метку для меня (то есть бота)
        if event.to_me:
            user_info = My_VkApi(group_access_token).get_user_info(event.user_id)
            user_sex = user_info[event.user_id]['sex']
            user_age = user_info[event.user_id]['age']
            opposite_sex = 2 if user_sex == 'Женский' else 1  # выбираем противоположный пол
            age_min = user_age - 10 if user_age - 10 >= 16 else 16 # выбираем минимальный возраст
            age_max = user_age + 5
            user_city = user_info[event.user_id]['city']

            # создаём запись в базе данных
            user_vk_id = event.user_id  # Получаем ID пользователя
            user_vk_sex = 2 if user_sex == 'Женский' else 1
            user_database = DB_editor()  # Создание экземпляра редактора БД
            user_database.register_user(user_vk_id, user_age, user_vk_sex, user_city)


            # Сообщение от пользователя
            user_request = event.text

            # Логика ответа
            if user_request.lower() == "поиск пары":  
                # создаем список всех пользователей
                try:
                    all_found_users = My_VkApi(user_token).search_users(opposite_sex, age_min, age_max, user_city)
                    # создаем генератор
                    all_found_users_generator = photo_generator(all_found_users)
                    # берем первого пользователя из списка
                    user_id, found_user_fio, top3_user_photos = next_found_user_message(next(all_found_users_generator))
                except TypeError:
                    write_msg(event.user_id, "Больше нет доступных фотографий.")

            elif user_request.lower() == "правила":
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

            elif user_request.lower() == "пропустить":
                try:
                    # берем следующего пользователя из списка
                    next_found_user_message(next(all_found_users_generator))
                except StopIteration:
                    # если список закончился
                    write_msg(event.user_id, "Больше нет доступных фотографий.")
                #     write_msg(event.user_id, "Список фотографий закончился. Возвращаемся в главное меню", start_buttons())

            elif user_request.lower() == "добавить в избранное":
                write_msg(event.user_id, f"https://vk.com/id{user_id}\nЗапись добавлена в избранное", create_keyboard())
                print(top3_user_photos)
                user_database.add_to_favourites(
                                                user_vk_id, 
                                                found_user_fio.split()[0],
                                                found_user_fio.split()[1],
                                                f'https://vk.com/id{user_id}',
                                                '{' + ''.join(top3_user_photos.split()) + '}'
                                            )
                user_id, found_user_fio, top3_user_photos = next_found_user_message(next(all_found_users_generator))


            elif user_request.lower() == "добавить в чёрный список":
                write_msg(event.user_id,  f"https://vk.com/id{user_id}\nЗапись добавлена в чёрный список", create_keyboard())
                user_database.add_to_black_list(user_vk_id, user_id)
                user_id, found_user_fio, top3_user_photos = next_found_user_message(next(all_found_users_generator))


            elif user_request.lower() == "просмотреть избранное":
                user_favourites = user_database.get_favourites(user_vk_id)
                favourites_list = [f"{favourite['name']} {favourite['last_name']}: {favourite['url']}" for favourite in user_favourites]
                favourites_message = '\n'.join(favourites_list)
                write_msg(event.user_id, f'Ваш список избранного:\n\n{favourites_message}', start_buttons())

            elif user_request.lower() == "вернуться в главное меню":
                write_msg(event.user_id, "Возвращаемся в главное меню", start_buttons())

            else:
                write_msg(event.user_id, "Не поняла вашего ответа... Выбери одну из кнопок:", start_buttons())