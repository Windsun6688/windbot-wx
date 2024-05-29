# WindBot Messenger Core - websocket wxapi
# May 2024

# Standard Lib Imports
import json

# Third Party Imports
import websocket
import time

# Local Imports
from wb_core_wx import output

# Initialize WebSocket Settings
websocket._logging._logger.level = -99
# websocket.enableTrace(True)

class Messenger(object):
    """Handling Messages with ws wxapi."""
    def __init__(self):
        # WebSocket msg Types
        self.PIC_MSG = 500
        self.AT_MSG = 550 # Not Working?
        self.TXT_MSG = 555
        self.USER_LIST = 5000
        self.ATTATCH_FILE = 5003
        self.CHATROOM_MEMBERLIST = 5010
        self.DEBUG_SWITCH = 6000
        self.PERSONAL_INFO = 6500
        self.PERSONAL_DETAIL = 6550
        self.DESTROY_ALL = 9999

    def _ws_init(self, WS_IP:str, WS_PORT:int, on_open, on_msg, on_err, on_close):
        ws_server = f"ws://{WS_IP}:{WS_PORT}"
        self.ws = websocket.WebSocketApp(ws_server,\
							on_open = on_open,\
							on_message = on_msg,\
							on_error = on_err,\
							on_close = on_close)

    # Provides a time-based ID for websocket
    def getid(self) -> str:
        return time.strftime("%Y%m%d%H%M%S")

    # websocket debug switch (Not Tested)
    def debug_switch(self) -> None:
        ws_data = {
            'id': self.getid(),
            'type': self.DEBUG_SWITCH,
            'content':'off',
            'wxid':'ROOT',
        }
        self.ws.send(json.dumps(ws_data))

    # websocket destroy all (Not Tested)
    def destroy_all(self) -> None:
        qs={
            'id': self.getid(),
            'type': self.DESTROY_ALL,
            'content':'none',
            'wxid':'node',
        }
        self.ws.send(json.dumps(ws_data))

    # Tells websocket wxapi to send a text message.
    def send_txt_msg(self, msg:str, wxid:str = 'null') -> None:
        ws_data = {
            'id': self.getid(),
            'type': self.TXT_MSG,
            'wxid': wxid,
            'roomid': 'null',
            'content': msg,
            'nickname': 'null',
            'ext': 'null'
        }
        self.ws.send(json.dumps(ws_data))
        output(f'{msg} -> {wxid}','SEND')

    # Tells websocket wxapi to send an attachment.
    def send_attatch(self, filepath:str, wxid:str = 'null') -> None:
        ws_data = {
            'id': self.getid(),
            'type': self.ATTATCH_FILE,
            'wxid': wxid,
            'roomid': 'null',
            'content': filepath,
            'nickname': 'null',
            'ext': 'null'
        }
        self.ws.send(json.dumps(ws_data))
        output(f'File @ {filepath} -> {wxid}','SEND')

    # Tells websocket wxapi to send a (picture) attachment. (Rarely Used)
    def send_pic(self, filepath:str, wxid:str = 'null') -> None:
        ws_data = {
            'id': self.getid(),
            'type': self.PIC_MSG,
            'wxid': wxid,
            'roomid': 'null',
            'content': filepath,
            'nickname': 'null',
            'ext': 'null'
        }
        self.ws.send(json.dumps(ws_data))
        output(f"Media @ {filepath} -> {wxid}",'SEND')

    # Tells websocket wxapi to fetch nicknames of a user in a room.
    def get_chat_nick_p(self, wxid:str, roomid:int) -> None:
        ws_data = {
            'id': self.getid(),
            'type': self.CHATROOM_MEMBER_NICK,
            'wxid': wxid,
            'roomid' : f'{roomid}@chatroom',
            'content' : 'null',
            'nickname': 'null',
            'ext': 'null'
        }
        self.ws.send(json.dumps(ws_data))

    # Tells websocket wxapi to fetch a member list in a room.
    def get_chatroom_memberlist(self, roomid:str = 'null') -> None:
        ws_data = {
            'id': self.getid(),
            'type': self.CHATROOM_MEMBERLIST,
            'roomid': roomid,
            'wxid': 'null',
            'content': 'op:list member',
            'nickname': 'null',
            'ext': 'null'
        }
        self.ws.send(json.dumps(ws_data))

    # Tells websocket wxapi to fetch personal detail of a wx user.
    def get_personal_detail(self, wxid:str) -> None:
        ws_data = {
            'id': self.getid(),
            'type': self.PERSONAL_DETAIL,
            'wxid': wxid,
            'roomid': 'null',
            'content': 'null',
            'nickname': 'null',
            'ext': 'null',
        }
        self.ws.send(json.dumps(ws_data))

    # Tells websocket wxapi to fetch personal info of a wx user.
    # Similar to get_personal_detail 
    def get_personal_info(self, wxid:str) -> None:
        ws_data = {
            'id': self.getid(),
            'type': self.PERSONAL_INFO,
            'content': 'null',
            'wxid': wxid,
            'roomid': 'null',
            'content': 'null',
            'nickname': 'null',
            'ext': 'null',
        }
        self.ws.send(json.dumps(ws_data))

    # Tells websocket wxapi to fetch all contacts of the bot account.  
    def get_wxuser_list(self) -> None:
        ws_data = { 
            'id': self.getid(),
            'type': self.USER_LIST,
            'roomid': 'null',
            'wxid': 'null',
            'content': 'null',
            'nickname': 'null',
            'ext': 'null',
        }
        self.ws.send(json.dumps(ws_data))
