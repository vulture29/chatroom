# -*- coding: utf-8 -*-

from client import *


def prompt_help():
    print(
        """
        命令格式: 命令 + 参数1 （+ 参数2）
        命令总览:
        register: 注册新用户， 无需参数
        login: 登录，无需参数
        create: 新建聊天室，参数1为聊天室名字
        enter: 进入聊天室，参数1为聊天室名字
        leave: 离开聊天室，参数1为聊天室名字
        chat: 聊天室内聊天，参数1为聊天室名字，参数2为发送内容
        chatat: 私信聊天，参数1为对方用户名，参数2为发送内容
        chatall: 大厅聊天，参数1为发送内容
        query: 查看本用户在线时长
        exit: 退出程序，无需参数
        """)


if __name__ == "__main__":
    prompt_help()
    client = Client()
    client.start_chat_client()
