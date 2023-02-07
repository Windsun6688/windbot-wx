import json,os,time
import requests as req
from ..sqlHelper import *

headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}
url_getmD = 'https://musics.pjsekai.moe/musicDifficulties.json'
url_getmc = 'https://musics.pjsekai.moe/musics.json'
url_e_data = 'https://database.pjsekai.moe/events.json'

def data_req(url):
    temp_res = req.get(url, headers = headers)
    re = json.loads(temp_res.text)
    return re

def fetchUsrdata(userid):
    url = f'https://api.pjsekai.moe/api/user/{userid}/profile'
    # output(url)
    getdata = req.get(url,headers = headers)
    return json.loads(getdata.text)

def countFlg(_list,TAG,difficulty,data1):
    a_count = 0
    for result in data1['userMusicResults']:
            if result['musicDifficulty'] == difficulty:
                if result[TAG] == True and result['musicId'] not in _list:
                    a_count = a_count + 1
                    _list.append(result['musicId'])
    return _list,a_count

def countClear(_list,difficulty,data1):
    a_count = 0
    for result in data1['userMusicResults']:
            if result['musicDifficulty'] == difficulty:
                if result['fullComboFlg'] == True and result['musicId'] not in _list:
                    a_count = a_count + 1
                    _list.append(result['musicId'])
                if result['playResult'] == 'clear' and result['musicId'] not in _list:
                    a_count = a_count + 1
                    _list.append(result['musicId'])
    for a in _list:
        if _list.count(a) >= 2:
            a_count = account - _list.count(a) + 1
    return _list,a_count

def pjskpf(datalist,callerid,roomid = None):
    userid = sql_fetch(cur,'Users',['pjskID'],f"wxid = '{callerid}'")[0][0]
    if userid == -1:
        return ['您未绑定Project Sekai ID。请使用Bind指令绑定。']

    data1 = fetchUsrdata(userid)
    if data1 == {}:
        return [f'API未返回任何数据。这可能是网络原因，也可能是绑定错误。\n您现在绑定的ID: {userid}']
    reply_txt = ""
    name = data1['user']['userGamedata']['name']
    rank = data1['user']['userGamedata']['rank']
    word = data1['userProfile']['word']
    if word:
        reply_txt += f"{name} - Rank {rank}\n「{word}」\n"
    else:
        reply_txt += f"{name} - Rank {rank}\n"

    dict_backup = []
    difficulty = ['easy','normal','hard','expert','master']
    for tag in difficulty:
        count = 0
        fc_count = 0
        ap_count = 0
        clr_list = []
        fc_list = []
        ap_list = []
        fc_list,fc_count = countFlg(fc_list,'fullComboFlg',tag,data1)
        ap_list,ap_count = countFlg(ap_list,'fullPerfectFlg',tag,data1)
        clr_list,count = countClear(clr_list,tag,data1)
        # output(fc_list)
        reply_txt += f"{tag.capitalize()}\nClear: {count} | FC: {fc_count} | AP: {ap_count}\n"
        dict_backup.append({tag:{'fc':fc_count,'ap':ap_count,'clear':count}})
    return [reply_txt]

def amIkaiden(datalist,callerid,roomid = None):
    userid = sql_fetch(cur,'Users',['pjskID'],f"wxid = '{callerid}'")[0][0]
    if userid == -1:
        return ['您未绑定Project Sekai ID。请使用Bind指令绑定。']

    data1 = fetchUsrdata(userid)
    if data1 == {}:
        return [f'API未返回任何数据。这可能是网络原因，也可能是绑定错误。\n您现在绑定的ID: {userid}']
    _,fc_count = countFlg([],'fullComboFlg','master',data1)
    _,ap_count = countFlg([],'fullPerfectFlg','master',data1)
    if fc_count < 30:
        return [f'您距离皆传还有{30-fc_count}张mas谱需要达成Full Combo,加油哦']
    elif fc_count >= 30 and ap_count < 30:
        return [f'您已经达成皆传!!\n距离真皆传还有{30-ap_count}张mas谱需要All Perfect,加油哦']
    else:
        return [f'我去，是AP了{ap_count}首mas的真皆爷爷']

def load_event_info(_data):
    i = -2
    close_time = int(_data[i]["closedAt"]/1000) 
    if time.time() > close_time: #说明倒数第二个活动已关闭，按最新的算
        i = -1
    return _data[i]['id'], _data[i]['name'], time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(_data[i]["aggregateAt"]/1000))),  _data[i]['eventType']
