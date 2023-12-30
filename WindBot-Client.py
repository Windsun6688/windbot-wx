# -*- coding:utf-8 -*-

import websocket,json,requests,rel,sqlite3,subprocess
import random,traceback
import sys
from datetime import datetime
from pytz import timezone
from threading import Thread
from bs4 import BeautifulSoup
from colorama import init
from Functions.gosenchoyen.generator import genImage
from Functions.arcaea.arcaea import *
from Functions.pjsk.pjsk import *
from Functions.maiCN.maimaiDX import *
from Functions.rss.rssPush import *

websocket._logging._logger.level = -99
init(autoreset = True)

'''Initialize Autohibernate'''
undisturbed_hb = 0

'''Initialize TickScheduler'''
global_event_tick = 0

'''Local Resource Path'''
project_path = os.path.join(os.path.dirname(__file__))
resource_path = os.path.join(project_path,'Resources')

'''Initialize Bot Config'''
try:
	wb_config_path = os.path.join(project_path,'config.json')
	json.load(open(wb_config_path))
except FileNotFoundError:
	# Generate WB config file
	with open(wb_config_path, 'w', encoding = 'utf-8') as f:
		init_config = { "botName": "YOUR TRIGGER FOR GROUPCHAT",
						"botDMTrigger": "YOUR TRIGGER FOR DM",
						"Sudoers": ["YOUR WXID"],
						"wxIP": "127.0.0.1",
						"wxPort": "5555"}
		f.write(json.dumps(init_config,ensure_ascii = False, indent = 4))
	print("Assuming running for the first time. Generating WB Config")
	time.sleep(5)
	sys.exit()

'''WindBot Config'''
wb_config = json.load(open(wb_config_path))
BOT_NAME = wb_config["botName"]
BOT_GC_TRIGGER = f"@{BOT_NAME}"
BOT_DM_TRIGGER = wb_config["botDMTrigger"]
SUDO_LIST = wb_config["Sudoers"]

FUNTOOL_IP = wb_config["wxIP"]
FUNTOOL_PORT = wb_config["wxPort"]

'''Msg Codes'''
SERVER = f"ws://{FUNTOOL_IP}:{FUNTOOL_PORT}"
HEART_BEAT = 5005
RECV_TXT_MSG = 1
RECV_TXT_CITE_MSG = 49
RECV_PIC_MSG = 3
USER_LIST = 5000
GET_USER_LIST_SUCCSESS = 5001
GET_USER_LIST_FAIL = 5002
TXT_MSG = 555
PIC_MSG = 500
AT_MSG = 550
CHATROOM_MEMBER = 5010
CHATROOM_MEMBER_NICK = 5020
PERSONAL_INFO = 6500
DEBUG_SWITCH = 6000
PERSONAL_DETAIL = 6550
DESTROY_ALL = 9999
STATUS_MSG = 10000
ATTATCH_FILE = 5003
# 'type':49 带引用的消息

'''Recent Logs List'''
latest_logs = []

################################# OUTPUT&SQL ################################
def getid():
	return time.strftime("%Y%m%d%H%M%S")

def output(msg,logtype = 'SYSTEM',mode = 'DEFAULT',background = 'DEFAULT'):
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
		'STOP_LINK':'031',
		'RSS': '037'
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
		'MINT' : ';46',
		'PURPLE' : ';45'
	}
	color = LogColor.get(logtype)
	mode = LogMode.get(mode)
	bg = LogBG.get(background)

	now = time.strftime("%Y-%m-%d %X")

	# Shorten logs of too long messages

	line_cnt = msg.count('\n') + 1
	if line_cnt > 10 and logtype != 'ERROR':
		msg = "\n".join(msg.split("\n")[:10])
		msg += '\n......'
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

def sql_insert(db,dbcur,\
			table: str,\
			rows: list,\
			values: list):
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

def sql_update(db, table: str, col: str, value: str, condition: str = None):
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

def sql_fetch(dbcur, table: str, cols: list = None, condition: str = None):
	if not cols:
		cols = ['*']
	cols = str(cols)[1:-1].replace('\'','')

	if condition:
		fetch_txt = f"SELECT {cols} FROM {table} WHERE {condition}"
	else:
		fetch_txt = f"SELECT {cols} FROM {table}"
	# output(fetch_txt,mode = 'HIGHLIGHT')
	dbcur.execute(fetch_txt)
	result = dbcur.fetchall()
	return [i for i in result]

def sql_match(db,dbcur,\
			table: str,\
			cols: list = ['*'],\
			conditionCol = None,\
			keyword = None):
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

def sql_destroy(db,table: str):
	destroy_txt = f"DROP TABLE {table}"
	db.execute(destroy_txt)
	db.commit()

def sql_delete(db, table: str, condition: str = None):
	if not condition:
		output('Did not specify which delete condition.','WARNING',\
				background = "WHITE")
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

def handle_chat_nick(j):
	data=eval(j['content'])
	nickname = data['nick']
	wxid = data['wxid']
	roomid = data['roomid']

	sql_update(conn,f'r{roomid[:-9]}','groupUsrName',nickname,\
				f"wxid = '{wxid}'")

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
		# 'content':'op:personal detail',
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
		output(f"[{i}] {item['wxid']} {item['name']}")

		# If item is chatroom
		if item['wxid'][-8:] == 'chatroom':
			room_id = item['wxid'][:-9]
			group_name = item['name']

			# Get if groupchat exist in record
			res = sql_fetch(cur,'Groupchats',['*'],f"roomid = '{room_id}'")

			# Does not exist, insert groupchat info into record
			if len(res) == 0:
				sql_insert(conn,cur,'Groupchats',\
							['roomid','groupname','announce','rssPush'],\
							[room_id,group_name,1,0])
			# Exists, update groupchat infomation
			else:
				sql_update(conn,'Groupchats','groupname',group_name,\
								f"roomid = '{room_id}'")

		# If item is single user
		else:
			sql_insert(conn,cur,'Users',['wxid','wxcode','realUsrName'],\
							[item['wxid'],item['wxcode'],item['name']])

	# Recursively start to update chatroom's members
	ws.send(get_chatroom_memberlist(item['wxid']))

