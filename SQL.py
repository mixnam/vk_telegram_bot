# -*- coding:utf-8 -*-
import sqlite3
import logging

logging.basicConfig(format='%(levelname)-8s [%(asctime)s] %(message)s',
                    level=logging.DEBUG,
                    filename='vk_bot_log.log')
log_count = 0


def clear_log(f):
    def wrap(*args, **kwargs):
        global log_count
        if log_count >= 200:
            with open('vk_bot_log.log', 'w'):
                pass
            log_count = 1
            f(*args, **kwargs)
        else:
            log_count += 1
            f(*args, **kwargs)

    return wrap


make_log = clear_log(logging.info)


def SQL_commit(f):
    def wrap(*args, **kwargs):
        connection = sqlite3.connect("musicbot.db")
        cursor = connection.cursor()

        sql, success = f(*args, **kwargs)

        try:
            cursor.execute(sql)
        except sqlite3.DatabaseError as err:
            make_log("Ошибка : %s" % err)
        else:
            make_log(success)
            connection.commit()

        cursor.close()
        connection.close()

    return wrap


def SQL_select(f):
    def wrap(*args, **kwargs):
        connection = sqlite3.connect("musicbot.db")
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()

        sql, success = f(*args, **kwargs)

        try:
            cursor.execute(sql)
        except sqlite3.DatabaseError as err:
            make_log("Ошибка : %s" % err)
        else:
            make_log(success)

        selected = cursor.fetchmany(50)
        cursor.close()
        connection.close()
        return selected

    return wrap


@SQL_commit
def make_new_user(chat_id, name):
    sql = """
    INSERT INTO users(chat_id, name)
    VALUES ('{0}', '{1}'); 
    """.format(chat_id,
               name)
    success = "Пользователь {} успешно добавлен".format(name)
    return sql, success


@SQL_commit
def turn_on_search(chat_id):
    sql = """
    UPDATE users
    SET search_is_on = 1
    WHERE chat_id = '{}'
    """.format(chat_id)
    success = "Статус поиска изменен на 1"
    return sql, success


@SQL_commit
def turn_off_search(chat_id):
    sql = """
    UPDATE users
    SET search_is_on = 0
    WHERE chat_id = '{}'
    """.format(chat_id)
    success = "Статус поиска изменен на 0"
    return sql, success


@SQL_commit
def rate(chat_id, rating):
    sql = """
    UPDATE users
    SET rating = {0}
    WHERE chat_id = '{1}'
    """.format(rating, chat_id)
    success = "Бот оценен"
    return sql, success


@SQL_commit
def add_track(track):
    artist = " ".join(track['artist'].split("'"))
    title = " ".join(track['title'].split("'"))

    sql = """
    INSERT INTO tracks(id, artist, title, url, dur, telegram_id)
    VALUES ('{0}','{1}','{2}','{3}', {4}, '{5}')
    """.format(track['id'],
               artist,
               title,
               track['url'],
               track['dur'],
               track['telegram_id'])
    success = "Трек успешно добавлен в базу данных"
    return sql, success


@SQL_commit
def update_track(id, telegram_id):
    sql = """
    UPDATE tracks
    SET telegram_id = '{0}'
    WHERE id = '{1}'
    """.format(telegram_id,
               id)
    success = "Трек успешно добавлен на сервера телеграмм"
    return sql, success


@SQL_commit
def update_page(chat_id, new_val):
    sql = """
    UPDATE users
    SET page = {0}
    WHERE chat_id = {1}
    """.format(new_val,
               chat_id)
    success = "Страница изменина на {0}".format(new_val)
    return sql, success


@SQL_commit
def like_track(chat_id, id):
    sql = """
    INSERT INTO users_tracks
    VALUES ('{0}', '{1}')
    """.format(chat_id, id)
    success = "Трек нравится"
    return sql, success


@SQL_commit
def dislike_track(chat_id, id):
    sql = """
    DELETE FROM users_tracks
    WHERE user_id = '{0}' AND track_id = '{1}'
    LIMIT 1
    """.format(chat_id, id)
    success = "Трек разонравился"
    return sql, success


@SQL_select
def get_tele_playlist(chat_id):
    sql = """
    SELECT id, telegram_id, title, artist, url, dur
    FROM tracks
    INNER JOIN users_tracks
    ON users_tracks.track_id = tracks.id
    WHERE users_tracks.user_id = '{}'
    """.format(chat_id)
    success = "Удачно достал треки"
    return sql, success


@SQL_select
def get_search_status(chat_id):
    sql = """
    SELECT search_is_on
    FROM users
    WHERE chat_id = '{}'
    """.format(chat_id)
    success = "Получен статус поиска"
    return sql, success


@SQL_select
def get_page(chat_id):
    sql = """
    SELECT page
    FROM users
    WHERE chat_id = '{}'
    """.format(chat_id)
    success = "Полученна страница"
    return sql, success


@SQL_select
def get_track(vk_id):
    sql = """
    SELECT *
    FROM tracks
    WHERE id = '{}'
    """.format(vk_id)
    success = "Получен трек"
    return sql, success
