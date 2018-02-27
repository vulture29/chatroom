# 使用说明

## 启动服务端
在chatroom文件夹下, 执行
python server/server_main.py

## 启动客户端
在chatroom文件夹下, 执行
python client/client_main.py

## 客户端使用
- 命令格式: 命令 + 参数1 （+ 参数2）
- 命令总览:
    - register: 注册新用户， 无需参数
    - login: 登录，无需参数
    - (以下命令必须在成功登录后才可执行）
    - create: 新建聊天室，参数1为聊天室名字
    - enter: 进入聊天室，参数1为聊天室名字
    - leave: 离开聊天室，参数1为聊天室名字
    - chat: 聊天室内聊天，参数1为聊天室名字，参数2为发送内容
    - chatat: 私信聊天，参数1为对方用户名，参数2为发送内容
    - chatall: 大厅聊天，参数1为发送内容
    - query: 查看本用户在线时长
    - exit: 退出程序，无需参数

# 注意事项
- 测试运行环境: MacOS Sierra 10.12.6, Python 2.7.13
- 可根据运行机器具体情况改动server.py, client.py中global常量的值，包括ip，端口号，存储文件路径，最大监听数等

# 服务端基本设计思路
- 保持一个连接list，当有新连接加入时把此socket加入该list
- 使用poll监听此socket list，当有socket就绪时，取出socket的信息并进行相应操作。
- 发送信息分三步，首先传递一个4字节的整数代表该消息的metadata长度，接着传递上一步所得长度的metadata，metadata包含了消息的真实长度，最后传输真实消息
- 使用shelve object storage实现在线时长以及用户名存储

# 客户端基本设计思路
- 保持一个连接list，此list只包含stdin和客户端本身的socket
- 使用select监听此list，判断就绪的连接来自stdin或者socket
- 若来自stdin，则在简单确认消息无问题后向服务器发对应请求
- 若来自remote socket，则根据消息信息打印相应的内容
- 发送信息步骤同服务端描述