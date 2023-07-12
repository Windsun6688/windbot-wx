# -*- coding:utf-8 -*-

import websocket,time,json,requests,os,rel,sqlite3,brotli
import random,string,traceback
from datetime import datetime
from pytz import timezone
from threading import Thread
from bs4 import BeautifulSoup
from colorama import init
from Functions.gosenchoyen.generator import genImage
from Functions.arcaea.arcaea import *
from Functions.pjsk.pjsk import *
from Functions.maiCN.maimaiDX import *

websocket._logging._logger.level = -99
init(autoreset = True)

ip='127.0.0.1'

port=5555

SERVER=f'ws://{ip}:{port}'
HEART_BEAT=5005
RECV_TXT_MSG=1
RECV_TXT_CITE_MSG=49
RECV_PIC_MSG=3
USER_LIST=5000
GET_USER_LIST_SUCCSESS=5001
GET_USER_LIST_FAIL=5002
TXT_MSG=555
PIC_MSG=500
AT_MSG=550
CHATROOM_MEMBER=5010
CHATROOM_MEMBER_NICK=5020
PERSONAL_INFO=6500
DEBUG_SWITCH=6000
PERSONAL_DETAIL=6550
DESTROY_ALL=9999
STATUS_MSG=10000
ATTATCH_FILE = 5003
# 'type':49 带引用的消息

ANIME_QUERY = """
query ($id: Int, $idMal:Int, $search: String) {
	Media (id: $id, idMal: $idMal, search: $search, type: ANIME) {
		id
		idMal
		title {
			romaji
			english
			native
		}
		format
		status
		episodes
		duration
		countryOfOrigin
		source (version: 2)
		trailer {
			id
			site
		}
		genres
		tags {
			name
		}
		averageScore
		relations {
			edges {
				node {
					title {
						romaji
						english
					}
					id
					type
				}
				relationType
			}
		}
		nextAiringEpisode {
			timeUntilAiring
			episode
		}
		isAdult
		isFavourite
		mediaListEntry {
			status
			score
			id
		}
		siteUrl
	}
}
"""

'''Initialize Autohibernate'''
undisturbed_hb = 0

'''Admins'''
OP_list = ['wxid_xd4gc9mu3stx12']

'''Local Resource Path'''
project_path = os.path.join(os.path.dirname(__file__))
resource_path = os.path.join(os.path.dirname(__file__),'Resources')

'''Recent Logs List'''
latest_logs = []

############################# MULTITHREADING ################################
class ThreadWithReturnValue(Thread):
	def __init__(self, group=None, target=None, name=None,
				 args=(), kwargs={}, Verbose=None):
		Thread.__init__(self, group, target, name, args, kwargs)
		self._return = None

	def run(self):
		if self._target is not None:
			self._return = self._target(*self._args,**self._kwargs)
			return self._return

	def join(self, *args):
		Thread.join(self, *args)
		return self._return

################################# OUTPUT&SQL ################################
def getid():
	return time.strftime("%Y%m%d%H%M%S")

def output(msg,logtype = 'SYSTEM',mode = 'DEFAULT',background = 'DEFAULT'):
	# print('got output')
	LogColor = {
		'SYSTEM': '034',
		'ERROR': '037',
		'GROUPCHAT': '036',
		'DM' : '033',
		'HEART_BEAT': '035',
		'PAT': '037',
		'SEND': '032',
		'CALL' : '031',
		'WARNING': '031',
		'CREATE_LINK':'032',
		'STOP_LINK':'031'
	}
	LogMode = {
		'DEFAULT': '0',
		'HIGHLIGHT': '1',
		'UNDERLINE': '4'
	}
	LogBG = {
		'DEFAULT': '',
		'RED' : ';41',
		'YELLOW' : ';43',
		'BLUE' : ';44',
		'WHITE' : ';47',
		'GREEN' : ';42',
		'MINT' : ';46'
	}
	color = LogColor.get(logtype)
	mode = LogMode.get(mode)
	bg = LogBG.get(background)


	now=time.strftime("%Y-%m-%d %X")
	print(f"[{now} \033[{mode};{color}{bg}m{logtype}\033[0m] {msg}")

	# Write Error Logs on to Local File
	if logtype == 'ERROR':
		error_log_file = open('ErrorLog.txt','a')
		error_log_file.write(f"[{now} {logtype}] {msg}\n")
		error_log_file.close()

	# Store Log into latest_logs list
	if logtype != 'HEART_BEAT':
		if len(latest_logs) == 20:
			latest_logs.pop(0)
		latest_logs.append(f"[{now} {logtype}] {msg}")

	# print("["+f"{color}[1;35m{LogType}{color}[0m"+"]"+' Success')
	# print(f'[{now}]:{msg}')

def sql_insert(db,dbcur,table,rows,values):
	'''
	Pre-Process
	'''
	# table = f'r{table[:-9]}'
	test_row = rows[-1]
	test_value = values[-1]
	rows = str(rows)[1:-1].replace('\'','')
	values = str(values)[1:-1]
	'''
	Check if line exsists
	'''
	if isinstance(test_value,str):
		check_txt = f"SELECT 1 FROM {table} WHERE {test_row}='{test_value}'"
	else:
		check_txt = f"SELECT 1 FROM {table} WHERE {test_row}={test_value}"
	# output(check_txt)
	dbcur.execute(check_txt)
	result = dbcur.fetchone()
	# output(result,mode = 'HIGHLIGHT')
	'''
	Value Exists or not
	'''
	if result:
		# output('Skipping This Insert Because Column Exists','WARNING')
		return
	else:
		insert_txt = f"INSERT INTO {table}({rows}) VALUES({values})"
		# print(insert_txt)
		db.execute(insert_txt)
		db.commit()

