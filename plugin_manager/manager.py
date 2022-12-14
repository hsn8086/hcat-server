import importlib
import logging
import os
from typing import Union

from server import HCatServer
from util import log_output


class HCat:
    def __init__(self, server):
        self.event_dict = {}
        self.plugin_list = []
        self.server: HCatServer = server
        self.count = 0

    def event_handle(self, func):
        arg_len = len(func.__annotations__)
        if arg_len > 1:
            raise 'unexpected arguments.'
        elif arg_len == 0:
            raise 'missing arguments'
        event_type = list(func.__annotations__.values())[0]
        if event_type not in self.event_dict:
            self.event_dict[event_type] = []
        self.event_dict[event_type].append(func)

    def __call__(self, e):

        if type(e) in self.event_dict:
            for f in self.event_dict[type(e)]:
                f(e)

    def load_all_plugins(self):
        if not os.path.exists('plugins'):
            os.mkdir('plugins')

        request_list = {}
        # 枚举插件
        for i in os.listdir('plugins'):
            dir_path = os.path.join('plugins', i)
            # 检查文件是否存在
            if os.path.isdir(dir_path) and os.path.exists(os.path.join(dir_path, '__init__.py')):
                module_name = 'plugins.' + i
                # 导入插件
                module = importlib.import_module(module_name)
                # 获取配置
                plugin_config = getattr(module, 'Config')()
                if 'main' in dir(module) and plugin_config.name not in self.plugin_list:
                    self.plugin_list.append(plugin_config.name)
                    request_list[plugin_config.name] = {'plugin_config': plugin_config, 'module': module,
                                                        'work_space': dir_path}
        for k in request_list:
            can_load = True
            plugin_config = request_list[k]['plugin_config']
            for i in plugin_config.depend:
                can_load = can_load and (i in request_list)
            if can_load:
                getattr(request_list[k]['module'], 'main')(self, request_list[k]['work_space'])
                log_output('Plugin', log_level=logging.INFO,
                           text='"{}" is loaded. ver:{}.'.format(plugin_config.name, plugin_config.version))
            else:
                log_output('Plugin', log_level=logging.WARN,
                           text='"{}" could not be loaded, Please check the dependencies: {}.'
                           .format(plugin_config.name,
                                   str(plugin_config.depend)))

    def reload_all_plugins(self):
        self.event_dict.clear()
        for i in self.plugin_list:
            importlib.reload(i)


class PluginConfig:
    def __init__(self):
        self.plugin_name: str = ''
        self.description: str = ''
        self.author: Union[str, list] = ''
        self.depend = []
        self.version: str = '1.0.0'
