# WindBot Main Core (Bridge)
# May 2024

# Local Imports
from wb_msgr_wx import Messenger
from wb_sql_wx import SQLHelper

# Standard Lib Imports
import os
import json
import time
import sys
import random
import importlib
import re
from threading import Thread
import traceback

# Third Party Imports
import rel
from colorama import init
from bs4 import BeautifulSoup

class Core(object):
    """Windbot Core Bridging Between Modules and wxapi Messenger"""
    def __init__(self, MSGR):
        self._init_static()

        # ASCII Art Credit: FigLet & Me
        start_ascii_art = ("",
        "#######################################################",
        "#                                                     #",
        "# ___       ______       ________________      _____  #",
        "# __ |     / /__(_)____________  /__  __ )_______  /_ #",
        "# __ | /| / /__  /__  __ \  __  /__  __  |  __ \  __/ #",
        "# __ |/ |/ / _  / _  / / / /_/ / _  /_/ // /_/ / /_   #",
        "# ____/|__/  /_/  /_/ /_/\__,_/  /_____/ \____/\__/   #",
        "#                                                     #",
        "#    ____ ____ ____ ____ ____ ___ ____ ____ ____ ___  #",
        "#    |--< |=== |--- |--| |___  |  [__] |--< |=== |__> #",
        "#                                                     #",
        "#######################################################",
        "")
        print("\n".join(start_ascii_art))

        # Initialize WB DB SQLHelper
        self.wb_db = SQLHelper(self.wb_db_path)

        # Initialize Messenger
        self.msgr = MSGR
        self.launch_msgr_ws()

        # Initialize ModuleLoader
        self.mdldr = ModuleLoader(self.BOT_MODULES, self.modules_path,\
                                  self.LOADED_MODULES)

        # Initialize Handler
        self.hdlr = Handler(self.msgr, self.wb_db, self.LOADED_MODULES)
        self.config_hdlr_static()

    # Initialize static values for Core
    def _init_static(self) -> None:
        # Local Resource Path
        self.project_path = os.path.join(os.path.dirname(__file__))
        self.static_path = os.path.join(self.project_path,'static')
        self.modules_path = os.path.join(self.project_path,'modules')
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
                                "Modules": ["core"],
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
        self.BOT_MODULES = wb_config["Modules"]
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

        self.ATTACH_FILE = 5003

        self.HEART_BEAT = 5005

        self.CHATROOM_MEMBER = 5010
        self.CHATROOM_MEMBER_NICK = 5020

        self.PERSONAL_INFO = 6500
        self.DEBUG_SWITCH = 6000
        self.PERSONAL_DETAIL = 6550
        self.DESTROY_ALL = 9999
        self.STATUS_MSG = 10000

        # Loaded Modules 
        self.LOADED_MODULES = dict()

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
            self.ATTACH_FILE: self.hdlr.handle_sent_msg,
            self.CHATROOM_MEMBER: self.hdlr.handle_memberlist,
            self.RECV_PIC_MSG: self.hdlr.handle_recv_pic,
            self.RECV_TXT_MSG: self.hdlr.handle_recv_msg,
            self.RECV_TXT_CITE_MSG: self.hdlr.handle_xml_msg,
            self.HEART_BEAT: self.hdlr.handle_hb,
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
        self.hdlr.SUDO_LIST = self.SUDO_LIST