def sql_update(db,table,col,value,condition = None):
	# table = f'r{table[:-9]}'
	# col = str(col).replace('\'','')

	if isinstance(value,str):
		if condition:
			update_txt = f"UPDATE {table} SET {col} = '{value}' WHERE {condition}"
		else:
			update_txt = f"UPDATE {table} SET {col} = '{value}'"
	else:
		if condition:
			update_txt = f"UPDATE {table} SET {col} = {value} WHERE {condition}"
		else:
			update_txt = f"UPDATE {table} SET {col} = {value}"

	# output(update_txt,mode = 'HIGHLIGHT')
	db.execute(update_txt)
	db.commit()

def sql_fetch(dbcur,table,cols = ['*'],condition = None):
	cols = str(cols)[1:-1].replace('\'','')
	# cols = str(cols)[1:-1]

	if condition:
		fetch_txt = f"SELECT {cols} FROM {table} WHERE {condition}"
	else:
		fetch_txt = f"SELECT {cols} FROM {table}"
	# output(fetch_txt,mode = 'HIGHLIGHT')
	dbcur.execute(fetch_txt)
	result = dbcur.fetchall()
	return [i for i in result]

def sql_match(db,dbcur,table,cols = ['*'],conditionCol = None,keyword = None):
	if not keyword:
		return ['-1']
	elif not conditionCol:
		return ['-1']

	source = db
	db = sqlite3.connect(":memory:")
	db.backup(source)
	dbcur = db.cursor()

	dbcur.execute('DROP TABLE IF EXISTS fuzzysearch')

	fetchcols = cols
	fetchcols.append(conditionCol)
	origin_data = sql_fetch(dbcur,table,fetchcols)
	# output(origin_data)

	cols = str(cols)[1:-1].replace('\'','')
	fetchcols_str = str(fetchcols)[1:-1].replace('\'','')

	dbcur.execute(f'create virtual table fuzzysearch using fts5({fetchcols_str}, tokenize="porter unicode61");')

	for row in origin_data:
		# output(str(row)[1:-1])
		dbcur.execute(f'insert into fuzzysearch ({fetchcols_str}) values ({str(row)[1:-1]});')

	db.commit()

	if isinstance(keyword,str):
		match_txt = f"SELECT {cols} FROM fuzzysearch WHERE {conditionCol} MATCH '{keyword}*'"
	else:
		match_txt = f"SELECT {cols} FROM fuzzysearch WHERE {conditionCol} MATCH {keyword}*"

	# output(match_txt)
	result = dbcur.execute(match_txt).fetchall()
	# output(result)

	dbcur.execute('DROP TABLE IF EXISTS fuzzysearch')
	db.commit()

	return [i for i in result]

def sql_destroy(db,table):
	destroy_txt = f"DROP TABLE {table}"
	db.execute(destroy_txt)
	db.commit()

def sql_delete(db,table,condition = None):
	if not condition:
		output('Did not specify which delete condition.','WARNING',background = "WHITE")
		return ['-1']

	delete_txt = f"DELETE FROM {table} WHERE {condition}"
	db.execute(delete_txt)
	db.commit()

################################### HTTP ####################################
def send(uri,data):
	base_data={
		'id':getid(),
		'type':'null',
		'roomid':'null',
		'wxid':'null',
		'content':'null',
		'nickname':'null',
		'ext':'null',
	}
	base_data.update(data)
	url=f'http://{ip}:{port}/{uri}'
	res=requests.post(url,json={'para':base_data},timeout=5)
	return res.json()

def get_member_nick(roomid = 'null',wxid = None):
	# 获取指定群的成员的昵称 或 微信好友的昵称
	uri='api/getmembernick'
	data={
		'type':CHATROOM_MEMBER_NICK,
		'wxid':wxid,
		'roomid':roomid or 'null'
	}
	respJson=send(uri,data)
	return json.loads(respJson['content'])['nick']

################################# websocket #################################
def debug_switch():
	qs={
		'id':getid(),
		'type':DEBUG_SWITCH,
		'content':'off',
		'wxid':'ROOT',
	}
	return json.dumps(qs)

def get_chat_nick_p(wxid,roomid):
	qs={
		'id':getid(),
		'type':CHATROOM_MEMBER_NICK,
		'wxid': wxid,
		'roomid' : f'{roomid}@chatroom',
		'content' : 'null',
		'nickname':'null',
		'ext':'null'
	}
	return json.dumps(qs)

def handle_nick(j):
	data=eval(j['content'])
	nickname = data['nick']
	wxid = data['wxid']
	roomid = data['roomid']

	sql_update(conn,f'r{roomid[:-9]}','groupUsrName',nickname,f"wxid = '{wxid}'")
	# output(f'nickname:{nickname}')

def get_chatroom_memberlist(roomid = 'null'):
	qs={
		'id':getid(),
		'type':CHATROOM_MEMBER,
		'roomid': roomid,
		'wxid':'null',
		'content':'op:list member',
		'nickname':'null',
		'ext':'null'
	}
	# 'content':'op:list member',
	return json.dumps(qs)

def handle_memberlist(j):
	data=j['content']
	for d in data:
		roomid = d['room_id']
		room_num = roomid[:-9]
		# output(f'roomid:{roomid}')
		members = d['member']

		sql_initialize_group(f'r{room_num}')

		for m in members:
			sql_insert(conn,cur,f'r{room_num}',['wxid'],[m])
			sql_insert(conn,cur,'Users',['wxid'],[m])
			ws.send(get_chat_nick_p(m,room_num))

def get_personal_detail(wxid):
	qs={
		'id':getid(),
		'type':PERSONAL_DETAIL,
		'content':'op:personal detail',
		'wxid': wxid,
		'roomid':'null',
		'content':'null',
		'nickname':'null',
		'ext':'null',
	}
	return json.dumps(qs)

def handle_personal_detail(j):
	output(j)

