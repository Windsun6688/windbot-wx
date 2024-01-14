import json,os,requests,base64,random,math
from rapidfuzz import fuzz
from PIL import Image, ImageDraw, ImageFont
from typing import List, Optional, Tuple, Union
from io import BytesIO
from ..sqlHelper import *

static = os.path.join(resource_root,'maiCN')
material = os.path.join(static,'material')
mai_func_dir = os.path.dirname(os.path.realpath(__file__))

diffs = ['Basic', 'Advanced', 'Expert', 'Master', 'Re:Master']
levelList = ['1', '2', '3', '4', '5', '6', '7', '7+', '8', '8+', '9','9+',\
        '10', '10+', '11', '11+', '12', '12+', '13', '13+', '14', '14+', '15']
achievementList = [50.0, 60.0, 70.0, 75.0, 80.0, 90.0, 94.0,\
                    97.0, 98.0, 99.0, 99.5, 100.0, 100.5]
BaseRa = [0.0, 5.0, 6.0, 7.0, 7.5, 8.5, 9.5, 10.5, 12.5, 12.7,\
                    13.0, 13.2, 13.5, 14.0]
BaseRaSpp = [7.0, 8.0, 9.6, 11.2, 12.0, 13.6, 15.2, 16.8, 20.0,\
                    20.3, 20.8, 21.1, 21.6, 22.4]

config = json.load(open("config.json", 'r', encoding='utf-8'))
dev_token = config["mai_dev_token"]
if dev_token == "":
    output("Continuing Without Developer Token",\
            'WARNING',background = 'WHITE')

MAI_API = "https://www.diving-fish.com/api/maimaidxprober"
MAI_ALIAS_API = "https://api.yuzuai.xyz/maimaidx"

