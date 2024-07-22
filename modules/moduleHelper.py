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
            "TXT_MSG" : 555,
            "PIC_MSG" : 500,
            "AT_MSG" : 550,
            "CHATROOM_MEMBER" : 5010,
            "CHATROOM_MEMBER_NICK" : 5020,
            "PERSONAL_INFO" : 6500,
            "DEBUG_SWITCH" : 6000,
            "PERSONAL_DETAIL" : 6550,
            "DESTROY_ALL" : 9999,
            "STATUS_MSG" : 10000,
            "ATTACH_FILE" : 5003,
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
            'id': self.getid(),
            'type': "TEXT",
            'content': msg,
        }
        return msg_content

    def compose_img_msg(self, filepath) -> dict:
        msg_content = {
            'id':self.getid(),
            'type': "PIC",
            'content': filepath,
        }
        return msg_content

    def compose_attach_msg(self, filepath) -> dict:
        msg_content = {
            'id':self.getid(),
            'type': "ATTACH",
            'content': filepath,
        }
        return msg_content

    def connect_db(self, db_path) -> sqlite3.Connection:
        """ Creates a Sqlite3 DB Connection for thread use """
        return sqlite3.connect(db_path)

    def load_json(self, json_path) -> dict:
        with open(json_path, "r", encoding = "utf-8") as f:
            return json.loads(f.read())

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
        return self.extra['version']
