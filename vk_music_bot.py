# -*- coding:utf-8 -*-
import os, sys

sys.path.append(os.getcwd())

import flask
import requests
import telebot
from telebot import types

import SQL
import bot_config
import emodji
from session import Session

BOT_TOKEN = bot_config.token_bot
WEBHOOK_PATH = '/{}/'.format(BOT_TOKEN)

bot = telebot.TeleBot(BOT_TOKEN)
vk_session = Session()

app = flask.Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    return 'Бот работает'


@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        flask.abort(403)


def pagination(page, chat_id):
    tracks_count = len(vk_session.tracks[chat_id])
    pages = tracks_count // 5
    if tracks_count % 5 > 0:
        pages += 1
    current_page = page // 5
    page_to_show = "{0}/{1}".format(current_page, pages)
    paginated = vk_session.tracks[chat_id][page - 5:page]
    return paginated, page_to_show


def keyboard_to_show(tracks, page_to_show):
    keyboard = types.InlineKeyboardMarkup()
    for j in tracks:
        SQL.add_track(j)
        sec = int(j['dur']) % 60
        minute = int(j['dur']) // 60
        if sec < 10:
            sec = "0{}".format(sec)
        time = "{0}:{1}".format(minute, sec)
        button = types.InlineKeyboardButton(text="{1} - {0}\t\t{2}".format(j['title'], j['artist'], time),
                                            callback_data="track?{0}".format(j['id']))
        keyboard.row(button)

    left_button = types.InlineKeyboardButton(text="{}".format(emodji.left),
                                             callback_data="left")
    right_button = types.InlineKeyboardButton(text="{}".format(emodji.right),
                                              callback_data="right")
    page = types.InlineKeyboardButton(text=page_to_show,
                                      callback_data=" ")
    keyboard.row(left_button, page, right_button)
    return keyboard


