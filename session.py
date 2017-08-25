# -*- coding: utf-8 -*-
import vk_api
import bot_config
from vk_api.audio import VkAudio
from SQL import make_log


class Session:
    def __init__(self):
        self.vk_session = self.vk_auth()
        self.tracks = {}

    @staticmethod
    def vk_auth():
        try:
            vk_session = vk_api.VkApi(login=bot_config.login,
                                      password=bot_config.password,
                                      client_secret=bot_config.client_secret,
                                      app_id=bot_config.app_id,
                                      token=bot_config.token_vk)
            vk_session.auth()
            return vk_session
        except vk_api.AuthError as error_msg:
            make_log(error_msg)

    def make_search(self, track, chat_id):
        vkaudio = VkAudio(self.vk_session)
        self.tracks[chat_id] = vkaudio.search(track, offset=0)

    def my_search(self):
        vkaudio = VkAudio(self.vk_session)
        audio = vkaudio.get(owner_id=34442400)
        return audio
