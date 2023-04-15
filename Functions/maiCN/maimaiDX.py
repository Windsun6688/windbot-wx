import json,os,requests,base64
from rapidfuzz import fuzz, utils
from PIL import Image, ImageDraw, ImageFont
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

def mai_api_get(gamertag: str):
    get_type = ['player']
    url = f'https://www.diving-fish.com/api/maimaidxprober/query/{get_type[0]}'
    j = {
        'username': gamertag
    }
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
    chart_const = playrecord['ds']
    chart_type = playrecord['type']
    acc = playrecord['achievements']
    racc = playrecord['dxScore']
    rate = playrecord['rate'].upper().replace('P','+')
    rating = playrecord['ra']
    fc = playrecord['fc']
    fs = playrecord['fs']
    fc_txt = ''
    fs_txt = ''
    if fc:
        fc_txt = full_combo_rank[combo_rank.index(fc)]
    if fs:
        fs_txt = full_sync_rank[sync_rank.index(fs)]

    return f"\n[{chart_type}]{title} | {level} {chart_const}\n{acc}({rate}) Rating:{rating} DXScore:{racc}\n{fc_txt}{fs_txt}\n"

def mai_music_get(local: bool = False):
    if local:
        with open(os.path.join(static, 'music_data.json'), 'r', encoding='utf-8') as f:
            songs = json.loads(f.read())
        with open(os.path.join(static, 'chart_stats.json'), 'r', encoding='utf-8') as f:
            stats = json.loads(f.read())
        return songs,stats

    # SONG DETAILS
    resp = requests.get('https://www.diving-fish.com/api/maimaidxprober/music_data')
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
            remas_txt = f' | ReMas{ds[4]}'

        reply_txt += f"\n[{is_DX}]{new_txt} {artist} - {title}\n-版本:{version} | 分区:{category} | BPM:{bpm}\n--Bas{ds[0]} | Adv{ds[1]} | Exp{ds[2]} | Mas{ds[3]}{remas_txt}---Song ID: {sid}"
    return [reply_txt]

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

#### Best Image Drawing ####

def draw_text(img_pil: Image.Image, text: str, offset_x: float):
    draw = ImageDraw.Draw(img_pil)
    font = ImageFont.truetype(fontpath, 48)
    width, height = draw.textsize(text, font)
    x = 5
    if width > 390:
        font = ImageFont.truetype(fontpath, int(390 * 48 / width))
        width, height = draw.textsize(text, font)
    else:
        x = int((400 - width) / 2)
    draw.rectangle((x + offset_x - 2, 360, x + 2 + width + offset_x, 360 + height * 1.2), fill=(0, 0, 0, 255))
    draw.text((x + offset_x, 360), text, font=font, fill=(255, 255, 255, 255))

def text_to_image(text: str) -> Image.Image:
    font = ImageFont.truetype(fontpath, 24)
    padding = 10
    margin = 4
    text_list = text.split('\n')
    max_width = 0
    for text in text_list:
        w, h = font.getsize(text)
        max_width = max(max_width, w)
    wa = max_width + padding * 2
    ha = h * len(text_list) + margin * (len(text_list) - 1) + padding * 2
    i = Image.new('RGB', (wa, ha), color=(255, 255, 255))
    draw = ImageDraw.Draw(i)
    for j in range(len(text_list)):
        text = text_list[j]
        draw.text((padding, padding + j * (margin + h)), text, font=font, fill=(0, 0, 0))
    return i

def image_to_base64(img: Image.Image, format='PNG') -> str:
    output_buffer = BytesIO()
    img.save(output_buffer, format)
    byte_data = output_buffer.getvalue()
    base64_str = base64.b64encode(byte_data).decode()
    return 'base64://' + base64_str

def draw_best_image():
    pass