class Handler(object):
    """Handling WebSocket Messages"""
    def __init__(self, MSGR, WBDB, LDMD):
        self._init_static()
        self.msgr = MSGR
        self.wb_db = WBDB
        self.loaded_modules = LDMD
        self._init_func_collection()

    # Initialize static variables
    def _init_static(self) -> None:
        self.pat_invoker = "拍了拍我"
        self.wb_invite_invokers = "邀请你加入了群聊"
        self.invite_invokers = ("邀请", "加入了群聊")
        self.wb_invite_msg = "感谢您选择WindBot！"
        self.wb_invite_msg += "\n请使用listfunc命令来查看所有功能。"
        self.wb_invite_repo = "WB进入了新群聊： "
        self.wb_greeting_msg = "欢迎进群"
        self.wb_summon_msg = ("您好!","我可以帮到您些什么?")
        self.wb_empty_call_msg = "请指明需要使用的功能。"
        self.power_weak_msg = "您的权限不足。"
        self.func_disabled_msg = "该功能暂时关闭。"
        self.unlogged_nickname_msg = "您可能更新了昵称，但是未被WB记录。请稍后再试。"
        self.depreciated_func_msg = {
            "b30": "Arcaea分数相关功能因Estertion查分器下线原因暂停使用。",
            "arcrecent": "Arcaea分数相关功能因Estertion查分器下线原因暂停使用。",
            "mb40": "请移步maimai b50。\n指令: mb50"
        }
        self.undisturbed_hb = 0
        self.uptime_hb_cnt = 0

    # Initialize the function collection
    def _init_func_collection(self) -> None:
        self.all_func = dict()
        self.avail_usr_func = dict()
        self.marked_usr_func = dict()
        self.avail_mngng_func = dict()
        self.usr_func_called_ranking = dict()

        for m in self.loaded_modules:
            module_instance = self.loaded_modules[m]
            user_func = module_instance.USER_FUNCTIONS
            mngng_func = module_instance.MNGNG_FUNCTIONS

            module_name = module_instance.META.get_name()

            usr_func_avail = dict()
            usr_func_mark = dict()
            usr_func_cnt = dict()
            mngng_func_avail = dict()
            for keyword in user_func:
                usr_func_avail[keyword] = True
                usr_func_mark[keyword] = False
                self.usr_func_called_ranking[keyword] = 0
                self.all_func[keyword] = user_func[keyword]

            for keyword in mngng_func:
                mngng_func_avail[keyword] = True
                self.all_func[keyword] = mngng_func[keyword]

            self.avail_usr_func[module_name] = usr_func_avail
            self.marked_usr_func[module_name] = usr_func_mark
            self.avail_mngng_func[module_name] = mngng_func_avail

    # wxapi: handle status message
    def handle_status_msg(self, msgJson) -> None:
        vis_content = msgJson["content"]["content"]
        from_id = msgJson["content"]["id1"]

        # User Pats WindBot
        if self.pat_invoker in vis_content:
            output(vis_content, "PAT", background = "MINT")
            self.handle_pat_wb(msgJson)

        # WindBot is Invited into a new Groupchat
        elif self.wb_invite_invokers in vis_content:
            output(vis_content)
            output("WindBot is being invited to a new group. Refreshing...")
            self.msgr.get_wxuser_list()

            self.msgr.send_txt_msg(self.wb_invite_msg, wxid = from_id)
            self.msgr.send_txt_msg(self.wb_invite_repo + from_id,\
                                   wxid = self.SUDO_LIST[0])

        # New User Join Groupchat 
        elif all(i in vis_content for i in self.invite_invokers):
            output(f"New User Joined {from_id}. Refreshing...")
            self.msgr.get_wxuser_list()
            self.msgr.send_txt_msg(self.wb_greeting_msg, wxid = from_id)

    # Helper of handle_status_msg. Handles pats
    def handle_pat_wb(self, msgJson):
        from_id = msgJson["content"]["id1"]
        vis_content = msgJson["content"]["content"]

        # If Pat comes from a Chatroom
        if from_id.endswith("@chatroom"):
            room_num = from_id.replace("@chatroom", "")
            usr_nickname = re.match(r"[^[]*\"([^]]*)\"", vis_content).groups()[0]
            # Getting wxid from usr_nickname
            wxid_query = self.wb_db.fetch(f"r{room_num}", ["wxid"],\
                             "groupUsrName", usr_nickname)

            # If the wxid has been updated but not recorded
            if wxid_query == []:
                self.msgr.send_txt_msg(self.unlogged_nickname_msg, from_id)
                # Update the User DB
                self.msgr.get_wxuser_list()
                return
            else:
                usr_id = wxid_query[0][0]
        # Pat Comes from DM 
        else:
            usr_id = from_id
        
        # Increment Recorded patTimes by 1
        rec_pat_times = self.wb_db.fetch("Users",['patTimes'],\
                                "wxid", usr_id)[0][0]
        new_pat_times = rec_pat_times + 1
        self.wb_db.update("Users","patTimes", new_pat_times,\
                          "wxid", usr_id)

        # PatAction
        ## Ban Check
        if self.banned_check(usr_id) == False:
            return

        ## Trigger PatAction
        pat_data = self.wb_db.fetch("Users", ["patAction"],\
                                    "wxid", usr_id)[0][0]
        # If user did not bind any action
        if pat_data == "-1":
            reply = "您没有绑定PatAction指令。\n"
            reply += f"示例绑定: {self.BOT_GC_INVOKER} bind pat mb50\n"
            reply += f"如果您不想再看到这条信息，请使用 {self.BOT_GC_INVOKER} bind pat nop"
            self.msgr.send_txt_msg(reply, from_id)
        # User binded action
        else:
            call_data = pat_data.split(" ")
            func_keyword = call_data[0]
            func_data = call_data[1:]

            if func_keyword not in ["nop", "swym"]:
                reply = f"正在执行『{pat_data}』"
                self.msgr.send_txt_msg(reply, from_id)

            self.pre_call(func_keyword, func_data, usr_id ,from_id)
            return

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

        if soup.appname.string == "哔哩哔哩":
            bili_text = f"BiliBili Video: {soup.title.string}"
            bili_text += f"\nURL: {soup.url.string}"
            output(bili_text, logtype = "GROUPCHAT")
            return
        else:
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

    #################### USER CALL RELATED FUNCTIONS BELOW ################## 
    # wxapi: handle text message
    def handle_recv_msg(self, msgJson) -> None:
        self.undisturbed_hb = 0
        isCite = False
        # If msg is a cite message
        if msgJson.get("refnick", -1) != -1 and \
            msgJson.get("refcontent", -1) != -1:
            isCite = True

        # If msg comes from a Chatroom
        if msgJson["wxid"].endswith("@chatroom"):
            isRoom = True

            room_id = msgJson['wxid'] #群id
            room_num = room_id.replace("@chatroom", "")
            sender_id = msgJson['id1'] #个人id

            nickname = self.wb_db.fetch(f"r{room_num}",["groupUsrName"],\
                                "wxid", sender_id)[0][0]

            roomname = self.wb_db.fetch("Groupchats",["groupname"],\
                                "roomid", room_num)[0][0]

            # Handle User Calls
            message = msgJson["content"].replace('\u2005','')

            if message.startswith(self.BOT_GC_INVOKER):
                usr_call = message.replace(self.BOT_GC_INVOKER, "", 1)
                output(f"{roomname}-{nickname}: {usr_call}", "CALL", "HIGHLIGHT")
                self.handle_recv_call(usr_call, sender_id, room_id)
                return

            # Log Normal Messages
            if isCite == False:
                output(f'{roomname}-{nickname}: {message}','GROUPCHAT')
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
            isRoom = False
            sender_id = msgJson['wxid'] #个人id

            nickname = self.wb_db.fetch("Users",["realUsrName"],\
                                "wxid", sender_id)[0][0]

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
            self.msgr.send_txt_msg(random.choice(self.wb_summon_msg),\
                                   wxid = destination)

    # Helper of handle_recv_msg. Handles function call processes.
    def handle_recv_call(self, usr_call, usr_id, destination) -> None:
        # Handles Q2B, Parsing User Call Data
        call_data = self.stringQ2B(usr_call.strip()).split(" ")
        ## Handle Empty Call
        if len(call_data) == 1 and call_data[0] == '':
            output("Did not specify function","WARNING",background = "WHITE")
            self.msgr.send_txt_msg(self.wb_empty_call_msg, destination)
            return
        ## Handle Mobile @
        if len(call_data) > 1 and call_data[0] == '':
            call_data = call_data[1:]

        # Retrieving User Call Data
        func_keyword = call_data[0].lower()
        func_data = call_data[1:]

        # Calling Function Execution Helper
        self.pre_call(func_keyword, func_data, usr_id, destination)

    # Helper of handle_recv_call. Handles function call classifying.
    def pre_call(self, func_keyword, func_data, usr_id, destination) -> None:
        # Ban Check
        if self.banned_check(usr_id) == False:
            return

        # Depreciated Functions
        if func_keyword in self.depreciated_func_msg:
            self.msgr.send_txt_msg(self.depreciated_func_msg[func_keyword],\
                                 destination)
            return

        # Non-Existent Functions
        if func_keyword not in self.all_func:
            output("Called non-existent function","WARNING",\
                   background = 'WHITE')
            func_non_existent_msg = \
                    f"没有该指令： {func_keyword}\n请使用listfunc查找您需要的指令。"

            self.msgr.send_txt_msg(func_non_existent_msg,\
                                 destination)
            return

        # User Functions
        for module in self.avail_usr_func:
            if func_keyword in self.avail_usr_func[module]:
                # Check if functions is disabled
                func_status = self.avail_usr_func[module][func_keyword]
                if func_status == False:
                    self.msgr.send_txt_msg(self.func_disabled_msg,\
                                           destination)
                    return

                execute_args = [func_data, usr_id, destination]
                ######## WATERPROOF TAPE PATCH ########
                ## Provide Access to WB Core Data for the Core Module.   
                if module == "Core":
                    execute_args.append([self.avail_usr_func,\
                                         self.avail_mngng_func,\
                                         self.wb_db,
                                         self.BOT_GC_INVOKER,
                                         self.all_func,
                                         self.marked_usr_func,
                                         self.msgr,
                                         self.usr_func_called_ranking,
                                         self.SUDO_LIST])
                ## Provide Access to WB Data for the Maimai Module.
                elif module == "Maimai":
                    execute_args.append([self.wb_db,\
                                         self.BOT_GC_INVOKER])

                ######## WATERPROOF TAPE PATCH ########

                # User Functions will be executed in threads
                tFunc = Thread(target = self.execute_call,\
                                args = (func_keyword,\
                                        execute_args, True))
                tFunc.start()
                return

        # Managing Functions
        for module in self.avail_mngng_func:
            if func_keyword in self.avail_mngng_func[module]:
                # Power Check for Managing Functions
                if self.power_check(usr_id, 3) == False:
                    self.msgr.send_txt_msg(self.power_weak_msg,\
                                           destination)
                    return

                execute_args = [func_data, usr_id, destination]
                ######## WATERPROOF TAPE PATCH ########
                ## Provide Access to WB Core Data for the Core Module.   
                if module == "Core":
                    execute_args.append([self.avail_usr_func,
                                         self.avail_mngng_func,
                                         self.wb_db,
                                         self.BOT_GC_INVOKER,
                                         self.all_func,
                                         self.marked_usr_func,
                                         self.msgr,
                                         self.usr_func_called_ranking,
                                         self.SUDO_LIST])
                ######## WATERPROOF TAPE PATCH ########

                # Managing Functions will be blocking
                self.execute_call(func_keyword,\
                                    execute_args, False)
                return

    # Helper of pre_call. Do actual function calling.
    def execute_call(self, req_func_keyword, execute_args, add_use_cnt) -> None:
        req_func = self.all_func[req_func_keyword]
        destination = execute_args[2]
        if add_use_cnt:
            self.usr_func_called_ranking[req_func_keyword] += 1
        try:
            reply_package = req_func(execute_args)

        # Error Happened. Push Error Msg to destination
        except Exception as e:
            output(f"ERROR ON CALL: {e}","ERROR","HIGHLIGHT",'RED')
            output(traceback.format_exc(),"ERROR","HIGHLIGHT","RED")
            ## Compose the Error Message.
            err_msg = f"WB遇到了一些意料外的问题。\n指令： {req_func_keyword}"
            err_msg += f"\n错误细节： {e}"
            err_msg += "\n请检查指令参数。"
            err_msg += "您也可以使用reperr和fdbk指令向WDS反馈这个问题。"
            err_msg += f"\n反馈指令：{self.BOT_GC_INVOKER} reperr {req_func_keyword}"
            self.msgr.send_txt_msg(err_msg, destination)
            return

        # No Error Happened. Move on to reply 
        # Multiple Replies
        if isinstance(reply_package, list):
            for reply in reply_package:
                content = reply["content"]
                if reply["type"] == "TEXT":
                    self.msgr.send_txt_msg(content, destination)
                elif reply["type"] == "ATTACH":
                    self.msgr.send_attach(content, destination)
                elif reply["type"] == "PIC":
                    self.msgr.send_pic(content, destination)
        # Single Reply
        else:
            content = reply_package["content"]
            if reply_package["type"] == "TEXT":
                self.msgr.send_txt_msg(content, destination)
            elif reply_package["type"] == "ATTACH":
                self.msgr.send_attach(content, destination)
            elif reply_package["type"] == "PIC":
                self.msgr.send_pic(content, destination)
        return

    # Helper to retrieve the banned status of calling user.
    def banned_check(self, wxid) -> bool:
        caller_ban_status = self.wb_db.fetch("Users",["banned"],\
                                      "wxid", wxid)[0][0]
        if bool(caller_ban_status) == True:
            return False
        return True

    # Helper to retrieve the powerlevel of calling user.
    def power_check(self, wxid, req_power) -> bool:
        caller_lvl = self.wb_db.fetch("Users",["powerLevel"],\
                                      "wxid", wxid)[0][0]
        if caller_lvl < req_power:
            return False
        return True

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
        return "".join([self.Q2B(uchar) for uchar in ustring])
    
    #################### WB & MISC RELATED FUNCTIONS BELOW ################## 
    # Handles the WebSocket Server Post Check.
    def handle_ws_postcheck(self, j) -> None:
        output("WebSocket Server CHECKED", background = "WHITE")

    # Handles Hearbeat Messages.
    def handle_hb(self, j) -> None:
        self.undisturbed_hb += 1
        self.uptime_hb_cnt += 1

        # Local Heartbeat Log
        if self.undisturbed_hb < 5:
            output("Success","HEART_BEAT","HIGHLIGHT")
        elif self.undisturbed_hb == 5:
            output("Undisturbed in 5 min. Hiding heartbeat logs. zZZ",\
                   logtype = "HEART_BEAT",mode = "HIGHLIGHT")

    #################### USER DB RELATED FUNCTIONS BELOW #################### 
    # Handles the bot account's contact list.
    def handle_wxuser_list(self, j) -> None:
        for (i,item) in enumerate(j["content"]):
            output(f"[{i+1}] {item['wxid']} {item['name']}")

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

