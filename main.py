import requests, json
import config

import telebot
bot = telebot.TeleBot(config.API_TOKEN_TELEGRAM, parse_mode="html")

import time

from threading import Thread


def get_themes():
    with open('themes.txt', 'r') as file:
        return [i.replace("\n", "").strip() for i in file.read().split(".") if i.replace("\n", "").strip() != '']

def edit_themes(new_themes):
    themes = [i+"." for i in new_themes]
    with open('themes.txt', 'w') as file:
        print(*themes, file=file)


def get_template():
    with open('template.txt', 'r') as file:
        return file.read()

def edit_template(new_template):
    with open('template.txt', 'w') as file:
        file.write(new_template)


def create_text_to_gpt(theme):
    text = get_template().split('*Theme Post*')
    return text[0]+theme+text[1]


def get_chatgpt_data(prompt):

    error = ""

    try:
        url = "https://api.openai.com/v1/chat/completions"

        prompt = [{"role": "user", "content": prompt}]

        data = {
            "model": "gpt-3.5-turbo",
            "messages": prompt,
            "max_tokens": 1000,
            "temperature": 0,
        }

        headers = {'Accept': 'application/json', 'Authorization': 'Bearer '+config.API_TOKEN_OPENAI}
        r = requests.post(url, headers=headers, json=data)

        error = r.text.strip()

        return r.json()['choices'][-1]['message']['content'].strip()

    except Exception as e:
        print(error)
        return f"Возникли некоторые трудности."




get_str_posts = lambda: "\n".join(get_themes())


@bot.message_handler(commands=['clear'])
def clearPost(message):
    edit_themes([])
    bot.send_message(message.chat.id, "Темы постов успешно очищены!")

@bot.message_handler(commands=['add'])
def addPosts(message):
    mesg = bot.send_message(message.chat.id, 'В следующем сообщении отправьте список тем постов. (Каждый с новой строки)')
    bot.register_next_step_handler(mesg, addPostsFunc)

def addPostsFunc(message):
    posts = get_themes()
    posts.extend(message.text.split('\n'))

    edit_themes(posts)

    bot.send_message(message.chat.id, "Темы постов успешно добавлены!")
    bot.send_message(message.chat.id, "<b>Активные посты:</b>\n\n" + get_str_posts())


@bot.message_handler(commands=['posts'])
def activePosts(message):
    bot.send_message(message.chat.id, "<b>Активные посты:</b>\n\n" + get_str_posts())


@bot.message_handler(commands=['template'])
def getTemplate(message):
    bot.send_message(message.chat.id, "<b>Активный шаблон:</b>\n\n" + get_template())


@bot.message_handler(commands=['edit_template'])
def editTemplate(message):
    mesg = bot.send_message(message.chat.id, 'В следующем сообщении отправьте новый шаблон с "*Theme Post*" - где будет втавляться тема поста.')
    bot.register_next_step_handler(mesg, editTemplateFunc)


def editTemplateFunc(message):

    if "*Theme Post*" in message.text:
        edit_template(message.text)
        bot.send_message(message.chat.id, "Шаблон успешно обновлен!")
    else:
        bot.send_message(message.chat.id, "В шаблоне нет темы поста!")



def deleteFirstTheme():
    posts = get_themes()
    posts.pop(0)

    edit_themes(posts)


def create_wp_post(title, text):
    url = "https://vm1254991.ssd.had.yt/public/f_project/resource/gpt-to-wp/send.php"

    payload = json.dumps({
        "title": title,
        "content": text,
        "key": "m.^7Gf=n6{>q>b$x"
    })
    headers = {
        'Content-Type': 'application/json',
    }

    response = requests.request("POST", url, headers=headers, data=payload)

def create_posts():
    while True:
        posts = get_themes()
        if posts:
            p = get_chatgpt_data(create_text_to_gpt(posts[0]))
            if len(p) < 1000:
                bot.send_message(config.admin_channel, "Не удалось сгенерировать пост на тему: "+posts[0])
            else:
                bot.send_message(config.main_channel, p)
                create_wp_post(posts[0], p)

            deleteFirstTheme()
        else:
            pass

        time.sleep(30)


def start_bot():
    bot.polling(none_stop=True)


p1 = Thread(target=create_posts)
p2 = Thread(target=start_bot)

if __name__ == '__main__':
    p2.start()
    p1.start()
