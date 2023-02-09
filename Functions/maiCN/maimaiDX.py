import json,os,pprint
from rapidfuzz import fuzz, utils
from ..sqlHelper import *

maiJson = open("maidata.json").read()
maiData = json.loads(maiJson)

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
            if fuzz.QRatio(keyword,song['title']) >= 95:
                results.append(song)
                break

    if len(results) == 0:
        return ['请尝试优化搜索词。']
    reply_txt = f"共找到以下{len(results)}个结果:\n"
    for s in results:
        output(s)
        isDX = '[DX]'

        title = s['title']
        artist = s['artist']
        category = s['category']
        try:
            bas_lvl = s['dx_lev_bas']
            adv_lvl = s['dx_lev_adv']
            exp_lvl = s['dx_lev_exp']
            mas_lvl = s['dx_lev_mas']
        except KeyError as e:
            # is STD song
            bas_lvl = s['lev_bas']
            adv_lvl = s['lev_adv']
            exp_lvl = s['lev_exp']
            mas_lvl = s['lev_mas']
            isDX = '[STD]'
        version = s['version']
        reply_txt += f"{isDX}{artist} - {title}\n版本:{version} 分区:{category}\nBAS{bas_lvl} | ADV{adv_lvl} | EXP {exp_lvl} | MAS {mas_lvl}\n"
    return [reply_txt]