def get_personal_info():
	qs={
		'id':getid(),
		'type':PERSONAL_INFO,
		'content':'null',
		'wxid': wxid,
		'roomid':'null',
		'content':'null',
		'nickname':'null',
		'ext':'null',
	}
	return json.dumps(qs)

def handle_personal_info(j):
	output(j)

def send_wxuser_list():
	'''
	获取微信通讯录用户名字和wxid
	'''
	qs={
		'id':getid(),
		'type':USER_LIST,
		'roomid':'null',
		'wxid':'null',
		'content':'null',
		'nickname':'null',
		'ext':'null',
	}
	return json.dumps(qs)

def handle_wxuser_list(j):
	i=0
	for item in j['content']:
		i+=1
		output(f"{i} {item['wxid']} {item['name']}")
		if item['wxid'][-8:] == 'chatroom':
			res = sql_fetch(cur,'Groupchats',['*'],f"roomid = '{item['wxid'][:-9]}'")
			if len(res) == 0:
				sql_insert(conn,cur,'Groupchats',['roomid','groupname'],[item['wxid'][:-9],item['name']])
			sql_update(conn,'Groupchats','groupname',item['name'],f"roomid = '{item['wxid'][:-9]}'")
		else:
			sql_insert(conn,cur,'Users',['wxid','wxcode','realUsrName'],[item['wxid'],item['wxcode'],item['name']])

	ws.send(get_chatroom_memberlist(item['wxid']))

################################# INITIALIZE ###############################
def heartbeat(msgJson):
	global undisturbed_hb
	undisturbed_hb += 1
	if undisturbed_hb < 5:
		output('Success','HEART_BEAT','HIGHLIGHT')
	elif undisturbed_hb == 5:
		output('Undisturbed in 5 min. Hiding heartbeat logs. zZZ',logtype = 'HEART_BEAT',mode = 'HIGHLIGHT')

	# print("["+f"\033[1;35m{LogType}\033[0m"+"] "+' Success')

def on_open(ws):
	#初始化
	ws.send(send_wxuser_list())
	for wxid in OP_list:
		sql_update(conn,'Users','powerLevel',3,f"wxid = '{wxid}'")

	now=time.strftime("%Y-%m-%d %X")
	ws.send(send_msg(f'启动完成\n{now}',OP_list[0]))
	# ws.send(get_chatroom_memberlist())

def on_error(ws,error):
	output(f'on_error:{error}','ERROR','HIGHLIGHT','RED')

def on_close(ws,signal,status):
	output("Server Closed",'WARNING','HIGHLIGHT','WHITE')

def sql_initialize_group(roomid):
	initialize_group = f'''CREATE TABLE IF NOT EXISTS {roomid}
			(wxid TEXT,
			groupUsrName TEXT);'''
	# print(initialize_users)
	conn.execute(initialize_group)
	conn.commit()

def sql_initialize_link(linkroomid,allselect):
	initialize_link = f'''CREATE TABLE IF NOT EXISTS {linkroomid}
			(wxid TEXT,
			arcID NUMBER,
			allselect NUMBER NOT NULL DEFAULT {allselect},
			songselect NUMBER NOT NULL DEFAULT 0,
			song TEXT NOT NULL DEFAULT -1,
			songStarted NUMBER NOT NULL DEFAULT -1,
			isOwner NUMBER NOT NULL DEFAULT 0);'''
	# output(initialize_link)
	conn.execute(initialize_link)
	conn.commit()
	output(f'Created Link Play Room of ID {linkroomid}','CREATE_LINK',background = 'WHITE')

def sql_initialize_users():
	initialize_users = f'''CREATE TABLE IF NOT EXISTS Users
			(wxid TEXT,
			wxcode TEXT,
			realUsrName TEXT,
			patTimes NUMBER NOT NULL DEFAULT 0,
			arcID NUMBER NOT NULL DEFAULT -1,
			qqID NUMBER NOT NULL DEFAULT -1,
			pjskID NUMBER NOT NULL DEFAULT -1,
			maiID TEXT NOT NULL DEFAULT -1,
			powerLevel NUMBER NULL DEFAULT 0,
			isInLink TEXT NOT NULL DEFAULT -1,
			banned NUMBER NOT NULL DEFAULT 0);'''
	conn.execute(initialize_users)
	conn.commit()

def sql_initialize_groupnames():
	initialize_gn = f'''CREATE TABLE IF NOT EXISTS Groupchats
			(roomid TEXT,
			groupname TEXT
			announce BOOL NOT NULL DEFAULT 0);'''
	conn.execute(initialize_gn)
	conn.commit()

################################# SEND MSG #################################
def destroy_all():
	qs={
		'id':getid(),
		'type':DESTROY_ALL,
		'content':'none',
		'wxid':'node',
	}
	return json.dumps(qs)

def send_msg(msg,wxid='null'):
	if msg.endswith('.png'):
		msg_type=PIC_MSG
	else:
		msg_type=TXT_MSG

	qs={
		'id':getid(),
		'type':msg_type,
		'wxid':wxid,
		'roomid':'null',
		'content':msg,
		'nickname':'null',
		'ext':'null'
	}

	output(f'{msg} -> {wxid}','SEND')
	return json.dumps(qs)

def send_attatch(filepath,wxid = 'null'):
	qs={
		'id':getid(),
		'type':ATTATCH_FILE,
		'wxid':wxid,
		'roomid':'null',
		'content':filepath,
		'nickname':'null',
		'ext':'null'
	}
	output(f'File @ {filepath} -> {wxid}','SEND')
	return json.dumps(qs)

def send_pic(filepath,wxid = 'null'):
	qs={
		'id':getid(),
		'type':PIC_MSG,
		'wxid':wxid,
		'roomid':'null',
		'content':filepath,
		'nickname':'null',
		'ext':'null'
	}
	output(f"Media @ {filepath} -> {wxid}",'SEND')
	return json.dumps(qs)

