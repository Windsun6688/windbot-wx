import json,os,requests,base64,random,math
from rapidfuzz import fuzz, utils
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, List, Optional, Tuple, Union
from io import BytesIO
from ..sqlHelper import *

static = os.path.join(os.path.dirname(__file__),'resource')
material = os.path.join(static,'material')

scoreRank = ['d', 'c', 'b', 'bb', 'bbb', 'a', 'aa', 'aaa', 's', 's+', 'ss', 'ss+', 'sss', 'sss+']
comboRank = ['fc', 'fc+', 'ap', 'ap+']
combo_rank = ['fc', 'fcp', 'ap', 'app']
full_combo_rank = ['[FULL COMBO] ','[FULL COMBO+] ','[ALL PERFECT] ','[ALL PERFECT+] ']
syncRank = ['fs', 'fs+', 'fdx', 'fdx+']
sync_rank = ['fs', 'fsp', 'fsd', 'fsdp']
full_sync_rank = ['<FULL SYNC> ','<FULL SYNC+> ','<FULL SYNC DX> ','<FULL SYNC DX+> ']
diffs = ['Basic', 'Advanced', 'Expert', 'Master', 'Re:Master']
levelList = ['1', '2', '3', '4', '5', '6', '7', '7+', '8', '8+', '9', '9+', '10', '10+', '11', '11+', '12', '12+', '13', '13+', '14', '14+', '15']
achievementList = [50.0, 60.0, 70.0, 75.0, 80.0, 90.0, 94.0, 97.0, 98.0, 99.0, 99.5, 100.0, 100.5]
BaseRa = [0.0, 5.0, 6.0, 7.0, 7.5, 8.5, 9.5, 10.5, 12.5, 12.7, 13.0, 13.2, 13.5, 14.0]
BaseRaSpp = [7.0, 8.0, 9.6, 11.2, 12.0, 13.6, 15.2, 16.8, 20.0, 20.3, 20.8, 21.1, 21.6, 22.4]

ALIAS = {
    'all': 'maimaidx_alias',
    'songs': 'get_song',
    'alias': 'get_song_alias',
    'status': 'get_alias_status',
    'apply': 'apply_alias',
    'agree': 'agree_user',
    'end': 'get_alias_end'
}

def mai_api_get(gamertag: str, b50: bool = False,type: str = 'player'):
    url = f'https://www.diving-fish.com/api/maimaidxprober/query/{type}'
    j = {
        'username': gamertag,
    }
    if b50:
        j['b50'] = True

    resp = requests.post(url,json = j)
    # print(resp)
    if resp.status_code == 403:
        return -2
    elif resp.status_code == 400:
        return -1
    elif resp.status_code == 200:
        data = resp.json()
    else:
        return 0

    return data

def process_record(playrecord: dict):
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

def mai_music_get(local: bool = False):
    if local:
        with open(os.path.join(static, 'music_data.json'), 'r', encoding='utf-8') as f:
            songs = json.loads(f.read())
        with open(os.path.join(static, 'chart_stats.json'), 'r', encoding='utf-8') as f:
            stats = json.loads(f.read())
        return songs,stats

    # SONG DETAILS
    resp = requests.get('https://www.diving-fish.com/api/maimaidxprober/music_data')
    # print(resp.status_code)

    if resp.status_code != 200:
        output('maimaiDX曲目数据获取失败,切换至本地暂存文件','WARNING',background = 'WHITE')
        with open(os.path.join(static, 'music_data.json'), 'r', encoding='utf-8') as f:
            songs = json.loads(f.read())
    else:
        songs = resp.json()
        with open(os.path.join(static, 'music_data.json'), 'w', encoding='utf-8') as f:
            f.write(json.dumps(songs, ensure_ascii=False, indent=4))

    # CHART DETAILS
    resp = requests.get('https://www.diving-fish.com/api/maimaidxprober/chart_stats')
    if resp.status_code != 200:
        output('maimaiDX谱面数据获取失败,切换至本地暂存文件','WARNING',background = 'WHITE')
        with open(os.path.join(static, 'chart_stats.json'), 'r', encoding='utf-8') as f:
            stats = json.loads(f.read())
    else:
        stats = resp.json()
        with open(os.path.join(static, 'chart_stats.json'), 'w', encoding='utf-8') as f:
            f.write(json.dumps(stats, ensure_ascii=False, indent=4))
    return songs,stats

