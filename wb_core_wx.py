# WindBot Main Core (Bridge)
# May 2024

# Local Imports
from wb_msgr_wx import Messenger
from wb_sql_wx import SQLHelper
from modules.core.main import CoreFunctions

# Standard Lib Imports
import os
import json
import time
import sys

# Third Party Imports
import rel
from colorama import init
from bs4 import BeautifulSoup

class Core(object):
    """Windbot Core Bridging Between Modules and wxapi Messenger"""
    def __init__(self, MSGR):
        self._init_static()

        # Initialize WB DB SQLHelper
        self.wb_db = SQLHelper(self.wb_db_path)

        # Initialize Messenger
        self.msgr = MSGR
        self.launch_msgr_ws()

        # Initialize Handler
        self.hdlr = Handler(self.msgr, self.wb_db)
        self.config_hdlr_static()

    # Initialize static values for Core
    def _init_static(self) -> None:
        # Local Resource Path
        self.project_path = os.path.join(os.path.dirname(__file__))
        self.static_path = os.path.join(self.project_path,'static')
        self.wb_db_path = os.path.join(self.project_path,'windbotDB.db')

        # Initialize Bot Config
        try:
            wb_config_path = os.path.join(self.project_path,'config.json')
            wb_config = json.load(open(wb_config_path))
        except FileNotFoundError:
            # Generate WB config file
            with open(self.wb_config_path, 'w', encoding = 'utf-8') as f:
                init_config = { "botName": "YOUR TRIGGER FOR GROUPCHAT",
                                "botDMInvoker": "YOUR TRIGGER FOR DM",
                                "Sudoers": ["YOUR WXID"],
                                "wxIP": "127.0.0.1",
                                "wxPort": "5555"}
                f.write(json.dumps(init_config, ensure_ascii = False, indent = 4))
            print("Assuming running for the first time. Generating WB Config")
            time.sleep(5)
            sys.exit()

        # WindBot Core Config
        self.BOT_NAME = wb_config["botName"]
        self.BOT_GC_INVOKER = f"@{self.BOT_NAME}"
        self.BOT_DM_INVOKER = wb_config["botDMInvoker"]
        self.SUDO_LIST = wb_config["Sudoers"]
        self.FUNTOOL_IP = wb_config["wxIP"]
        self.FUNTOOL_PORT = wb_config["wxPort"]

        # WebSocket Server Return Msg Types
        self.WS_POSTCHECK_MSG = 5

        self.RECV_TXT_MSG = 1
        self.RECV_PIC_MSG = 3
        self.RECV_TXT_CITE_MSG = 49

        self.PIC_MSG = 500
        self.AT_MSG = 550
        self.TXT_MSG = 555

        self.USER_LIST = 5000
        self.GET_USER_LIST_SUCCSESS = 5001
        self.GET_USER_LIST_FAIL = 5002

        self.ATTATCH_FILE = 5003

        self.HEART_BEAT = 5005

        self.CHATROOM_MEMBER = 5010
        self.CHATROOM_MEMBER_NICK = 5020

        self.PERSONAL_INFO = 6500
        self.DEBUG_SWITCH = 6000
        self.PERSONAL_DETAIL = 6550
        self.DESTROY_ALL = 9999
        self.STATUS_MSG = 10000

    # On WebsocketApp Open
    def on_open(self, ws):
        # Initialize WB DB (If not yet)
        self.wb_db._usr_table_init()
        self.wb_db._group_overview_table_init() 

        # Refresh User Data
        self.msgr.get_wxuser_list()

        # Update Admin List
        for wxid in self.SUDO_LIST:
            self.wb_db.update('Users', 'powerLevel', 3, "wxid", wxid)

        start_time = time.strftime("%Y-%m-%d %X")
        self.msgr.send_txt_msg(f"启动完成\n{start_time}", self.SUDO_LIST[0])

        # ASCII Art Credit: FigLet & Me
        start_ascii_art = ("",
        "#######################################################",
        "# ___       ______       ________________      _____  #",
        "# __ |     / /__(_)____________  /__  __ )_______  /_ #",
        "# __ | /| / /__  /__  __ \  __  /__  __  |  __ \  __/ #",
        "# __ |/ |/ / _  / _  / / / /_/ / _  /_/ // /_/ / /_   #",
        "# ____/|__/  /_/  /_/ /_/\__,_/  /_____/ \____/\__/   #",
        "#                                                     #",
        "#######################################################",
        "")
        print("\n".join(start_ascii_art))

    # On WebsocketApp Error (Unlikely)
    def on_error(self, ws, error):
        output(f"Error: {error}",'ERROR','HIGHLIGHT','RED')

    # On Websocket Server Close (Very Unlikely)
    def on_close(self, ws, signal, status):
        output("Server Closed",'WARNING','HIGHLIGHT','WHITE')

    # On Websocket Message (wx message)
    def on_localapi_message(self, ws, message):
        j = json.loads(message)
        resp_type = j['type']

        # Case Switch 
        action = {
            self.WS_POSTCHECK_MSG: self.hdlr.handle_ws_postcheck,
            self.CHATROOM_MEMBER_NICK: self.hdlr.handle_chat_nick,
            self.AT_MSG: self.hdlr.handle_at_msg,
            self.DEBUG_SWITCH: print,
            self.PERSONAL_INFO: self.hdlr.handle_personal_info,
            self.PERSONAL_DETAIL: self.hdlr.handle_personal_detail,
            self.TXT_MSG: self.hdlr.handle_sent_msg,
            self.PIC_MSG: self.hdlr.handle_sent_msg,
            self.ATTATCH_FILE: self.hdlr.handle_sent_msg,
            self.CHATROOM_MEMBER: self.hdlr.handle_memberlist,
            self.RECV_PIC_MSG: self.hdlr.handle_recv_pic,
            self.RECV_TXT_MSG: self.hdlr.handle_recv_msg,
            self.RECV_TXT_CITE_MSG: self.hdlr.handle_xml_msg,
            self.HEART_BEAT: print,
            self.USER_LIST: self.hdlr.handle_wxuser_list,
            self.GET_USER_LIST_SUCCSESS: print,
            self.GET_USER_LIST_FAIL: print,
            self.STATUS_MSG: self.hdlr.handle_status_msg,
        }
        action.get(resp_type, print)(j)

    # Launch the WebsocketApp of Messenger
    def launch_msgr_ws(self) -> None:
        self.msgr._ws_init(self.FUNTOOL_IP, self.FUNTOOL_PORT,\
                           self.on_open,\
                           self.on_localapi_message,\
                           self.on_error,\
                           self.on_close)

    # Configure some static for Helper Handler
    def config_hdlr_static(self)-> None:
        self.hdlr.BOT_GC_INVOKER = self.BOT_GC_INVOKER
        self.hdlr.BOT_DM_INVOKER = self.BOT_DM_INVOKER