################################# INITIALIZE ###############################
def heartbeat_trigger(msgJson):
	global undisturbed_hb, global_event_tick
	undisturbed_hb += 1
	global_event_tick += 1

	# Local Log of Heartbeat
	if undisturbed_hb < 5:
		output('Success','HEART_BEAT','HIGHLIGHT')
	elif undisturbed_hb == 5:
		output('Undisturbed in 5 min. Hiding heartbeat logs. zZZ',logtype = 'HEART_BEAT',mode = 'HIGHLIGHT')

	# Every 60 min, Trigger a User Database Refresh
	if global_event_tick % 60 == 0 and global_event_tick != 0:
		ws.send(send_wxuser_list())
		global_event_tick = 0

	# Every 30 min, Trigger a rss fetch
	if global_event_tick % 30 == 0 and global_event_tick != 0:
		tRss = Thread(target = rss_trigger, args = ())
		tRss.start()

	# Every 15 min, Trigger a battery check
	if global_event_tick % 15 == 0 and global_event_tick != 0:
		tBtry = Thread(target = btry_check_auto, args = ())
		tBtry.start()

def on_open(ws):
	#初始化 更新用户数据
	ws.send(send_wxuser_list())

	# Update Global Admin List
	for wxid in SUDO_LIST:
		sql_update(conn,'Users','powerLevel',3,f"wxid = '{wxid}'")

	now=time.strftime("%Y-%m-%d %X")
	ws.send(send_txt_msg(f'启动完成\n{now}',SUDO_LIST[0]))

	# ASCII Art Credit: FigLet & Me
	start_ascii_art = """

#######################################################
# ___       ______       ________________      _____  #
# __ |     / /__(_)____________  /__  __ )_______  /_ #
# __ | /| / /__  /__  __ \  __  /__  __  |  __ \  __/ #
# __ |/ |/ / _  / _  / / / /_/ / _  /_/ // /_/ / /_   #
# ____/|__/  /_/  /_/ /_/\__,_/  /_____/ \____/\__/   #
#                                                     #
#######################################################

	"""
	print(start_ascii_art)

def on_error(ws,error):
	output(f"on_error:{error}",'ERROR','HIGHLIGHT','RED')

def on_close(ws,signal,status):
	output("Server Closed",'WARNING','HIGHLIGHT','WHITE')

def sql_initialize_group(roomid):
	initialize_group = f'''CREATE TABLE IF NOT EXISTS {roomid}
			(wxid TEXT,
			groupUsrName TEXT);'''
	conn.execute(initialize_group)
	conn.commit()

def sql_initialize_users():
	initialize_users = f'''CREATE TABLE IF NOT EXISTS Users
			(wxid TEXT,
			wxcode TEXT,
			realUsrName TEXT,
			patTimes NUMBER NOT NULL DEFAULT 0,
			patAction TEXT NOT NULL DEFAULT -1,
			arcID NUMBER NOT NULL DEFAULT -1,
			qqID NUMBER NOT NULL DEFAULT -1,
			pjskID NUMBER NOT NULL DEFAULT -1,
			maiID TEXT NOT NULL DEFAULT -1,
			powerLevel NUMBER NULL DEFAULT 0,
			banned NUMBER NOT NULL DEFAULT 0);'''
	conn.execute(initialize_users)
	conn.commit()

def sql_initialize_groupnames():
	initialize_gn = f'''CREATE TABLE IF NOT EXISTS Groupchats
			(roomid TEXT,
			groupname TEXT
			announce BOOL NOT NULL DEFAULT 0,
			rssPush BOOL NOT NULL DEFAULT 1);'''
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

def send_txt_msg(msg,wxid='null'):
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
	vis_content = msgJson['content']['content']
	if '拍了拍我' in vis_content:
		output(vis_content,'PAT',background = 'MINT')
		pat_wb(msgJson)

	elif '邀请' in vis_content:
		ws.send(send_wxuser_list())
		roomid=msgJson['content']['id1']
		ws.send(send_txt_msg(f'欢迎进群',wxid=roomid))

def handle_sent_msg(msgJson):
	output(msgJson['content'],mode = 'HIGHLIGHT')

def handle_xml_msg(msgJson):
	# 处理带引用的文字消息和转发链接
	msgXml=msgJson['content']['content'].replace('&amp;','&').replace('&lt;','<').replace('&gt;','>')
	soup=BeautifulSoup(msgXml,features="xml")

	if soup.appname.string == '哔哩哔哩':
		output(f'Video from BiliBili: {soup.title.string} URL: {soup.url.string}',logtype = 'GROUPCHAT')
		return

	refmsg = soup.refermsg

	msgJson={
		'content':soup.select_one('title').text,
		'refcontent': refmsg.select_one('content').text,
		'refnick': refmsg.select_one('displayname').text,
		'id':msgJson['id'],
		'id1':msgJson['content']['id2'],
		'id2': refmsg.select_one('chatusr').text,
		'id3':'',
		'srvid':msgJson['srvid'],
		'time':msgJson['time'],
		'type':msgJson['type'],
		'wxid':msgJson['content']['id1']
	}
	handle_recv_msg(msgJson)

def handle_at_msg(msgJson):
	output(msgJson)
	output('AT_msg')

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
		nickname = sql_fetch(cur,'Users',['realUsrName'],\
							f"wxid = '{senderid}'")[0][0]
		'''
		Terminal Log
		'''
		output(f'{nickname}: [IMAGE]','DM')

