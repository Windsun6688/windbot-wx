# WindBot Module Helper

# Standard Lib Imports
import os
import sqlite3
import time
import json


class ModuleHelper:
    """Provide Helpers For Modules to interact with the Main program."""

    main_path: str
    static_root: str
    type_dict: dict

    def __init__(self):
        self.main_path = os.getcwd()
        self.static_root = os.path.join(self.main_path, "static")
        self.type_dict = {
            "TXT_MSG": 555,
            "PIC_MSG": 500,
            "AT_MSG": 550,
            "CHATROOM_MEMBER": 5010,
            "CHATROOM_MEMBER_NICK": 5020,
            "PERSONAL_INFO": 6500,
            "DEBUG_SWITCH": 6000,
            "PERSONAL_DETAIL": 6550,
            "DESTROY_ALL": 9999,
            "STATUS_MSG": 10000,
            "ATTACH_FILE": 5003,
        }

    def get_main_root(self) -> str:
        return self.main_path

    def get_static_root(self) -> str:
        return self.static_root

    def compose_static_path(self, subpath) -> str:
        if not isinstance(subpath, str):
            return -1
        return os.path.join(self.static_root, subpath)

    def getid(self) -> str:
        return time.strftime("%Y%m%d%H%M%S")

    def compose_txt_msg(self, msg) -> dict:
        msg_content = {
            "id": self.getid(),
            "type": "TEXT",
            "content": msg,
        }
        return msg_content

    def compose_img_msg(self, filepath) -> dict:
        msg_content = {
            "id": self.getid(),
            "type": "PIC",
            "content": filepath,
        }
        return msg_content

    def compose_attach_msg(self, filepath) -> dict:
        msg_content = {
            "id": self.getid(),
            "type": "ATTACH",
            "content": filepath,
        }
        return msg_content

    def connect_db(self, db_path) -> sqlite3.Connection:
        """Creates a Sqlite3 DB Connection for thread use"""
        return sqlite3.connect(db_path)

    def load_json(self, json_path) -> dict:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.loads(f.read())

    # Custom Print Wrapper
    def output(self, msg, logtype="SYSTEM", mode="DEFAULT", background="DEFAULT"):
        LogColor = {
            "SYSTEM": "034",
            "ERROR": "037",
            "GROUPCHAT": "036",
            "DM": "033",
            "HEART_BEAT": "035",
            "PAT": "037",
            "SEND": "032",
            "CALL": "031",
            "WARNING": "031",
            "CREATE_LINK": "032",
            "STOP_LINK": "031",
            "RSS": "037",
        }
        LogMode = {"DEFAULT": "0", "HIGHLIGHT": "1", "UNDERLINE": "4"}
        LogBG = {
            "DEFAULT": "",
            "RED": ";41",
            "YELLOW": ";43",
            "BLUE": ";44",
            "WHITE": ";47",
            "GREEN": ";42",
            "MINT": ";46",
            "PURPLE": ";45",
        }
        color = LogColor.get(logtype)
        mode = LogMode.get(mode)
        bg = LogBG.get(background)

        now = time.strftime("%Y-%m-%d %X")

        # Shorten logs of too long messages
        line_cnt = msg.count("\n") + 1
        if line_cnt > 10 and logtype != "ERROR":
            msg = "\n".join(msg.split("\n")[:10])
            msg += "\n......"

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


class ModuleMetadata(object):
    """Standard Structure for the Metadata of a Module"""

    name: str
    desc: str
    extra: dict

    def __init__(self, name, desc, extra):
        super(ModuleMetadata, self).__init__()
        self.name = name
        self.desc = desc
        self.extra = extra

    def get_name(self) -> str:
        return self.name

    def get_desc(self) -> str:
        return self.desc

    def get_author(self) -> list:
        return self.extra["author"]

    def get_moduleuid(self) -> str:
        return self.extra["moduleid"]

    def get_version(self) -> str:
        return self.extra["version"]