############################## HANDLES #####################################
def handle_status_msg(msgJson):
	# output(f'收到消息:{msgJson}')
	if '拍了拍我' in msgJson['content']['content']:
		# output(msgJson

		output(f"{msgJson['content']['content']}",'PAT',background = 'MINT')

		wxid = msgJson['content']['id1']

		if wxid[-8:] == 'chatroom':
			roomid = wxid
			username = msgJson['content']['content'].split('"')[1]
			wxid = sql_fetch(cur,f'r{roomid[:-9]}',['wxid'],f"groupUsrName = '{username}'")[0][0]
			# output(f'{roomid} {username} {wxid}')

		new_pat_times = sql_fetch(cur,'Users',['patTimes'],f"wxid = '{wxid}'")[0][0]+1
		# output(new_pat_times)

		sql_update(conn,'Users','patTimes',new_pat_times,f"wxid = '{wxid}'")

		ws.send(send_msg(f'第{new_pat_times}次了！',msgJson['content']['id1']))

	if '邀请' in msgJson['content']['content']:
		ws.send(send_wxuser_list())
		roomid=msgJson['content']['id1']
		# nickname=msgJson['content']['content'].split('"')[-2]
		ws.send(send_msg(f'欢迎进群',wxid=roomid))

def handle_sent_msg(msgJson):
	output(msgJson['content'],mode = 'HIGHLIGHT')

def handle_cite_msg(msgJson):
	# 处理带引用的文字消息和转发链接
	msgXml=msgJson['content']['content'].replace('&amp;','&').replace('&lt;','<').replace('&gt;','>')
	soup=BeautifulSoup(msgXml,features="xml")
	if soup.appname.string == '哔哩哔哩':
		output(f'Video from BiliBili: {soup.title.string} URL: {soup.url.string}')
		return
	# print(soup.prettify())
	refmsg = [child for child in soup.refermsg.strings if child != '\n']
	# output(refmsg)

	msgJson={
		'content':soup.select_one('title').text,
		'refcontent': refmsg[5],
		'refnick': refmsg[4],
		'id':msgJson['id'],
		'id1':msgJson['content']['id2'],
		'id2': refmsg[2],
		'id3':'',
		'srvid':msgJson['srvid'],
		'time':msgJson['time'],
		'type':msgJson['type'],
		'wxid':msgJson['content']['id1']
	}
	handle_recv_msg(msgJson)

def handle_at_msg(msgJson):
	output(msgJson)

def handle_recv_pic(msgJson):
	msgJson = msgJson['content']

	if msgJson['id2']:
		roomid=msgJson['id1'] #群id
		senderid=msgJson['id2'] #个人id

		nickname = sql_fetch(cur,f'r{roomid[:-9]}',['groupUsrName'],f"wxid = '{senderid}'")[0][0]
		roomname = sql_fetch(cur,'Groupchats',['groupname'],f'roomid = {roomid[:-9]}')[0][0]
		'''
		Terminal Log
		'''
		output(f'{roomname}-{nickname}: [IMAGE]','GROUPCHAT')
	else:
		senderid=msgJson['id1'] #个人id
		destination = senderid

		nickname = sql_fetch(cur,'Users',['realUsrName'],f"wxid = '{senderid}'")[0][0]
		'''
		Terminal Log
		'''
		output(f'{nickname}: [IMAGE]','DM')

def handle_recv_call(keyword,callerid,destination,nickname,roomname = None):
	caller_isbanned = sql_fetch(cur,'Users',['banned'],f"wxid = '{callerid}'")
	if caller_isbanned[0][0] == 1:
		return
	call_data = stringQ2B(keyword).split(' ')
	if len(call_data) == 0:
		ws.send('请指明需要调用的功能。')
		return
	#handle mobile @
	if len(call_data) > 1 and call_data[0] == '':
		call_data = call_data[1:]

	functions = {
		'bind': bindID,
		'patstat': patstat,
		'gosen': gen_5000,
		'ban': ban,
		'unban':unban,
		'refresh': refresh,
		'setadmin':setadmin,
		'punch':punch,
		'setsuper': setsuper,
		'announce': announce,
		'annswitch': switch_announce,
		'annview': view_announce,
		'logs': fetch_logs,

		'ainfo': arc_music_search,
		'randarc': arc_random,
		'acinfo': arc_chart_info,
		'alookup': arc_lookup,
		'awhat': arc_alias_search,
		'grablevel': grablevel,
		'constable': constable,
		'addalias': addalias,

		'minfo': mai_music_search,
		'mwhat':mai_alias_search,
		'mupdate': mai_update,

		'pjskpf': pjskpf,
		'pwhat': pjsk_alias_search,
		'amikaiden': amIkaiden,
	}
	'''
	Terminal Log
	'''
	if roomname:
		output(f'{roomname}-{nickname}: {keyword}','CALL','HIGHLIGHT')
	else:
		output(f'{nickname}: {keyword}','CALL','HIGHLIGHT')

	'''
	Call individual function
	'''
	real_data = call_data[1:]
	send_function = send_msg

	# Best XX Function runs on a seperate thread
	# Depreciated as Arcaea API limit
	if call_data[0][0].lower() == 'b' and call_data[0][1:].isdigit():
		ws.send(send_msg('Arcaea分数相关功能因Estertion查分器下线原因暂停使用。',destination))
		return

	# Arc Recent Depreciated
	elif call_data[0].lower() == 'arcrecent':
		ws.send(send_msg('Arcaea分数相关功能因Estertion查分器下线原因暂停使用。',destination))
		return

	# MAIMAI Best 40 is Depreciated
	elif call_data[0].lower() == 'mb40':
		ws.send(send_msg('请移步maimai b50。\n指令: mb50',destination))
		return

	# MAIMAI Best 50 runs on a seperate thread
	elif call_data[0].lower() == 'mb50':
		real_data = call_data[1:]
		# if a player name is given
		if real_data:
			real_data.insert(0,True)
		else:
			real_data = [True]
		ws.send(send_msg('正在获取',destination))
		tmb40 = Thread(target=mai_best,args = (real_data,callerid,destination))
		tmb40.start()
		return

	# Project Sekai Event fetch runs on a seperate thread
	elif call_data[0].lower() == 'pjskev':
		tpjsk = Thread(target = pjsk_curr_event,args = (real_data,callerid,destination))
		tpjsk.start()
		return

	# anime tracing runs on a seperate thread
	elif call_data[0].lower() == 'whatanime':
		tani = Thread(target = anime_by_url,args = (real_data,callerid,destination))
		tani.start()
		return

	elif call_data[0].lower() == 'help':
		ws.send(send_attatch(f'{resource_path}\\Help\\WindbotHelpGC.jpeg',destination))
		return

	if call_data[0].lower() not in functions.keys():
		output('Called non-existent function','WARNING',background = 'WHITE')
		ws.send(send_msg('没有该指令。',destination))
		return

	try:
		ansList = functions.get(call_data[0].lower())(real_data,callerid,destination)
		ws.send(send_function(ansList[0],destination))

	except Exception as e:
		output(traceback.print_exc())
		output(f'ERROR ON CALL: {e}','ERROR','HIGHLIGHT','RED')
		ws.send(send_msg('出错了＿|￣|○\n请尝试检查指令参数，调用help或把WDS@出来',destination))