def handle_recv_call(keyword, callerid, destination):
	caller_isbanned = sql_fetch(cur,'Users',['banned'],\
								f"wxid = '{callerid}'")
	if caller_isbanned[0][0] == 1:
		return

	call_data = stringQ2B(keyword.strip()).split(' ')
	if len(call_data) == 0:
		ws.send('请指明需要调用的功能。')
		return

	# Handle Mobile @
	if len(call_data) > 1 and call_data[0] == '':
		call_data = call_data[1:]

	### HBD EASTER EGG ###
	if call_data == ['minfo', '11391', 'mas', 'cb', '555']:
		ws.send(send_txt_msg("HAPPY BIRTHDAY!!!",destination))
		return
	### HBD EASTER EGG ###

	'''
	Call individual function
	'''
	func_name = call_data[0].lower()
	real_data = call_data[1:]

	# MAIMAI Best 50 runs on a seperate thread
	if func_name == 'mb50':
		ws.send(send_txt_msg('正在获取',destination))

	elif func_name == 'help':
		help_path = os.path.join(resource_path,"Help")
		ws.send(send_attatch(os.path.join(help_path,"WindbotHelpGC.jpeg"),\
				destination))
		return

	execute_call(func_name,real_data,callerid,destination)

# Helper of handle_recv_call
def execute_call(func_name, real_data, callerid, destination):
	# Depreciated Functions
	if func_name in DEPRECIATED_FUNC_DICT:
		ws.send(send_txt_msg(DEPRECIATED_FUNC_DICT[func_name],destination))
		return

	# Functions that runs on a independent thread
	elif func_name in THREADED_FUNC_DICT:
		tFunc = Thread(target = THREADED_FUNC_DICT[func_name],\
						args = (real_data,callerid,destination))
		tFunc.start()
		return

	# Normal Functions
	elif func_name in WB_FUNC_DICT:
		try:
			ansList = WB_FUNC_DICT.get(func_name)\
					(real_data,callerid,destination)

		# Error Happened. Push Error Msg to destination
		except Exception as e:
			output(f'ERROR ON CALL: {e}','ERROR','HIGHLIGHT','RED')
			output(traceback.format_exc(),'ERROR','HIGHLIGHT','RED')
			ws.send(send_txt_msg(f"出错了＿|￣|○\n指令: {func_name}\n错误细节: {e}\n请尝试检查指令参数，调用help或把WDS@出来",destination))
			return

		# No Error Happened
		ws.send(send_txt_msg(ansList[0],destination))
		return

	# Non-Existent Function
	else:
		output('Called non-existent function','WARNING',background = 'WHITE')
		ws.send(send_txt_msg(f"没有该指令: {func_name}",destination))
		return

def handle_recv_msg(msgJson):
	global undisturbed_hb
	undisturbed_hb = 0
	# output(msgJson)

	isCite = False
	# If msg is a cite message
	if msgJson.get('refnick',-1) != -1 and \
		msgJson.get('refcontent',-1) != -1:
		isCite = True

	if '@chatroom' in msgJson['wxid']:
		roomid=msgJson['wxid'] #群id
		senderid=msgJson['id1'] #个人id

		nickname = sql_fetch(cur,f'r{roomid[:-9]}',['groupUsrName'],\
							f"wxid = '{senderid}'")[0][0]
		roomname = sql_fetch(cur,'Groupchats',['groupname'],\
							f'roomid = {roomid[:-9]}')[0][0]

		# Handle User Calls
		keyword=msgJson['content'].replace('\u2005','')
		if keyword[:8] == BOT_GC_TRIGGER:
			output(f'{roomname}-{nickname}: {keyword[8:]}','CALL','HIGHLIGHT')
			handle_recv_call(keyword[8:],senderid,roomid)
			return

		# Terminal Log Normal Messages
		if not isCite:
			output(f'{roomname}-{nickname}: {keyword}','GROUPCHAT')
		else:
			# little patch that makes no sense at all
			refcontent = msgJson['refcontent'].split("\n")
			if len(refcontent) > 1:
				refcontent = refcontent[4]
			else:
				refcontent = refcontent[0]
			output(f"{roomname}-{nickname}: {keyword}\n\
				「-> {msgJson['refnick']} : {refcontent}",\
				'GROUPCHAT')
	else:
		roomid = None
		senderid=msgJson['wxid'] #个人id
		destination = senderid

		nickname = sql_fetch(cur,'Users',['realUsrName'],\
							f"wxid = '{senderid}'")[0][0]

		# Handle User Calls
		keyword=msgJson['content'].replace('\u2005','')
		if keyword[:2] == BOT_DM_TRIGGER:
			output(f'{nickname}: {keyword}','CALL','HIGHLIGHT')
			handle_recv_call(keyword[2:],senderid,senderid)
			return

		# Terminal Log Normal Messages
		if not isCite:
			output(f'{nickname}: {keyword}','DM')
		else:
			output(f"{nickname}: {keyword}\n\
				「-> {msgJson['refnick']} : {msgJson['refcontent']}",'DM')
	'''
	RESPOND TO KEYWORD
	'''
	if keyword == 'help':
		help_path = os.path.join(resource_path,"Help")
		if roomid:
			ws.send(send_attatch(os.path.join(help_path,"WindbotHelpGC.jpeg"),\
								msgJson['wxid']))
		else:
			ws.send(send_attatch(os.path.join(help_path,"WindbotHelpDM.jpeg"),\
								msgJson['wxid']))
	elif keyword == 'ding':
		ws.send(send_txt_msg('dong', wxid = msgJson['wxid']))
	elif keyword == 'dong':
		ws.send(send_txt_msg('ding', wxid = msgJson['wxid']))
	elif keyword == 'bing':
		ws.send(send_txt_msg('bong', wxid = msgJson['wxid']))
	elif keyword == 'bong':
		ws.send(send_txt_msg('bing', wxid = msgJson['wxid']))
	elif keyword == 'BONG':
		ws.send(send_txt_msg('DONG', wxid = msgJson['wxid']))
	elif keyword == '6':
		if roomid:
			ws.send(send_txt_msg('WB很不喜欢单走一个6哦',wxid=msgJson['wxid']))
			# ban([msgJson['id1']],SUDO_LIST[0],msgJson['wxid'])
	elif keyword == '‎‎':
		resp_list = ['‎‎',\
					'全ては一つの幸福に集约された。今日という日は人类が真の幸切った辉かしい历史の転换である']
		ws.send(send_txt_msg(random.choice(resp_list),wxid=msgJson['wxid']))
	elif keyword == '‎':
		reply_txt = "₂ₓ"
		ws.send(send_txt_msg(reply_txt, wxid = msgJson['wxid']))
	elif keyword == '∩':
		reply_txt = '‎'
		ws.send(send_txt_msg(reply_txt, wxid = msgJson['wxid']))
	elif keyword.lower() == 'wb':
		resp_list = ["您好!","我可以帮到您些什么?"]
		ws.send(send_txt_msg(random.choice(resp_list),wxid = msgJson['wxid']))

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
def on_localapi_message(ws,message):
	j=json.loads(message)
	resp_type=j['type']
	# output(j)
	# output(resp_type)

	# switch结构
	action={
		CHATROOM_MEMBER_NICK:handle_chat_nick,
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
		RECV_TXT_CITE_MSG:handle_xml_msg,
		HEART_BEAT:heartbeat_trigger,
		USER_LIST:handle_wxuser_list,
		GET_USER_LIST_SUCCSESS:handle_wxuser_list,
		GET_USER_LIST_FAIL:handle_wxuser_list,
		STATUS_MSG:handle_status_msg,
	}
	action.get(resp_type,print)(j)

