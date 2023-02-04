# -*- coding:utf-8 -*-

import websocket,time,json,requests,os,rel,sqlite3,brotli,objectpath
import random,string
from datetime import datetime
from threading import Thread
from bs4 import BeautifulSoup
from Functions.gosenchoyen.generator import genImage
from Functions.arcaea.arcaea import *

websocket._logging._logger.level = -99

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

'''Initialize Autohibernate'''
undisturbed_hb = 0

'''Admins'''
OP_list = ['wxid_xd4gc9mu3stx12']

############################# MULTITHREADING ################################
class ThreadWithReturnValue(Thread):
    
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None

    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args,**self._kwargs)

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

def get_personal_info():
	# 获取本机器人的信息
	uri='/api/get_personal_info'
	data={
		'id':getid(),
		'type':PERSONAL_INFO,
		'content':'op:personal info',
		'wxid':'null',
	}
	respJson=send(uri,data)
	print(respJson)

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
			sql_insert(conn,cur,'Groupchats',['roomid','groupname'],[item['wxid'][:-9],item['name']])
			sql_update(conn,'Groupchats','groupname',item['name'],f"roomid = '{item['wxid'][:-9]}'")
		else:
			sql_insert(conn,cur,'Users',['wxid','wxcode','realUsrName'],[item['wxid'],item['wxcode'],item['name']])


	ws.send(get_chatroom_memberlist(item['wxid']))

	# output('启动完成')

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
		# output(wxid)
		sql_update(conn,'Users','powerLevel',3,f"wxid = '{wxid}'")

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
			chartLevel NUMBER NOT NULL DEFAULT -1,
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
			maiID TEXT NOT NULL DEFAULT -1,
			powerLevel NUMBER NULL DEFAULT 0,
			isInLink TEXT NOT NULL DEFAULT -1,
			banned NUMBER NOT NULL DEFAULT 0);'''
	conn.execute(initialize_users)
	conn.commit()

def sql_initialize_groupnames():
	initialize_gn = f'''CREATE TABLE IF NOT EXISTS Groupchats
			(roomid TEXT,
			groupname TEXT);'''
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

def handleMsg_cite(msgJson):
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

	call_data = keyword.split(' ')
	#handle mobile @
	if len(call_data) > 1 and call_data[0] == '':
		call_data = call_data[1:]

	functions = {
		'bind': bindID,
		'arclookup': arc_lookup,
		'whatis': whatis,
		'patstat': patstat,
		'arcrecent': arc_recent,
		'friday': today_is_friday_in_california,
		'ban': ban,
		'unban':unban,
		'refresh': refresh,
		'setadmin':setadmin,
		'punch':punch,
		'setsuper': setsuper,
		'link':arc_link,
		'stoplink':arc_link_destroy,
		'signup':arc_signup,
		'search': search,
		'linkselect': arc_link_select,
		'linkstart': arc_link_start,
		'quitlink': arc_link_quit,
		'random': arc_random,
		'chartdetail': chartdetail,
		'grablevel': grablevel,
		'constable': constable,
		'addalias': addalias,
		'gosen': gen_5000
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

	# Best XX Function runs on a single thread
	if call_data[0][0] == 'b' and call_data[0][1:].isdigit():
		real_data = call_data[1:]
		real_data.insert(0,int(call_data[0][1:]))
		ws.send(send_msg('这可能需要一会,请耐心等待。',destination))
		tbest = Thread(target=arc_best,args = (real_data,callerid,destination))
		tbest.start()
		return

	if call_data[0].lower() not in functions.keys():
		output('Called non-existent function','WARNING',background = 'WHITE')
		ws.send(send_msg('没有该指令。',destination))
		return

	try:
		ansList = functions.get(call_data[0].lower())(real_data,callerid,destination)
		ws.send(send_function(ansList[0],destination))
	except Exception as e:
		output(type(e))
		output(f'ERROR ON CALL: {e}','ERROR','HIGHLIGHT','RED')
		ws.send(send_msg('出错了＿|￣|○\n请尝试检查指令参数，调用help或把WDS@出来',destination))

	# ws.send(send_msg('收到调用',dest))

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
			ws.send(send_attatch('C:\\users\\public\\Help\\WindbotHelpGC.jpg',msgJson['wxid']))
		else:
			help_txt = open('WindBotHelpDM.txt','r').read()
			ws.send(send_msg(f'{help_txt}',wxid = msgJson['wxid']))
	elif keyword == 'linkhelp':
		ws.send(send_attatch('C:\\users\\public\\Help\\WindbotLinkHelp.jpg',msgJson['wxid']))
	elif keyword=='ding':
		ws.send(send_msg('dong',wxid=msgJson['wxid']))
	elif keyword=='dong':
		ws.send(send_msg('ding',wxid=msgJson['wxid']))
	elif keyword == '6':
		ws.send(send_msg('WB很不喜欢单走一个6哦',wxid=msgJson['wxid']))

######################### ON MSG SWITCH #####################################
def on_message(ws,message):
	j=json.loads(message)
	resp_type=j['type']
	# output(j)
	# output(resp_type)

	# switch结构
	action={
		CHATROOM_MEMBER_NICK:handle_nick,
		PERSONAL_DETAIL:handle_personal_detail,
		AT_MSG:handle_at_msg,
		DEBUG_SWITCH:handle_recv_msg,
		PERSONAL_INFO:handle_recv_msg,
		TXT_MSG:handle_sent_msg,
		PIC_MSG:handle_sent_msg,
		ATTATCH_FILE:handle_sent_msg,
		CHATROOM_MEMBER:handle_memberlist,
		RECV_PIC_MSG:handle_recv_pic,
		RECV_TXT_MSG:handle_recv_msg,
		RECV_TXT_CITE_MSG:handleMsg_cite,
		HEART_BEAT:heartbeat,
		USER_LIST:handle_wxuser_list,
		GET_USER_LIST_SUCCSESS:handle_wxuser_list,
		GET_USER_LIST_FAIL:handle_wxuser_list,
		STATUS_MSG:handle_status_msg,

	}
	action.get(resp_type,print)(j)

	# output('on message ok')

############################# FUNCTIONS #####################################
def bindID(datalist,callerid,roomid = None):
	bindapp = {
		'arc': 'arcID',
		'qq': 'qqID',
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

def today_is_friday_in_california(datalist,callerid,roomid = None):
	if datetime.today().weekday() == 4:
		ws.send(send_attatch('C:\\users\\public\\Friday\\Today is Friday in California.mp4',roomid))
		return ['Today is Friday in California.']
	return ['Today is not Friday in California.']

def gen_5000(datalist,callerid,roomid):
	if len(datalist) == 0:
		first_keyword = "5000兆円"
		second_keyword = "欲しい!"
	elif len(datalist) != 2:
		return ['请尝试检查指令参数。']
	else:
		first_keyword = datalist[0]
		second_keyword = datalist[1]

	genImage(word_a = first_keyword,word_b = second_keyword).save("/Users/windsun/Library/Application Support/CrossOver/Bottles/WechatServer/drive_c/users/Public/Gosenchoyen/5000.jpeg")
	ws.send(send_attatch("/Users/windsun/Library/Application Support/CrossOver/Bottles/WechatServer/drive_c/users/Public/Gosenchoyen/5000.jpeg",roomid))
	return ['您的五千兆图:']

def arc_best(datalist,callerid,roomid = None):
    conn_thread = sqlite3.connect('./windbotDB.db')
    cur_thread = conn_thread.cursor()

    clear_list = ['Track Lost', 'Normal Clear', 'Full Recall', 'Pure Memory', 'Easy Clear', 'Hard Clear']
    diff_list = ['PST', 'PRS', 'FTR', 'BYD']

    wsarc = websocket.create_connection("wss://arc.estertion.win:616/")

    userid = sql_fetch(cur_thread,'Users',['arcID'],f"wxid = '{callerid}'")[0][0]
    output(f"Fetching best for {userid}")

    if userid == -1:
        ws.send(send_msg('您未绑定ArcaeaID。请使用Bind指令绑定。',roomid))
        return
    try:
        num = int(datalist[0])
    except Exception as e:
        ws.send(send_msg('请指明有效获取数。',roomid))
        return
    if num < 1 or num > 100:
        ws.send(send_msg('非有效获取数。',roomid))
        return

    if len(datalist) > 1:
        userid = datalist[1]

    wsarc.send(str(userid))

    buffer = ""
    scores = []
    userinfo = {}
    song_title = {}
    count = 0

    while buffer != "bye":
        # output('got buWffer')
        try:
            buffer = wsarc.recv()
        except websocket._exceptions.WebSocketConnectionClosedException:
            ws.send(send_msg(f'查分服务器关闭了链接。\n这可能是用户绑定错误ID导致，也可能是网络原因。\n您现在绑定的arcID: {userid}',roomid))
            return

        if type(buffer) == type(b''):
            obj = json.loads(str(brotli.decompress(buffer), encoding='utf-8'))
            # output(obj)
            # al.append(obj)
            if obj['cmd'] == 'songtitle':
                song_title = obj['data']
            elif obj['cmd'] == 'scores':
                count += 1
                scores += obj['data']
                if count % 10 == 0:
                    output(f'Got {count} songs.')
            elif obj['cmd'] == 'userinfo':
                userinfo = obj['data']
                #Put In WINDOWS LOCATION
                output_file = open("/Users/windsun/Library/Application Support/CrossOver/Bottles/WechatServer/drive_c/users/Public/Best/%s Best.txt" % userinfo['name'],'w')
                # output_file = open("./Best/%s Best.txt" % userinfo['name'],'w')


    scores.sort(key=cmp, reverse=True)

    output('数据已拿全,正在整理')    

    output_file.write("%s's Top %d Songs:\n" % (userinfo['name'], num))
    for j in range(0, int((num - 1) / 15) + 1):
        for i in range(15 * j, 15 * (j + 1)):
            if i >= num:
                break
            try:
                score = scores[i]
            except IndexError:
                break
            output_file.write("#%d  %s  %s %.1f  \n\t%s\n\tPure: %d(%d)\n\tFar: %d\n\tLost: %d\n\tScore: %d\n\tRating: %.2f\n" % (i+1, song_title[score['song_id']]['en'], diff_list[score['difficulty']], score['constant'], clear_list[score['clear_type']],score["perfect_count"], score["shiny_perfect_count"], score["near_count"], score["miss_count"], score["score"], score["rating"]))

    ws.send(send_attatch(f"C:\\users\\Public\\Best\\{userinfo['name']} Best.txt",roomid))

def arc_room_id():
    alphabet = string.ascii_lowercase + string.digits
    return 'LR'+''.join(random.choices(alphabet, k=8))

def arc_link(datalist,callerid,roomid = None):
    user_status = sql_fetch(cur,'Users',['isInLink'],f"wxid = '{callerid}'")[0][0]
    if user_status != '-1':
        return ['您已在房间中。']

    user_arcID = sql_fetch(cur,'Users',['arcID'],f"wxid = '{callerid}'")[0][0]
    if user_arcID == -1:
        return ['您未绑定ArcaeaID。请使用Bind指令绑定。']

    allselect = -1

    if len(datalist) > 0:
        if datalist[0] == 'a' or datalist[0] == 'all':
            allselect = 1
        else:
            return[f'没有为{datalist[0]}的模式。']

    room_id = arc_room_id()
    sql_initialize_link(room_id,allselect)
    ws.send(send_msg(f'您的房间号是:',roomid))
    time.sleep(0.3)
    ws.send(send_msg(f'{room_id}',roomid))
    return arc_signup([room_id],callerid,isOwner = True)

def arc_signup(datalist,callerid,roomid = None,isOwner = None):
    user_status = sql_fetch(cur,'Users',['isInLink'],f"wxid = '{callerid}'")[0][0]
    if user_status != '-1':
        return ['您已在房间中。']

    user_arcID = sql_fetch(cur,'Users',['arcID'],f"wxid = '{callerid}'")[0][0]
    if user_arcID == -1:
        return ['您未绑定ArcaeaID。请使用Bind指令绑定。']

    link_room_id = datalist[0]
    if isOwner:
        isOwner = 1
        can_select = 1
    else:
        isOwner = 0
        can_select = -1 

        is_all = sql_fetch(cur,link_room_id,['allselect'])
        if is_all[0][0] == 1:
            can_select = 1

    try:
        sql_insert(conn,cur,link_room_id,['wxid','arcID','songselect','isOwner'],[callerid,user_arcID,can_select,isOwner])
    except Exception as e:
        return ['房间号错误或不存在。']

    sql_update(conn,'Users','isInLink',link_room_id,f"wxid = '{callerid}'")

    link_player_cnt = len(sql_fetch(cur,link_room_id,['wxid']))
    return [f'加入成功。目前房间内有{link_player_cnt}人。']

def arc_link_destroy(datalist,callerid,roomid = None):
    if len(datalist) == 0:
        link_room_id = sql_fetch(cur,'Users',['isInLink'],f"wxid = '{callerid}'")[0][0]
        if link_room_id == '-1':
            return ['您不在房间中。']
    else:
        link_room_id = datalist[0]

    user_is_owner = sql_fetch(cur,link_room_id,['isOwner'],f"wxid = '{callerid}'")
    if len((user_is_owner)) == 0:
        return ['出现错误。可能是房间ID输入错误。']
    user_is_owner = user_is_owner[0][0]

    user_level = sql_fetch(cur,'Users',['powerLevel'],f"wxid = '{callerid}'")[0][0]

    if user_is_owner != 1:
        if user_level < 2:
            return ['您没有权限结束该房间。']

    room_users = sql_fetch(cur,link_room_id,['wxid'])

    sql_destroy(conn,link_room_id)

    for wxid in room_users:
        wxid = wxid[0]
        sql_update(conn,'Users','isInLink',-1,f"wxid = '{wxid}'")
    output(f'Stopped Link Play Room of ID {link_room_id}','STOP_LINK',background = "WHITE")
    return ['房间已结束。']   

def arc_link_select(datalist,callerid,roomid):
    link_room_id = sql_fetch(cur,'Users',['isInLink'],f"wxid = '{callerid}'")[0][0]
    if link_room_id == '-1':
        return['您不在房间中。']

    user_can_select = sql_fetch(cur,link_room_id,['songselect'],f"wxid = '{callerid}'")[0]
    if user_can_select[0] != 1:
        return ['您没有选择歌曲的权限。']

    song_started = sql_fetch(cur,link_room_id,['songStarted'])[0][0]
    if song_started == 1:
        return ['已有进行中的歌曲。']

    diff_lvl = {
        'PST': 0,
        'PRS': 1,
        'FTR': 2,
        'BYD': 3
    }

    if datalist[-1].upper() not in diff_lvl.keys():
        return['请指明有效的歌曲难度。']

    keyword = ''
    for word in datalist[0:-1]:
        keyword += (word + ' ')
    keyword = keyword[:-1]
    # output(keyword)
    selected_song = sql_fetch(arcur,'charts',condition = f"name_en = '{keyword}'")

    if len(selected_song) == 0:
        sid = whatis([f"{keyword}"],callerid)[1]
        if sid == -1:
            return['没有找到相关歌曲。']
    else:
        sid = selected_song[0][0]

    if len(selected_song) > 4:
        ws.send(send_msg('啊哈 是重名歌曲 默认选Quon(Lanota)哦\n选Quon(wacca)的话直接说quon2 我懒（',roomid))

    try:
        given_diff = datalist[-1].upper()
        chart_diff = diff_lvl.get(given_diff)
        # output(chart_diff)
        chart_detail = sql_fetch(arcur,'charts',condition = f"song_id = '{sid}' AND rating_class = {chart_diff}")
        if len(chart_detail) == 0:
            return ['没有该难度。']
    except Exception as e:
        return ['没有该难度。']

    level = chart_detail[0]
    en_name = level[2]
    jp_name = level[3]
    artist = level[4]
    charter = level[18].replace('\n',' ')

    sql_update(conn,link_room_id,'song',sid)
    sql_update(conn,link_room_id,'chartLevel',chart_diff)

    if jp_name:
        reply_txt = f'已选择歌曲: {artist} - {en_name}({jp_name}) \n难度: {given_diff} 谱师: {charter}'
    else:
        reply_txt = f'已选择歌曲: {artist} - {en_name} \n难度: {given_diff} 谱师: {charter}'
    return [reply_txt]

def arc_link_start(datalist,callerid,roomid = None):
    link_room_id = sql_fetch(cur,'Users',['isInLink'],f"wxid = '{callerid}'")[0][0]
    if link_room_id == '-1':
        return ['您不在房间中。']

    user_can_start = sql_fetch(cur,link_room_id,['songselect'],f"wxid = '{callerid}'")[0][0]

    if user_can_start != 1:
        return ['您没有权限开始。']

    song = sql_fetch(cur,link_room_id,['song'])[0][0]
    if song == '-1':
        return ['没有选择歌曲。']

    song_started = sql_fetch(cur,link_room_id,['songStarted'])[0][0]
    if song_started == 1:
        return ['已有进行中的歌曲。']

    ws.send(send_msg('歌曲将在5秒钟后开始。',roomid))

    t = Thread(target=arc_link_results,args = (link_room_id,roomid))
    t.start()
    sql_update(conn,link_room_id,'songStarted',1)
    time.sleep(5)

    return ['已开始计时。']

def arc_link_results(link_room_id,destination):
    conn_thread = sqlite3.connect('./windbotDB.db')
    cur_thread = conn_thread.cursor()

    arcdb_thread = sqlite3.connect('./arcsong.db')
    arcur_thread = arcdb_thread.cursor()

    players = [p[0] for p in sql_fetch(cur_thread,link_room_id,['arcID'])]

    link_song = sql_fetch(cur_thread,link_room_id,['song'])[0][0]
    song_level = sql_fetch(cur_thread,link_room_id,['chartLevel'])[0][0]

    chart_detail = sql_fetch(arcur_thread,'charts',condition = f"song_id = '{link_song}' AND rating_class = {song_level}")[0]
    link_time = chart_detail[8]
    results = {}
    reply_txt = "下面是结果！\n"

    # output(players)
    # output(link_time)

    time.sleep(link_time+25)

    for p in players:
        wsarc_thread = websocket.create_connection("wss://arc.estertion.win:616/")
        wsarc_thread.send(f"{p} -1 -1")
        buffer = ""
        scores = []
        userinfo = {}
        song_title = {}
        while buffer != "bye":
            try:
                buffer = wsarc_thread.recv()
            except websocket._exceptions.WebSocketConnectionClosedException:
                wsarc_thread = websocket.create_connection("wss://arc.estertion.win:616/")
                wsarc_thread.send(f"{p} -1 -1")
            if type(buffer) == type(b''):
                obj = json.loads(str(brotli.decompress(buffer), encoding='utf-8'))
                # output(obj)
                if obj['cmd'] == 'userinfo':
                    userinfo = obj['data']
                    name = userinfo['name']

                    recent_song = userinfo['recent_score'][0]

                    sid = recent_song['song_id']
                    diff = recent_song['difficulty']
                    score = recent_song['score']

                    if sid == link_song and diff == song_level:
                        results[name] = score
                    else:
                        results[name] = -1
    i = 1
    for p,s in sorted(results.items(), key=lambda p:p[1]):
        reply_txt += f"{i}位！ {p} {s}\n"

    ws.send(send_msg(reply_txt,destination))
    sql_update(conn_thread,link_room_id,'songStarted',0)

def arc_link_quit(datalist,callerid,roomid):
    link_room_id = sql_fetch(cur,'Users',['isInLink'],f"wxid = '{callerid}'")[0][0]
    if link_room_id == '-1':
        return ['您不在房间中。']

    song_started = sql_fetch(cur,link_room_id,['songStarted'])[0][0]
    if song_started == 1:
        return ['歌曲正在进行中。']

    link_player_cnt = len(sql_fetch(cur,link_room_id,['wxid']))
    if link_player_cnt == 1:
        arc_link_destroy([link_room_id],OP_list[0],roomid)
        return['最后一位玩家退出房间。已结束房间。']

    sql_delete(conn,link_room_id,f"wxid = '{callerid}'")
    return ['您已退出房间。']

def constable(datalist,callerid,roomid = None):
    ws.send(send_attatch('C:\\users\\public\\ArcaeaConstantTable.jpg',roomid))
    return ['您要的阿卡伊定数表']

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
	# output(caller_level)

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
	return['LOL']

################################ MAIN #######################################
if __name__ == "__main__":
	''' Initialize SQL'''
	conn = sqlite3.connect('./windbotDB.db')
	cur = conn.cursor()
	sql_initialize_users()
	sql_initialize_groupnames()	

	arcdb = sqlite3.connect('./arcsong.db')
	arcur = arcdb.cursor()

	'''Initialize Websocket'''
	# websocket.enableTrace(True)
	ws = websocket.WebSocketApp(SERVER,
							on_open=on_open,
							on_message=on_message,
							on_error=on_error,
							on_close=on_close)

	ws.run_forever(dispatcher=rel, reconnect=5)  # Set dispatcher to automatic reconnection, 5 second reconnect delay if connection closed unexpectedly
	rel.signal(2, rel.abort)  # Keyboard Interrupt
	rel.dispatch()
