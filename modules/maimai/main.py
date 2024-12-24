"""
[M A I M A I]
WindBot MaimaiDX Module
Author: Windsun
Jul 25 2024
"""

# Standard Lib Imports
import json
import os
import re

# Third Party Imports
from typing import List, Optional, Tuple, Union
import random
import math
import requests
from rapidfuzz import fuzz
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# Module Helper Imports
from ..moduleHelper import ModuleHelper, ModuleMetadata

mh = ModuleHelper()

__module_meta__ = ModuleMetadata(
    name="Maimai",
    desc="Windbot Maimai Module",
    extra={
        "moduleuid": "maimai_cn",
        "version": "0.0.1",
        "author": ["Windsun"],
    },
)


class Maimai(object):
    # Module Properties
    META: ModuleMetadata
    USER_FUNCTIONS: dict
    MNGNG_FUNCTIONS: dict
    STATIC_PATH: str
    MAI_DATA_API: str
    MAI_ALIAS_API: str
    DIVING_FISH_WEBSITE: str
    DIVING_FISH_GUIDE: str
    DIFF_LIST: list
    DIFF_LIST_SHORT: list
    JPVER_2_CNVER: dict
    PLATE_2_VER: dict

    def __init__(self):
        self.META = __module_meta__
        self.USER_FUNCTIONS = {
            "mb50": self.maimai_b50,
            "mrand": self.music_random,
            "minfo": self.music_search,
            "mgrade": self.view_single_grade,
            "mwhat": self.music_alias_search,
            "mgrab": self.music_grab_level,
            "mcsts": self.charter_stat_view,
            "mvs": self.music_artist_vs,
        }
        self.MNGNG_FUNCTIONS = {
            "mupdate": self.static_update,
        }
        self.STATIC_PATH = mh.compose_static_path("maimai")

        self._init_static()
        self._init_dev_token()
        self.b50_helper = Mai_B50(self._music_get(True)[0], self.MATERIAL_PATH)

    # Initialize static data.
    def _init_static(self):
        self.CONFIG_PATH = os.path.join(self.STATIC_PATH, "config.json")
        self.MATERIAL_PATH = os.path.join(self.STATIC_PATH, "material")
        self.MAI_BEST_IMG_PATH = os.path.join(self.STATIC_PATH, "mai_best_pics")
        self.MAI_DATA_API = "https://www.diving-fish.com/api/maimaidxprober"
        self.MAI_ALIAS_API = "https://api.yuzuchan.moe/maimaidx"
        self.DIVING_FISH_WEBSITE = "https://www.diving-fish.com/maimaidx/prober/"
        self.DIVING_FISH_GUIDE = "https://www.diving-fish.com/maimaidx/prober_guide"

        self.DIFF_LIST = ["Basic", "Advanced", "Expert", "Master", "RE:Master"]
        self.DIFF_LIST_SHORT = ["BAS", "ADV", "EXP", "MAS", "REM"]

        self.JPVER_2_CNVER = {
            "maimai": "maimai",
            "maimai PLUS": "maimai PLUS",
            "maimai GreeN": "maimai GreeN",
            "maimai GreeN PLUS": "maimai GreeN PLUS",
            "maimai ORANGE": "maimai ORANGE",
            "maimai ORANGE PLUS": "maimai ORANGE PLUS",
            "maimai PiNK": "maimai PiNK",
            "maimai PiNK PLUS": "maimai PiNK PLUS",
            "maimai MURASAKi": "maimai MURASAKi",
            "maimai MURASAKi PLUS": "maimai MURASAKi PLUS",
            "maimai MiLK": "maimai MiLK",
            "maimai MiLK PLUS": "maimai MiLK PLUS",
            "maimai FiNALE": "maimai FiNALE",
            "maimai でらっくす": "舞萌DX",
            "maimai でらっくす PLUS": "舞萌DX",
            "maimai でらっくす Splash": "舞萌DX2021",
            "maimai でらっくす Splash PLUS": "舞萌DX2021",
            "maimai でらっくす UNiVERSE": "舞萌DX2022",
            "maimai でらっくす UNiVERSE PLUS": "舞萌DX2022",
            "maimai でらっくす FESTiVAL": "舞萌DX2023",
            "maimai でらっくす FESTiVAL PLUS": "舞萌DX2023",
        }

        self.PLATE_2_VER = {
            "初": "maimai",
            "真": "maimai PLUS",
            "超": "maimai GreeN",
            "檄": "maimai GreeN PLUS",
            "橙": "maimai ORANGE",
            "暁": "maimai ORANGE PLUS",
            "晓": "maimai ORANGE PLUS",
            "桃": "maimai PiNK",
            "櫻": "maimai PiNK PLUS",
            "樱": "maimai PiNK PLUS",
            "紫": "maimai MURASAKi",
            "菫": "maimai MURASAKi PLUS",
            "堇": "maimai MURASAKi PLUS",
            "白": "maimai MiLK",
            "雪": "MiLK PLUS",
            "輝": "maimai FiNALE",
            "辉": "maimai FiNALE",
            "熊": "maimai でらっくす",
            "華": "maimai でらっくす",
            "华": "maimai でらっくす",
            # '華': 'maimai でらっくす PLUS', # Changed in maiCN
            # '华': 'maimai でらっくす PLUS', # Changed in maiCN
            "爽": "maimai でらっくす Splash",
            "煌": "maimai でらっくす Splash",
            # '煌': 'maimai でらっくす Splash PLUS', # Changed in maiCN
            "宙": "maimai でらっくす UNiVERSE",
            "星": "maimai でらっくす UNiVERSE PLUS",
            "祭": "maimai でらっくす FESTiVAL",
            "祝": "maimai でらっくす FESTiVAL PLUS",
        }

    # Initialize diving-fish dev token.
    def _init_dev_token(self):
        if not os.path.isfile(self.CONFIG_PATH):
            # Generate maimai config file
            with open(self.CONFIG_PATH, "w", encoding="utf-8") as f:
                init_config = {"mai_dev_token": ""}
                f.write(json.dumps(init_config, ensure_ascii=False, indent=4))
                mh.output(
                    "Did not found config.json. Generated default config.",
                    "WARNING",
                    background="WHITE",
                )

        config = json.load(open(self.CONFIG_PATH, "r", encoding="utf-8"))
        self.dev_token = config["mai_dev_token"]
        if self.dev_token == "":
            mh.output(
                "Continuing Without Developer Token", "WARNING", background="WHITE"
            )

    # Request wrapper.
    def _request(self, method: str, url: str, **kwargs):
        # Request based on method given
        if method == "GET":
            resp = requests.get(url, **kwargs)
        elif method == "POST":
            resp = requests.post(url, **kwargs)
        else:
            return 0

        data = None

        if self.MAI_DATA_API in url:
            if resp.status_code == 200:
                data = resp.json()
            elif resp.status_code == 400:
                data = -1
            elif resp.status_code == 403:
                data = -2
            else:
                data = 0
        elif self.MAI_ALIAS_API in url:
            if resp.status_code == 200:
                data = resp.json()["content"]
            elif resp.status_code == 400:
                data = -1
            elif resp.status_code == 500:
                data = -3
            else:
                data = 0

        return data

    ######## API Functions ########
    # Gets user data from diving-fish API.
    def _api_query_user(self, gamertag: str, func: str, plates: list = None) -> dict:
        """
        func 获取数据种类有:
        - plate 获取指定代的游玩数据
        - b50 获取b50数据
        """

        j = {
            "username": gamertag,
        }

        if func == "plate":
            j["version"] = plates
            method = f"/query/plate"
        elif func == "b50":
            j["b50"] = True
            method = f"/query/player"
        else:
            return 0

        url = self.MAI_DATA_API + method

        return self._request("POST", url, json=j)

    # Gets full/specific user data from diving-fish API.
    def _api_query_dev(self, gamertag: str, func: str, music_id=None) -> dict:
        """
        func 获取数据种类有:
        - records: 全部数据
        - single: 部分指定数据
        """

        headers = {"developer-token": self.dev_token}
        params = {"username": gamertag}

        if func == "records":
            method = "/dev/player/records"
            comm_method = "GET"
        elif func == "single":
            method = "/dev/player/record"
            params["music_id"] = music_id
            comm_method = "POST"
        else:
            return 0

        url = self.MAI_DATA_API + method
        if func == "records":
            return self._request(comm_method, url, headers=headers, params=params)
        else:
            return self._request(comm_method, url, headers=headers, json=params)

    # Gets Music data from diving-fish API.
    def _api_data_get(self, func: str):
        """
        func 获取数据种类有:
        - music 获取曲目数据
        - chart 获取单曲数据
        - ranking 获取查分器ranking排行榜
        """
        if func == "music":
            method = f"/music_data"
        elif func == "chart":
            method = f"/chart_stats"
        elif func == "ranking":
            method = f"/rating_ranking"
        else:
            return 0

        url = self.MAI_DATA_API + method

        return self._request("GET", url)

    # Gets data from yuzuchan API.
    def _alias_api_data_get(self, func: str, music_id: int = None):
        """
        func 获取数据种类:
        - alias 所有别名
        - id2alias 返回id对应的别名
        - aliastatus 正在进行的别名投票
        - aliasend 五分钟内结束的别名投票
        - music 曲目数据
        - charts 曲目数据
        """
        params = None

        if func == "alias":
            method = f"/maimaidxalias"
        elif func == "id2alias":
            method = f"/getsongsalias"
            params = dict()
            params["id"] = music_id
        elif func == "aliastatus":
            method = f"/getaliasstatus"
        elif func == "aliasend":
            method = f"/getaliasend"
        elif func == "music":
            method = f"/getmaimaidxmusic"
        elif func == "charts":
            method = f"/getmaimaidxchartstats"
        else:
            return 0

        url = self.MAI_ALIAS_API + method
        if params != None:
            return self._request("GET", url, params=params)
        else:
            return self._request("GET", url)

    ######## Resources Update & Local Data Retrieval ########
    # Retrieves Song Data / Overwrite(Update) Song Data
    def _music_get(self, local: bool) -> Tuple[dict, bool]:
        """
        Not Local: Get Song Data From Diving Fish Server
        Local: Read Song Data From Local File
        """
        success = True
        if not local:
            music_data = self._api_data_get("music")

            if isinstance(music_data, list):
                with open(
                    os.path.join(self.STATIC_PATH, "music_data.json"),
                    "w",
                    encoding="utf-8",
                ) as f:
                    f.write(json.dumps(music_data, ensure_ascii=False, indent=4))
            else:
                mh.output(
                    "maimaiDX曲目数据获取失败,切换至本地暂存文件",
                    "WARNING",
                    background="WHITE",
                )
                local = True
                success = False

        if local:
            with open(
                os.path.join(self.STATIC_PATH, "music_data.json"), "r", encoding="utf-8"
            ) as f:
                music_data = json.loads(f.read())

        return (music_data, success)

    # Retrieves Chart Data / Overwrite(Update) Chart Data
    def _chart_stat_get(self, local: bool) -> Tuple[dict, bool]:
        """
        Not Local: Get Chart Stats From Diving Fish Server
        Local: Read Chart Stats From Local File
        """
        success = True
        if not local:
            chart_stats = self._api_data_get("chart")

            if isinstance(chart_stats, dict):
                with open(
                    os.path.join(self.STATIC_PATH, "chart_stats.json"),
                    "w",
                    encoding="utf-8",
                ) as f:
                    f.write(json.dumps(chart_stats, ensure_ascii=False, indent=4))
            else:
                mh.output(
                    "maimaiDX谱面数据获取失败,切换至本地暂存文件",
                    "WARNING",
                    background="WHITE",
                )
                local = True
                success = False

        if local:
            with open(
                os.path.join(self.STATIC_PATH, "chart_stats.json"),
                "r",
                encoding="utf-8",
            ) as f:
                chart_stats = json.loads(f.read())

        return (chart_stats, success)

    # Retrieves Chart Data / Overwrite(Update) Chart Data
    def _alias_get(self, local: bool) -> Tuple[dict, bool]:
        """
        Not Local: Get Song Alias From yuzuai Server
        Local: Read Alias From Local File
        """
        success = True
        if not local:
            alias_data = self._alias_api_data_get("alias")

            if isinstance(alias_data, list):
                with open(
                    os.path.join(self.STATIC_PATH, "music_alias.json"),
                    "w",
                    encoding="utf-8",
                ) as f:
                    f.write(json.dumps(alias_data, ensure_ascii=False, indent=4))
            else:
                mh.output(
                    "maimaiDX歌曲别名数据获取失败,切换为本地暂存文件",
                    "WARNING",
                    background="WHITE",
                )
                local = True
                success = False
        if local:
            with open(
                os.path.join(self.STATIC_PATH, "music_alias.json"),
                "r",
                encoding="utf-8",
            ) as f:
                alias_data = json.loads(f.read())

        return (alias_data, success)

    # Aggregate Update Function
    def static_update(self, args):
        status = ["ERROR", "OK"]
        resp = "更新结果:\n"
        resp += f"曲目数据: {status[int(self._music_get(local = False)[1])]}\n"
        resp += f"谱面数据: {status[int(self._chart_stat_get(local = False)[1])]}\n"
        resp += f"别名数据: {status[int(self._alias_get(local = False)[1])]}\n"

        return mh.compose_txt_msg(resp)

    ######## Draw Maimai Best 50 Image ########
    # Drawing the best image.
    def _draw_best_image(self, gamertag: str):
        # Get User Data
        user_data = self._api_query_user(gamertag, "b50")
        if user_data == -2:
            return -2
        elif user_data == -1:
            return -1
        elif user_data == 0:
            return 0

        # Update the Music Data for B50 Helper
        self.b50_helper._update_music_data(self._music_get(True)[0])

        # Extract Data
        ra = user_data["rating"]
        add_ra = user_data["additional_rating"]
        nickname = user_data["nickname"]
        plate = user_data["plate"]
        old_best = list(user_data["charts"]["sd"])
        new_best = list(user_data["charts"]["dx"])

        # Load Fonts
        meiryo = self.b50_helper.meiryo
        siyuan = self.b50_helper.siyuan
        Torus_SemiBold = self.b50_helper.Torus_SemiBold
        nosa = self.b50_helper.nosa

        # Load Assets
        PIC_PATH = self.b50_helper.PIC_PATH
        PLATE_PATH = self.b50_helper.PLATE_PATH

        icon_pic = self.b50_helper.icon_pic
        logo_pic = self.b50_helper.logo
        name_base_pic = self.b50_helper.name_base_pic
        shougou_base_pic = self.b50_helper.shougou_base_pic
        dx_rating_pic = Image.open(
            os.path.join(PIC_PATH, self.b50_helper._rating_pic(ra))
        ).resize((425, 80))
        match_level_pic = Image.open(
            os.path.join(PIC_PATH, self.b50_helper._match_level_pic(add_ra))
        ).resize((128, 58))
        # class_pic = Image.open(os.path.join(PIC_PATH,\
        #                         "UI_FBR_Class_00.png")).resize((144, 87))

        # Load Plate if any
        if plate:
            plate_pic = Image.open(os.path.join(PLATE_PATH, f"{plate}.png")).resize(
                (1420, 230)
            )
        else:
            plate_pic = Image.open(
                os.path.join(PIC_PATH, "UI_Plate_300101.png")
            ).resize((1420, 230))

        ### Generate Best Image ###
        # Base Image
        im = Image.open(os.path.join(PIC_PATH, "b50_bg.png")).convert("RGBA")
        # Draw Logo
        im.alpha_composite(logo_pic, (5, 130))

        # Draw Plate
        im.alpha_composite(plate_pic, (390, 100))

        # Draw Icon
        im.alpha_composite(icon_pic, (398, 108))

        # Draw User Info Base
        im.alpha_composite(dx_rating_pic, (620, 108))
        im.alpha_composite(name_base_pic, (620, 200))
        im.alpha_composite(match_level_pic, (935, 205))
        im.alpha_composite(shougou_base_pic, (620, 275))

        # Writing Information
        text_im = ImageDraw.Draw(im)

        # Custom font style and font size
        _meiryo = ImageFont.truetype(meiryo, 40)
        _siyuan = ImageFont.truetype(siyuan, 25)
        _tb = ImageFont.truetype(Torus_SemiBold, 44)
        _nosa = ImageFont.truetype(nosa, 40)

        # Write Player Name
        text_im.text(
            (635, 235), nickname.upper(), font=_tb, fill=(0, 0, 0, 255), anchor="lm"
        )

        # Write Split Rating
        total_ra = ra
        total_ra = f"{total_ra:05d}"
        text_im.text(
            (847, 300),
            f"STAYIN' IN THE FESTiVAL",
            font=_siyuan,
            fill=(0, 0, 0, 255),
            anchor="mm",
        )

        # Write Credits
        credits_msg = (
            "Generated by WINDBOT | Ported by Windsun | Design by Yuri-YuzuchaN"
        )
        text_im.text(
            (900, 2365), credits_msg, font=_tb, fill=(103, 20, 141, 255), anchor="mm"
        )

        # Write Rating(Shougou) Bar
        for n, i in enumerate(total_ra):
            if n == 0 and i == 0:
                continue
            num_pic = Image.open(os.path.join(PIC_PATH, f"UI_NUM_Drating_{i}.png"))
            im.alpha_composite(num_pic, (820 + 33 * n, 133))

        ## Drawing Song Info
        im = self.b50_helper.best_2_image(im, new_best, False)
        im = self.b50_helper.best_2_image(im, old_best, True)

        return im

    # The User's Maimai B50 Function.
    def maimai_b50(self, args):
        func_data = args[0]
        usr_id = args[1]
        wb_db = args[-1][0]
        BOT_GC_INVOKER = args[-1][1]

        # User Provided Gamertag
        if len(func_data) > 0:
            gamertag = func_data[0]
        # User didn't provide Gamertag, get from WB DB
        else:
            gamertag = wb_db.fetch("Users", ["maiID"], "wxid", usr_id)[0][0]
            if gamertag == "-1":
                resp = "您未绑定maimai查分器ID。请使用bind指令绑定。\n"
                resp += f"请注意，请绑定您在{self.DIVING_FISH_WEBSITE}中的用户名。\n"
                resp += f"示例: {BOT_GC_INVOKER} bind mai xxxxx"
                return mh.compose_txt_msg(resp)

        # Draw the Image
        image = self._draw_best_image(gamertag)

        # If error happened in image drawing
        if isinstance(image, int):
            # No Disclose Error
            if image == -2:
                resp = "该用户选择不公开数据。"

            # No Data Error
            elif image == -1:
                resp = f"查分器没有返回数据,请检查您绑定的查分器用户ID。\n"
                resp += f"目前绑定: {gamertag}\n"
                resp += f"如果您没有导入过游玩数据,请参考{self.DIVING_FISH_GUIDE}。"

            # Unknown Error
            elif image == 0:
                resp = "发生未知错误。"
            return mh.compose_txt_msg(resp)
        else:
            storage_path = os.path.join(self.MAI_BEST_IMG_PATH, f"{gamertag}.png")
            image.save(storage_path, optimize=True, quality=60)
            return mh.compose_attach_msg(storage_path)

    ######## Helper Functions ########
    # Fuzzy find music data by title.
    def _music_by_fuzzy_title(self, title, QRatio) -> list:
        music_data = self._music_get(local=True)[0]
        results = list()
        for song in music_data:
            song_title = song["title"]

            if fuzz.QRatio(title.lower(), song_title.lower()) >= QRatio:
                results.append(song)
        return results

    # Find music data by song_id
    def _music_by_id(self, song_id: int) -> list:
        music_data = self._music_get(local=True)[0]
        result = list()

        for song in music_data:
            if song["id"] == str(song_id):
                result.append(song)
        return result

    # Find music by artist name.
    def _music_by_artist(self, target_artist: str) -> list:
        music_data = self._music_get(local = True)[0]
        result = list()

        for song in music_data:
            artist = song["basic_info"]["artist"]
            artist_splitted = artist.split(" ")
            if (target_artist == artist) or (target_artist in artist_splitted):
                result.append(song)

        return result

    # Find charts by constant.
    def _charts_by_constant(self, target_constant: float) -> dict:
        music_data = self._music_get(local=True)[0]
        result = dict()

        for song in music_data:
            matching_idx = [i for i, x in enumerate(song["ds"]) if x == target_constant]
            result[song["id"]] = [song, matching_idx]

        return result

    # Find numbers of chart by charter
    def _charts_cnt_by_charter(self) -> dict:
        music_data = self._music_get(local=True)[0]
        result = dict()

        for song in music_data:
            for chart in song["charts"]:
                if result.get(chart["charter"], None) == None:
                    result[chart["charter"]] = 1
                else:
                    result[chart["charter"]] += 1

        return result

    ######## User Functions ########
    # Random
    def music_random(self, args) -> dict:
        func_data = args[0]
        music_data = self._music_get(local=True)[0]
        random_type = None

        # If user does not specify level, do all random
        if len(func_data) == 0:
            random_type = "wildcard"
            result_songs = music_data

        # Precise level indicator
        elif func_data[0].lower() == "p":
            random_type = "precise"
            result_songs = list()
            const = func_data[1]
            for song in music_data:
                if float(const) in song["ds"]:
                    result_songs.append(song)

        # General level indicator
        else:
            random_type = "general"
            result_songs = list()
            level = func_data[0]
            for song in music_data:
                if level in song["level"]:
                    result_songs.append(song)

        # If no results found
        if len(result_songs) == 0:
            resp = f"WB没有找到歌曲。"
            return mh.compose_txt_msg(resp)

        # Random
        chosen_song_data = random.choice(result_songs)

        # Build Reply
        resp = f"WB为您从{len(result_songs)}首歌曲中选择了:\n"

        title = chosen_song_data["basic_info"]["title"]
        artist = chosen_song_data["basic_info"]["artist"]
        genre = chosen_song_data["basic_info"]["genre"]
        song_id = chosen_song_data["id"]
        chart_type = chosen_song_data["type"]

        # Different Reply based on random type
        if random_type == "precise":
            for i in range(len(chosen_song_data["ds"])):
                if float(const) == chosen_song_data["ds"][i]:
                    level_diff = self.DIFF_LIST_SHORT[i]
            resp += f"[{chart_type} {level_diff} {const}] {artist} - {title}\n"

        elif random_type == "general":
            for i in range(len(chosen_song_data["level"])):
                if level == chosen_song_data["level"][i]:
                    level_diff = self.DIFF_LIST_SHORT[i]
            resp += f"[{chart_type} {level_diff} {level}] {artist} - {title}\n"

        elif random_type == "wildcard":
            max_diff = len(chosen_song_data["level"])
            random_diff = random.randint(0, max_diff - 1)

            level_diff = self.DIFF_LIST_SHORT[random_diff]
            const = chosen_song_data["ds"][random_diff]

            resp += f"[{chart_type} {level_diff} {const}] {artist} - {title}\n"

        resp += f"分区：{genre} | SID {song_id}"
        return mh.compose_txt_msg(resp)

    # The user's Maimai Info Search.
    def music_search(self, args) -> dict:
        func_data = args[0]
        search_type = None

        # No Data Provided
        if len(func_data) == 0:
            resp = "请提供搜索的乐曲标题或SID。"
            return mh.compose_txt_msg(resp)

        # Precise search
        if func_data[0].lower() == "p":
            search_type = "precise"
            keyword = " ".join(func_data[1:])
            results = self._music_by_fuzzy_title(keyword, 90)

        # Fuzzy Search & Song ID Search
        else:
            keyword = " ".join(func_data)

            # Song ID Search
            if keyword.isnumeric():
                search_type = "sid"
                results = self._music_by_id(int(keyword))

            # Fuzzy Search [DEFAULT]
            else:
                search_type = "fuzzy"
                results = self._music_by_fuzzy_title(keyword, 65)

        # No Results
        if len(results) == 0:
            if search_type == "sid":
                resp = f"WB没有搜寻到结果。您查找了SID: {keyword}"
            else:
                resp = f"WB没有搜寻到结果。您查找了: {keyword}"
            return mh.compose_txt_msg(resp)

        # Too Many Results
        elif len(results) > 5:
            resp = "WB找到的结果过多（很沉！>_<）。\n"
            resp += "请尝试优化搜索词。"
            return mh.compose_txt_msg(resp)

        # Reasonable Results
        resp = f"共找到以下{len(results)}个结果:"
        for song in results:
            song_id = song["id"]
            title = song["title"]
            chart_type = song["type"]

            artist = song["basic_info"]["artist"]
            JP_version = song["basic_info"]["from"]
            CN_version = self.JPVER_2_CNVER.get(JP_version, JP_version)
            category = song["basic_info"]["genre"]
            bpm = song["basic_info"]["bpm"]
            new_txt = "" if song["basic_info"]["is_new"] == False else " [NEW]"

            diffs_info = list()
            for i in range(len(song["ds"])):
                diff = self.DIFF_LIST_SHORT[i]
                const = song["ds"][i]
                diff_str = f"{diff}{const}"
                diffs_info.append(diff_str)
            diffs_info_str = " | ".join(diffs_info)

            resp += f"\n[{chart_type}]{new_txt} {artist} - {title}"
            resp += f"\n-版本：{CN_version} | 分区：{category} | BPM{bpm}"
            resp += f"\n--{diffs_info_str}"
            resp += f"\n---SID：{song_id}\n"

        return mh.compose_txt_msg(resp)

    # The user's Maimai Single Grade View.
    def view_single_grade(self, args) -> dict:
        func_data = args[0]
        usr_id = args[1]
        wb_db = args[-1][0]
        BOT_GC_INVOKER = args[-1][1]

        # Get Gamertag
        gamertag = wb_db.fetch("Users", ["maiID"], "wxid", usr_id)[0][0]
        if gamertag == "-1":
            resp = "您未绑定maimai查分器ID。请使用bind指令绑定。\n"
            resp += f"请注意，请绑定您在{self.DIVING_FISH_WEBSITE}中的用户名。\n"
            resp += f"示例: {BOT_GC_INVOKER} bind mai xxxxx"
            return mh.compose_txt_msg(resp)

        # User did not provide SID
        if len(func_data) == 0:
            resp = "请提供SID。"
            return mh.compose_txt_msg(resp)

        target_sid_list = func_data
        song_info_list = list()

        # Not Numeric
        for target_sid in target_sid_list:
            if not target_sid.isnumeric():
                resp = f"请提供纯数字的SID。"
                return mh.compose_txt_msg(resp)

            song_info = self._music_by_id(int(target_sid))
            if len(song_info) == 0:
                resp = f"WB没有找到SID为{target_sid}的歌曲。"
                return mh.compose_txt_msg(resp)
            else:
                song_info_list += song_info

        usr_record = self._api_query_dev(gamertag, "single", target_sid_list)
        # User choose to not disclose data
        if usr_record == -2:
            resp = "该用户选择不公开数据。"
            return mh.compose_txt_msg(resp)

        resp = f"Player: {gamertag}"

        for idx, song_info in enumerate(song_info_list):
            song_id = target_sid_list[idx]
            song_record = usr_record.get(song_id, list())

            resp += f"\n[{idx+1}] {song_info['title']} <ID{song_id}>"

            for i, const in enumerate(song_info["ds"]):
                diff_str = self.DIFF_LIST_SHORT[i]
                achievement = "无数据"
                dx_score = "无数据"
                for record in song_record:
                    if record["level_index"] == i:
                        achievement = f"{record['achievements']}%"
                        dx_score = record["dxScore"]
                resp += f"\n-[{diff_str} {const}] {achievement} (DxS:{dx_score})"

            resp += "\n"

        return mh.compose_txt_msg(resp)

    # The user's Maimai Alias Search.
    def music_alias_search(self, args) -> dict:
        alias_data = self._alias_get(local=True)[0]
        func_data = args[0]

        results = list()
        # User didn't provide input
        if len(func_data) == 0:
            resp = "请提供WB用于搜索的别名。"
            return mh.compose_txt_msg(resp)

        # Search for alias
        keyword = " ".join(func_data)
        for song in alias_data:
            if keyword in song["Alias"]:
                song_info = self._music_by_id(song["SongID"])
                results += song_info

        if len(results) == 0:
            resp = f"WB没有找到结果。您查找了：{keyword}"
        elif len(results) > 10:
            resp = f"WB找到了太多结果({len(results)}个！)"
            resp += "\n请尝试搜索其他别名。"
        else:
            resp = f"这个别名可能指向以下{len(results)}首歌："
            for idx, song_info in enumerate(results):
                title = song_info["title"]
                song_id = song_info["id"]
                resp += f"\n[{idx+1}] {title} (ID{song_id})"
        return mh.compose_txt_msg(resp)

    # The user's Maimai Grab-Song-By-Constant Search.
    def music_grab_level(self, args: list) -> dict:
        func_data = args[0]
        if len(func_data) == 0:
            resp = "请提供具体定数。"
        else:
            target_constant = func_data[0]
            try:
                target_constant = float(target_constant)
            except:
                resp = "您需要指明具体定数。"
                return mh.compose_txt_msg(resp)

            music_data = self._music_get(local=True)[0]
            matching_songs = self._charts_by_constant(target_constant)

            if len(matching_songs) == 0:
                resp = f"WB没有在{target_constant}难度找到谱面。"
            else:
                resp = f"WB在{target_constant}找到了以下谱面：\n"
                cnt = 1
                for song_id in matching_songs.keys():
                    # Bypass Utage Maps
                    if int(song_id) > 100000:
                        continue

                    song_info = matching_songs[song_id][0]
                    target_chart_ids = matching_songs[song_id][1]

                    title = song_info["basic_info"]["title"]
                    artist = song_info["basic_info"]["artist"]

                    for chart_id in target_chart_ids:
                        diff_short = self.DIFF_LIST_SHORT[chart_id]
                        charter = song_info["charts"][chart_id]["charter"]
                        resp += f"[{diff_short}] {artist} - {title} <{charter}>"
                        resp += f" (ID{song_id})\n"
                        cnt += 1

                resp += f"共{cnt-1}张谱面。"

        return mh.compose_txt_msg(resp)

    # The user's Maimai Charter stat view.
    def charter_stat_view(self, args: list) -> dict:
        func_data = args[0]

        # Didn't specify, default to 10
        viewing_cnt = 10
        # Specified
        if len(func_data) != 0:
            viewing_cnt_str = func_data[0]
            if viewing_cnt_str.isnumeric():
                viewing_cnt = int(viewing_cnt_str)
                if viewing_cnt > 35:
                    resp = "WB找到了太多结果，搬不回来了。请尝试减少数值。"
                    return mh.compose_txt_msg(resp)
            else:
                resp = "请提供具体Top数值。"
                return mh.compose_txt_msg(resp)

        charter_stat = self._charts_cnt_by_charter()
        charter_sorted = sorted(
            charter_stat.items(), key=lambda item: item[1], reverse=True
        )

        resp = f"WB在当前版本共找到了{len(charter_stat)}位谱师：\n"
        for i in range(viewing_cnt):
            charter_info = charter_sorted[i]
            charter = charter_info[0]
            charted_cnt = charter_info[1]

            resp += f"[{i+1}] {charter}: {charted_cnt}张谱面\n"

        return mh.compose_txt_msg(resp)

    # The user's Maimai Artist Versus tool.
    def music_artist_vs(self, args:list) -> dict:
        func_data = args[0]

        # Blank Input
        if len(func_data) == 0:
            resp = "请提供作曲家。"
            return mh.compose_txt_msg(resp)

        artist = " ".join(func_data)

        # Search
        results = self._music_by_artist(artist)

        # No result
        if len(results) == 0:
            resp = f"WB没有找到{artist}的歌曲。"
        # Reasonable Result
        else:
            resp = f"如果您想大战{artist}，您可以选："
            for i in range(len(results)):
                song_info = results[i]
                song_id = song_info["id"]

                title = song_info["basic_info"]["title"]
                artist = song_info["basic_info"]["artist"]

                resp += f"\n[{i+1}] {artist} - {title} <ID{song_id}>"

        return mh.compose_txt_msg(resp)