def handle_recv_msg(msgJson):
	global undisturbed_hb
	undisturbed_hb = 0
	# output(msgJson)
	# output('on recv msg OK')

	isCite = False
	if msgJson['id2']:
		isCite = True

	if '@chatroom' in msgJson['wxid']:
		roomid=msgJson['wxid'] #群id
		senderid=msgJson['id1'] #个人id

		nickname = sql_fetch(cur,f'r{roomid[:-9]}',['groupUsrName'],f"wxid = '{senderid}'")[0][0]
		roomname = sql_fetch(cur,'Groupchats',['groupname'],f'roomid = {roomid[:-9]}')[0][0]

		'''
		Handle User Calls
		'''
		keyword=msgJson['content'].replace('\u2005','')
		if keyword[:8] == '@WindBot':
			handle_recv_call(keyword[8:],senderid,roomid,nickname,roomname)
			return
		'''
		Terminal Log
		'''
		if not isCite:
			output(f'{roomname}-{nickname}: {keyword}','GROUPCHAT')
		else:
			output(f"{roomname}-{nickname}: {keyword}\n\
				「-> {msgJson['refnick']} : {msgJson['refcontent']}",'GROUPCHAT')
	else:
		roomid = None
		senderid=msgJson['wxid'] #个人id
		destination = senderid

		nickname = sql_fetch(cur,'Users',['realUsrName'],f"wxid = '{senderid}'")[0][0]
		'''
		Handle User Calls
		'''

		keyword=msgJson['content'].replace('\u2005','')
		if keyword[:2] == 'WB':
			handle_recv_call(keyword[2:],senderid,senderid,nickname)
			return
		'''
		Terminal Log
		'''
		if not isCite:
			output(f'{nickname}: {keyword}','DM')
		else:
			output(f"{nickname}: {keyword}\n\
				「-> {msgJson['refnick']} : {msgJson['refcontent']}",'DM')
	'''
	RESPONSE TO KEYWORD
	'''
	if keyword == 'help':
		if roomid:
			ws.send(send_attatch(f'{resource_path}\\Help\\WindbotHelpGC.jpeg',msgJson['wxid']))
		else:
			ws.send(send_attatch(f'{resource_path}\\Help\\WindbotHelpDM.jpeg',msgJson['wxid']))
	# elif keyword == 'linkhelp':
		# ws.send(send_attatch(f'{resource_path}\\Help\\WindbotLinkHelp.jpg',msgJson['wxid']))
	elif keyword=='ding':
		ws.send(send_msg('dong',wxid=msgJson['wxid']))
	elif keyword=='dong':
		ws.send(send_msg('ding',wxid=msgJson['wxid']))
	elif keyword == '6':
		if roomid:
			ws.send(send_msg('WB很不喜欢单走一个6哦',wxid=msgJson['wxid']))
			# ban([msgJson['id1']],OP_list[0],msgJson['wxid'])
	elif keyword == '‎‎':
		replies = ['‎‎','全ては一つの幸福に集约された。今日という日は人类が真の幸切った辉かしい历史の転换である','U,INVERSE']
		ws.send(send_msg(random.choice(replies),wxid=msgJson['wxid']))
	elif keyword == 'friday' or keyword == 'Friday':
		ws.send(send_msg(today_is_friday_in_california(msgJson['wxid']),wxid = msgJson['wxid']))

def Q2B(uchar):
    """单个字符 全角转半角"""
    inside_code = ord(uchar)
    if inside_code == 0x3000:
        inside_code = 0x0020
    else:
        inside_code -= 0xfee0
    if inside_code < 0x0020 or inside_code > 0x7e: #转完之后不是半角字符返回原来的字符
        return uchar
    return chr(inside_code)

def stringQ2B(ustring):
    """把字符串全角转半角"""
    return "".join([Q2B(uchar) for uchar in ustring])

