from urllib.parse import urlencode

from app.plugins import _PluginBase
from app.core.event import eventmanager, Event
from app.schemas.types import EventType, NotificationType
from app.utils.http import RequestUtils
from typing import Any, List, Dict, Tuple
from app.log import logger


class PushPlusMsg(_PluginBase):
    # 插件名称
    plugin_name = "ZAPushPlus"
    # 插件描述
    plugin_desc = "支持使用PushPlus发送消息通知。"
    # 插件图标
    plugin_icon = "Pushplus_A.png"
    # 插件版本
    plugin_version = "1.0"
    # 插件作者
    plugin_author = "za"
    # 作者主页
    author_url = "https://github.com/zau11berer"
    # 插件配置项ID前缀
    plugin_config_prefix = "zapushplus_"
    # 加载顺序
    plugin_order = 29
    # 可使用的用户级别
    auth_level = 1

    # 私有属性
    _enabled = False
    _token = None
    _msgtypes = []

    def init_plugin(self, config: dict = None):
        if config:
            self._enabled = config.get("enabled")
            self._token = config.get("token")
            self._msgtypes = config.get("msgtypes") or []

    def get_state(self) -> bool:
        return self._enabled and (True if self._token else False)

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        pass

    def get_api(self) -> List[Dict[str, Any]]:
        pass

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """
        拼装插件配置页面，需要返回两块数据：1、页面配置；2、数据结构
        """
        # 编历 NotificationType 枚举，生成消息类型选项
        MsgTypeOptions = []
        for item in NotificationType:
            MsgTypeOptions.append({
                "title": item.value,
                "value": item.name
            })
        return [
            {
                'component': 'VForm',
                'content': [
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 6
                                },
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'enabled',
                                            'label': '启用插件',
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'token',
                                            'label': 'PushPlus令牌',
                                            'placeholder': 'c3f0**',
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12
                                },
                                'content': [
                                    {
                                        'component': 'VSelect',
                                        'props': {
                                            'multiple': True,
                                            'chips': True,
                                            'model': 'msgtypes',
                                            'label': '消息类型',
                                            'items': MsgTypeOptions
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                ]
            }
        ], {
            "enabled": False,
            'token': '',
            'msgtypes': []
        }

    def get_page(self) -> List[dict]:
        pass

    @eventmanager.register(EventType.NoticeMessage)
    def send(self, event: Event):
        """
        消息发送事件
        """
        if not self.get_state():
            return

        if not event.event_data:
            return

        msg_body = event.event_data
        # 渠道
        channel = msg_body.get("channel")
        if channel:
            return
        # 类型
        msg_type: NotificationType = msg_body.get("type")
        # 标题
        title = msg_body.get("title")
        # 文本
        text = msg_body.get("text")

        if not title and not text:
            logger.warn("标题和内容不能同时为空")
            return

        if (msg_type and self._msgtypes
                and msg_type.name not in self._msgtypes):
            logger.info(f"消息类型 {msg_type.value} 未开启消息发送")
            return

        try:
            sc_url = "http://www.pushplus.plus/send"
            event_info = {
                "token": self._token,
                "title": title,
                "content": text,
                "template": "txt",
                "channel":"wechat"
            }
            res = RequestUtils(content_type="application/json").post_res(sc_url, json=event_info)
            if res and res.status_code == 200:
                ret_json = res.json()
                code = ret_json.get('code')
                msg = ret_json.get('msg')
                if code == 200:
                    logger.info("PushPlus消息发送成功")
                else:
                    logger.warn(f"PushPlus消息发送，接口返回失败，错误码：{code}，错误原因：{msg}")
            elif res is not None:
                logger.warn(f"PushPlus消息发送失败，错误码：{res.status_code}，错误原因：{res.reason}")
            else:
                logger.warn("PushPlus消息发送失败，未获取到返回信息")
        except Exception as msg_e:
            logger.error(f"PushPlus消息发送异常，{str(msg_e)}")

    def stop_service(self):
        """
        退出插件
        """
        pass