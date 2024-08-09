import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from VK_class import My_VkApi
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import json
from db_tools import DB_editor


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


class PhotoIterator:
    def __init__(self, photos):
        # Сохраняем список фотографий
        self.photos = list(photos)  # Преобразуем в список <------- ЭТО ОСНОВНАЯ ПРОБЛЕМА, работает долго
        self.index = 0  # Индекс для отслеживания текущего элемента

    def __iter__(self):
        return self

    def __next__(self):
        # Проверяем, есть ли еще элементы
        if self.index < len(self.photos):
            target_obj = self.photos[self.index]
            self.index += 1
            return target_obj
        else:
            raise StopIteration  # Останавливаем итерацию, если объекты закончились


def generate_new_target(iterator):
    try:
        target_obj = next(iterator)  # Получаем следующий элемент
        target_name = target_obj[0]
        target_last_name = target_obj[1]
        target_url = target_obj[2]
        target_attachments = target_obj[3]
        write_msg(event.user_id, f'{target_name} {target_last_name}\n{target_url}\n', create_keyboard(), attachment=f'{" ,".join(target_attachments)}')
        return target_name, target_last_name, target_url, target_attachments 
    
    except StopIteration:
        write_msg(event.user_id, "Больше нет доступных фотографий.")


photo_iterator = None
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
            user_vk_id = next(iter(user_info))  # Получаем ID пользователя
            user_vk_sex = 2 if user_sex == 'Женский' else 1
            user_database = DB_editor()  # Создание экземпляра редактора БД
            user_database.register_user(user_vk_id, user_age, user_vk_sex, user_city)

            # Поиск людей
            if photo_iterator is None:
                potential_users = My_VkApi(user_token).search_users(opposite_sex, age_min, age_max, user_city)
                user_photos = My_VkApi(user_token).find_users_photos(potential_users)
                photo_iterator = PhotoIterator(user_photos)

            # Сообщение от пользователя
            user_request = event.text

            # Логика ответа
            if user_request.lower() == "поиск пары":  
                try:              
                    target_name, target_last_name, target_url, target_attachments = generate_new_target(photo_iterator)
                except Exception as e:
                    write_msg(event.user_id, "Список фотографий закончился. Возвращаемся в главное меню", start_buttons())
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
                write_msg(event.user_id, "Вы пропустили эту запись", create_keyboard())
                try:
                    target_name, target_last_name, target_url, target_attachments = generate_new_target(photo_iterator)
                except Exception as e:
                    write_msg(event.user_id, "Список фотографий закончился. Возвращаемся в главное меню", start_buttons())

            elif user_request.lower() == "добавить в избранное":
                user_database.add_to_favourites(user_vk_id, target_name, target_last_name, target_url, target_attachments)
                write_msg(event.user_id, f"{target_url}\nЗапись добавлена в избранное", create_keyboard())
                target_name, target_last_name, target_url, target_attachments = generate_new_target(photo_iterator)

            elif user_request.lower() == "добавить в чёрный список":
                target_user_id = target_url.replace('https://vk.com/id', '')
                user_database.add_to_black_list(user_vk_id, target_user_id)
                write_msg(event.user_id,  f"{target_url}\nЗапись добавлена в чёрный список", create_keyboard())
                target_name, target_last_name, target_url, target_attachments = generate_new_target(photo_iterator)

            elif user_request.lower() == "просмотреть избранное":
                user_favourites = user_database.get_favourites(user_vk_id)
                favourites_list = [f"{favourite['name']} {favourite['last_name']}: {favourite['url']}" for favourite in user_favourites]
                favourites_message = '\n'.join(favourites_list)
                write_msg(event.user_id, f'Ваш список избранного:\n\n{favourites_message}', start_buttons())

            elif user_request.lower() == "вернуться в главное меню":
                write_msg(event.user_id, "Возвращаемся в главное меню", start_buttons())

            else:
                write_msg(event.user_id, "Не поняла вашего ответа... Выбери одну из кнопок:", start_buttons())