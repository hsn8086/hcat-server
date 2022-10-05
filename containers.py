import time

from flask import jsonify

from server import HCatServer
from util import get_random_token


class EventContainer:
    def __init__(self, data_base, lock):
        self.lock = lock
        self.lock.acquire()
        self.data_base = data_base
        while True:
            rid = get_random_token(8)
            if not self.data_base.exists(rid):
                break
        self.rid = rid
        self.json = {}
        self.can_write = True

    def __call__(self, key, value):
        self.json[key] = value

    def write(self):
        if self.can_write:
            self.data_base.set(self.rid, self.json)
            self.lock.release()
            self.can_write = False

    def __del__(self):
        if self.lock.locked():
            self.lock.release()

    def add(self, key, value):
        self.json[key] = value
        return self


class ReturnData:
    ERROR = 1
    NULL = 2
    OK = 0

    def __init__(self, status=0, msg=''):
        if status == 0:
            status_text = 'ok'
        elif status == 1:
            status_text = 'error'
        elif status == 2:
            status_text = 'null'
        else:
            status_text = 'error'
        self.json_data = {'status': status_text, 'message': msg}

    def add(self, key, value):
        self.json_data[key] = value
        return self

    def json(self):
        return jsonify(self.json_data)

    def __call__(self):
        return self.json_data


class Group:
    def __init__(self, group_id):
        self.id = group_id
        self.name = ''
        self.member_list = []
        self.member_data = {}
        self.owner = ''
        self.admin_list = []
        '''
        verification_method:
        ac:administrator consent--需要管理同意
        fr:free--自由进出
        aw:answer question--需要回答问题
        na:not allowed--不允许加入
        '''
        self.group_settings = {'verification_method': 'ac', 'question': '', 'answer': ''}

    def send_msg(self, server: HCatServer, username, msg):
        for i in self.member_list:
            if i != username:
                # 创建事件
                ec = EventContainer(server.event_log_db, server.event_log_db_lock)
                ec.add('type', 'group_msg'). \
                    add('rid', ec.rid). \
                    add('username', username). \
                    add('group_id', self.id). \
                    add('msg', msg). \
                    add('time', time.time())
                ec.write()

                # 将群聊消息事件写入成员的todo_list
                server.data_db_lock.acquire()
                member_data = server.get_user_data(username)
                member_data['todo_list'].append(ec.json)
                server.data_db.set(i, member_data)
                server.data_db_lock.release()

                del ec