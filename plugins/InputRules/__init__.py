from events.chat import *

from plugin_manager.manager import HCat, PluginConfig


def main(hcat: HCat, workspace: str):
    @hcat.event_handle
    def send_msg(e: SendFriendMsg):
        if e.msg == '':
            e.return_data = ReturnData(ReturnData.ERROR, 'input content cannot be empty')
            del_list = []
            e.cancel = True
        pass


class Config(PluginConfig):
    def __init__(self):
        super().__init__()
        self.name = 'InputRules'
        self.description = 'This is a plug-in that restricts input'
        self.author = 'hsn'
        self.depend = []
        self.version = '1.0.0'