def mai_music_search(datalist,callerid,roomid = None):
    # 载入数据
    mai_songs,mai_charts = mai_music_get(local = True)

    results = []
    # Fuzzy text search
    if datalist[0].lower() == 'f':
        keyword = ''
        for word in datalist[1:]:
            keyword += (word + ' ')
        keyword = keyword[:-1]
        for song in mai_songs:
            # print(song)
            if fuzz.QRatio(keyword,song['title']) >= 65:
                results.append(song)
    else:
        keyword = ''
        for word in datalist:
            keyword += (word + ' ')
        keyword = keyword[:-1]

        # If user uses ID search
        if keyword.isnumeric():
            for song in mai_songs:
                if song['id'] == keyword:
                    results.append(song)
                    break

        # Precise Text Search
        else:
            for song in mai_songs:
                if fuzz.QRatio(keyword,song['title']) >= 90:
                    results.append(song)
                    break

    if len(results) == 0:
        return ['没有搜寻到结果,或搜索模式关键词错误。']
    elif len(results) > 5:
        return ['请尝试优化搜索词。']

    reply_txt = f"共找到以下{len(results)}个结果:"
    for s in results:
        # output(s,background = 'MINT')
        sid = s['id']
        is_DX = s['type']
        title = s['title']

        artist = s['basic_info']['artist']
        version = s['basic_info']['from']
        category = s['basic_info']['genre']
        bpm = s['basic_info']['bpm']
        ds = s['ds']

        new_txt = ''
        if s['basic_info']['is_new']:
            new_txt = '[NEW]'

        remas_txt = '\n'
        if len(ds) == 5:
            remas_txt = f' | ReMas{ds[4]}\n'

        reply_txt += f"\n[{is_DX}]{new_txt} {artist} - {title}\n-版本:{version} | 分区:{category} | BPM:{bpm}\n--Bas{ds[0]} | Adv{ds[1]} | Exp{ds[2]} | Mas{ds[3]}{remas_txt}---Song ID: {sid}"
    return [reply_txt]

def mai_music_by_id(song_id: int):
    songs = mai_music_get(True)[0]
    for s in songs:
        if s["id"] == str(song_id):
            return s
    return -1

def mai_music_by_title(title: str):
    songs = mai_music_get(True)[0]
    for s in songs:
        if s["title"] == title:
            return s
    return -1

def mai_music_random():
    songs = mai_music_get(True)[0]
    return random.choice(songs)

def mai_alias_get(type: str = 'all',params: dict = None, local: bool = False):
    """
    - `all`: 所有曲目的别名
    - `songs`: 该别名的曲目
    - `alias`: 该曲目的所有别名
    - `status`: 正在进行的别名申请
    - `end`: 已结束的别名申请
    """
    if local:
        with open(os.path.join(static, 'song_alias.json'), 'r', encoding='utf-8') as f:
                data = json.loads(f.read())
        return data

    try:
        resp = requests.get(f'https://api.yuzuai.xyz/maimaidx/{ALIAS[type]}',params = params)

        if resp.status_code != 200:
            output('maimaiDX歌曲别名数据获取失败,切换为本地暂存文件','WARNING',background = 'WHITE')
            with open(os.path.join(static, 'song_alias.json'), 'r', encoding='utf-8') as f:
                data = json.loads(f.read())
        else:
            data = resp.json()
            with open(os.path.join(static, 'song_alias.json'), 'w', encoding='utf-8') as f:
                f.write(json.dumps(data, ensure_ascii=False, indent=4))
    except Exception as e:
        output(f'获取别名时发生错误: {e}','WARNING',background = 'WHITE')
        return -1

    return data

def mai_alias_search(datalist,callerid,roomid = None):
    # 载入数据
    song_alias = mai_alias_get(local = True)
    if song_alias == -1:
        return ['加载别名时出现未知错误。']

    results = []

    keyword = ''
    for word in datalist:
        keyword += (word)

    for song in song_alias:
        if keyword in song['Alias']:
            results.append(song)

    if len(results) == 0:
        return ['没有搜寻到结果,或搜索模式关键词错误。']
    elif len(results) > 5:
        return ['请尝试优化搜索词。']

    reply_txt = f"这个别名可能指向以下{len(results)}首歌:"
    cnt = 1
    for s in results:
        sid = s['ID']
        title = s['Name']
        reply_txt += f"\n{cnt}.{title} (ID:{sid})"
        cnt += 1

    return [reply_txt]

