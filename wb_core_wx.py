# WindBot Main Core (Bridge)
# May 2024

# Local Imports
from wb_msgr_wx import Messenger

# Standard Lib Imports
import os
import json
import time
import sys

# Third Party Imports
import rel

class Core(object):
    """Windbot Core Bridging Between Modules and wxapi Messenger"""
    def __init__(self, MSGR):
        self._init_static()
        self.msgr = MSGR
        self.launch_msgr_ws()

    # Initialize static values for Core
    def _init_static(self) -> None:
        # Local Resource Path
        project_path = os.path.join(os.path.dirname(__file__))
        static_path = os.path.join(project_path,'static')

        # Initialize Bot Config
        try:
            wb_config_path = os.path.join(project_path,'config.json')
            wb_config = json.load(open(wb_config_path))
        except FileNotFoundError:
            # Generate WB config file
            with open(wb_config_path, 'w', encoding = 'utf-8') as f:
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

    # On WebsocketApp Open
    def on_open(self, ws):
        # Refresh User Data
        # self.msgr.get_wxuser_list()

        # Update Admin List
        for wxid in self.SUDO_LIST:
            pass

        start_time = time.strftime("%Y-%m-%d %X")
        self.msgr.send_txt_msg(f"启动完成\n{now}", self.SUDO_LIST[0])

        # ASCII Art Credit: FigLet & Me
        start_ascii_art = """

        #######################################################
        # ___       ______       ________________      _____  #
        # __ |     / /__(_)____________  /__  __ )_______  /_ #
        # __ | /| / /__  /__  __ \  __  /__  __  |  __ \  __/ #
        # __ |/ |/ / _  / _  / / / /_/ / _  /_/ // /_/ / /_   #
        # ____/|__/  /_/  /_/ /_/\__,_/  /_____/ \____/\__/   #
        #                                                     #
        #######################################################

        """.strip()
        print(start_ascii_art)

    # On WebsocketApp Error (Unlikely)
    def on_error(self, ws, error):
        self.output(f"WebSocket On_Error:{error}",'ERROR','HIGHLIGHT','RED')

    # On Websocket Server Close (Very Unlikely)
    def on_close(self, ws, signal, status):
        self.output("Server Closed",'WARNING','HIGHLIGHT','WHITE')

    # On Websocket Message (wx message)
    def on_localapi_message(self, ws, message):
        j = json.loads(message)
        resp_type = j['type']
        # Case Switch 
        action = {
            # CHATROOM_MEMBER_NICK:handle_chat_nick,
            # PERSONAL_DETAIL:handle_personal_detail,
            # AT_MSG:handle_at_msg,
            # DEBUG_SWITCH:handle_recv_msg,
            # PERSONAL_INFO:handle_personal_info,
            # PERSONAL_DETAIL:handle_personal_detail,
            # TXT_MSG:handle_sent_msg,
            # PIC_MSG:handle_sent_msg,
            # ATTATCH_FILE:handle_sent_msg,
            # CHATROOM_MEMBER:handle_memberlist,
            # RECV_PIC_MSG:handle_recv_pic,
            # RECV_TXT_MSG:handle_recv_msg,
            # RECV_TXT_CITE_MSG:handle_xml_msg,
            # HEART_BEAT:heartbeat_trigger,
            # USER_LIST:handle_wxuser_list,
            # GET_USER_LIST_SUCCSESS:handle_wxuser_list,
            # GET_USER_LIST_FAIL:handle_wxuser_list,
            # STATUS_MSG:handle_status_msg,
        }
        action.get(resp_type, print)(j)

    def launch_msgr_ws(self) -> None:
        self.msgr._ws_init(self.FUNTOOL_IP, self.FUNTOOL_PORT,\
                           self.on_open,\
                           self.on_localapi_message,\
                           self.on_error,\
                           self.on_close)

    def output(self, msg, logtype='SYSTEM', mode ='DEFAULT', background='DEFAULT'):
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
    # Set dispatcher to automatic reconnection
    # 5 second reconnect delay if connection closed unexpectedly
    WB_MSGR = Messenger()
    WB_CORE = Core(WB_MSGR)

    WB_MSGR.ws.run_forever(dispatcher = rel, reconnect = 5)
    rel.signal(2, rel.abort)  # Keyboard Interrupt
    rel.dispatch()

if __name__ == "__main__":
    main()
        