class Mai_B50(object):
    """Maimai B50 Image Drawing"""

    def __init__(self, music_data, material_path):
        super(Mai_B50, self).__init__()
        self.MATERIAL_PATH = material_path
        self.MAI_PATH = os.path.join(self.MATERIAL_PATH, "mai")
        self.COVER_PATH = os.path.join(self.MAI_PATH, "cover")
        self.PIC_PATH = os.path.join(self.MAI_PATH, "pic")
        self.PLATE_PATH = os.path.join(self.MAI_PATH, "plate")
        self.MAI_MUSIC_DATA = music_data

        self._init_material()

    # Load Material Assets.
    def _init_material(self) -> None:
        # Load DX Stars
        self.dx_star_pics = [
            Image.open(
                os.path.join(self.PIC_PATH, f"UI_GAM_Gauge_DXScoreIcon_0{_ + 1}.png")
            )
            for _ in range(5)
        ]

        # Load Difficulty Background
        bas_bg = Image.open(os.path.join(self.PIC_PATH, "b50_score_basic.png"))
        adv_bg = Image.open(os.path.join(self.PIC_PATH, "b50_score_advanced.png"))
        exp_bg = Image.open(os.path.join(self.PIC_PATH, "b50_score_expert.png"))
        mas_bg = Image.open(os.path.join(self.PIC_PATH, "b50_score_master.png"))
        remas_bg = Image.open(os.path.join(self.PIC_PATH, "b50_score_remaster.png"))
        self.diff_bg = [bas_bg, adv_bg, exp_bg, mas_bg, remas_bg]

        # Load Fonts
        self.Torus_SemiBold = os.path.join(self.MATERIAL_PATH, "Torus SemiBold.otf")
        self.siyuan = os.path.join(self.MATERIAL_PATH, "SourceHanSansSC-Bold.otf")
        self.meiryo = os.path.join(self.MATERIAL_PATH, "meiryo.ttc")
        self.nosa = os.path.join(self.MATERIAL_PATH, "NOSA.ttf")

        # Load Pic Assets
        self.logo = Image.open(os.path.join(self.PIC_PATH, "logo.png")).resize(
            (378, 172)
        )

        self.icon_pic = Image.open(
            os.path.join(self.PIC_PATH, "UI_Icon_309503.png")
        ).resize((214, 214))

        self.name_base_pic = Image.open(os.path.join(self.PIC_PATH, "Name.png"))
        self.shougou_base_pic = Image.open(
            os.path.join(self.PIC_PATH, "UI_CMN_Shougou_Rainbow.png")
        ).resize((454, 50))

    # Updates the music data.
    def _update_music_data(self, music_data) -> None:
        self.MAI_MUSIC_DATA = music_data

    # Image 2 base64 Helper.
    def image_to_base64(self, img: Image.Image, fileFormat="PNG") -> str:
        output_buffer = BytesIO()
        img.save(output_buffer, fileFormat)
        byte_data = output_buffer.getvalue()
        base64_str = base64.b64encode(byte_data).decode()

        return "base64://" + base64_str

    # Check if a character is CJK
    def is_cjk(self, character):
        """ "
        Checks whether character is CJK.

            >>> is_cjk(u'\u33fe')
            True
            >>> is_cjk(u'\ufe5f')
            False

        :param character: The character that needs to be checked.
        :type character: char
        :return: bool
        """
        return any(
            [
                start <= ord(character) <= end
                for start, end in [
                    (4352, 4607),
                    (11904, 42191),
                    (43072, 43135),
                    (44032, 55215),
                    (63744, 64255),
                    (65072, 65103),
                    (65381, 65500),
                    (131072, 196607),
                ]
            ]
        )

    # Rating Computation from Constant & Achievement
    def computeRa(
        self,
        ds: float,
        achievement: float,
        onlyrate: bool = False,
        israte: bool = False,
    ) -> Union[int, Tuple[int, str]]:
        if achievement < 50:
            baseRa = 7.0
            rate = "D"
        elif achievement < 60:
            baseRa = 8.0
            rate = "C"
        elif achievement < 70:
            baseRa = 9.6
            rate = "B"
        elif achievement < 75:
            baseRa = 11.2
            rate = "BB"
        elif achievement < 80:
            baseRa = 12.0
            rate = "BBB"
        elif achievement < 90:
            baseRa = 13.6
            rate = "A"
        elif achievement < 94:
            baseRa = 15.2
            rate = "AA"
        elif achievement < 97:
            baseRa = 16.8
            rate = "AAA"
        elif achievement < 98:
            baseRa = 20.0
            rate = "S"
        elif achievement < 99:
            baseRa = 20.3
            rate = "Sp"
        elif achievement < 99.5:
            baseRa = 20.8
            rate = "SS"
        elif achievement < 100:
            baseRa = 21.1
            rate = "SSp"
        elif achievement < 100.5:
            baseRa = 21.6
            rate = "SSS"
        else:
            baseRa = 22.4
            rate = "SSSp"

        if israte:
            data = (math.floor(ds * (min(100.5, achievement) / 100) * baseRa), rate)
        elif onlyrate:
            data = rate
        else:
            data = math.floor(ds * (min(100.5, achievement) / 100) * baseRa)

        return data

    # Character Width Helper
    def _getCharWidth(self, o) -> int:
        widths = [
            (126, 1),
            (159, 0),
            (687, 1),
            (710, 0),
            (711, 1),
            (727, 0),
            (733, 1),
            (879, 0),
            (1154, 1),
            (1161, 0),
            (4347, 1),
            (4447, 2),
            (7467, 1),
            (7521, 0),
            (8369, 1),
            (8426, 0),
            (9000, 1),
            (9002, 2),
            (11021, 1),
            (12350, 2),
            (12351, 1),
            (12438, 2),
            (12442, 0),
            (19893, 2),
            (19967, 1),
            (55203, 2),
            (63743, 1),
            (64106, 2),
            (65039, 1),
            (65059, 0),
            (65131, 2),
            (65279, 1),
            (65376, 2),
            (65500, 1),
            (65510, 2),
            (120831, 1),
            (262141, 2),
            (1114109, 1),
        ]
        if o == 0xE or o == 0xF:
            return 0
        for num, wid in widths:
            if o <= num:
                return wid
        return 1

    # Column Width Helper
    def _columnWidth(self, s: str) -> int:
        res = 0
        for ch in s:
            res += self._getCharWidth(ord(ch))
        return res

    # Changing Column Width Helper
    def _changeColumnWidth(self, s: str, length: int) -> str:
        res = 0
        sList = []
        for ch in s:
            res += self._getCharWidth(ord(ch))
            if res <= length:
                sList.append(ch)
        return "".join(sList)

    # Concatenate File Name for Rating Picture
    def _rating_pic(self, rating: int) -> str:
        if rating < 1000:
            num = "01"
        elif rating < 2000:
            num = "02"
        elif rating < 4000:
            num = "03"
        elif rating < 7000:
            num = "04"
        elif rating < 10000:
            num = "05"
        elif rating < 12000:
            num = "06"
        elif rating < 13000:
            num = "07"
        elif rating < 14000:
            num = "08"
        elif rating < 14500:
            num = "09"
        elif rating < 15000:
            num = "10"
        else:
            num = "11"
        return f"UI_CMN_DXRating_{num}.png"

    # Concatenate File Name for Friend Match Picture
    def _match_level_pic(self, add_rating: int) -> str:
        if add_rating <= 10:
            num = f"{add_rating:02d}"
        else:
            num = f"{add_rating + 1:02d}"
        return f"UI_DNM_DaniPlate_{num}.png"

    # DX Score to Star Helper.
    def dxscore_2_star(self, dx: int, target_sid: int, lvl: int) -> int:
        # Find Song
        song_data = None
        for song in self.MAI_MUSIC_DATA:
            if song["id"] == target_sid:
                song_data = song
        if song_data == None:
            return -1

        notes_cnt = song_data["charts"][lvl]["notes"]
        max_dx = sum(notes_cnt)
        dx_ratio = dx / max_dx * 100

        if dx_ratio <= 85:
            result = 0
        elif dx_ratio <= 90:
            result = 1
        elif dx_ratio <= 93:
            result = 2
        elif dx_ratio <= 95:
            result = 3
        elif dx_ratio <= 97:
            result = 4
        else:
            result = 5
        return result

    # Best List to Image
    def best_2_image(self, output: Image.Image, data: list, isOld: bool):
        """
        isOld = True 放在旧版本位置
        isOld = False 放在新版本位置
        """
        y = 430 if isOld else 1670
        dy = 170

        TEXT_COLOR = [
            (255, 255, 255, 255),
            (255, 255, 255, 255),
            (255, 255, 255, 255),
            (255, 255, 255, 255),
            (103, 20, 141, 255),
        ]

        # Load Fonts
        _tb = ImageFont.truetype(self.Torus_SemiBold, 20)
        _tbAchieve1 = ImageFont.truetype(self.Torus_SemiBold, 35)
        _tbAchieve2 = ImageFont.truetype(self.Torus_SemiBold, 25)
        _tbRating = ImageFont.truetype(self.Torus_SemiBold, 22)
        _siyuan = ImageFont.truetype(self.siyuan, 20)

        text_output = ImageDraw.Draw(output)

        num = 0
        x = 0
        # Draw Image For Each Song
        for song_record in data:
            # 每首歌间距/5首歌换行
            if num % 5 == 0:
                x = 70
                y += dy if num != 0 else 0
            else:
                x += 416

            # 结构: [title,level,diff,song_id,chart_const,chart_type,acc,racc,star,rate,rating,fc,fs]

            # Draw Level Difficulty Base (BAS, ADV, EXP, MAS, REMAS)
            chart_diff = song_record["level_index"]
            output.alpha_composite(self.diff_bg[chart_diff], (x, y))

            # Draw Cover
            song_id = song_record["song_id"]
            try:
                cover = Image.open(
                    os.path.join(self.COVER_PATH, f"{song_id}.png")
                ).resize((135, 135))
            except FileNotFoundError as e:
                cover = Image.open(
                    os.path.join(self.COVER_PATH, f"{random.randint(1,1)*-1}.png")
                ).resize((135, 135))
            output.alpha_composite(cover, (x + 5, y + 5))

            # Draw Chart Type (DX, STD)
            chart_type = song_record["type"]
            chart_type_pic = Image.open(
                os.path.join(self.PIC_PATH, f"{chart_type.upper()}.png")
            ).resize((55, 19))
            output.alpha_composite(chart_type_pic, (x + 80, y + 141))

            # Draw Achievement Rank
            achievement_rank = song_record["rate"].upper().replace("P", "p")
            achievement_rank_pic = Image.open(
                os.path.join(self.PIC_PATH, f"UI_TTR_Rank_{achievement_rank}.png")
            ).resize((95, 44))
            output.alpha_composite(achievement_rank_pic, (x + 150, y + 98))

            # if FC, Draw Full Combo Pic
            fc_status = song_record["fc"]
            if fc_status:
                fc = Image.open(
                    os.path.join(self.PIC_PATH, f"UI_MSS_MBase_Icon_{fc_status}.png")
                ).resize((45, 45))
                output.alpha_composite(fc, (x + 246, y + 99))

            # if FS, Draw Full Sync Pic
            fs_status = song_record["fs"]
            if fs_status:
                fs = Image.open(
                    os.path.join(self.PIC_PATH, f"UI_MSS_MBase_Icon_{fs_status}.png")
                ).resize((45, 45))
                output.alpha_composite(fs, (x + 291, y + 99))

            # Draw DX Star
            dx_score = song_record["dxScore"]
            dx_num = self.dxscore_2_star(dx_score, song_id, chart_diff)
            if dx_num != -1:
                output.alpha_composite(self.dx_star_pics, (x + 335, y + 102))

            # Write Song Information
            ## Song ID
            text_output.text((x + 40, y + 148), f"ID{song_id}", font=_tb, anchor="mm")

            ## Title
            title = song_record["title"]
            if self._columnWidth(title) > 18:
                title = self._changeColumnWidth(title, 17) + "..."
            text_output.text(
                (x + 155, y + 20),
                title,
                font=_siyuan,
                fill=TEXT_COLOR[chart_diff],
                anchor="lm",
            )

            ## Achievement
            achievement_rate = song_record["achievements"]
            p, s = f"{achievement_rate:.4f}".split(".")
            r = _tbAchieve1.getbbox(p)

            text_output.text(
                (x + 155, y + 70),
                p,
                font=_tbAchieve1,
                fill=TEXT_COLOR[chart_diff],
                anchor="ld",
            )

            text_output.text(
                (x + 155 + r[2], y + 68),
                f".{s}%",
                font=_tbAchieve2,
                fill=TEXT_COLOR[chart_diff],
                anchor="ld",
            )

            # Single Rating
            chart_const = song_record["ds"]
            computed_ra = self.computeRa(chart_const, achievement_rate)
            text_output.text(
                (x + 155, y + 80),
                f"Rating {chart_const} -> {computed_ra}",
                font=_tbRating,
                fill=TEXT_COLOR[chart_diff],
                anchor="lm",
            )

            # Increment the Song Per Row Record
            num += 1

        return output