class Handler(object):
    """Handling WebSocket Messages"""
    def __init__(self, MSGR, WBDB):
        self._init_static()
        self.msgr = MSGR
        self.wb_db = WBDB

    def _init_static(self) -> None:
        self.pat_invoker = "拍了拍我"
        self.wb_invite_invokers = ("邀请你","加入群聊")
        self.invite_invokers = ("邀请", "加入群聊")
        self.wb_invite_msg = "感谢您选择WindBot！"
        self.wb_greeting_msg = "欢迎进群"

    # wxapi: handle status message
    def handle_status_msg(self, msgJson) -> None:
        vis_content = msgJson["content"]["content"]

        # User Pats WindBot
        if self.pat_invoker in vis_content:
            output(vis_content, "PAT", background = "MINT")
            # CoreFunctions.pat_wb(msgJson)

        # WindBot is Invited into a new Groupchat
        elif all(i in vis_content for i in self.wb_invite_invokers):
            output(vis_content)
            output("WindBot is being invited to a new group. Refreshing...")
            self.msgr.get_wxuser_list()

            roomid = msgJson['content']['id1']
            self.msgr.send_txt_msg(self.wb_invite_msg, wxid = roomid)

        # New User Join Groupchat 
        elif all(i in vis_content for i in self.invite_invokers):
            roomid = msgJson['content']['id1']
            output(f"New User Joined {roomid}. Refreshing...")
            self.msgr.get_wxuser_list()
            self.msgr.send_txt_msg(self.wb_greeting_msg, wxid = roomid)

    # wxapi: handle sent message
    def handle_sent_msg(self, msgJson) -> None:
        output(msgJson['content'], mode = 'HIGHLIGHT')

    # wxapi: handle xml message *A bit Broken :|
    def handle_xml_msg(self, msgJson) -> None:
        # Handles Shared Links and refermsg
        msgXml = msgJson['content']['content'].replace('&amp;','&')\
                                            .replace('&lt;','<')\
                                            .replace('&gt;','>')
        soup = BeautifulSoup(msgXml, features = "xml")

        try:
            if soup.appname.string == "哔哩哔哩":
                bili_text = f"BiliBili Video: {soup.title.string}"
                bili_text += f"\nURL: {soup.url.string}"
                output(bili_text, logtype = 'GROUPCHAT')

        except Exception as e:
            # XMLs are used in refermsg as well
            refmsg = soup.refermsg

            msgJson = {
                'content':soup.select_one('title').text,
                'refcontent': refmsg.select_one('content').text,
                'refnick': refmsg.select_one('displayname').text,
                'id':msgJson['id'],
                'id1':msgJson['content']['id2'],
                'id2': refmsg.select_one('chatusr').text,
                'id3':'',
                'srvid':msgJson['srvid'],
                'time':msgJson['time'],
                'type':msgJson['type'],
                'wxid':msgJson['content']['id1']
            }
            self.handle_recv_msg(msgJson)

    # wxapi: handle at message * Doesn't Work As Expected. Archived Here
    def handle_at_msg(self, msgJson) -> None:
        output("Received AT_MSG (FINALLY?)")
        output(msgJson)

    # wxapi: handle picture message
    def handle_recv_pic(self, msgJson) -> None:
        output("Received Image")
        # msgJson = msgJson['content']
        #
        # if msgJson['id2']:
        #     roomid = msgJson['id1'] #群id
        #     sender_id = msgJson['id2'] #个人id
        #
        #     nickname = sql_fetch(cur,f'r{roomid[:-9]}',['groupUsrName'],\
        #                         f"wxid = '{sender_id}'")[0][0]
        #     roomname = sql_fetch(cur,'Groupchats',['groupname'],\
        #                          f'roomid = {roomid[:-9]}')[0][0]
        #     # Terminal Log
        #     output(f'{roomname}-{nickname}: [IMAGE]','GROUPCHAT')
        # else:
        #     sender_id = msgJson['id1'] #个人id
        #     nickname = sql_fetch(cur,'Users',['realUsrName'],\
        #                         f"wxid = '{sender_id}'")[0][0]
        #     # Terminal Log
        #     output(f'{nickname}: [IMAGE]','DM')

    # wxapi: handle text message
    def handle_recv_msg(self, msgJson) -> None:
        isCite = False
        # If msg is a cite message
        if msgJson.get("refnick", -1) != -1 and \
            msgJson.get("refcontent", -1) != -1:
            isCite = True

        # If msg comes from a Chatroom
        if msgJson["wxid"].endswith("@chatroom"):
            room_id = msgJson['wxid'] #群id
            room_num = room_id.replace("@chatroom", "")
            sender_id = msgJson['id1'] #个人id

            nickname = self.wb_db.fetch(f"r{room_num}","groupUsrName",\
                                "wxid", sender_id)[0][0]

            roomname = self.wb_db.fetch("Groupchats","groupname",\
                                "room_id", f"r{room_num}")[0][0]

            # Handle User Calls
            message = msgJson["content"].replace('\u2005','')

            if message.startswith(self.BOT_GC_INVOKER):
                usr_call = message.replace(self.BOT_GC_INVOKER, "", 1)
                output(f"{roomname}-{nickname}: {usr_call}", "CALL", "HIGHLIGHT")
                self.handle_recv_call(usr_call, sender_id, room_id)
                return

            # Log Normal Messages
            if isCite == False:
                output(f'{room_num}-{nickname}: {message}','GROUPCHAT')
            else:
                # little patch that makes no sense at all
                # WX Why you do this to me!!!!! *Dies*
                refcontent = msgJson['refcontent'].split("\n")
                if len(refcontent) > 1:
                    refcontent = refcontent[4]
                else:
                    refcontent = refcontent[0]
                output(f"{roomname}-{nickname}: {message}\n\
                    「-> {msgJson['refnick']} : {refcontent}",\
                    'GROUPCHAT')
        # If msg comes from DM 
        else:
            sender_id = msgJson['wxid'] #个人id

            nickname = self.wb_db.fetch("Users",["realUsrName"],\
                                f"wxid = '{sender_id}'")[0][0]

            # Handle User Calls
            message = msgJson['content'].replace('\u2005','')
            if message.startswith(self.BOT_DM_INVOKER):
                usr_call = message.replace(self.BOT_DM_INVOKER, "", 1)

                output(f"{nickname}: {usr_call}", "CALL", "HIGHLIGHT")
                self.handle_recv_call(usr_call, sender_id, sender_id) 
                return

            # Terminal Log Normal Messages
            if not isCite:
                output(f'{nickname}: {message}','DM')
            else:
                output(f"{nickname}: {message}\n\
                    「-> {msgJson['refnick']} : {msgJson['refcontent']}",'DM')

        # Normal Messages go through a keyword trigger
        isRoom = bool(roomid)
        self.handle_recv_keyword(message, msgJson["wxid"], isRoom)

    # Helper of handle_recv_msg. Checks Keyword Triggers.
    def handle_recv_keyword(self, keyword, destination, isRoom) -> None: #@TODO
        # RESPOND TO KEYWORD
        if keyword == 'help':
            # help_path = os.path.join(resource_path,"Help")
            if isRoom == True:
                # Send Chatroom Help
                pass
            else:
                # Send DM Help
                pass
        elif keyword == "ping":
            self.msgr.send_txt_msg("pong", wxid = destination)
        elif keyword == "pong":
            self.msgr.send_txt_msg("ping", wxid = destination)
        elif keyword.lower() == "wb":
            resp_list = ["您好!","我可以帮到您些什么?"]
            self.msgr.send_txt_msg(random.choice(resp_list), wxid = destination)

    # Helper of handle_recv_msg, Handles function call processes1.
    def handle_recv_call(self, usr_call, usr_id, destination) -> None: #@TODO
        output("CALLED")

    # Character Q2B
    def Q2B(self, uchar) -> str:
        """单个字符 全角转半角"""
        inside_code = ord(uchar)
        if inside_code == 0x3000:
            inside_code = 0x0020
        else:
            inside_code -= 0xfee0
        if inside_code < 0x0020 or inside_code > 0x7e: #转完之后不是半角字符返回原来的字符
            return uchar
        return chr(inside_code)

    # String Q2B
    def stringQ2B(self, ustring) -> str:
        """把字符串全角转半角"""
        return "".join([Q2B(uchar) for uchar in ustring])
    
    # Handles the WebSocket Server Post Check.
    def handle_ws_postcheck(self, j) -> None:
        output("WebSocket Server CHECKED", background = "WHITE")

    #################### USER DB RELATED FUNCTIONS BELOW #################### 
    # Handles the bot account's contact list.
    def handle_wxuser_list(self, j) -> None:
        for (i,item) in enumerate(j["content"]):
            output(f"[{i}] {item['wxid']} {item['name']}")

            # If item is Chatroom
            if item["wxid"].endswith("@chatroom"):
                room_id = item["wxid"].replace("@chatroom", "")
                group_name = item["name"]

                # Check if Chatroom existed in record
                res = self.wb_db.fetch("Groupchats", "*", "roomid", room_id)

                # Does not exist, insert groupchat info into record
                if len(res) == 0:
                    self.wb_db.insert('Groupchats',\
                                ['roomid','groupname','announce','rssPush'],\
                                [room_id, group_name, 1, 0], 'roomid', room_id)
                    self.wb_db._gc_table_init(f"r{room_id}")

                # Exists, update groupchat infomation
                else:
                    self.wb_db.update('Groupchats','groupname', group_name,\
                                      "roomid", room_id)

            # If item is single user
            else:
                self.wb_db.insert('Users',['wxid','wxcode','realUsrName'],\
                                  [item['wxid'],item['wxcode'],item['name']],\
                                  'wxid', item['wxid'])

        # Recursively start to update chatroom's members
        # output(item['wxid'])
        self.msgr.get_chatroom_memberlist(item['wxid'])

    # Handles memberlist for each Chatroom.
    def handle_memberlist(self, j) -> None:
        data = j["content"]
        for room in data:
            room_id = room["room_id"].replace("@chatroom", "")

            members = room['member']
            for m in members:
                self.wb_db.insert(f"r{room_id}", ["wxid"], [m], "wxid", m)
                self.wb_db.insert("Users",["wxid"], [m], "wxid", m)
                self.msgr.get_chat_nick_p(m, room_id)

    # Handles a single User's nickname in a Chatroom.
    def handle_chat_nick(self, j) -> None:
        data = eval(j['content'])

        nickname = data['nick']
        wxid = data['wxid']
        room_id = data['roomid'].replace("@chatroom", "")

        self.wb_db.update(f"r{room_id}", "groupUsrName", nickname,\
                    "wxid", wxid)

    # Handles a single User's details. @TODO
    def handle_personal_detail(self, j) -> None:
        output(j)

    # Handles a single User's info. @TODO
    def handle_personal_info(self, j) -> None:
        output(j)