########################## USER FUNCTIONS ###################################
def no_op(datalist,callerid,roomid = None):
	return ['']

def list_functions(datalist,callerid,roomid = None):
	date = time.strftime("%Y-%m-%d")
	reply_txt = f"WB的目前可用指令({date}):\n"
	for func_name in WB_FUNC_DICT:
		reply_txt += f"{func_name}\n"
	for func_name in THREADED_FUNC_DICT:
		reply_txt += f"{func_name}\n"
	return [reply_txt]

def bind(datalist,callerid,roomid = None):
	bind_categories = {
		'arc': 'arcID',
		# 'qq': 'qqID', # For Now, QQID Serves no purpose.
		'pjsk': 'pjskID',
		'mai': 'maiID',
		'pat': 'patAction'
	}

	if len(datalist) == 0:
		return ["请指明需要绑定的项目类型和内容。"]

	reply_txt = ""

	keyword = datalist[0]

	# bind view
	if keyword == "view":
		reply_txt = bind_view(callerid)

	# Category not found
	elif keyword not in bind_categories:
		reply_txt = f"没有该项目: {datalist[0]}"

	# bind xxx yyyy
	else:
		app = datalist[0]
		content = stringQ2B(" ".join(datalist[1:]).strip())
		app_sql_ID = bind_categories.get(app)

		# For Game IDs
		if app_sql_ID != 'patAction':
			reply_txt = f"已绑定至 {app_sql_ID}: {content}"
		# For PatAction
		else:
			if len(content) > 30:
				reply_txt = "您的PatAction超过了30个字符。"
				return [reply_txt]
			elif content.isspace() or content == "":
				reply_txt = "请提供PatAction。"
				return [reply_txt]
			elif "bind" in content:
				reply_txt = "https://www.google.com/search?q=recursion"
				return [reply_txt]
			elif "patstat" in content:
				reply_txt = "为了解决WB对群聊具有高度侵入性的情况,您不可以将patstat绑定为PatAction。谢谢您的理解。"
				return [reply_txt]
			else:
				reply_txt = f"已将PatAction设置为: {content}"

		# Bind User's content to corresponding app_sql_ID item
		sql_update(conn, 'Users', app_sql_ID, content, f"wxid = '{callerid}'")

	return [reply_txt]

# Helper for bind Function
def bind_view(callerid:str) -> str:
	# Format: [(arcID,maiID,pjskID,funccall)]
	usrInfo = sql_fetch(cur,'Users',['arcID','maiID','pjskID','patAction'],\
						f"wxid = '{callerid}'")[0]
	id_type = ['Arcaea','maimai查分器','pjsk','PatAction指令']

	reply_txt = ""

	unbound_cnt = 0
	# For Game IDs
	for i in range(len(usrInfo)-1):
		if str(usrInfo[i]) != '-1':
			reply_txt += f'已绑定的{id_type[i]}ID: {usrInfo[i]}\n'
		else:
			unbound_cnt += 1
			reply_txt += f'您没有绑定{id_type[i]}ID\n'

	# For patAction
	if usrInfo[-1] == '-1':
		pat_action = f"无\n示例PatAction绑定: {BOT_GC_TRIGGER} bind pat mb50\n"
	else:
		pat_action = usrInfo[-1]

	reply_txt += f"PatAction指令: {pat_action}"

	if unbound_cnt == len(usrInfo) - 1:
		reply_txt = f"您还没有绑定任何ID。\n示例: {BOT_GC_TRIGGER} bind mai xxxxx"

	return reply_txt