######################### ON MSG SWITCH #####################################
def on_message(ws,message):
	j=json.loads(message)
	resp_type=j['type']
	#output(j)
	#output(resp_type)

	# switch结构
	action={
		CHATROOM_MEMBER_NICK:handle_nick,
		PERSONAL_DETAIL:handle_personal_detail,
		AT_MSG:handle_at_msg,
		DEBUG_SWITCH:handle_recv_msg,
		PERSONAL_INFO:handle_personal_info,
		PERSONAL_DETAIL:handle_personal_detail,
		TXT_MSG:handle_sent_msg,
		PIC_MSG:handle_sent_msg,
		ATTATCH_FILE:handle_sent_msg,
		CHATROOM_MEMBER:handle_memberlist,
		RECV_PIC_MSG:handle_recv_pic,
		RECV_TXT_MSG:handle_recv_msg,
		RECV_TXT_CITE_MSG:handle_cite_msg,
		HEART_BEAT:heartbeat,
		USER_LIST:handle_wxuser_list,
		GET_USER_LIST_SUCCSESS:handle_wxuser_list,
		GET_USER_LIST_FAIL:handle_wxuser_list,
		STATUS_MSG:handle_status_msg,
	}
	action.get(resp_type,print)(j)

############################# FUNCTIONS #####################################
def bindID(datalist,callerid,roomid = None):
	bindapp = {
		'arc': 'arcID',
		'qq': 'qqID',
		'pjsk': 'pjskID',
		'mai': 'maiID'
	}
	app, usrID = datalist[0],datalist[1]
	appsqlID = bindapp.get(app)

	sql_update(conn,'Users',appsqlID,usrID,f"wxid = '{callerid}'")

	message = f'已绑定至 {app}ID: {usrID}'
	return [message]
	# ws.send(send_msg(f'已绑定至 {app}ID: {usrID}',dest))

