import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from VK_class import My_VkApi

def write_msg(user_id, message):
    vk.method('messages.send', {'user_id': user_id, 'message': message, 'random_id': 0})

# Авторизуемся как сообщество
with open('token.json', 'r') as file:
    data_json = json.load(file)
    group_access_token = data_json["group_access_token"]
    access_token = data_json["access_token"]
vk = vk_api.VkApi(token=group_access_token)

# Работа с сообщениями
longpoll = VkLongPoll(vk)


# Основной цикл
for event in longpoll.listen():

    # Если пришло новое сообщение
    if event.type == VkEventType.MESSAGE_NEW:

        # Если оно имеет метку для меня(то есть бота)
        if event.to_me:
            vk_user = My_VkApi(group_access_token).get_user(event.user_id)
            print(vk_user, event.text)
            # Сообщение от пользователя
            request = event.text

            # Каменная логика ответа
            if request == "привет":
                write_msg(event.user_id, "Хай")
            elif request == "пока":
                write_msg(event.user_id, "Пока((")
            else:
                write_msg(event.user_id, "Не поняла вашего ответа...")