@bot.message_handler(commands=["start"])
def start_menu_handler(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

    button_playlist = types.KeyboardButton(text="{}  Плейлист".format(emodji.music))
    button_search = types.KeyboardButton(text="{}  Поиск".format(emodji.search))
    button_help = types.KeyboardButton(text="{}  Поддержать".format(emodji.finger_up))

    keyboard.row(button_playlist, button_search)
    keyboard.row(button_help)

    user_name = message.from_user.first_name
    chat_id = str(message.chat.id)
    SQL.make_new_user(chat_id=chat_id, name=user_name)

    bot.send_message(message.chat.id,
                     ("Приветствуем, {}!\n"
                      "Я помогу вам разобраться с музыкой!\n"
                      "[beta/1.0]").format(user_name),
                     reply_markup=keyboard)


@bot.message_handler(func=lambda m: m.text == "{}  Поддержать".format(emodji.finger_up))
def support_menu(message):
    keyboard = types.InlineKeyboardMarkup()

    button_rate_1 = types.InlineKeyboardButton(text="{0}".format(emodji.star),
                                               callback_data="rate_1")
    button_rate_2 = types.InlineKeyboardButton(text="{0}{0}".format(emodji.star),
                                               callback_data="rate_2")
    button_rate_3 = types.InlineKeyboardButton(text="{0}{0}{0}".format(emodji.star),
                                               callback_data="rate_3")
    button_rate_4 = types.InlineKeyboardButton(text="{0}{0}{0}{0}".format(emodji.star),
                                               callback_data="rate_4")
    button_rate_5 = types.InlineKeyboardButton(text="{0}{0}{0}{0}{0}".format(emodji.star),
                                               callback_data="rate_5")

    keyboard.add(button_rate_1)
    keyboard.add(button_rate_2)
    keyboard.add(button_rate_3)
    keyboard.add(button_rate_4)
    keyboard.add(button_rate_5)

    bot.send_message(chat_id=message.chat.id,
                     text="Пожалуйста оцените меня на стадии beta",
                     reply_markup=keyboard)


@bot.message_handler(func=lambda m: m.text == "{}  Плейлист".format(emodji.music))
def playlist_menu(message):
    chat_id = message.chat.id
    SQL.turn_off_search(chat_id)
    SQL.update_page(chat_id, 5)

    keyboard = types.InlineKeyboardMarkup()

    button_vk_playlist = types.InlineKeyboardButton(text="Плейлист VK", callback_data="vk_playlist")
    button_telegram_playlist = types.InlineKeyboardButton(text="Плейлист Telegram", callback_data="tele_playlist")

    keyboard.row(button_vk_playlist)
    keyboard.row(button_telegram_playlist)

    bot.send_message(message.chat.id,
                     ("{}  Плейлист\n\n"
                      "<b>Плейлист VK</b> - это ваш плейтист с сайта vk.com\n"
                      "<b>Плейлист Telegram</b> - это плейлист, который вы можете составить "
                      "при помощи меня и в дальнейшем прослушивать").format(emodji.music),
                     parse_mode="HTML",
                     reply_markup=keyboard)


@bot.message_handler(func=lambda m: m.text == "{}  Поиск".format(emodji.search))
def search_handler(message):
    chat_id = str(message.chat.id)
    SQL.turn_on_search(chat_id)
    bot.send_message(message.chat.id,
                     ("{}  Поиск\n\n"
                      "Напишите название песни, которую вы хотите найти.\n"
                      "Например 'Smells like teen spirit'").format(emodji.search))


@bot.message_handler(func=lambda m: m.text)
def make_search_handler(message):
    chat_id = message.chat.id
    search_status = SQL.get_search_status(chat_id)[0]['search_is_on']
    if search_status == 1:
        SQL.update_page(chat_id=chat_id,
                        new_val=0)
        page = 5
        vk_session.make_search(track=message.text,
                               chat_id=chat_id)
        tracks_to_show, page_to_show = pagination(page=page,
                                                  chat_id=chat_id)
        keyboard = keyboard_to_show(tracks_to_show, page_to_show)

        bot.send_message(message.chat.id,
                         "Результаты поиска:",
                         reply_markup=keyboard)

        for i in tracks_to_show:
            track = SQL.get_track(i['id'])[0]
            if track['telegram_id'] is not None:
                pass
            else:
                response = requests.get(i['url'])
                audio = response.content
                sended_message = bot.send_audio('@vk_music_storage',
                                                audio=audio,
                                                duration=i['dur'],
                                                performer=i['artist'],
                                                title=i['title'])
                SQL.update_track(id=i['id'],
                                 telegram_id=sended_message.audio.file_id)


@bot.callback_query_handler(func=lambda callback: True)
def callback_answer(callback):
    if callback.data.split("?")[0] == "track":
        track_id = callback.data.split("?")[1]
        keyboard = types.InlineKeyboardMarkup()
        like_botton = types.InlineKeyboardButton(text="{}".format(emodji.finger_up),
                                                 callback_data="like?{}".format(track_id))
        dislike_button = types.InlineKeyboardButton(text="{}".format(emodji.finger_down),
                                                    callback_data="dislike?{}".format(track_id))
        keyboard.row(like_botton, dislike_button)

        track = SQL.get_track(track_id)[0]
        if track['telegram_id'] is not None:
            bot.send_audio(chat_id=callback.message.chat.id,
                           audio=track['telegram_id'],
                           reply_markup=keyboard)
        else:
            bot.send_message(callback.message.chat.id,
                             "Этой композиции еще нет, на серверах телеграмма, подождите пока я ее загружу.")
            audio = requests.get(track['url']).content
            sended_message = bot.send_audio(chat_id=callback.message.chat.id,
                                            audio=audio,
                                            title=track['title'],
                                            performer=track['artist'],
                                            duration=track['dur'],
                                            reply_markup=keyboard)
            SQL.update_track(telegram_id=sended_message.audio.file_id,
                             id=callback.data.split("?")[1])

    elif callback.data == "vk_playlist":
        chat_id = callback.message.chat.id
        bot.edit_message_text(text=("К сожалению этот раздел еще в разработке, "
                                    "но я опевещу вас, как только он будет доступен"),
                              chat_id=chat_id,
                              message_id=callback.message.message_id)

    elif callback.data == "tele_playlist":
        chat_id = callback.message.chat.id
        tracks = SQL.get_tele_playlist(chat_id)
        vk_session.tracks[chat_id] = tracks
        page = SQL.get_page(chat_id)[0]["page"]
        tracks_to_show, page_to_show = pagination(page=page,
                                                  chat_id=chat_id)
        keyboard = keyboard_to_show(tracks_to_show, page_to_show)

        bot.edit_message_text(text="Ваш плейлист в телеграмм",
                              chat_id=chat_id,
                              message_id=callback.message.message_id,
                              reply_markup=keyboard)

    elif callback.data.split('_')[0] == "rate":
        chat_id = callback.message.chat.id
        rate = callback.data.split('_')[1]
        SQL.rate(chat_id, rate)

        bot.edit_message_text(text="Спасибо за вашу оценку !",
                              chat_id=chat_id,
                              message_id=callback.message.message_id)

    elif callback.data == "left":
        chat_id = callback.message.chat.id
        page = SQL.get_page(chat_id)[0]['page']
        if page == 5:
            pass
        else:
            page -= 5
            SQL.update_page(chat_id=chat_id,
                            new_val=page)
            tracks_to_show, page_to_show = pagination(page=page,
                                                      chat_id=chat_id)
            keyboard = keyboard_to_show(tracks_to_show, page_to_show)

            bot.edit_message_text(chat_id=chat_id,
                                  message_id=callback.message.message_id,
                                  reply_markup=keyboard,
                                  text="Результаты поиска:")

    elif callback.data == "right":
        chat_id = callback.message.chat.id
        page = SQL.get_page(chat_id)[0]['page']
        if page == 50:
            pass
        else:
            page += 5
            SQL.update_page(chat_id=chat_id,
                            new_val=page)
            tracks_to_show, page_to_show = pagination(page=page,
                                                      chat_id=chat_id)
            keyboard = keyboard_to_show(tracks_to_show, page_to_show)

            bot.edit_message_text(chat_id=chat_id,
                                  message_id=callback.message.message_id,
                                  reply_markup=keyboard,
                                  text="Результаты поиска:")

    elif callback.data.split("?")[0] == "like":
        chat_id = callback.message.chat.id
        track_id = callback.data.split("?")[1]
        SQL.like_track(chat_id=chat_id,
                       id=track_id)

    elif callback.data.split("?")[0] == "dislike":
        chat_id = callback.message.chat.id
        track_id = callback.data.split("?")[1]
        SQL.dislike_track(chat_id=chat_id,
                          id=track_id)


if __name__ == '__main__':
    bot.polling(none_stop=True)