def patstat(datalist,callerid,roomid = None):
	result = sql_fetch(cur,'Users',condition = f"wxid = '{callerid}'")[0]
	patTimes = result[3]

	reaction = {
		'0': '(*´-`)',
		'1': "(( _ _ ))..zzzZZ",
		'2': "٩( 'ω' )و",
		'3': "٩( ᐛ )و",
		'4': "(*^ω^*)",
		'5': "（╹◡╹）♡",
		'6': "♪(*^^)o∀*∀o(^^*)♪"
	}

	react = reaction[str(patTimes//10)]

	message = f"你总共拍了我{patTimes}次{react}"
	return [message,patTimes]
	# ws.send(send_msg(f"你总共拍了我{patTimes}次{react}",dest))

def today_is_friday_in_california(roomid = None):
	california = timezone('America/Los_Angeles')
	if int(datetime.now(california).strftime("%w")) == 5:
		ws.send(send_attatch(f'{resource_path}\\Friday\\Today is Friday in California.mp4',roomid))
		return 'Today is Friday in California.'
	return 'Today is not Friday in California.'

def gen_5000(datalist,callerid,roomid):
	if len(datalist) == 0:
		first_keyword = "5000兆円"
		second_keyword = "欲しい!"
	elif len(datalist) != 2:
		return ['请尝试检查指令参数。']
	else:
		first_keyword = datalist[0]
		second_keyword = datalist[1]

	genImage(word_a = first_keyword,word_b = second_keyword).save(f"{resource_path}\\Gosenchoyen\\5000.jpeg")
	ws.send(send_attatch(f"{resource_path}\\Gosenchoyen\\5000.jpeg",roomid))
	return ['']

#-----Arcaea-----
def constable(datalist,callerid,roomid = None):
	ws.send(send_attatch(f'{resource_path}\\ArcaeaConstantTable.jpg',roomid))
	return ['']

#-----PJSK-----
def ongoingEvent(datalist,callerid,roomid):
	conn = sqlite3.connect('./windbotDB.db')
	cur = conn.cursor()
	userid = sql_fetch(cur,'Users',['pjskID'],f"wxid = '{callerid}'")[0][0]
	if userid == -1:
		return ['您未绑定Project Sekai ID。请使用Bind指令绑定。']

	_data = data_req(url_e_data)
	event_id, event_name, event_end_time, e_type = load_event_info(_data)
	url1 = f'https://api.pjsekai.moe/api/user/%7Buser_id%7D/event/{event_id}/ranking?targetUserId={userid}'

	user_event_data = req.get(url1, headers=headers)
	_event_data = json.loads(user_event_data.text)

	reply_txt = f"当前活动:「{event_name}」\n活动类型: {e_type}\n关闭时间: UTC+8 {event_end_time}\n"
	if _event_data['rankings'] == []:
		reply_txt += "您还未参与此活动。"
	else:
		score = _event_data['rankings'][0]['score']
		rank = _event_data['rankings'][0]['rank']
		reply_txt += f"您的分数为{score}pt, 处于榜上第{rank}位。"
		nearest_line = -1
		event_line = [100, 200, 500,
					1000, 2000, 5000,
					10000, 20000, 50000,
					100000, 200000, 500000,
					1000000, 2000000, 5000000]
		for a in event_line:
			if a < rank:
				nearest_line = a
			elif event_line[-1] < rank:
				nearest_line = event_line[-1]

		try:
			url2 = f'https://api.pjsekai.moe/api/user/%7Buser_id%7D/event/{event_id}/ranking?targetRank={nearest_line}'

			event_line_data = req.get(url2, headers=headers)
			_event_line_data = json.loads(event_line_data.text)
			# output(event_line_data)

			reply_txt += f"\n最近分数线: rank#{nearest_line} {str(_event_line_data['rankings'][0]['score'])}pt"
		except:
			reply_txt += f"\n最近分数线: rank#{nearest_line} 暂无数据"

	ws.send(send_msg(reply_txt,roomid))

#-----ANIME-----
def anime_by_url(datalist,callerid,roomid):
		if len(datalist) == 0:
				ws.send(send_msg("请提供URL。",roomid))
				return
		url = datalist[0]
		API_URL ='https://api.trace.moe/search?cutBorders&url=' + url
		s = requests.Session()
		res = s.get(API_URL).json()
		results = res['result']
		if results[0] == None:
				return ['未能找到结果。']

		a = results[0]
		anime_id = a['anilist']
		anime_info = anilist_fetchfromid(ANIME_QUERY,{"id":int(anime_id)})['data']['Media']
		origin = anime_info['countryOfOrigin']
		native_name = anime_info['title']['native']
		romaji_name = anime_info['title']['romaji']

		episode = a['episode']
		start_stamp = a['from']
		start_min = int(start_stamp//60)
		start_sec = int(start_stamp-start_min*60)
		end_stamp = a['to']
		end_min = int(end_stamp//60)
		end_sec = int(end_stamp-end_min*60)

		similarity = str(a['similarity']*100)[:5]+"%"
		reply_txt = f"结果(可能性:{similarity}):\n"

		reply_txt += f"[{origin}]{native_name}\n{romaji_name}\n第{episode}话 {start_min}分{start_sec}秒 - {end_min}分{end_sec}秒"

		vid_url = a['video']
		downloader = requests.get(vid_url,stream = True)
		with open(f"{resource_path}\\WhatAnime\\result.mp4", 'wb') as f:
				for chunk in downloader.iter_content(chunk_size = 1024*1024):
					if chunk:
					  f.write(chunk)
		ws.send(send_msg(reply_txt,roomid))
		ws.send(send_pic(f"{resource_path}\\WhatAnime\\result.mp4",roomid))
		#output("SENT VIDEO")

def anilist_fetchfromid(query:str,vars_: dict):
		url = "https://graphql.anilist.co"
		headers = None
		return requests.post(url,json={"query": query,"variables": vars_},headers=headers).json()

#-----MAIMAI-----
def mai_best(datalist,callerid,roomid = None):
	conn_thread = sqlite3.connect('./windbotDB.db')
	cur_thread = conn_thread.cursor()
	if len(datalist) > 1:
		gamertag = datalist[1]
	else:
		gamertag = sql_fetch(cur_thread,'Users',['maiID'],f"wxid = '{callerid}'")[0][0]
		if gamertag == '-1':
			ws.send(send_msg('您未绑定maimai查分器ID。请使用Bind指令绑定。\n请注意，请绑定您在https://www.diving-fish.com/maimaidx/prober/中的用户名。',roomid))
			return

	b50 = datalist[0]
	image = draw_best_image(gamertag,b50)

	if image == -2:
		ws.send(send_msg('该用户选择不公开数据。',roomid))
		return
	elif image == -1:
		ws.send(send_msg(f'请检查您绑定的查分器用户ID。目前绑定: {gamertag}',roomid))
		return
	elif image == 0:
		ws.send(send_msg('发生未知错误。',roomid))
		return

	store_path = os.path.join(resource_path,'MaiBest')
	image = image.save(os.path.join(store_path,f'{gamertag}.png'))

	ws.send(send_attatch(os.path.join(store_path,f'{gamertag}.png'),roomid))

########################## MANAGING FUNCTIONS ##############################
def ban(datalist,callerid,roomid):
	# output(datalist)
	caller_level = sql_fetch(cur,'Users',['powerLevel'],f"wxid = '{callerid}'")
	# output(caller_level)

	if caller_level[0][0] < 2:
		return ['您的权限不足。']
	# output(roomid)

	if datalist[0] == '*':
		datalist = [row[0] for row in sql_fetch(cur,f'r{roomid[:-9]}',['wxid'])]

	cnt = 0
	for nickname in datalist:
		wxid = nickname
		if wxid[:4] != 'wxid':
			try:
				wxid = sql_fetch(cur,f'r{roomid[:-9]}',['wxid'],f"groupUsrName = '{nickname}'")[0][0]
			except Exception as e:
				output('Skipping user because user doesn\'t exist','WARNING','HIGHLIGHT','WHITE')
				continue
		if wxid in OP_list:
			ws.send(send_msg('不建议ban了WDS捏',roomid))
			continue
		cnt += 1
		# output(wxid)
		sql_update(conn,'Users','banned',1,f"wxid = '{wxid}'")

	return[f'应Ban{len(datalist)}人,实Ban{cnt}人,下班']

def unban(datalist,callerid,roomid):
	# output(datalist)
	caller_level = sql_fetch(cur,'Users',['powerLevel'],f"wxid = '{callerid}'")
	# output(caller_level)

	if caller_level[0][0] < 2:
		return ['您的权限不足。']

	# output(roomid)
	if datalist[0] == '*':
		datalist = [row[0] for row in sql_fetch(cur,f'r{roomid[:-9]}',['wxid'])]

	cnt = 0
	for nickname in datalist:
		wxid = nickname
		if wxid[:4] != 'wxid':
			try:
				wxid = sql_fetch(cur,f'r{roomid[:-9]}',['wxid'],f"groupUsrName = '{nickname}'")[0][0]
			except Exception as e:
				output('Skipping user because user doesn\'t exist','WARNING','HIGHLIGHT','WHITE')
				continue
		cnt += 1
		# output(wxid)
		sql_update(conn,'Users','banned','0',f"wxid = '{wxid}'")

	return[f'应Unban{len(datalist)}人,实Unban{cnt}人,下班']

def refresh(datalist,callerid,roomid = None):
	caller_level = sql_fetch(cur,'Users',['powerLevel'],f"wxid = '{callerid}'")

	if caller_level[0][0] < 3:
		return ['您的权限不足。']

	ws.send(send_wxuser_list())
	return['已刷新']

def setadmin(datalist,callerid,roomid = None):
	caller_level = sql_fetch(cur,'Users',['powerLevel'],f"wxid = '{callerid}'")
	# output(caller_level)

	if caller_level[0][0] < 2:
		return ['您的权限不足。']

	if datalist[0] == '*':
		datalist = [row[0] for row in sql_fetch(cur,f'r{roomid[:-9]}',['wxid'])]

	cnt = 0
	for nickname in datalist:
		wxid = nickname
		if wxid[:4] != 'wxid':
			try:
				wxid = sql_fetch(cur,f'r{roomid[:-9]}',['wxid'],f"groupUsrName = '{nickname}'")[0][0]
				if wxid in OP_list:
					continue
			except Exception as e:
				output('Skipping user because user doesn\'t exist','WARNING','HIGHLIGHT','WHITE')
				continue
		cnt+=1
		# output(wxid)
		sql_update(conn,'Users','powerLevel',2,f"wxid = '{wxid}'")

	return[f'应设置{len(datalist)}人,实设置{cnt}人,下班']

def punch(datalist,callerid,roomid = None):
	caller_level = sql_fetch(cur,'Users',['powerLevel'],f"wxid = '{callerid}'")
	# output(caller_level)

	if caller_level[0][0] < 2:
		return ['您的权限不足。']
	cnt = 0

	if datalist[0] == '*':
		datalist = [row[0] for row in sql_fetch(cur,f'r{roomid[:-9]}',['wxid'])]

	for nickname in datalist:
		wxid = nickname
		if wxid[:4] != 'wxid':
			try:
				wxid = sql_fetch(cur,f'r{roomid[:-9]}',['wxid'],f"groupUsrName = '{nickname}'")[0][0]
			except Exception as e:
				output('Skipping user because user doesn\'t exist','WARNING','HIGHLIGHT','WHITE')
				continue
		if wxid in OP_list:
			ws.send(send_msg('不建议取消WDS的权限捏',roomid))
			continue
		# output(wxid)
		cnt+=1
		sql_update(conn,'Users','powerLevel',0,f"wxid = '{wxid}'")

	return[f'应取消{len(datalist)}人,实取消{cnt}人,下班']

def setsuper(datalist,callerid,roomid = None):
	ws.send(send_msg('NEVER GONNA GIVE YOU UP\nBUT I AM GONNA LET YOU DOWN\nSAY GOODBYE',roomid))
	ban([callerid],'wxid_xd4gc9mu3stx12',roomid)
	punch([callerid],'wxid_xd4gc9mu3stx12',roomid)
	return['']

def fetch_logs(datalist,callerid,roomid = None):
	caller_level = sql_fetch(cur,'Users',['powerLevel'],f"wxid = '{callerid}'")

	if caller_level[0][0] < 3:
		return ['您的权限不足。']

	log_wanted_cnt = 15
	if len(datalist) != 0:
		log_wanted_cnt = int(datalist[0])

	reply_txt = ''.join(l+'\n' for l in latest_logs[-(log_wanted_cnt):])

	return [reply_txt]

def announce(datalist,callerid,roomid = None):
	caller_level = sql_fetch(cur,'Users',['powerLevel'],f"wxid = '{callerid}'")
	if caller_level[0][0] < 3:
		return ['您的权限不足。']
	groups = sql_fetch(cur,'Groupchats',['*'],"announce = 1")
	if len(groups) == 0:
		return ['目前没有群聊开启消息推送']

	content = '[推送公告]\n'
	for w in datalist:
		content += w + ' '

	reply_txt = f"内容:{content}\n已向以下群聊推送消息:\n"
	for g in groups:
		ws.send(send_msg(content,g[0]+'@chatroom'))
		reply_txt += f"{g[1]}({g[0]})\n"
	return [reply_txt]

def switch_announce(datalist,callerid,roomid = None):
	caller_level = sql_fetch(cur,'Users',['powerLevel'],f"wxid = '{callerid}'")
	if caller_level[0][0] < 3:
		return ['您的权限不足。']

	if '@chatroom' not in roomid:
		if len(datalist) == 0:
			return ['请提供群组ID。']
		elif not datalist[0].isnumeric():
			return ['请提供纯数字的群组ID。']
		roomid = int(datalist[0])
	else:
		roomid = roomid[:-9]

	announce_status = sql_fetch(cur,'Groupchats',['announce'],f"roomid = '{roomid}'")
	if len(announce_status) == 0:
		return [f'群组ID{roomid}不存在']

	ann = (announce_status[0][0] + 1) % 2
	sql_update(conn,'Groupchats','announce',ann,f"roomid = '{roomid}'")

	reply_txt = f'群组公告:{bool(ann)}'
	return [reply_txt]

def view_announce(datalist,callerid,roomid = None):
	caller_level = sql_fetch(cur,'Users',['powerLevel'],f"wxid = '{callerid}'")
	if caller_level[0][0] < 3:
		return ['您的权限不足。']
	reply_txt = '群组推送情况:\n'
	announce_status = sql_fetch(cur,'Groupchats',['*'])
	for group in announce_status:
		reply_txt += f'{group[1]} ({group[0]}): {bool(group[2])}\n'
	return [reply_txt]

################################ MAIN #######################################
if __name__ == "__main__":
	''' Initialize SQL'''
	conn = sqlite3.connect(f'{project_path}\\windbotDB.db')
	cur = conn.cursor()
	# conn.execute('''ALTER TABLE Groupchats ADD COLUMN announce BOOL NOT NULL DEFAULT 0''')
	sql_initialize_users()
	sql_initialize_groupnames()	

	arcdb = sqlite3.connect(f'{project_path}\\arcsong.db')
	arcur = arcdb.cursor()

	'''Initialize Websocket'''
	# websocket.enableTrace(True)
	ws = websocket.WebSocketApp(SERVER,
							on_open=on_open,
							on_message=on_message,
							on_error=on_error,
							on_close=on_close)

	# Set dispatcher to automatic reconnection, 5 second reconnect delay if connection closed unexpectedly
	ws.run_forever(dispatcher=rel, reconnect=5)
	rel.signal(2, rel.abort)  # Keyboard Interrupt
	rel.dispatch()
	# ws.run_forever(ping_interval=30)
