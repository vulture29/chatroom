from client import *


def prompt_help():
    print("this is the help")


if __name__ == "__main__":
    prompt_help()
    client = Client()
    client.start_chat_client()
