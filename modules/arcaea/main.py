"""
[A R C A E A]
WindBot Arcaea Module
Author: Windsun
Feb 10 2024
"""

# Module Helper Imports
from ..moduleHelper import ModuleHelper, ModuleMetadata

# Standard Lib Imports
import json
import os

# Third Party Imports
from typing import List, Optional, Tuple, Union
import random
import requests
import rapidfuzz

mh = ModuleHelper()

__module_meta__ = ModuleMetadata(
    name =  "Arcaea",
    desc =  "Windbot Arcaea Module",
    extra = {
        "moduleuid": "arcaea",
        "version": "0.0.1",
        "author": ["Windsun"],
    }
)

class Arcaea(object):
    # Module Properties
    META: ModuleMetadata
    USER_FUNCTIONS: dict
    MNGNG_FUNCTIONS: dict
    STATIC_PATH: str
    ARC_WIKI_API: str

    def __init__(self):
        self.META = __module_meta__
        self.USER_FUNCTIONS = {
            "arand": self.music_random,
            "agrab": self.grablevel,
        }
        self.MNGNG_FUNCTIONS = {
            "aupdate": self.static_update,
        }
        self.STATIC_PATH = mh.compose_static_path("arcaea")

        self.ARC_WIKI_API = "https://arcwiki.mcd.blue/api.php?action=parse&format=json&curtimestamp=1&redirects=1&prop=wikitext&page="

    def get_module_meta(self) -> ModuleMetadata:
        return self.META

    def arc_wiki_data_get(self, item:str):
        """
        page Arc中文维基页面名称:

        Template%3AChartConstant.json 定数JSON
        Template%3ASonglist.json 歌曲数据JSON
        """

        pages = {
                "constant": "Template%3AChartConstant.json",
                "songlist": "Template%3ASonglist.json",
        }

        api_page_url = self.ARC_WIKI_API + pages[item]

        resp = requests.get(api_page_url)

        if resp.status_code == 200:
            data = resp.json()
            return data
        elif resp.status_code == 403:
            return -2
        elif resp.status_code == 400:
            return -1
        else:
            return 0

    def music_get(self, local: bool = False) -> Tuple[dict,bool]:
        """
        Not Local: Get Song Data From Arcaea Wiki
        Local: Read Song Data From Local File
        """

        success = True
        if not local:
            resp = self.arc_wiki_data_get("songlist")

            if isinstance(resp, dict):
                song_dict = resp["parse"]["wikitext"]["*"]
                with open(os.path.join(static, 'song_dict.json'), 'w', \
                        encoding='utf-8') as f:
                    f.write(song_dict)
                    f.close()
            else:
                output('Arcaea曲目数据获取失败,切换至本地暂存文件',\
                        'WARNING',background = 'WHITE')
                local = True
                success = False

        if local:
            with open(os.path.join(static, 'song_dict.json'), 'r', \
                    encoding='utf-8') as f:
                song_dict = json.loads(f.read())

        return (song_dict, success)

    def chart_get(self, local: bool) -> Tuple[dict,bool]:
        """
        Not Local: Get Chart Constant Data From Arcaea Wiki
        Local: Read Chart Constant Data From Local File
        """

        success = True
        if not local:
            resp = self.arc_wiki_data_get("constant")

            if isinstance(resp, dict):
                const_dict = resp["parse"]["wikitext"]["*"]
                with open(os.path.join(static, 'const_dict.json'), 'w', \
                        encoding='utf-8') as f:
                    f.write(const_dict)
                    f.close()
            else:
                output('Arcaea谱面定数数据获取失败,切换至本地暂存文件',\
                        'WARNING',background = 'WHITE')
                local = True
                success = False
        if local:
            with open(os.path.join(static, 'const_dict.json'), 'r', \
                    encoding='utf-8') as f:
                const_dict = json.loads(f.read())

        return (const_dict, success)

    def static_update(self, args: list) -> dict:
        status = ["ERROR","OK"]
        resp = "更新结果:\n"
        resp += f"曲目数据: {status[int(self.music_get(local = False)[1])]}"
        resp += f"定数数据: {status[int(self.chart_get(local = False)[1])]}"
        resp_msg = mh.compose_txt_msg(resp)
        return resp_msg

    def music_random(self, args: list) -> dict:
        pass

    def grablevel(self, args: list) -> dict:
        pass