class ModuleLoader(object):
    """Dynamically Loads and Initializes Modules"""
    def __init__(self, include_modules, modules_path, instances_dict):
        self.include_modules = include_modules
        self.modules_path = modules_path
        self.found_modules = dict()
        self.module_instances = instances_dict
        self.std_filename = "main"
        self.scan_module()
        self.aggregate_load()

    def scan_module(self) -> None:
        output("Scanning Modules", background = "WHITE")
        for item in os.scandir(self.modules_path):
            if item.is_dir():
                # Skip __pycache__
                if item.name == "__pycache__":
                    continue

                # Check if main.py is present
                main_found = False
                for sub_item in os.scandir(item.path):
                    if sub_item.is_file():
                        if sub_item.name == f"{self.std_filename}.py":
                            output(f"Found Module [{item.name}]",\
                                   background = "WHITE")
                            main_found = True
                            import_path = f"modules.{item.name}.{self.std_filename}"
                            self.found_modules[item.name] = import_path
                            break

                # Warn the user if no main.py present
                if not main_found:
                    output(f"No main.py found in module folder '{item.name}'",\
                           "WARNING", background = "WHITE")

        output(f"Found {len(self.found_modules)} Modules", background = "WHITE")

    def aggregate_load(self) -> None:
        output(f"Loading Modules {str(self.include_modules)}",\
               background = "WHITE")
        for module_name in self.include_modules:
            # Check if Designated Module is found
            if module_name not in self.found_modules.keys():
                output(f"User designated Module [{module_name}] not found",\
                       "WARNING", background = "WHITE")
                continue

            # Import the module
            path = self.found_modules[module_name]
            loaded_module = self.load_module(module_name, path)
            self.module_instances[module_name] = loaded_module

    def load_module(self, module_name, file_path) -> list:
        # Importing the Source File

        ## Example from the importlib Documentation
        ## Well that didnt work
        # spec = importlib.util.spec_from_file_location(module_name, file_path)
        # module = importlib.util.module_from_spec(spec)
        # sys.modules[module_name] = module
        # spec.loader.exec_module(module)

        module = importlib.import_module(file_path)

        # Module info with __module_meta__
        module_meta = getattr(module, "__module_meta__")
        name = module_meta.get_name()
        ver = module_meta.get_version()
        author = module_meta.get_author()
        author_str = ", ".join(author)

        # Load the Module Function Class
        module_instance = getattr(module, name)()

        output(f"Loaded Module {name} [Ver {ver}] by {author_str}",\
               background = "WHITE")
        return module_instance

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