def mai_update(datalist,callerid,roomid = None):
    resp = "更新结果:\n"
    mai_music_get()
    resp += "曲目:ok\n"
    if mai_alias_get() == -1:
        resp += "别名:错误"
    else:
        resp += "别名:ok"
    return [resp]

#### Best Image Drawing ####
def image_to_base64(img: Image.Image, format='PNG') -> str:
    output_buffer = BytesIO()
    img.save(output_buffer, format)
    byte_data = output_buffer.getvalue()
    base64_str = base64.b64encode(byte_data).decode()
    return 'base64://' + base64_str

def Q2B(uchar):
    """单个字符 全角转半角"""
    inside_code = ord(uchar)
    if inside_code == 0x3000:
        inside_code = 0x0020
    else:
        inside_code -= 0xfee0
    # 转完之后不是半角字符返回原来的字符
    if inside_code < 0x0020 or inside_code > 0x7e:
        return uchar
    return chr(inside_code)

def stringQ2B(ustring):
    """把字符串全角转半角"""
    return "".join([self._Q2B(uchar) for uchar in ustring])

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

def _changeColumnWidth(s: str, len: int) -> str:
    res = 0
    sList = []
    for ch in s:
        res += _getCharWidth(ord(ch))
        if res <= len:
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
        elif rating < (14500 if b50 else 8000):
            num = '08'
        elif rating < (15000 if b50 else 8500):
            num = '09'
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

def best_2_image(output: Image.Image,data: list,type: bool):
    # type = True 放在旧版本位置
    # type = False 放在新版本位置
    y = 430 if type else 1670
    dy = 170

    # Old Color Schemes
    # TEXT_COLOR = [(14, 117, 54, 255), (199, 69, 12, 255), (192, 32, 56, 255), (103, 20, 141, 255), (230, 230, 230, 255)]
    # TEXT_COLOR = [(14, 117, 54, 255), (199, 69, 12, 255), (175, 0, 50, 255), (103, 20, 141, 255), (103, 20, 141, 255)]

    TEXT_COLOR = [(255, 255, 255, 255), (255, 255, 255, 255), (255, 255, 255, 255), (255, 255, 255, 255), (103, 20, 141, 255)]
    DXSTAR_DEST = [0, 330, 320, 310, 300, 290]

    comboPic = ['', 'FC', 'FCp', 'AP', 'APp']
    syncPic = ['', 'FS', 'FSp', 'FSD', 'FSDp']
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
        info = process_record(s)

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

def draw_best_image(gamertag: str, b50: bool):
    user_data = mai_api_get(gamertag,True)

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
    cover_dir = os.path.join(material,'cover')
    mai_dir = os.path.join(material,'pic')

    # Load Assets
    logo = Image.open(os.path.join(mai_dir, 'logo.png')).resize((378, 172))
    dx_rating = Image.open(os.path.join(mai_dir, rating_picture(ra+add_ra,b50))).resize((425, 80))
    Name = Image.open(os.path.join(mai_dir, 'Name.png'))
    MatchLevel = Image.open(os.path.join(mai_dir, friend_match_picture(add_ra))).resize((134, 55) if b50 else (128, 58))
    rating = Image.open(os.path.join(mai_dir, 'UI_CMN_Shougou_Rainbow.png')).resize((454, 50))

    ### Generate Best Image ###
    im = Image.open(os.path.join(mai_dir,'b40_bg.png')).convert('RGBA')
    im.alpha_composite(logo,(5,130))

    # If user achieved any plates
    if plate:
        plate = Image.open(os.path.join(mai_dir, f'{plate}.png')).resize((1420, 230))
    else:
        plate = Image.open(os.path.join(mai_dir, 'UI_Plate_300101.png')).resize((1420, 230))
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
    text_im.text((847, 300), f'底分：{ra} + 段位分：{add_ra}' if not b50 else 'New Rating System', font=_siyuan, fill= (0, 0, 0, 255),anchor = 'mm')

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