def pat_wb(msgJson):
	from_id = msgJson['content']['id1']
	username = None

	# If Pat Comes From a Groupchat
	if from_id[-8:] == 'chatroom':
		username = msgJson['content']['content'].split('"')[1]

		# Getting the wxid
		wxid_query = sql_fetch(cur,f'r{from_id[:-9]}',['wxid'],\
							f"groupUsrName = '{username}'")
		# If the wxid has been updated but not recorded
		if wxid_query == []:
			ws.send(send_txt_msg("您可能更新了昵称,但是未被WB记录。请稍后再试。",\
								from_id))
			# Update the User DB
			ws.send(send_wxuser_list())
			return
		wxid = wxid_query[0][0]
	else:
		wxid = from_id

	# Increment Recorded patTimes by 1
	rec_pat_times = sql_fetch(cur,'Users',['patTimes'],\
							f"wxid = '{wxid}'")[0][0]
	new_pat_times = rec_pat_times + 1
	sql_update(conn,'Users','patTimes',new_pat_times,f"wxid = '{wxid}'")

	# Check if patter is banned
	caller_isbanned = sql_fetch(cur,'Users',['banned'],\
								f"wxid = '{wxid}'")
	if caller_isbanned[0][0] == 1:
		return

	# Trigger PatAction
	pat_data = sql_fetch(cur,'Users',['patAction'],f"wxid = '{wxid}'")[0][0]
	# If user did not bind any action
	if pat_data == "-1":
		reply_txt = f"您没有绑定PatAction指令。\n示例绑定: {BOT_GC_TRIGGER} bind pat mb50\n"
		reply_txt += f"如果您不想再看到这条信息，请使用 {BOT_GC_TRIGGER} bind pat nop"
		ws.send(send_txt_msg(reply_txt,from_id))
	# User binded action
	else:
		call_data = pat_data.split(" ")
		func_name = call_data[0]
		real_data = call_data[1:]
		callerid = wxid
		if pat_data not in ['nop', 'swym']:
			ws.send(send_txt_msg(f"正在执行『{pat_data}』",from_id))
		execute_call(func_name,real_data,callerid,from_id)

	# Reply
	## Removed. WB was never meant to be intrusive to the chat.
	# reply_txt = f"第{new_pat_times}次了！"
	# ws.send(send_txt_msg(reply_txt,from_id))