JPVER_2_CNVER = {
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

PLATE_2_VER = {
    '初': 'maimai',
    '真': 'maimai PLUS',
    '超': 'maimai GreeN',
    '檄': 'maimai GreeN PLUS',
    '橙': 'maimai ORANGE',
    '暁': 'maimai ORANGE PLUS',
    '晓': 'maimai ORANGE PLUS',
    '桃': 'maimai PiNK',
    '櫻': 'maimai PiNK PLUS',
    '樱': 'maimai PiNK PLUS',
    '紫': 'maimai MURASAKi',
    '菫': 'maimai MURASAKi PLUS',
    '堇': 'maimai MURASAKi PLUS',
    '白': 'maimai MiLK',
    '雪': 'MiLK PLUS',
    '輝': 'maimai FiNALE',
    '辉': 'maimai FiNALE',
    '熊': 'maimai でらっくす',
    '華': 'maimai でらっくす',
    '华': 'maimai でらっくす',
    # '華': 'maimai でらっくす PLUS', # Changed in maiCN
    # '华': 'maimai でらっくす PLUS', # Changed in maiCN
    '爽': 'maimai でらっくす Splash',
    '煌': 'maimai でらっくす Splash',
    # '煌': 'maimai でらっくす Splash PLUS', # Changed in maiCN
    '宙': 'maimai でらっくす UNiVERSE',
    '星': 'maimai でらっくす UNiVERSE PLUS',
    '祭': 'maimai でらっくす FESTiVAL',
    '祝': 'maimai でらっくす FESTiVAL PLUS'
}

######## API Functions ########
def mai_api_query_user(gamertag: str, func:str, plates: list = None):
    """
    func 获取数据种类有:
    - plate 获取指定代的游玩数据
    - b50 获取b50数据
    """

    j = {
        'username': gamertag,
    }

    if func == "plate":
        j['version'] = plates
        method = f"/query/plate"
    elif func == "b50":
        j['b50'] = True
        method = f"/query/player"
    else:
        return 0

    url = MAI_API + method

    resp = requests.post(url,json = j)
    if resp.status_code == 200:
        data = resp.json()
        return data
    elif resp.status_code == 403:
        return -2
    elif resp.status_code == 400:
        return -1
    else:
        return 0

def mai_api_query_user_dev(gamertag: str, func: str):
    """
    func 获取数据种类有:
    - records: 全部数据
    """
    if func == "records":
        method = "/dev/player/records"
    else:
        return 0

    url = MAI_API + method

    params = {'username': gamertag}
    headers = {'developer-token': dev_token}

    resp = requests.get(url, headers = headers, params = params)

    if resp.status_code == 403:
        return -2
    elif resp.status_code == 400:
        return -1
    elif resp.status_code == 200:
        data = resp.json()
    else:
        return 0

    return data

def mai_api_data_get(func:str):
    """
    func 获取数据种类有:
    - music 获取曲目数据
    - chart 获取单曲数据
    - ranking 获取查分器ranking排行榜
    """
    if func == 'music':
        method = f"/music_data"
    elif func == 'chart':
        method = f"/chart_stats"
    elif func == 'ranking':
        method = f"/rating_ranking"
    else:
        return 0

    url = MAI_API + method

    resp = requests.get(url)

    if resp.status_code == 200:
        data = resp.json()
        return data
    elif resp.status_code == 403:
        return -2
    elif resp.status_code == 400:
        return -1
    else:
        return 0

def mai_alias_api_get(func:str, sid:int = None):
    """
    func 获取数据种类:
    - alias 所有别名
    - id2alias 返回id对应的别名
    - aliastatus 正在进行的别名投票
    - aliasend 五分钟内结束的别名投票
    - music 曲目数据
    - charts 曲目数据
    """
    params = {}

    if func == "alias":
        method = f"/maimaidxalias"
    elif func == "id2alias":
        method = f"/getsongsalias"
        params["id"] = sid
    elif func == 'aliastatus':
        method = f"/getaliasstatus"
    elif func == 'aliasend':
        method = f"/getaliasend"
    elif func == 'music':
        method = f"/getmaimaidxmusic"
    elif func == 'charts':
        method = f"/getmaimaidxchartstats"
    else:
        return 0

    url = MAI_ALIAS_API + method

    resp = requests.get(url, params = params)

    if resp.status_code == 200:
        data = resp.json()
        return data
    elif resp.status_code == 403:
        return -2
    elif resp.status_code == 400:
        return -1
    else:
        return 0

######## Resources Update & Local Data Retrieval ########
def mai_music_get(local: bool = False) -> Tuple[dict,bool]:
    """
    Not Local: Get Song Data From Diving Fish Server
    Local: Read Song Data From Local File
    """
    success = True
    if not local:
        songs = mai_api_data_get("music")

        if isinstance(songs,list):
            with open(os.path.join(static, 'music_data.json'), 'w', \
                    encoding='utf-8') as f:
                f.write(json.dumps(songs, ensure_ascii=False, indent=4))
        else:
            output('maimaiDX曲目数据获取失败,切换至本地暂存文件',\
                    'WARNING',background = 'WHITE')
            local = True
            success = False
    if local:
        with open(os.path.join(static, 'music_data.json'), 'r', \
                encoding='utf-8') as f:
            songs = json.loads(f.read())

    return (songs, success)

def mai_chartstats_get(local: bool = False) -> Tuple[dict,bool]:
    """
    Not Local: Get Chart Stats From Diving Fish Server
    Local: Read Chart Stats From Local File
    """
    success = True
    if not local:
        chart_stats = mai_api_data_get("chart")

        if isinstance(chart_stats, dict):
            with open(os.path.join(static, 'chart_stats.json'), 'w', \
                    encoding='utf-8') as f:
                f.write(json.dumps(chart_stats, ensure_ascii=False, indent=4))
        else:
            output('maimaiDX谱面数据获取失败,切换至本地暂存文件',\
                    'WARNING',background = 'WHITE')
            local = True
            success = False
    if local:
        with open(os.path.join(static, 'chart_stats.json'), 'r', \
                encoding='utf-8') as f:
            chart_stats = json.loads(f.read())

    return (chart_stats, success)

def mai_alias_get(local: bool = False) -> Tuple[dict,bool]:
    """
    Not Local: Get Song Alias From yuzuai Server
    Local: Read Alias From Local File
    """
    success = True
    if not local:
        alias = mai_alias_api_get("alias")

        if isinstance(alias, dict):
            with open(os.path.join(static, 'song_alias.json'), 'w',\
                    encoding='utf-8') as f:
                f.write(json.dumps(alias, ensure_ascii=False, indent=4))
        else:
            output('maimaiDX歌曲别名数据获取失败,切换为本地暂存文件',\
                    'WARNING',background = 'WHITE')
            local = True
            success = False
    if local:
        with open(os.path.join(static,'song_alias.json'), 'r',\
                encoding='utf-8') as f:
            alias = json.loads(f.read())

    return (alias, success)

def mai_update(datalist,callerid,roomid = None):
    status = ["ERROR","OK"]
    resp = "更新结果:\n"
    resp += f"曲目: {status[int(mai_music_get()[1])]}\n"
    resp += f"谱面: {status[int(mai_chartstats_get()[1])]}\n"
    resp += f"别名: {status[int(mai_alias_get()[1])]}\n"

    return [resp]

######## Helper Functions ########
def mai_process_record(playrecord: dict):
    title = playrecord['title']
    level = playrecord['level_label']
    diff = playrecord['level_index']
    song_id = playrecord['song_id']
    chart_const = playrecord['ds']
    chart_type = playrecord['type']
    acc = playrecord['achievements']
    racc = playrecord['dxScore']
    rate = playrecord['rate'].upper().replace('P','p')
    rating = playrecord['ra']
    fc = playrecord['fc'].upper().replace('P','p')
    fs = playrecord['fs'].upper().replace('P','p')

    star = dxscore_2_star(racc,song_id,diff)
    return [title,level,diff,song_id,chart_const,chart_type,acc,racc,star,rate,rating,fc,fs]

######## Plate Checking  ########
def mai_plate_status(gamertag,datalist):
    # Translate phrase to plate plan
    versions,plan = mai_phrase_2_plate(datalist[0])
    # No such plate or plan exists
    if (versions,plan) == (-1,-1):
        return f"不存在该名牌版: {datalist[0]}"

    try:
        usr_data = mai_api_query_user(gamertag, "plate", versions)
    except:
        return "和Diving-Fish服务器通信失败。请稍后再试。"

    # Getting Data Failed
    if isinstance(usr_data,str):
        return usr_data

    usr_plate_data = usr_data['verlist']

    # Check Remaining Songs
    remaining, remaining_hard = mai_plate_check(usr_plate_data,versions,plan)

    remaining_bas_cnt = len(remaining[0])
    remaining_adv_cnt = len(remaining[1])
    remaining_exp_cnt = len(remaining[2])
    remaining_mas_cnt = len(remaining[3])
    remaining_rem_cnt = len(remaining[4])
    remaining_cnt_list = [remaining_bas_cnt,remaining_adv_cnt,\
                        remaining_exp_cnt,remaining_mas_cnt,remaining_rem_cnt]

    # Calculate the Total Remaining Cnt
    total_remaining_cnt = sum(remaining_cnt_list[:-1])

    # Include Re:Master or Not
    include_rem = (datalist[0][0] in ['舞','霸'])
    if include_rem:
        total_remaining_cnt += remaining_rem_cnt

    plate_states = ["未确认","已确认","已完成"]

    # User Plate Completion Status
    if total_remaining_cnt == 0:
        plate_state_id = 2
    elif remaining_mas_cnt == 0:
        plate_state_id = 1
    else:
        plate_state_id = 0

    reply_txt = f"{gamertag} - 名牌版『{datalist[0]}』\n"
    reply_txt += f"{plate_states[plate_state_id]}\n"

    # Plate Not Completed
    if plate_state_id == 0:
        for i in range(0,4):
            reply_txt += f"- {diffs[i]}难度剩余{remaining_cnt_list[i]}张谱面\n"
        if include_rem:
            reply_txt += f"- {diffs[4]}难度剩余{remaining_cnt_list[4]}张谱面\n"
        reply_txt += f"- 总计: {total_remaining_cnt}张谱面\n"

        # List Remaining 5 Hard Songs
        final_remaining_hard = []
        if not include_rem:
            for song in remaining_hard:
                if song[2] != diffs[4]:
                    final_remaining_hard.append(song)
        else:
            final_remaining_hard = remaining_hard

        hard_song_num = min(5,len(final_remaining_hard))
        reply_txt += f"13+以上谱面{hard_song_num}选:\n"
        for k in range(hard_song_num):
            remaining_hard_song = final_remaining_hard[k]
            s_id = remaining_hard_song[0]
            s_title = remaining_hard_song[1]
            s_diff = remaining_hard_song[2]
            s_ds = remaining_hard_song[3]
            reply_txt += f"[{s_diff} {s_ds}] {s_title} (ID: {s_id})\n"

    # Plate is Confirmed
    elif plate_state_id == 1:
        for i in range(0,3):
            reply_txt += f"- {diffs[i]}难度剩余{remaining_cnt_list[i]}张谱面\n"
        reply_txt += f"- 总共: {total_remaining_cnt}张谱面\n"

    # Plate is Completed
    else:
        reply_txt += "祝贺！"

    return reply_txt

def mai_plate_left(gamertag, datalist):
    # Read query_cnt
    if len(datalist) < 2:
        query_cnt = 15
        plate = datalist[0]
    else:
        query_cnt = int(datalist[0])
        plate = datalist[1]
    # Translate phrase to plate plan
    versions,plan = mai_phrase_2_plate(plate)

    # No such plate or plan exists
    if (versions,plan) == (-1,-1):
        return f"不存在该名牌版: {plate}"

    try:
        usr_data = mai_api_query_user(gamertag, "plate", versions)
    except:
        return "和Diving-Fish服务器通信失败。请稍后再试。"

    # Getting Data Failed
    if isinstance(usr_data,str):
        return usr_data

    usr_plate_data = usr_data['verlist']

    # Check Remaining Songs
    remaining, remaining_hard = mai_plate_check(usr_plate_data,versions,plan)

    # Include Re:Master or Not
    include_rem = (plate[0] in ['舞','霸'])

    query_cnt = min(len(remaining_hard),query_cnt)

    # Concat the reply text
    reply_txt = f"{gamertag} - 名牌版『{plate}』\n"
    reply_txt += f"剩余曲目{query_cnt}选(13.6以上定数倒序):\n"
    final_remaining_hard = []

    if not include_rem:
        for song in remaining_hard:
            if song[2] != diffs[4]:
                final_remaining_hard.append(song)
    else:
        final_remaining_hard = remaining_hard

    for s in range(query_cnt):
        song = final_remaining_hard[s]
        s_id = song[0]
        s_title = song[1]
        s_diff = song[2]
        s_ds = song[3]
        reply_txt += f"[{s_diff} {s_ds}] {s_title} (ID: {s_id})\n"
    return reply_txt

def mai_plate_check(usr_plate_data:list,versions: list,plan:int):
    '''
    plan对照
    0: 极    1: 将
    2: 神    3: 舞舞
    4: 霸者
    '''
    # Load Songs Locally
    mai_songs = mai_music_get(local = True)[0]

    # Initialize Lists to track Remaining / Played
    remain_bas = []
    remain_adv = []
    remain_exp = []
    remain_mas = []
    remain_rem = []
    remaining = [remain_bas,remain_adv,remain_exp,remain_mas,remain_rem]
    remaining_hard = []

    played_bas = []
    played_adv = []
    played_exp = []
    played_mas = []
    played_rem = []
    played = [played_bas, played_adv, played_exp, played_mas, played_rem]

    # Switch Structure for qualification standards
    check_item = ['fc','achievements','fc','fs','achievements']
    item_2_check = check_item[plan]

    # Checking each record in usr_plate_data
    for record in usr_plate_data:
        song_id = record['id']
        chart_diff = record['level_index']
        chart_level = record['level']

        played[chart_diff].append(song_id)

        qualify_item = record[item_2_check]
        # Didn't pass check, add to remaining
        if mai_plate_item_check(qualify_item,plan) == False:
            remaining[chart_diff].append(song_id)

    # Check for Remaining Songs
    for song in mai_songs:
        song_version = song['basic_info']['from']
        if song_version in versions:
            song_id = int(song['id'])
            # Skip ジングルベル
            if song_id == 70:
                continue

            # Remove Append Remaster Songs when querying 舞 Series
            append_remas_id = [
                                47,  # 源平大戦絵巻テーマソング
                                133, # We Gonna Party
                                144, # Air's Gravity
                                219, # 記憶、記録
                                239, # System “Z”
                                240, # Beat of Getting EntangledWBW
                                364, # D✪N’T ST✪P R✪CKIN'
                                367, # Dragoon
                                378, # planet dancer
                                389, # FLOWER
                                463, # FEEL the BEATS
                                464, # Revive the Rave
                                472, # アージェントシンメトリー
                                629, # Limit Break
                                704, # SPILL OVER COLORS
            ]
            if song_id in append_remas_id:
                song['ds'] = song['ds'][:-1]

            song_title = song['title']
            # Check all diffs for this song
            diff_cnt = 0
            for ds in song['ds']:
                if song_id in remaining[diff_cnt]:
                    if ds > 13.6:
                        remaining_hard.append((song_id,song_title,\
                                                diffs[diff_cnt], ds))
                if song_id not in played[diff_cnt]:
                    remaining[diff_cnt].append(song_id)
                    if ds > 13.6:
                        remaining_hard.append((song_id,song_title,\
                                                diffs[diff_cnt], ds))
                diff_cnt += 1

    remaining_hard = sorted(remaining_hard, key = lambda i: i[3],\
                            reverse = True)
    return remaining,remaining_hard

def mai_plate_item_check(item, plan:int)-> bool:
    # 极
    if plan == 0:
        return item in ['fc', 'fcp','ap','app']
    # 将
    elif plan == 1:
        return item >= 100.0
    # 神
    elif plan == 2:
        return item in ['ap', 'app']
    # 舞舞
    elif plan == 3:
        return item in ['fsd', 'fsdp']
    # Clear
    elif plan == 4:
        return item >= 80.0

def mai_phrase_2_plate(phrase: str) -> (list,str):
    ver = phrase[0]
    plan = phrase[1:]
    # Process Version
    if ver in ['霸', '舞']:
        version = list(set(_v for _v in list(PLATE_2_VER.values())[:-9]))
    elif ver == '真':
        version = list(set(_v for _v in list(PLATE_2_VER.values())[0:2]))
    elif ver == '星':
        version = [PLATE_2_VER['宙']]
    elif ver == '祝':
        version = [PLATE_2_VER['祭']]
    else:
        version = [PLATE_2_VER.get(ver,-1)]
        if version == [-1]:
            return (-1,-1)

    # Process Plan
    if plan in ['極', '极']:
        plan_num = 0
    elif plan == '将':
        # No such plate
        if ver == '真':
            return (-1,-1)
        plan_num = 1
    elif plan == '神':
        plan_num = 2
    elif plan == '舞舞':
        plan_num = 3
    elif plan == '者' and ver == '霸':
        plan_num = 4
    else:
        return (-1,-1)

    return (version,plan_num)

######## Single Score ########
def mai_single_score(gamertag:str, sid:int):
    try:
        usr_data = mai_api_query_user_dev(gamertag, "records")
    except:
        return "和Diving-Fish服务器通信失败。请稍后再试。"
    song_info = mai_music_by_id(sid)
    usr_single_grade = [grade for grade in usr_data["records"]\
                        if grade['song_id'] == sid]

    reply_txt = f"{gamertag} - 单曲『{song_info['title']}』成绩:\n"

    # For each level the song has
    for i in range(len(song_info["ds"])):
        diff = diffs[i]
        ds = song_info["ds"][i]
        achievement = "无数据"
        for g in usr_single_grade:
            if g['level_index'] == i:
                achievement = str(g['achievements']) + "%"

        reply_txt += f"- [{diff} {ds}] {achievement}\n"
    return reply_txt

######## Music Functions  ########
def mai_music_search(datalist,callerid,roomid = None):
    # Fuzzy text search
    if datalist[0].lower() == 'f':
        keyword = " ".join(datalist[1:])
        results = mai_music_by_fuzzy_title(keyword,65)
    # Other Searches
    else:
        keyword = " ".join(datalist)

        # If user uses ID search
        if keyword.isnumeric():
            results = []
            results.append(mai_music_by_id(int(keyword)))

        # (A Bit More) Precise Text Search
        else:
            results = mai_music_by_fuzzy_title(keyword,90)

    if len(results) == 0:
        return [f'没有搜寻到结果。您查找了:{keyword}']
    elif len(results) > 5:
        return ['结果过多。请尝试优化搜索词。']

    reply_txt = f"共找到以下{len(results)}个结果:"
    for s in results:
        sid = s['id']
        is_DX = s['type']
        title = s['title']

        artist = s['basic_info']['artist']
        JP_version = s['basic_info']['from']
        CN_version = JPVER_2_CNVER.get(JP_version,JP_version)
        category = s['basic_info']['genre']
        bpm = s['basic_info']['bpm']
        ds = s['ds']

        new_txt = ''
        if s['basic_info']['is_new']:
            new_txt = '[NEW]'

        remas_txt = '\n'
        if len(ds) == 5:
            remas_txt = f' | ReMas{ds[4]}\n'

        reply_txt += f"\n[{is_DX}]{new_txt} {artist} - {title}\n-版本:{CN_version} | 分区:{category} | BPM:{bpm}\n--Bas{ds[0]} | Adv{ds[1]} | Exp{ds[2]} | Mas{ds[3]}{remas_txt}---Song ID: {sid}\n"
    return [reply_txt]

def mai_music_by_id(song_id: int):
    songs = mai_music_get(local = True)[0]
    for s in songs:
        if s["id"] == str(song_id):
            return s
    return -1

def mai_music_by_fuzzy_title(title: str, QRatio: int):
    songs = mai_music_get(local = True)[0]
    results = []
    for s in songs:
        if fuzz.QRatio(title.lower(),s['title'].lower()) >= QRatio:
            results.append(s)
    return results

def mai_music_by_bpm(bpm: int):
    songs = mai_music_get(local = True)[0]
    results = []
    for s in songs:
        if s["basic_info"]["bpm"] == bpm:
            results.append(s)
    return results

def mai_music_random(datalist,callerid,roomid = None):
    # If no diff specified, random over the whole collection
    if len(datalist) == 0:
        songs = mai_music_get(True)[0]
    # If a number of diffs are specified
    else:
        collection = mai_music_get(True)[0]
        songs = []
        for s in collection:
            for diff in s['level']:
                if diff in datalist:
                    songs.append(s)
        if len(songs) == 0:
            return['没有找到在这些难度的歌曲。']

    choice = random.choice(songs)
    reply_txt = "WB为你随机抽取了以下歌曲:\n"
    reply_txt += f"{choice['title']} (id: {choice['id']})"
    return [reply_txt]

def mai_music_new(datalist,callerid,roomid = None):
    songs = mai_music_get(local = False)[0]
    reply_txt = "当前CN最新版本歌曲列表:\n"
    has_new = False
    for s in songs:
        if s['basic_info']['is_new']:
            has_new = True
            reply_txt += f"{s['title']} (id: {s['id']})\n"
    if has_new:
        return [reply_txt]
    else:
        return ['当前还没有新歌。']

def mai_music_bpm(datalist,callerid,roomid = None):
    if len(datalist) < 1:
        return ['请提供需要查询的BPM。']
    elif len(datalist) > 1:
        return ['WB只能查询一个BPM。']

    bpm = datalist[0]
    if not bpm.isnumeric():
        return [f'请提供一个数字。\n您正在尝试查询:{bpm}']

    bpm = int(bpm)
    results = mai_music_by_bpm(bpm)
    results_cnt = len(results)

    if results_cnt == 0:
        reply_txt = f"没有{bpm}BPM的歌曲。"
        return [reply_txt]

    reply_txt = f"在{bpm}BPM的歌曲共有{results_cnt}首:\n"
    for i in range(results_cnt):
        song_info = results[i]
        song_title = song_info["title"]
        song_id = song_info["id"]
        reply_txt += f"{i+1}. {song_title} (ID:{song_id})\n"
    return [reply_txt]

def mai_alias_search(datalist,callerid,roomid = None):
    # 载入数据
    song_alias = mai_alias_get(local = True)[0]
    if song_alias == -1:
        return ['加载别名时出现未知错误。']

    results = []

    keyword = ''
    for word in datalist:
        keyword += (word)

    for sid in song_alias:
        if keyword in song_alias[sid]['Alias']:
            results.append([sid,song_alias[sid]['Name']])

    if len(results) == 0:
        return ['没有搜寻到结果,或搜索模式关键词错误。']
    elif len(results) > 10:
        return ['请尝试优化搜索词。']

    reply_txt = f"这个别名可能指向以下{len(results)}首歌:"
    cnt = 1
    for s in results:
        reply_txt += f"\n{cnt}. {s[1]} (ID:{s[0]})"
        cnt += 1

    return [reply_txt]

######## Best Image Drawing ########
def image_to_base64(img: Image.Image, fileFormat='PNG') -> str:
    output_buffer = BytesIO()
    img.save(output_buffer, fileFormat)
    byte_data = output_buffer.getvalue()
    base64_str = base64.b64encode(byte_data).decode()
    return 'base64://' + base64_str

def is_cjk(character):
    """"
    Checks whether character is CJK.

        >>> is_cjk(u'\u33fe')
        True
        >>> is_cjk(u'\uFE5F')
        False

    :param character: The character that needs to be checked.
    :type character: char
    :return: bool
    """
    return any([start <= ord(character) <= end for start, end in
                [(4352, 4607), (11904, 42191), (43072, 43135), (44032, 55215),
                 (63744, 64255), (65072, 65103), (65381, 65500),
                 (131072, 196607)]
                ])

def computeRa(ds: float, achievement: float, spp: bool = False, israte: bool = False) -> Union[int, Tuple[int, str]]:
    baseRa = 22.4 if spp else 14.0
    rate = 'SSSp'
    if achievement < 50:
        baseRa = 7.0 if spp else 0.0
        rate = 'D'
    elif achievement < 60:
        baseRa = 8.0 if spp else 5.0
        rate = 'C'
    elif achievement < 70:
        baseRa = 9.6 if spp else 6.0
        rate = 'B'
    elif achievement < 75:
        baseRa = 11.2 if spp else 7.0
        rate = 'BB'
    elif achievement < 80:
        baseRa = 12.0 if spp else 7.5
        rate = 'BBB'
    elif achievement < 90:
        baseRa = 13.6 if spp else 8.5
        rate = 'A'
    elif achievement < 94:
        baseRa = 15.2 if spp else 9.5
        rate = 'AA'
    elif achievement < 97:
        baseRa = 16.8 if spp else 10.5
        rate = 'AAA'
    elif achievement < 98:
        baseRa = 20.0 if spp else 12.5
        rate = 'S'
    elif achievement < 99:
        baseRa = 20.3 if spp else 12.7
        rate = 'Sp'
    elif achievement < 99.5:
        baseRa = 20.8 if spp else 13.0
        rate = 'SS'
    elif achievement < 100:
        baseRa = 21.1 if spp else 13.2
        rate = 'SSp'
    elif achievement < 100.5:
        baseRa = 21.6 if spp else 13.5
        rate = 'SSS'

    if israte:
        data = (math.floor(ds * (min(100.5, achievement) / 100) * baseRa), rate)
    else:
        data = math.floor(ds * (min(100.5, achievement) / 100) * baseRa)

    return data

def _getCharWidth(o) -> int:
    widths = [
        (126, 1), (159, 0), (687, 1), (710, 0), (711, 1), (727, 0), (733, 1), (879, 0), (1154, 1), (1161, 0),
        (4347, 1), (4447, 2), (7467, 1), (7521, 0), (8369, 1), (8426, 0), (9000, 1), (9002, 2), (11021, 1),
        (12350, 2), (12351, 1), (12438, 2), (12442, 0), (19893, 2), (19967, 1), (55203, 2), (63743, 1),
        (64106, 2), (65039, 1), (65059, 0), (65131, 2), (65279, 1), (65376, 2), (65500, 1), (65510, 2),
        (120831, 1), (262141, 2), (1114109, 1),
    ]
    if o == 0xe or o == 0xf:
        return 0
    for num, wid in widths:
        if o <= num:
            return wid
    return 1

def _columnWidth(s: str) -> int:
    res = 0
    for ch in s:
        res += _getCharWidth(ord(ch))
    return res

def _changeColumnWidth(s: str, length: int) -> str:
    res = 0
    sList = []
    for ch in s:
        res += _getCharWidth(ord(ch))
        if res <= length:
            sList.append(ch)
    return ''.join(sList)

def rating_picture(rating: int, b50: bool) -> str:
        num = '11'
        if rating < 1000:
            num = '01'
        elif rating < 2000:
            num = '02'
        elif rating < (4000 if b50 else 3000):
            num = '03'
        elif rating < (7000 if b50 else 4000):
            num = '04'
        elif rating < (10000 if b50 else 5000):
            num = '05'
        elif rating < (12000 if b50 else 6000):
            num = '06'
        elif rating < (13000 if b50 else 7000):
            num = '07'
        elif rating < (14000 if b50 else 7000):
            num = '08'
        elif rating < (14500 if b50 else 8000):
            num = '09'
        elif rating < (15000 if b50 else 8500):
            num = '10'
        return f'UI_CMN_DXRating_{num}.png'

def friend_match_picture(addrating: int) -> str:
        t = '01'
        if addrating < 250:
            t = '01'
        elif addrating < 500:
            t = '02'
        elif addrating < 750:
            t = '03'
        elif addrating < 1000:
            t = '04'
        elif addrating < 1200:
            t = '05'
        elif addrating < 1400:
            t = '06'
        elif addrating < 1500:
            t = '07'
        elif addrating < 1600:
            t = '08'
        elif addrating < 1700:
            t = '09'
        elif addrating < 1800:
            t = '10'
        elif addrating < 1850:
            t = '11'
        elif addrating < 1900:
            t = '12'
        elif addrating < 1950:
            t = '13'
        elif addrating < 2000:
            t = '14'
        elif addrating < 2010:
            t = '15'
        elif addrating < 2020:
            t = '16'
        elif addrating < 2030:
            t = '17'
        elif addrating < 2040:
            t = '18'
        elif addrating < 2050:
            t = '19'
        elif addrating < 2060:
            t = '20'
        elif addrating < 2070:
            t = '21'
        elif addrating < 2080:
            t = '22'
        elif addrating < 2090:
            t = '23'
        elif addrating < 2100:
            t = '24'
        else:
            t = '25'

        return f'UI_DNM_DaniPlate_{t}.png'

def dxscore_2_star(dxscore: int, song_id: int, level: int):
    song = mai_music_by_id(song_id)
    if song == -1:
        return -1

    notes = song["charts"][level]['notes']
    value = 0
    for i in notes:
        value += i

    dx = dxscore / (value * 3) * 100
    if dx <= 85:
        result = (0, 0)
    elif dx <= 90:
        result = (0, 1)
    elif dx <= 93:
        result = (0, 2)
    elif dx <= 95:
        result = (1, 3)
    elif dx <= 97:
        result = (1, 4)
    else:
        result = (2, 5)
    return result

def get_cover_len4_id(mid: str) -> str:
    mid = int(mid)

    if 10001 <= mid:
        # mid -= 10000
        return mid

    return f'{mid:04d}'

def best_2_image(output: Image.Image,data: list,isOld: bool):
    # isOld = True 放在旧版本位置
    # isOld = False 放在新版本位置
    y = 430 if isOld else 1670
    dy = 170

    # Old Color Schemes
    # TEXT_COLOR = [(14, 117, 54, 255), (199, 69, 12, 255), (192, 32, 56, 255), (103, 20, 141, 255), (230, 230, 230, 255)]
    # TEXT_COLOR = [(14, 117, 54, 255), (199, 69, 12, 255), (175, 0, 50, 255), (103, 20, 141, 255), (103, 20, 141, 255)]

    TEXT_COLOR = [(255, 255, 255, 255), (255, 255, 255, 255), (255, 255, 255, 255), (255, 255, 255, 255), (103, 20, 141, 255)]

    cover_dir = os.path.join(material,'cover')
    mai_dir = os.path.join(material,'pic')

    # Load Assets
    dxstar = [Image.open(os.path.join(mai_dir, f'UI_RSL_DXScore_Star_0{_ + 1}.png')).resize((20, 20)) for _ in range(3)]

    bas_bg = Image.open(os.path.join(mai_dir,'b40_score_basic.png'))
    adv_bg = Image.open(os.path.join(mai_dir,'b40_score_advanced.png'))
    exp_bg = Image.open(os.path.join(mai_dir,'b40_score_expert.png'))
    mas_bg = Image.open(os.path.join(mai_dir,'b40_score_master.png'))
    remas_bg = Image.open(os.path.join(mai_dir,'b40_score_remaster.png'))

    diff_bg = [bas_bg,adv_bg,exp_bg,mas_bg,remas_bg]

    Torus_SemiBold = os.path.join(material, 'Torus SemiBold.otf')
    siyuan = os.path.join(material, 'SourceHanSansSC-Bold.otf')

    _tb = ImageFont.truetype(Torus_SemiBold, 20)
    _tbAchieve1 = ImageFont.truetype(Torus_SemiBold, 35)
    _tbAchieve2 = ImageFont.truetype(Torus_SemiBold, 25)
    _tbRating = ImageFont.truetype(Torus_SemiBold, 22)
    _siyuan = ImageFont.truetype(siyuan, 20)

    text_output = ImageDraw.Draw(output)

    num = 0
    x = 0
    for s in data:
        # 每首歌间距/5首歌换行
        if num % 5 == 0:
                x = 70
                y += dy if num != 0 else 0
        else:
                x += 416

        # 结构: [title,level,diff,song_id,chart_const,chart_type,acc,racc,star,rate,rating,fc,fs]
        info = mai_process_record(s)

        # Used to use 4 digit ids. Depreciated
        ## songid = get_cover_len4_id(info[3])
        # Fixed
        try:
            cover = Image.open(os.path.join(cover_dir, f'{info[3]}.png')).resize((135, 135))
        except FileNotFoundError as e:
            cover = Image.open(os.path.join(cover_dir, f'{random.randint(1,2)*-1}.png')).resize((135, 135))

        version = Image.open(os.path.join(mai_dir, f'UI_RSL_MBase_Parts_{info[5]}.png')).resize((55, 19))
        rate = Image.open(os.path.join(mai_dir, f'UI_TTR_Rank_{info[9]}.png')).resize((95, 44))

        output.alpha_composite(diff_bg[info[2]],(x,y))
        output.alpha_composite(cover,(x+5, y+5))
        output.alpha_composite(version,(x+80,y+141))
        output.alpha_composite(rate,(x+150,y+98))

        # if FC
        if info[11]:
           fc = Image.open(os.path.join(mai_dir, f'UI_MSS_MBase_Icon_{info[11]}.png')).resize((45, 45))
           output.alpha_composite(fc, (x+260, y+98))

        # if FS
        if info[12]:
           fs = Image.open(os.path.join(mai_dir, f'UI_MSS_MBase_Icon_{info[12]}.png')).resize((45, 45))
           output.alpha_composite(fs, (x+315,y+98))

        # DX Star
        dx = info[8]
        for _ in range(dx[1]):
            output.alpha_composite(dxstar[dx[0]], (x + 355, y + 40 + 20 * _))

        ## Write Song Information

        # Song ID
        text_output.text((x+40,y+148),str(info[3]),font=_tb,anchor = 'mm')

        # Title
        title = info[0]
        if _columnWidth(title) > 18:
            title = _changeColumnWidth(title,17) + '...'

        text_output.text((x+155,y+20),title,font=_siyuan,fill = TEXT_COLOR[info[2]],anchor = 'lm')

        # Achievement
        p, s = f"{info[6]:.4f}".split('.')
        r = _tbAchieve1.getbbox(p)

        text_output.text((x+155,y+70),p,font=_tbAchieve1,fill = TEXT_COLOR[info[2]],anchor = 'ld')

        text_output.text((x+155+ r[2],y+68),f'.{s}%',font=_tbAchieve2,fill = TEXT_COLOR[info[2]],anchor = 'ld')

        # Single Rating
        text_output.text((x+155,y+80),f'Rating {info[4]} -> {computeRa(info[4], info[6], True)}',font = _tbRating, fill = TEXT_COLOR[info[2]], anchor = 'lm')

        num += 1

    return output

def draw_best_image(gamertag: str):
    user_data = mai_api_query_user(gamertag, "b50")

    if user_data == -2:
        return -2
    elif user_data == -1:
        return -1
    elif user_data == 0:
        return 0

    # Extract Data
    ra = user_data['rating']
    add_ra = user_data['additional_rating']
    nickname = user_data['nickname']
    plate = user_data['plate']
    sd_best = list(user_data['charts']['sd'])
    dx_best = list(user_data['charts']['dx'])

    # Load Fonts & Directories
    meiryo = os.path.join(material, 'meiryo.ttc')
    siyuan = os.path.join(material, 'SourceHanSansSC-Bold.otf')
    Torus_SemiBold = os.path.join(material, 'Torus SemiBold.otf')
    nosa = os.path.join(material, 'NOSA.ttf')
    mai_dir = os.path.join(material,'pic')

    # Load Assets
    logo = Image.open(os.path.join(mai_dir, 'logo.png')).resize((378, 172))
    dx_rating = Image.open(os.path.join(mai_dir, \
                    rating_picture(ra+add_ra,b50 = True))).resize((425, 80))
    Name = Image.open(os.path.join(mai_dir, 'Name.png'))
    MatchLevel = Image.open(os.path.join(mai_dir, \
                            friend_match_picture(add_ra))).resize((128, 58))
    rating = Image.open(os.path.join(mai_dir,\
                            'UI_CMN_Shougou_Rainbow.png')).resize((454, 50))

    ### Generate Best Image ###
    im = Image.open(os.path.join(mai_dir,'b40_bg.png')).convert('RGBA')
    im.alpha_composite(logo,(5,130))

    # If user achieved any plates
    if plate:
        plate = Image.open(os.path.join(mai_dir, \
                                        f'{plate}.png')).resize((1420, 230))
    else:
        plate = Image.open(os.path.join(mai_dir, \
                                'UI_Plate_300101.png')).resize((1420, 230))
    # Draw Plate
    im.alpha_composite(plate, (390, 100))

    # Draw Icon
    icon = Image.open(os.path.join(mai_dir, 'UI_Icon_309503.png')).resize((214, 214))
    im.alpha_composite(icon, (398, 108))

    # Draw Parts Base
    im.alpha_composite(dx_rating, (620, 108))
    im.alpha_composite(Name, (620, 200))
    im.alpha_composite(MatchLevel, (935, 205))
    im.alpha_composite(rating,(620,275))

    ## Writing Information
    text_im = ImageDraw.Draw(im)

    # Custom font style and font size
    _meiryo = ImageFont.truetype(meiryo, 40)
    _siyuan = ImageFont.truetype(siyuan, 25)
    _tb = ImageFont.truetype(Torus_SemiBold, 48)
    _nosa = ImageFont.truetype(nosa, 40)

    # Write Player Name
    text_im.text((635,235),nickname.upper(),font=_tb,fill =(0,0,0,255),anchor = 'lm')

    # Write Split Rating
    text_im.text((847, 300),'New Rating System', font=_siyuan, fill= (0, 0, 0, 255),anchor = 'mm')

    # Write Credits
    text_im.text((900, 2365), 'Generated by WINDBOT | Assets&Design by Yuri-YuzuChaN & BlueDeer233', font = _tb, fill = (103, 20, 141, 255), anchor = 'mm')

    # Write Rating Bar
    total_ra = ra + add_ra

    # New Rating Recalculation
    total_ra = 0
    for s in sd_best:
        total_ra += computeRa(s["ds"],s["achievements"],True)
    for s in dx_best:
        total_ra += computeRa(s["ds"],s["achievements"],True)

    total_ra = f"{total_ra:05d}"

    for n, i in enumerate(total_ra):
        if n == 0 and i == 0:
            continue
        im.alpha_composite(Image.open(os.path.join(mai_dir, f'UI_NUM_Drating_{i}.png')), (820 + 33 * n, 133))

    ## Drawing Song Info
    im = best_2_image(im,dx_best,False)
    im = best_2_image(im,sd_best,True)

    return im
