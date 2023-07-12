import json,os,time
import requests as req
from ..sqlHelper import *

headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}
url_getmD = 'https://musics.pjsekai.moe/musicDifficulties.json'
url_getmc = 'https://musics.pjsekai.moe/musics.json'
url_e_data = 'https://database.pjsekai.moe/events.json'
resource = os.path.join(resource_root,'PJSK')

def data_req(url:str):
    temp_res = req.get(url, headers = headers)
    re = json.loads(temp_res.text)
    return re

def get_usr_data(userid:str):
    url = f'https://api.unipjsk.com/api/user/{userid}/profile'
    return data_req(url)

def getCnt(data:dict,diff_idx:int,tag = 'all'):
    cnt_list = data['userMusicDifficultyClearCount'][diff_idx]
    if tag == 'all':
        return cnt_list['allPerfect'],cnt_list['fullCombo'],cnt_list['liveClear']
    else:
        return cnt_list[tag]

def pjskpf(datalist,callerid,roomid = None):
    userid = sql_fetch(cur,'Users',['pjskID'],f"wxid = '{callerid}'")[0][0]
    if userid == -1:
        return ['您未绑定Project Sekai ID。请使用Bind指令绑定。']

    usr_data = get_usr_data(userid)
    if usr_data == {}:
        return [f'API未返回任何数据。这可能是网络原因，也可能是绑定错误。\n您现在绑定的ID: {userid}']
    reply_txt = ""
    name = usr_data['user']['name']
    rank = usr_data['user']['rank']
    bio = usr_data['userProfile']['word']
    twi = usr_data['userProfile']['twitterId']
    reply_txt += f"{name} - Rank {rank}\n"
    if bio:
        reply_txt += f"「{bio}」\n"
    if twi:
        reply_txt += f"Twi@{twi}\n"

    difficulty = {'Easy':0,'Normal':1,'Hard':2,'Expert':3,'Master':4}
    for tag in difficulty:
        ap_cnt,fc_cnt,clr_cnt = getCnt(usr_data,difficulty[tag],'all')
        reply_txt += f"{tag} | Clear:{clr_cnt} | FC:{fc_cnt} | AP:{ap_cnt}\n"
    reply_txt += f'ID: {userid}'
    return [reply_txt]

def amIkaiden(datalist,callerid,roomid = None):
    userid = sql_fetch(cur,'Users',['pjskID'],f"wxid = '{callerid}'")[0][0]
    if userid == -1:
        return ['您未绑定Project Sekai ID。请使用Bind指令绑定。']

    usr_data = get_usr_data(userid)
    if usr_data == {}:
        return [f'API未返回任何数据。这可能是网络原因，也可能是绑定错误。\n您现在绑定的ID: {userid}']
    fc_cnt = getCnt(usr_data,4,'fullCombo')
    ap_cnt = getCnt(usr_data,4,'allPerfect')
    if fc_cnt < 30:
        return [f'您距离皆传还有{30-fc_cnt}张mas谱需要达成Full Combo,加油哦']
    elif fc_cnt >= 30 and ap_cnt < 30:
        return [f'您已经达成皆传!!\n距离真皆传还有{30-ap_cnt}张mas谱需要All Perfect,加油哦']
    else:
        return [f'我去，是AP了{ap_cnt}首mas的真皆爷爷']

def pjsk_alias_search(datalist,callerid,roomid = None):
    keyword = ''
    for word in datalist:
        keyword += (word)
    keyword = keyword.strip()
    url = f'https://api.unipjsk.com/getsongid/{keyword}'
    result = data_req(url)
    if result['status'] == 'false':
        return ['没有匹配的歌曲。']
    reply_txt = f"该别名可能指向以下歌曲:(匹配度{int(result['match']*100)}%)\n"
    cn_title = f"({result['translate']})" if result['translate'] else ''
    reply_txt += f"-{result['title']}{cn_title}\n--ID: {result['musicId']}"
    return [reply_txt]

def pjsk_event_get(local: bool = False):
    if local:
        with open(os.path.join(resource, 'event_data.json'), 'r', encoding='utf-8') as f:
            data = json.loads(f.read())
    else:
        resp = req.get(url_e_data)
        if resp.status_code != 200:
            output('pjsk活动数据获取失败,切换至本地暂存文件','WARNING',background = 'WHITE')
            with open(os.path.join(resource, 'event_data.json'), 'r', encoding='utf-8') as f:
                data = json.loads(f.read())
        else:
            data = resp.json()
            with open(os.path.join(resource, 'event_data.json'), 'w', encoding='utf-8') as f:
                f.write(json.dumps(data, ensure_ascii=False, indent=4))
    return data

def pjsk_music_get(local: bool = False):
    if local:
        with open(os.path.join(resource, 'music_data.json'), 'r', encoding='utf-8') as f:
            data = json.loads(f.read())
    else:
        resp = req.get(url_getmc)
        if resp.status_code != 200:
            output('pjsk歌曲数据获取失败,切换至本地暂存文件','WARNING',background = 'WHITE')
            with open(os.path.join(resource, 'music_data.json'), 'r', encoding='utf-8') as f:
                data = json.loads(f.read())
        else:
            data = resp.json()
            with open(os.path.join(resource, 'music_data.json'), 'w', encoding='utf-8') as f:
                f.write(json.dumps(data, ensure_ascii=False, indent=4))
    return data

def load_event_info(_data):
    i = -2
    close_time = int(_data[i]["closedAt"]/1000) 
    if time.time() > close_time:
        i = -1
    return _data[i]['id'], _data[i]['name'], time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(_data[i]["aggregateAt"]/1000))),  _data[i]['eventType']

def pjsk_curr_event(datalist,callerid,roomid = None):
    pjsk_event_get()
    return ['']

def pjsk_data_update(datalist,callerid,roomid = None):
