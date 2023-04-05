import json,os,pprint,requests
from rapidfuzz import fuzz, utils
from ..sqlHelper import *

maiJson = open("maidata.json",encoding='UTF-8').read()
maiData = json.loads(maiJson)

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

def maisearch(datalist,callerid,roomid = None):
    if datalist[0].lower() == 'f':
        keyword = ''
        for word in datalist[1:]:
            keyword += (word + ' ')
        keyword = keyword[:-1]
        results = []
        for song in maiData:
            if fuzz.QRatio(keyword,song['title']) >= 65:
                results.append(song)
    else:
        keyword = ''
        for word in datalist[0:]:
            keyword += (word + ' ')
        keyword = keyword[:-1]
        results = []
        for song in maiData:
            if fuzz.QRatio(keyword,song['title']) >= 90:
                results.append(song)
                break

    if len(results) == 0:
        return ['没有搜寻到结果,或搜索模式关键词错误。']
    elif len(results) > 5:
        return ['请尝试优化搜索词。']

    reply_txt = f"共找到以下{len(results)}个结果:\n"
    for s in results:
        output(s,background = 'MINT')
        isDX = '[DX]'
        title = s['title']
        artist = s['artist']
        category = s['category']
        remas_txt = ''

        try:
            bas_lvl = s['dx_lev_bas']
            adv_lvl = s['dx_lev_adv']
            exp_lvl = s['dx_lev_exp']
            mas_lvl = s['dx_lev_mas']
            if len(s) > 9:
                remas_txt = f" | ReMas{s['dx_lev_remas']}"
        except KeyError as e:
            # is STD song
            isDX = '[STD]'
            bas_lvl = s['lev_bas']
            adv_lvl = s['lev_adv']
            exp_lvl = s['lev_exp']
            mas_lvl = s['lev_mas']
            if len(s) > 9:
                remas_txt = f" | ReMas{s['lev_remas']}"

        version = s['version']
        reply_txt += f"{isDX}{artist} - {title}\n-版本:{version} | 分区:{category}\n--Bas{bas_lvl} | Adv{adv_lvl} | Exp{exp_lvl} | Mas{mas_lvl}{remas_txt}\n"

    return [reply_txt]

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
    fc = playrecord['fc']
    fs = playrecord['fs']
    fc_txt = ''
    fs_txt = ''
    if fc:
        fc_txt = full_combo_rank[combo_rank.index(fc)]
    if fs:
        fs_txt = full_sync_rank[sync_rank.index(fs)]

    return f"\n[{chart_type}]{title} | {level} {chart_const}\n{acc}({rate}) DXScore: {racc}\n{fc_txt}{fs_txt}\n"