def patstat(datalist,callerid,roomid = None):
	patTimes = sql_fetch(cur,'Users',['patTimes'],f"wxid = '{callerid}'")[0][0]

	if patTimes > 109:
		reply_txt = f"你总共拍了WB{patTimes}次。\n0MG"
		return [reply_txt]

	reaction = {
		0: '(*´-`)',
		1: "(( _ _ ))..zzzZZ",
		2: "٩( 'ω' )و",
		3: "٩( ᐛ )و",
		4: "(*^ω^*)",
		5: "（╹◡╹）♡",
		6: "♪(*^^)o∀*∀o(^^*)♪",
		7: "（＾Ｏ＾☆♪",
		8: "☆彡",
		9: "(=´∀｀)人(´∀｀=)",
		10: "♪───Ｏ（≧∇≦）Ｏ────♪"
	}

	react = reaction[patTimes//10]
	reply_txt = f"你总共拍了我{patTimes}次{react}"
	return [reply_txt]

def today_is_friday_in_california(datalist,callerid,roomid = None):
	california = timezone('America/Los_Angeles')
	# If Today is Friday in California
	if int(datetime.now(california).strftime("%w")) == 5:
		friday_path = os.path.join(resource_path,"Friday")
		shoot_vid = os.path.join(friday_path,\
								"Today is Friday in California.mp4")
		ws.send(send_attatch(shoot_vid,roomid))
		reply_txt = "Today is Friday in California.\nSHOOT!"
	# If today is not Friday in California
	else:
		reply_txt = "Today is not Friday in California."
	ws.send(send_txt_msg(reply_txt,roomid))

def gen_5000(datalist,callerid,roomid = None):
	if len(datalist) == 0:
		first_keyword = "5000兆円"
		second_keyword = "欲しい!"
	elif len(datalist) != 2:
		ws.send("请尝试检查指令参数。",roomid)
		return
	else:
		first_keyword = datalist[0]
		second_keyword = datalist[1]

	gosenImagePath = os.path.join(os.path.join(resource_path,"Gosenchoyen"),\
									"5000.jpeg")
	genImage(word_a = first_keyword,word_b=second_keyword).save(gosenImagePath)
	ws.send(send_attatch(gosenImagePath,roomid))

def party_parrot(datalist,callerid,roomid = None):
	if len(datalist) >= 1:
		keyword = datalist[0]
	else:
		keyword = None

	parrot_path = os.path.join(resource_path,"Parrot")
	hd_parrot_path = os.path.join(parrot_path,"hd")

	if keyword == None:
		chosen_path = hd_parrot_path
	elif keyword == "l":
		chosen_path = parrot_path
	else:
		ws.send(send_txt_msg(f"没有该参数: {keyword}",roomid))
		return

	chosen_parrot = random.choice(os.listdir(chosen_path))
	# If the folder "hd" is randomly chosen
	while chosen_parrot == "hd":
		chosen_parrot = random.choice(os.listdir(chosen_path))

	chosen_parrot_path = os.path.join(chosen_path,chosen_parrot)

	reply_txt = f"你的鹦鹉是:\n{chosen_parrot[:-4]}"
	ws.send(send_txt_msg(reply_txt,roomid))
	ws.send(send_attatch(chosen_parrot_path,roomid))

#-----Arcaea-----
def constable(datalist,callerid,roomid = None):
	ws.send(send_attatch(f'{resource_path}\\ArcaeaConstantTable.jpg',roomid))
	return ['']

#-----PJSK-----
def pjsk_curr_event(datalist,callerid,roomid = None):
	event_type_dict = {
		'普活': 'marathon', '马拉松': 'marathon', 'marathon': 'marathon',
		'5v5': 'cheerful_carnival', '嘉年华': 'cheerful_carnival', 'cheerful_carnival': 'cheerful_carnival'
	}
	event_type_dict = {'marathon': '普活','cheerful_carnival': '5v5嘉年华'}
	unit_dict = {
		'light_sound': 'Leo/need', 'idol': 'More More Jump', \
		'street': 'Vivid Bad Squad','theme_park': 'Wonderlands x Showtime',\
		'school_refusal': '25时', 'none': '未指明不知道是哪个团但是感觉会很开心的'
	}
	data = pjsk_event_get(local = False)[0]
	event = load_event_info(data)
	end_text = '(进行中)' if event[-1] else '(已结束)'
	reply_txt = f'{unit_dict[event[4]]}活动！\n「{event[1]}」\n类型: {event_type_dict[event[3]]}\n结束时间: {event[2]} {end_text}'
	ws.send(send_txt_msg(reply_txt,roomid))

#-----ANIME-----
def anime_by_url(datalist,callerid,roomid):
		if len(datalist) == 0:
				ws.send(send_txt_msg("请提供URL。",roomid))
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
		ws.send(send_txt_msg(reply_txt,roomid))
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
	if datalist != []:
		gamertag = datalist[0]
	else:
		gamertag = sql_fetch(cur_thread,'Users',['maiID'],\
							f"wxid = '{callerid}'")[0][0]
		if gamertag == '-1':
			ws.send(send_txt_msg(f'您未绑定maimai查分器ID。请使用bind指令绑定。\n请注意，请绑定您在https://www.diving-fish.com/maimaidx/prober/中的用户名。\n示例: {BOT_GC_TRIGGER} bind mai xxxxx',roomid))
			return

	image = draw_best_image(gamertag)

	if image == -2:
		ws.send(send_txt_msg('该用户选择不公开数据。',roomid))
		return
	elif image == -1:
		ws.send(send_txt_msg(f'查分器没有返回数据,请检查您绑定的查分器用户ID。目前绑定: {gamertag}\n如果您没有导入过游玩数据,请参考https://www.diving-fish.com/maimaidx/prober_guide。',roomid))
		return
	elif image == 0:
		ws.send(send_txt_msg('发生未知错误。',roomid))
		return

	store_path = os.path.join(os.path.join(resource_path,'maiCN'),'MaiBest')
	image = image.save(os.path.join(store_path,f'{gamertag}.png'))
	ws.send(send_attatch(os.path.join(store_path,f'{gamertag}.png'),roomid))

def mai_plate(datalist,callerid,roomid = None):
	conn_thread = sqlite3.connect('./windbotDB.db')
	cur_thread = conn_thread.cursor()
	# User need to specify which plate to check
	if not datalist:
		ws.send(send_txt_msg('请提供要查询的名牌版。',roomid))
		return

	# User can only check their plate progress
	gamertag = sql_fetch(cur_thread,'Users',['maiID'],\
						f"wxid = '{callerid}'")[0][0]
	if gamertag == '-1':
		ws.send(send_txt_msg(f'您未绑定maimai查分器ID。请使用bind指令绑定。\n请注意，请绑定您在https://www.diving-fish.com/maimaidx/prober/中的用户名。\n示例: {BOT_GC_TRIGGER} bind mai xxxxx',roomid))
		return

	reply_txt = mai_plate_status(gamertag, datalist)
	ws.send(send_txt_msg(reply_txt,roomid))
	return

#-----RSS-----
def test_rss_wrapper(datalist,callerid,roomid = None):
	rss_trigger()
	return ['Tested']

def rss_trigger():
	pushed = False
	for subscribed in rss_subscriptions:
		# Format: check_rss(route,usrID)
		to_push = check_rss(*subscribed)

		# Has new feed
		if to_push not in (-1,-2,-3):
			pushed = True
			for feed in to_push:
				final_feed = finalize_feed(*feed)
				rss_push(final_feed)
		elif to_push == -2:
			output(f'Website Blocked Feed (412) for {subscribed}',\
					logtype = 'RSS',background = 'RED')
		elif to_push == -3:
			output(f'Connection Timed Out for {subscribed}',\
					logtype = 'RSS',background = 'RED')
	if pushed:
		output('Pushed New Feed',logtype = 'RSS',background = 'PURPLE')
	# No New Feed
	elif to_push == -1:
		output('No New Feed',logtype = 'RSS',background = 'PURPLE')

def rss_push(feed):
	conn_thread = sqlite3.connect('./windbotDB.db')
	cur_thread = conn_thread.cursor()
	groups = sql_fetch(cur_thread,'Groupchats',['*'],"rssPush = 1")
	if len(groups) == 0:
		ws.send(send_txt_msg('目前没有群聊开启rss推送',SUDO_LIST[0]))
	else:
		feed_content = f"""{feed[0][3]}@{feed[0][1]}:\n{feed[0][0]}\
							\nLink: {feed[0][2]}"""

		content = f'[rss推送]\n{feed_content}'
		op_fdbk_txt = f"内容:{content}\n已向以下群聊推送rss消息:\n"

		for g in groups:
			group_id = f"{g[0]}@chatroom"
			# Send text feed
			ws.send(send_txt_msg(content,group_id))
			# If the feed contain images
			if feed[1] != None:
				ws.send(send_attatch(feed[1],group_id))
			# Record group in feedback
			op_fdbk_txt += f"{g[1]}({g[0]})\n"
		# Feedback
		ws.send(send_txt_msg(op_fdbk_txt,SUDO_LIST[0]))

########################## MANAGING FUNCTIONS ##############################
def manual_refresh(datalist,callerid,roomid = None):
	caller_level = sql_fetch(cur,'Users',['powerLevel'],f"wxid = '{callerid}'")

	if caller_level[0][0] < 3:
		return ['您的权限不足。']

	# Start the Refresh Process
	ws.send(send_wxuser_list())

	return['已刷新']

def fetch_logs(datalist,callerid,roomid = None):
	caller_level = sql_fetch(cur,'Users',['powerLevel'],f"wxid = '{callerid}'")

	if caller_level[0][0] < 3:
		return ['您的权限不足。']

	log_wanted_cnt = 15
	if len(datalist) != 0:
		log_wanted_cnt = int(datalist[0])

	reply_txt = ''.join(l+'\n' for l in latest_logs[-(log_wanted_cnt):])
	reply_txt += f"===END OF LOG (Total {log_wanted_cnt})==="

	return [reply_txt]

def announce(datalist,callerid,roomid = None):
	caller_level = sql_fetch(cur,'Users',['powerLevel'],f"wxid = '{callerid}'")
	if caller_level[0][0] < 3:
		return ['您的权限不足。']
	groups = sql_fetch(cur,'Groupchats',['*'],"announce = 1")
	if len(groups) == 0:
		return ['目前没有群聊开启公告推送']

	content = '[推送公告]\n'
	for w in datalist:
		content += w + ' '

	reply_txt = f"内容:{content}\n已向以下群聊推送公告:\n"
	for g in groups:
		ws.send(send_txt_msg(content,g[0]+'@chatroom'))
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
		else:
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
	reply_txt = '群组公告推送情况:\n'
	announce_status = sql_fetch(cur,'Groupchats',['*'])
	for group in announce_status:
		reply_txt += f'{group[1]} ({group[0]}): {bool(group[2])}\n'
	return [reply_txt]

def switch_rss(datalist,callerid,roomid = None):
	caller_level = sql_fetch(cur,'Users',['powerLevel'],f"wxid = '{callerid}'")
	if caller_level[0][0] < 3:
		return ['您的权限不足。']

	if '@chatroom' not in roomid:
		if len(datalist) == 0:
			return ['请提供群组ID。']
		elif not datalist[0].isnumeric():
			return ['请提供纯数字的群组ID。']
		else:
			roomid = int(datalist[0])
	else:
		roomid = roomid[:-9]

	rss_status = sql_fetch(cur,'Groupchats',['rssPush'],f"roomid = '{roomid}'")
	if len(rss_status) == 0:
		return [f'群组ID{roomid}不存在']

	ann = (rss_status[0][0] + 1) % 2
	sql_update(conn,'Groupchats','rssPush',ann,f"roomid = '{roomid}'")

	reply_txt = f'群组rss推送:{bool(ann)}'
	return [reply_txt]

def view_rss(datalist,callerid,roomid = None):
	caller_level = sql_fetch(cur,'Users',['powerLevel'],f"wxid = '{callerid}'")
	if caller_level[0][0] < 3:
		return ['您的权限不足。']
	reply_txt = '群组rss推送情况:\n'
	rss_status = sql_fetch(cur,'Groupchats',['*'])
	for group in rss_status:
		reply_txt += f'{group[1]} ({group[0]}): {bool(group[3])}\n'
	return [reply_txt]

def execute_cmd(datalist):
	timeout_s = 10
	try:
		shell = subprocess.Popen(datalist,stdout=subprocess.PIPE,\
				stderr=subprocess.PIPE, text=True, shell = True)
		shell.wait()
	except subprocess.TimeoutExpired:
		return 'Timeout for {datalist} ({timeout_s}s) expired'
	shell_res, shell_err = shell.communicate()
	shell.kill()
	if shell_res == '':
		return shell_err
	else:
		return shell_res

def cmd_trigger(datalist,callerid,roomid = None):
	conn = sqlite3.connect(f'{project_path}\\windbotDB.db')
	cur = conn.cursor()
	caller_level = sql_fetch(cur,'Users',['powerLevel'],f"wxid = '{callerid}'")
	if caller_level[0][0] < 3:
		ws.send(send_txt_msg('您的权限不足。',roomid))
		return
	ws.send(send_txt_msg(execute_cmd(datalist),roomid))

def feedback(datalist,callerid,roomid = None):
	if len(datalist) == 0:
		return ['请提供反馈内容']
	else:
		msg = ''
		if roomid:
			roomname = sql_fetch(cur,'Groupchats',['groupname'],\
								f'roomid = {roomid[:-9]}')[0][0]
			nickname = sql_fetch(cur,f'r{roomid[:-9]}',['groupUsrName'],\
								f"wxid = '{callerid}'")[0][0]
			msg += f"来自{roomname}-{nickname}({callerid})的反馈:\n"
		else:
			nickname = sql_fetch(cur,'Users',['realUsrName'],\
								f"wxid = '{callerid}'")[0][0]
			msg += f"来自{nickname}({callerid})的DM反馈:\n"
		msg += " ".join(datalist)
		handler = SUDO_LIST[0]
		ws.send(send_txt_msg(msg,handler))
		return ['发送完成']

def sys_battery_status():
	cmd = "WMIC Path Win32_Battery Get BatteryStatus"
	datalist = cmd.split(" ")
	result = execute_cmd(datalist).strip().split("\n")
	status = int(result[2])
	status_dict = { 1: "Other",
					2: "Unknown",
					3: "Fully Charged",
					4: "Low",
					5: "Critical",
					6: "Charging",
					7: "Charging and High",
					8: "Charging and Low",
					9: "Charging and Critical",
					10: "Undefined"}
	btry_description = status_dict.get(status, "NULL")

	# Discharging
	if status in [1,4,5]:
		btry_status =  0
	# Charging
	elif status in [2,6,7,8,9]:
		btry_status =  1
	# FULL
	elif status == 3:
		btry_status =  2
	# No Battery Instance
	elif status == 10:
		btry_status =  -1
	# Unknown Value
	else:
		btry_status =  -2

	return (btry_status, btry_description)

def btry_check_auto():
	status, description = sys_battery_status()
	if status == 0:
		ws.send(send_txt_msg("[警告] 机器目前电池情况: {description}"),SUDO_LIST[0])
		output(f"DISCHARGING BATTERY - {description}",\
				logtype = "WARNING", background = "RED")
	else:
		output(f"OK BATTERY STATUS - {description}",\
				logtype = "SYSTEM", background = "WHITE")

def btry_check_trigger(datalist,callerid,roomid = None):
	caller_level = sql_fetch(cur,'Users',['powerLevel'],f"wxid = '{callerid}'")
	if caller_level[0][0] < 3:
		ws.send(send_txt_msg('您的权限不足。',roomid))
		return
	status, description = sys_battery_status()
	status_str = ["DISCHARGING", "Charging", "Full", "Unknown" ,"No Battery"]
	reply_txt = f"Battery Status: {status_str[status]}\n{description}"
	return [reply_txt]

##################### GROUP MANAGING FUNCTIONS ##############################
def ban(datalist,callerid,roomid = None):
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
			except Exception as _:
				output('Skipping user because user doesn\'t exist','WARNING','HIGHLIGHT','WHITE')
				continue
		if wxid in SUDO_LIST:
			ws.send(send_txt_msg('已跳过管理员',roomid))
			continue
		cnt += 1
		# output(wxid)
		sql_update(conn,'Users','banned',1,f"wxid = '{wxid}'")

	return[f'应Ban{len(datalist)}人,实Ban{cnt}人,下班']

def unban(datalist,callerid,roomid = None):
	caller_level = sql_fetch(cur,'Users',['powerLevel'],f"wxid = '{callerid}'")

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

def set_admin(datalist,callerid,roomid = None):
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
				wxid = sql_fetch(cur,f'r{roomid[:-9]}',['wxid'],\
								f"groupUsrName = '{nickname}'")[0][0]
				if wxid in SUDO_LIST:
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
		if wxid in SUDO_LIST:
			ws.send(send_txt_msg('已跳过WDS',roomid))
			continue
		# output(wxid)
		cnt+=1
		sql_update(conn,'Users','powerLevel',0,f"wxid = '{wxid}'")

	return[f'应取消{len(datalist)}人,实取消{cnt}人,下班']

def set_super(datalist,callerid,roomid = None):
	ws.send(send_txt_msg('NEVER GONNA GIVE YOU UP\nBUT I AM GONNA LET YOU DOWN\nSAY GOODBYE',roomid))
	ban([callerid],SUDO_LIST[0],roomid)
	punch([callerid],SUDO_LIST[0],roomid)
	return['']

def list_admin(datalist,callerid,roomid = None):
	# If comes from DM
	if callerid == roomid:
		ws.send(send_txt_msg("DM不支持listadmin。",roomid))
		return
	group_user_list = sql_fetch(cur,f"r{roomid[:-9]}",\
								["wxid","groupUsrName"])
	# print(group_user_list)
	group_admins = []

	for usrInfo in group_user_list:
		wxid, username = usrInfo[0], usrInfo[1]
		power_level = sql_fetch(cur,'Users',['powerLevel'],\
								f"wxid = '{wxid}'")[0][0]
		if power_level >= 2:
			group_admins.append((username,power_level))

	# No Admins in this group
	if len(group_admins) == 0:
		reply_txt = "本群无Admin。"
	# Found Admin in this group
	else:
		reply_txt = "本群Admin:\n"
		power_level_list = ["管理员","Sudoer"]
		for usrInfo in group_admins:
			username, power_level = usrInfo[0], usrInfo[1]
			reply_txt += f"{username} - {power_level_list[power_level-2]}\n"
	return [reply_txt]

################################ MAIN #######################################
if __name__ == "__main__":
	''' Initialize SQL'''
	conn = sqlite3.connect(os.path.join(project_path, "windbotDB.db"))
	cur = conn.cursor()

	# conn.execute('''UPDATE Users SET patAction = '-1' WHERE patAction = 'patstat' ''')

	sql_initialize_users()
	sql_initialize_groupnames()	

	arcdb = sqlite3.connect(os.path.join(project_path, "arcsong.db"))
	arcur = arcdb.cursor()

	'''Initialize Function Switches'''
	WB_FUNC_DICT = {
		'bind': bind,
		'patstat': patstat,
		'fdbk': feedback,
		'btry': btry_check_trigger,
		'listfunc': list_functions,
		'swym': no_op,
		'nop': no_op,

		'ban': ban,
		'unban':unban,
		'refresh': manual_refresh,
		'setadmin': set_admin,
		'listadmin': list_admin,
		'punch':punch,
		'setsuper': set_super,
		'announce': announce,
		'annswitch': switch_announce,
		'annview': view_announce,
		'rssswitch': switch_rss,
		'rssview': view_rss,
		# 'testrss': test_rss_wrapper,

		'logs': fetch_logs,

		'ainfo': arc_music_search,
		'randarc': arc_random,
		'acinfo': arc_chart_info,
		'awhat': arc_alias_search,
		'grablevel': grablevel,
		'constable': constable,
		'addalias': addalias,

		'minfo': mai_music_search,
		'mwhat':mai_alias_search,
		'mnew': mai_music_new,
		'randmai': mai_music_random,
		'mupdate': mai_update,

		'pjskpf': pjskpf,
		'pwhat': pjsk_alias_search,
		'pinfo': pjsk_music_search,
		'pcinfo': pjsk_chart_search,
		'amikaiden': amIkaiden,
		'pupdate': pjsk_data_update
	}

	DEPRECIATED_FUNC_DICT = {
		"b30": "Arcaea分数相关功能因Estertion查分器下线原因暂停使用。",
		"arcrecent": "Arcaea分数相关功能因Estertion查分器下线原因暂停使用。",
		"mb40": "请移步maimai b50。\n指令: mb50"
	}

	THREADED_FUNC_DICT = {
		"gosen": gen_5000, # Thank you Kevin
		"friday": today_is_friday_in_california,
		"parrot": party_parrot,
		"mb50": mai_best,
		"mplate": mai_plate,
		"pjskev": pjsk_curr_event,
		"whatanime": anime_by_url,
		"cmd": cmd_trigger
	}

	''' Initialize Anime Query '''
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

	'''Initialize Websocket'''
	# websocket.enableTrace(True)
	ws = websocket.WebSocketApp(SERVER,
							on_open = on_open,
							on_message = on_localapi_message,
							on_error = on_error,
							on_close = on_close)

	# Set dispatcher to automatic reconnection, 5 second reconnect delay if connection closed unexpectedly
	ws.run_forever(dispatcher = rel, reconnect = 5)
	rel.signal(2, rel.abort)  # Keyboard Interrupt
	rel.dispatch()
