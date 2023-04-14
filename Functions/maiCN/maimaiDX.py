import json,os,requests
from rapidfuzz import fuzz, utils
from ..sqlHelper import *

static = os.path.join(os.path.dirname(__file__),'resource')

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

def mai_api_get(gamertag):
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

def mai_music_get():
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

mai_songs,mai_charts = mai_music_get()

def maisearch(datalist,callerid,roomid = None):
    results = []
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
        for word in datalist[0:]:
            keyword += (word + ' ')
        keyword = keyword[:-1]
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

        reply_txt += f"\n[{is_DX}]{new_txt} {artist} - {title}\n-版本:{version} | 分区:{category} | BPM:{bpm}\n--Bas{ds[0]} | Adv{ds[1]} | Exp{ds[2]} | Mas{ds[3]}{remas_txt}"

    return [reply_txt]

