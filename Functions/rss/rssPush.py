import requests,json,xmltodict,html2text,os
import cv2
from ..sqlHelper import resource_root,output

rss_subscriptions = [["biliDynamic","404145357"],# Arcaea BiliDynamic\
					# ["biliDynamic","481648327"],# MaimaiCN Official\
					["biliDynamic","552507635"],# MaimaiJP Repost\
					# ["biliDynamic","295204807"],# Test Account
					# ["fgoNews",""],# FGO JP NEWS\
					]

pic_cache_dir = os.path.join(resource_root,"rss")
rss_func_dir = os.path.dirname(os.path.realpath(__file__))

config = json.load(open(os.path.join(rss_func_dir,'config.json')))
hub = config["rsshub"]
routes = config["routes"]
feed_data = {}

def check_rss(route:str,usrID:str = None):
	global feed_data
	r = routes[route]
	try:
		rss_reply = requests.get(hub + r + usrID)
	except:
		return -3
	try:
		listjson = xmltodict.parse(rss_reply.text)
	# Website Blocking Access
	except: #ExpatError wasnt picked up, idk
		return -2
	feed_data[route+usrID] = feed_data.get(route+usrID,{})

	# First time loading from source
	if feed_data[route+usrID] == {}:
		feed_data[route+usrID] = listjson
		return -1

	#### TESTING PURPOSES ####
	# old_listjson = copy.deepcopy(listjson)
	# print(old_listjson['rss']['channel']['item'].pop(0))
	# print(old_listjson == listjson)
	# feed_data[route+usrID] = old_listjson
	#### TESTING END ####

	first_feed_index = 0
	while True:
		# Reached Bottom of the channel
		# *Bro deleted all posts crazy*
		if first_feed_index == len(feed_data[route+usrID]\
									['rss']['channel']['item']):
			feed_data[route+usrID] = {}
			output('BRO DELETED ALL OF HIS POSTS CRAZY LOL')
			return -1

		# Start from the first_feed_index
		if listjson['rss']['channel']['item'][0]['link'] != \
			feed_data[route+usrID]['rss']['channel']['item']\
									[first_feed_index]['link']:
			# 先去找原来的第一个在不在新的里面
			found = False
			i = 0
			for newfeed in listjson['rss']['channel']['item']:
				# 遍历新数据
				if newfeed['link'] == \
					feed_data[route+usrID]['rss']['channel']['item']\
											[first_feed_index]['link']:
					found = True
					break
				i += 1
			# 需要推送新数据
			if found:
				to_push = []
				for a in range(0, i):
					b = i - 1 - a
					feed = listjson['rss']['channel']['item'][b]
					to_push.append((feed,route))
				# Update the feed data archive
				feed_data[route+usrID] = listjson
				return to_push
			# 没有找到原来的第一个
			else:
				# 从原来的第二个开始重新搜索
				first_feed_index += 1
		# 如果原来的第一个link符合新的第一个link 没有更新
		else:
			return -1

def get_image(url:str,route:str,pic_id:int):
	data = requests.get(url).content
	pic_loc = os.path.join(pic_cache_dir,f"{route}img{pic_id}.jpg")
	f = open(pic_loc,'wb')
	f.write(data)
	f.close()
	img = cv2.imread(pic_loc)
	return (img,pic_loc)

def process_feed(feed:dict,route:str):
	text = html2text.html2text(feed['description'])
	time = feed['pubDate']
	link = feed['link']
	author = feed['author']
	pic_cnt = text.count('![]')
	parts = [e.strip() for e in text.split('\n')\
			if e and not e.isspace()]
	pic = []
	lines = parts
	if pic_cnt > 0:
		pic = [e[1:-1] for e in parts[-1].split("![]") if e]
		lines = parts[:-1]
	reply_txt = "\n".join(lines)
	return (reply_txt,pic,time,link,author)

def finalize_feed(feed:dict,route:str):
	msg, img, pub_time, link, author = process_feed(feed,route)
	local_imgs = []
	for i in range(len(img)):
		local_imgs.append(get_image(img[i],route,i))

	# More than 1 Image is vertically concatenated
	if len(local_imgs) > 1:
		final = cv2.vconcat([i[0] for i in local_imgs])
		pic_loc = os.path.join(pic_cache_dir,f"{route}Final.jpg")
		cv2.imwrite(pic_loc, final)

	# If there's only one image, just set that as the image
	elif len(local_imgs) == 1:
		pic_loc = local_imgs[0][1]

	# If there's no image, directly return the msg
	else:
		return ((msg,pub_time,link,author),None)

	# If there is image,return the msg and the picture location
	return ((msg,pub_time,link,author),pic_loc)

def test_rss_feed():
	global feed_data
	biliID = "404145357"
	rss = requests.get(hub + routes['biliDynamic'] + biliID)
	listjson = xmltodict.parse(rss.text)
	feed = listjson['rss']['channel']['item'][0]
	print(feed)

	old_listjson = listjson
	old_listjson['rss']['channel']['item'].pop(0)

	feed_data = {"biliDynamic404145357":old_listjson}
	check_rss('biliDynamic',"404145357")
