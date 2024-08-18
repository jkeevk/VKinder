import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from VK_class import My_VkApi
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import json
from db_tools import DB_editor
from VK_class import get_top3_likes


class VkBot:
    """
    Класс VkBot предназначен для взаимодействия с API ВКонтакте,
    создания и управления чат-ботом на основе событий и команд пользователей.

    Методы:
    write_msg: Отправляет сообщение пользователю с опциональной клавиатурой и вложениями.
    start_buttons: Создает стартовую клавиатуру для бота.
    create_keyboard: Создает клавиатуру для поиска пары.
    create_favourite_keyboard: Создает клавиатуру для управления избранным.
    create_black_list_keyboard: Создает клавиатуру для управления списком заблокированных.
    photo_generator: Генерирует пользователей из списка.
    start_bot: Инициализирует пользователя, собирает информацию и сохраняет в базу данных.
    next_found_user_message: Генерирует сообщение о найденном пользователе, проверяет его наличие в черном списке.
    send_next_photo: Получает следующую фотографию пользователя и отправляет информацию о ней.
    handle_add_to_favourites: Обрабатывает добавление пользователя в избранное.
    handle_add_to_blacklist: Обрабатывает добавление пользователя в черный список.
    handle_city_request: Обрабатывает запрос пользователя о городе и обновляет информацию.
    view_favourites: Просмотр избранных пользователей и отправка их списка.
    process_event: Основная логика обработки сообщений от пользователя ВКонтакте.
    
    """

    def __init__(self, token_file: str) -> None:
        with open(token_file, 'r') as file:
            data_json = json.load(file)
            self.group_access_token = data_json["group_access_token"]
            self.access_token = data_json["access_token"]
            self.user_token = self.access_token
            
        self.vk = vk_api.VkApi(token=self.group_access_token)
        self.longpoll = VkLongPoll(self.vk)
        self.database = DB_editor()
        self.all_found_users_generator = None
        self.user_vk_id = None

        # Инструкции для пользователя
        self.instructions = (
            "Привет! Я бот, который поможет вам найти людей для знакомства в социальной сети ВКонтакте 🥰\n\n"
            "1. Поиск пары🔍: Нажмите на кнопку «Поиск пары», чтобы начать поиск. Я постараюсь помочь вам найти интересных людей для общения!\n\n"
            "2. Добавить в избранное❤️: Если вам понравился кто-то, просто нажмите «Добавить в избранное», чтобы сохранить этот профиль.\n\n"
            "3. Добавить в чёрный список⛔️: Если вы встретили пользователя, с которым не хотите общаться, нажмите «Добавить в чёрный список», чтобы прекратить взаимодействие.\n\n"
            "4. Просмотреть избранное🧾: Вы можете просмотреть всех, кого вы добавили в избранное, нажав на кнопку «Просмотреть избранное».\n\n"
            "5. Пропустить⏭: Если вы не хотите взаимодействовать с текущим пользователем, просто нажмите кнопку «Пропустить».\n\n"
            "✨ Нажмите на кнопку, чтобы продолжить!😊"
        )

    def write_msg(self, user_id: int, message: str, keyboard=None, attachment=None) -> None:
        """
        Отправляет сообщение пользователю с опциональной клавиатурой и вложениями.

        Параметры:
            user_id (int): Идентификатор пользователя, которому отправляется сообщение.
            message (str): Текст сообщения.
            keyboard: Опциональная клавиатура для сообщения.
            attachment: Опциональные вложения для сообщения.

        Возвращаемое значение:
            None
        """
        self.vk.method('messages.send', {
            'user_id': user_id,
            'message': message,
            'random_id': 0,
            'keyboard': keyboard,
            'attachment': attachment
        })

    def start_buttons(self):
        """
        Создает стартовую клавиатуру для бота.

        Возвращаемое значение:
            Клавиатура в формате строки для отправки пользователю.
        """
        keyboard = VkKeyboard(one_time=True)
        keyboard.add_button('Поиск пары', color=VkKeyboardColor.POSITIVE)
        keyboard.add_button('Правила', color=VkKeyboardColor.PRIMARY)
        keyboard.add_line()  
        keyboard.add_button('Сменить город', color=VkKeyboardColor.SECONDARY)
        return keyboard.get_keyboard()

    def create_keyboard(self):
        """
        Создает клавиатуру для поиска пары.

        Возвращаемое значение:
            Клавиатура в формате строки для отправки пользователю.
        """
        keyboard = VkKeyboard(one_time=True)  # Создаем клавиатуру
        keyboard.add_button('Добавить в избранное', color=VkKeyboardColor.POSITIVE)
        keyboard.add_button('Пропустить', color=VkKeyboardColor.NEGATIVE)
        keyboard.add_line()  
        keyboard.add_button('Добавить в Чёрный список', color=VkKeyboardColor.SECONDARY)
        keyboard.add_button('Просмотреть избранное', color=VkKeyboardColor.PRIMARY)
        keyboard.add_line()
        keyboard.add_button('Вернуться в главное меню', color=VkKeyboardColor.PRIMARY)
        return keyboard.get_keyboard()

    def create_favourite_keyboard(self):
        """
        Создает клавиатуру для управления избранным.

        Возвращаемое значение:
            Клавиатура в формате строки для отправки пользователю.
        """
        keyboard = {
            "inline": True,
            "buttons": [
                [
                    {"action": {"type": "text", "label": "Очистить список"}, "color": "negative"},
                    {"action": {"type": "text", "label": "Убрать последнюю запись"}, "color": "primary"},
                ],
                [
                    {"action": {"type": "text", "label": "Поиск пары"}, "color": "positive"},
                    {"action": {"type": "text", "label": "Вернуться в главное меню"}, "color": "default"},
                ] 
            ]       
        }
        return json.dumps(keyboard)  # Преобразование в JSON-строку перед отправкой

    def create_black_list_keyboard(self):
        """
        Создает клавиатуру для управления списком заблокированных.

        Возвращаемое значение:
            Клавиатура в формате строки для отправки пользователю.
        """
        keyboard = {
            "inline": True,
            "buttons": [
                [
                    {"action": {"type": "text", "label": "Очистить black list"}, "color": "negative"},
                    {"action": {"type": "text", "label": "Убрать последнего пользователя"}, "color": "primary"},
                ],
                [
                    {"action": {"type": "text", "label": "Поиск пары"}, "color": "positive"},
                    {"action": {"type": "text", "label": "Вернуться в главное меню"}, "color": "default"},
                ] 
            ]       
        }
        return json.dumps(keyboard) 

    def photo_generator(self, user_list: list):
        """
        Генерирует пользователей из списка.

        Параметры:
            user_list (list): Список найденных пользователей.

        Возвращаемое значение:
            Идентификатор пользователя.
        """
        for user_id in user_list:
            yield user_id  # берем пользователя из списка найденых

    def start_bot(self, user_id: int) -> tuple:
        """
        Инициализирует пользователя, собирает информацию и сохраняет в базу данных.

        Параметры:
            user_id (int): Идентификатор пользователя для инициализации.

        Возвращаемое значение:
            Кортеж с информацией о пользователе (ID, пол, возраст, противоположный пол, минимальный и максимальный возраст, город, экземпляр базы данных).
        """
        user_id = event.user_id
        user_info = My_VkApi(self.group_access_token).get_user_info(user_id)
        user_sex = user_info[user_id]["sex"]
        user_age = user_info[user_id]["age"]
        opposite_sex = (
            2 if user_sex == "Женский" else 1
        )  # выбираем противоположный пол
        age_min = (
            user_age - 10 if user_age - 10 >= 16 else 16
        )  # выбираем минимальный возраст
        age_max = user_age + 5

        user_vk_id = user_id  # Получаем ID пользователя
        user_vk_sex = 2 if user_sex == "Женский" else 1

        user_city = user_info[user_id]['city_id']

        # if not self.database.get_user_city(user_id):
        #     user_city = user_info[user_id].get(
        #         "city", "Неизвестен"
        #     )  # Используем get для безопасного доступа
        # else:
        #     user_city = self.database.get_user_city(user_id)

        self.database.register_user(user_vk_id, user_age, user_vk_sex, user_city)
        return user_vk_id, user_sex, user_age, opposite_sex, age_min, age_max, user_city, self.database

    def next_found_user_message(self, user_id: int) -> tuple:
        """
        Генерирует сообщение о найденном пользователе, проверяет его наличие в черном списке.

        Параметры:
            user_id (int): Идентификатор пользователя, о котором требуется получить информацию.

        Возвращаемое значение:
            Кортеж с идентификатором пользователя, его ФИО и топ-3 фотографии, или None в случае
            ошибки или если пользователь заблокирован.
        """
        blocked_list = self.database.get_black_list_user_id(event.user_id) # список заблокированных
        blocked_list.extend([int(favourite['url']) for favourite in self.database.get_favourites(event.user_id)]) # список избранных
        try:
            if user_id not in blocked_list:
                found_user_fio = My_VkApi(self.access_token).get_short_user_info(user_id)
                # Получаем все фотографии пользователя
                found_user_photos = My_VkApi(self.access_token).get_user_photos(user_id)
                # Выбираем топ 3 лайкнувших фотографии
                top3_user_photos = get_top3_likes(found_user_photos)
                self.write_msg(event.user_id,
                        f"{str(found_user_fio)}\nhttps://vk.com/id{user_id}",
                        self.create_keyboard(),
                        attachment=f"{top3_user_photos}")
                return user_id, found_user_fio, top3_user_photos
            else:
                self.next_found_user_message(next(self.all_found_users_generator))
        except Exception as e:
                self.write_msg(event.user_id, f"Error fetching new user: {e}")
                return None
        
    def send_next_photo(self, event_user_id: int, all_found_users_generator) -> tuple:
        """
        Получает следующую фотографию пользователя и отправляет информацию о ней.

        Параметры:
            event_user_id (int): ID события, пользователь, получающий сообщение.
            all_found_users_generator: Генератор найденных пользователей.

        Возвращаемое значение:
            tuple: user_id, found_user_fio, top3_user_photos или (None, None, None) в случае исключения.
        """
        try:
            user_id, found_user_fio, top3_user_photos = self.next_found_user_message(next(all_found_users_generator))
            return user_id, found_user_fio, top3_user_photos
        except (StopIteration, TypeError) as e:
            # Обработка исключений
            if isinstance(e, StopIteration):
                self.write_msg(event_user_id, "Больше нет доступных фотографий.", self.start_buttons())
            elif isinstance(e, TypeError):
                self.write_msg(event_user_id, "Произошла ошибка при обработке. Пожалуйста, проверьте входные данные.", self.start_buttons())
            return None, None, None  # Возврат значений по умолчанию, чтобы не вызывалась ошибка распаковки

    def handle_add_to_favourites(self, event_user_id: int, user_id: int, found_user_fio: str, top3_user_photos: str) -> None:
        """
        Обрабатывает добавление пользователя в избранное.

        Параметры:
            event_user_id (int): ID события, пользователь, получающий сообщение.
            user_id (int): ID пользователя, которого добавляют в избранное.
            found_user_fio (str): ФИО найденного пользователя.
            top3_user_photos (str): Строка с URL-ссылками на три фотографии пользователя.

        Возвращаемое значение:
            None
        """
        try:
            self.database.add_to_favourites(event_user_id, found_user_fio.split()[0], found_user_fio.split()[1], user_id, "{" + "".join(top3_user_photos.split()) + "}")
            self.write_msg(event_user_id, f"https://vk.com/id{user_id}\nЗапись добавлена в избранное", self.create_keyboard())
        except StopIteration:
            self.write_msg(event_user_id, "Больше нет доступных фотографий.", self.start_buttons())

    def handle_add_to_blacklist(self, event_user_id: int, user_id: int) -> None:
        """
        Обрабатывает добавление пользователя в черный список.

        Параметры:
            event_user_id (int): ID события, пользователь, получающий сообщение.
            user_id (int): ID пользователя, который добавляется в черный список.

        Возвращаемое значение:
            None
        """
        try:
            self.database.add_to_black_list(event_user_id, user_id)
            self.write_msg(event_user_id, f"https://vk.com/id{user_id}\nЗапись добавлена в чёрный список", self.create_black_list_keyboard())
        except StopIteration:
            self.write_msg(event_user_id, "Больше нет доступных фотографий", self.start_buttons())

    def handle_city_request(self, event_user_id: int) -> bool:
        """
        Обрабатывает запрос пользователя о городе и обновляет информацию.

        Параметры:
            event_user_id (int): ID события, пользователь, получающий сообщение.

        Возвращаемое значение:
            bool: Состояние конфигурации пользователя (False - сбросить настройки для нового города).
        """
        user_request = event.text
        found_city = My_VkApi(self.access_token).search_city(user_request)
        if event.text:
            if user_request.lower() == "правила":
                self.write_msg(event.user_id, self.instructions, self.start_buttons())
            elif found_city == "Город не найден":
                self.write_msg(event.user_id, "Укажите ваш город", self.start_buttons())
            elif not found_city == "Город не найден":
                self.write_msg(
                    event_user_id, f"Выбран город: {found_city}", self.start_buttons()
                )
                self.database.update_user_city(event.user_id, found_city)
                state_configed = False  # Сбрасываем настройку пользователя для генерации для нового города
                return state_configed
        else:
            self.write_msg(event.user_id, "Не поняла вашего ответа...", self.start_buttons())

    def view_favourites(self, event_user_id) -> None:
        """
        Просмотр избранных пользователей и отправка их списка.

        Параметры:
            event_user_id (int): ID события, пользователь, получающий сообщение.

        Возвращаемое значение:
            None
        """
        user_favourites = self.database.get_favourites(event_user_id)
        favourites_list = [
            f"{favourite['name']} {favourite['last_name']}: https://vk.com/id{favourite['url']}"
            for favourite in user_favourites
        ]

        favourites_message = "\n".join(favourites_list) if favourites_list else "Ваш список избранного пуст."    
        self.write_msg(
            event_user_id,
            f"Ваш список избранного:\n\n{favourites_message}",
            self.create_favourite_keyboard()
        )

    def process_event(self, event: VkEventType) -> None:
        """
        Основная логика обработки сообщений от пользователя ВКонтакте.

        Этот метод отвечает за обработку новых сообщений от пользователя. 
        Если сообщение новое и адресовано боту, информация о пользователе 
        извлекается и инициализируются необходимые переменные.

        """

        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            user_vk_id, self.user_sex, self.user_age, opposite_sex, age_min, age_max, user_city, self.database = self.start_bot(event.user_id)
            # Инициализация состояний
            state_configed = False
            # Если город известен, то запускаем генерацию пользователей
            if self.database.get_user_city(event.user_id) != "Неизвестен":
                if not state_configed: # Проверяем флаг конфигурации
                    # user_city = self.database.get_user_city(user_vk_id)
                    all_found_users = My_VkApi(self.user_token).search_users(opposite_sex, age_min, age_max, int(user_city))
                    all_found_users_generator = self.photo_generator(all_found_users)
                    state_configed = True
                # Сообщение от пользователя
                user_request = event.text.lower()
                if state_configed:
                    if user_request == "поиск пары":
                        self.user_id, self.found_user_fio, self.top3_user_photos = self.send_next_photo(event.user_id, all_found_users_generator)
                    elif user_request == "правила":
                        self.write_msg(event.user_id, self.instructions, self.start_buttons())
                    elif user_request == "сменить город": 
                        self.database.update_user_city(event.user_id, "Неизвестен")
                        self.write_msg(event.user_id, "Укажите ваш город", self.start_buttons())
                        state_configed = False
                    elif user_request == "пропустить":
                        self.user_id, self.found_user_fio, self.top3_user_photos = self.send_next_photo(event.user_id, all_found_users_generator)
                    elif user_request == "добавить в избранное":
                        self.handle_add_to_favourites(event.user_id, self.user_id, self.found_user_fio, self.top3_user_photos)
                        self.user_id, self.found_user_fio, self.top3_user_photos = self.send_next_photo(event.user_id, all_found_users_generator)
                    elif user_request == "добавить в чёрный список":
                        self.handle_add_to_blacklist(event.user_id, self.user_id)
                    elif user_request == "просмотреть избранное":
                        self.view_favourites(event.user_id)
                    elif user_request == "вернуться в главное меню":
                        self.write_msg(event.user_id, "Возвращаемся в главное меню", self.start_buttons())
                    elif user_request == 'очистить список':
                        self.database.delete_all_favourites(event.user_id)
                        self.write_msg(event.user_id, "Удаляем весь список", self.start_buttons())
                    elif user_request == 'убрать последнюю запись':
                        self.database.delete_last_favourite(event.user_id)
                        self.write_msg(event.user_id, "Последняя запись удалена", self.start_buttons())
                    elif user_request == 'очистить black list':
                        self.database.delete_all_blocked(event.user_id)
                        self.write_msg(event.user_id, "Удаляем весь список", self.start_buttons())
                    elif user_request == 'убрать последнего пользователя':
                        self.database.delete_last_blocked(event.user_id)
                        self.write_msg(event.user_id, "Последняя запись удалена", self.start_buttons())
                    else:
                        self.write_msg(event.user_id, "Не поняла вашего ответа... Выберите одну из кнопок:", self.start_buttons())
            # Если город еще неизвестен или находимся в состоянии смены города
            elif self.database.get_user_city(event.user_id) == "Неизвестен":
                self.handle_city_request(event.user_id)


if __name__ == "__main__":
    print('Bot is running')
    bot = VkBot('token.json')
    for event in bot.longpoll.listen():
        bot.process_event(event)