# Custom Print Wrapper
def output(msg, logtype='SYSTEM', mode='DEFAULT', background='DEFAULT'):
    LogColor = {
        'SYSTEM': '034',
        'ERROR': '037',
        'GROUPCHAT': '036',
        'DM' : '033',
        'HEART_BEAT': '035',
        'PAT': '037',
        'SEND': '032',
        'CALL' : '031',
        'WARNING': '031',
        'CREATE_LINK':'032',
        'STOP_LINK':'031',
        'RSS': '037'
    }
    LogMode = {
        'DEFAULT': '0',
        'HIGHLIGHT': '1',
        'UNDERLINE': '4'
    }
    LogBG = {
        'DEFAULT': '',
        'RED' : ';41',
        'YELLOW' : ';43',
        'BLUE' : ';44',
        'WHITE' : ';47',
        'GREEN' : ';42',
        'MINT' : ';46',
        'PURPLE' : ';45'
    }
    color = LogColor.get(logtype)
    mode = LogMode.get(mode)
    bg = LogBG.get(background)

    now = time.strftime("%Y-%m-%d %X")

    # Shorten logs of too long messages
    line_cnt = msg.count('\n') + 1
    if line_cnt > 10 and logtype != 'ERROR':
        msg = "\n".join(msg.split("\n")[:10])
        msg += '\n......'

    print(f"[{now} \033[{mode};{color}{bg}m{logtype}\033[0m] {msg}")

    # Write Error Logs on to Local File
    # if logtype == 'ERROR':
    #     error_log_file = open('ErrorLog.txt','a')
    #     error_log_file.write(f"[{now} {logtype}] {msg}\n")
    #     error_log_file.close()

    # Store Log into latest_logs list
    # if logtype != 'HEART_BEAT':
    #     if len(latest_logs) == 20:
    #         latest_logs.pop(0)
    #     latest_logs.append(f"[{now} {logtype}] {msg}")

# Main Invoker on Program Run
def main():
    # Initialize Colorama Windows Colorful Output
    init(autoreset = True)

    # Set dispatcher to automatic reconnection
    # 5 second reconnect delay if connection closed unexpectedly
    WB_MSGR = Messenger()
    WB_CORE = Core(WB_MSGR)

    WB_MSGR.ws.run_forever(dispatcher = rel, reconnect = 5)
    rel.signal(2, rel.abort)  # Keyboard Interrupt
    rel.dispatch()

if __name__ == "__main__":
    main()
        
