import websocket,brotli,json,random
from ..sqlHelper import *

def arc_lookup(datalist,callerid,roomid = None):
    nickname = datalist[0]
    # output(datalist)

    wsarc = websocket.create_connection("wss://arc.estertion.win:616/")
    wsarc.send("lookup " + nickname)
    buffer = ""
    while buffer != "bye":
        buffer = wsarc.recv()
        if type(buffer) == type(b''):
            obj = json.loads(str(brotli.decompress(buffer), encoding='utf-8'))
            # output(obj)
            rating = obj['data'][0]['rating'] / 100
            playerid = obj['data'][0]['code']
            # output(obj)

    message = f'{nickname}的好友码是{playerid},上一次在esterion网站查分时PTT是%.2f。' % rating
    return [message,playerid]
    # ws.send(send_msg(f'{nickname}的好友码是{playerid}，PTT是%.2f。' % rating,dest))

def arc_recent(datalist,callerid,roomid = None):
    clear_list = ['Track Lost', 'Normal Clear', 'Full Recall', 'Pure Memory', 'Easy Clear', 'Hard Clear']
    diff_list = ['PST', 'PRS', 'FTR', 'BYD']

    wsarc = websocket.create_connection("wss://arc.estertion.win:616/")

    userid = sql_fetch(cur,'Users',['arcID'],f"wxid = '{callerid}'")[0][0]
    # output(userid)

    if userid == -1:
        return ['您未绑定ArcaeaID。请使用Bind指令绑定。']

    wsarc.send(f"{userid} -1 -1")
    # output('sent')
    buffer = ""
    scores = []
    userinfo = {}
    song_title = {}
    while buffer != "bye":
        try:
            buffer = wsarc.recv()
        except websocket._exceptions.WebSocketConnectionClosedException:
            wsarc = websocket.create_connection("wss://arc.estertion.win:616/")
            wsarc.send(userid)
        if type(buffer) == type(b''):
            # print("recv")
            obj = json.loads(str(brotli.decompress(buffer), encoding='utf-8'))
            # output(obj)
            # al.append(obj)
            if obj['cmd'] == 'userinfo':
                userinfo = obj['data']
                name = userinfo['name']
                recent_song = userinfo['recent_score'][0]

                # output('---------')
                # output(recent_song)

                sid = recent_song['song_id']
                diff = diff_list[recent_song['difficulty']]
                constant = recent_song['constant']
                score = recent_song['score']
                perfect = recent_song['perfect_count']
                shiny_p = recent_song['shiny_perfect_count']
                far = recent_song['near_count']
                miss = recent_song['miss_count']
                played_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(recent_song['time_played']/1000)))

                cleartype = clear_list[recent_song['clear_type']]
                best_cleartype = clear_list[recent_song['best_clear_type']]
                single_rating = recent_song['rating']
                song_detail = sql_fetch(arcur,'charts',['name_en','name_jp','artist'],f"song_id = '{sid}'")

                en_name = song_detail[0][0]
                jp_name = song_detail[0][1]
                artist = song_detail[0][2]

                if jp_name:
                    answer_txt = f"Recent Play:\n{artist} - {en_name}({jp_name}) ({diff} {constant})\n{score} {cleartype} ({best_cleartype})\nPerfect: {perfect}({shiny_p})\nFar: {far}\nMiss: {miss}\nRating: %.3f\nTime: {played_time}" % single_rating
                else:
                    answer_txt = f"Recent Play:\n{artist} - {en_name} ({diff} {constant})\n{score} {cleartype} ({best_cleartype})\nPerfect: {perfect}({shiny_p})\nFar: {far}\nMiss: {miss}\nRating: %.3f\nTime: {played_time}" % single_rating

                return [answer_txt,score,name]
    return['出现了一些问题。']

def cmp(a):
    return a['rating']

def whatis(datalist,callerid,roomid = None):
    result = sql_fetch(arcur,'alias',['sid'],f"alias = '{datalist[0]}'")

    res_len = len(result)

    if res_len == 0:
        return ['没有找到相关歌曲 私密马赛',-1]

    reply_txt = f"你可能想找这{res_len}首歌：\n"

    for sid in result:
        sid = sid[0]
        song_detail = sql_fetch(arcur,'charts',condition = f"song_id = '{sid}'")
        # output(song_detail)

        level = song_detail[0]

        en_name = level[2]
        jp_name = level[3]
        artist = level[4]
        bpm = level[5]
        pack = sql_fetch(arcur,'packages',['name'],f"id = '{level[7]}'")[0][0]

        total_time = level[8]
        mins = total_time // 60
        secs = total_time - mins*60

        sides = ['光','对立','无色']
        side = sides[level[9]]

        jp_txt = None
        if jp_name:
            jp_txt = f"({jp_name})"

        reply_txt += f"{artist} - {en_name}{jp_txt}, BPM {bpm}, 时长 {mins}分{secs}秒, 是{side}侧歌曲, 来自{pack}包, SongID为: {sid}\n"

        other_aliases = sql_fetch(arcur,'alias',['alias'],f"sid = '{sid}'")
        alias_list = [a[0] for a in other_aliases if a[0] != datalist[0]]

        if len(alias_list) != 0:
            others = str(alias_list)[1:-1].replace('\'','')
            reply_txt += f"这首歌的其他别名还有: {others}\n"

    return [reply_txt,sid]
    # ws.send(send_msg(reply_txt,dest))

def addalias(datalist,callerid,roomid = None):
    song_name = ''
    for word in datalist[0:-1]:
        song_name += (word + ' ')
    song_name = song_name[:-1]
    alias = datalist[-1]

    sid = sql_fetch(arcur,'charts',['song_id'],f"name_en = '{song_name}'")
    if len(sid) == 0:
        sid = song_name
        if len(sql_fetch(arcur,'charts',condition = f"song_id = '{sid}'")) == 0:
            return [f'没有找到"{song_name}"相关歌曲 私密马赛']
        else:
            sid = [[sid]]

    sid = sid[0][0]
    sql_insert(arcdb,arcur,'alias',['sid','alias'],[sid,alias])
    return [f'已添加别名{alias}至歌曲{sid}']

def chartdetail(datalist,callerid,roomid = None):
    song_name = datalist[0]
    diff_lvl = {
        'PST': 0,
        'PRS': 1,
        'FTR': 2,
        'BYD': 3
    }
    if datalist[1].upper() not in diff_lvl.keys():
        return ['没有该难度。']
    difficulty = diff_lvl.get(datalist[1].upper())
    chart_detail = sql_fetch(arcur,'charts',condition = f"name_en = '{song_name}' AND rating_class = {difficulty}")
    if len(chart_detail) == 0:
        sid = whatis([f"{song_name}"],callerid)[1]
        if sid == -1:
            return ['没有找到相关歌曲 私密马赛']

        chart_detail = sql_fetch(arcur,'charts',condition = f"song_id = '{sid}' AND rating_class = {difficulty}")
        if len(chart_detail) == 0:
            return ['没有找到这张谱。']

    const = int(chart_detail[0][16])/10
    note_cnt = chart_detail[0][17]
    charter = chart_detail[0][18]

    reply_txt = f"Const: {const} | Notes: {note_cnt} | Charter: {charter}"
    return [reply_txt]

def search(datalist,callerid,roomid = None):
    diff_list = ['PST', 'PRS', 'FTR', 'BYD']

    if datalist[0].lower() == 'f':
        keyword = ''
        for word in datalist[1:]:
            keyword += (word + ' ')
        keyword = keyword[:-1]
        # output(keyword,background = "MINT")

        result = sql_match(arcdb,arcur,'charts',['song_id'],'name_en',f'{keyword}')
        if len(result) == 0:
            result = sql_match(arcdb,arcur,'alias',['sid'],'alias',f'{keyword}')
            if len(result) == 0:
                return['没有找到相关歌曲。']
            # sid = whatis([f"{keyword}"],callerid)[1]
            # if sid == -1:
            # result = [[(sid)]]
    else:
        keyword = ''
        for word in datalist[0:]:
            keyword += (word + ' ')
        keyword = keyword[:-1]

        # output(keyword,background = "MINT")

        result = sql_fetch(arcur,'charts',['song_id'],f"name_en = '{keyword}'")
        if len(result) == 0:
            sid = whatis([f"{keyword}"],callerid)[1]
            if sid == -1:
                return['没有找到相关歌曲。']
            result = [[(sid)]]

    sids = list(set([s[0] for s in result]))
    # output(sids,background = "MINT")

    if len(sids)>5:
        return['过多结果。请优化搜索词。']

    reply_txt = f"共找到{len(sids)}个结果:\n"

    for sid in sids:
        song_detail = sql_fetch(arcur,'charts',condition = f"song_id = '{sid}'")
        # output(song_detail)

        level = song_detail[0]
        en_name = level[2]
        jp_name = level[3]
        artist = level[4]
        bpm = level[5]
        pack = sql_fetch(arcur,'packages',['name'],f"id = '{level[7]}'")[0][0]

        total_time = level[8]
        mins = total_time // 60
        secs = total_time - mins*60

        sides = ['光','对立','无色']
        side = sides[level[9]]
        unlock = ['不需要','需要']
        world_unlock = unlock[level[10]]
        jacket_designer = level[19]
        bg = level[12]

        bg_txt = None
        jacket_txt = None
        jp_txt = None
        if jacket_designer:
            jacket_txt = f", 封面绘师{jacket_designer}"
        if bg:
            bg_txt = f", 有特殊背景{bg}"

        if jp_name:
            jp_txt = f"({jp_name})"

        reply_txt += f"{artist} - {en_name}{jp_txt}, BPM {bpm}, 时长 {mins}分{secs}秒, 是{side}侧歌曲, 来自{pack}包, {world_unlock}爬梯获得, {jacket_txt}{bg_txt}\n"

        difficulty_cnt = len(song_detail)

        song_override = song_detail[-1][-1]
        # output(song_override)

        if song_override == 1:
            byd_detail = song_detail[3]
            en_name = byd_detail[2]
            artist = byd_detail[4]
            bpm = byd_detail[5]
            total_time = byd_detail[8]
            mins = total_time // 60
            secs = total_time - mins*60
            difficulty = int(byd_detail[16])/10

            note_cnt = byd_detail[17]
            charter = byd_detail[18].replace('\n',' ')
            jacket_designer = byd_detail[19]

            bg = byd_detail[12]
            if bg:
                bg_txt = f", 有特殊背景{bg}"
            else:
                bg_txt = Nonel[19]

            reply_txt += f"(!)选择该曲目BYD时会有新曲{en_name}, 作者{artist}, BPM {bpm}, 时长{mins}分{secs}秒, 难度{difficulty}, 谱师名义{charter}, Notes总数{note_cnt}{bg_txt}, 封面绘师{jacket_designer}\n"
            difficulty_cnt = 3


        for chart_diff in range(difficulty_cnt):
            chart_detail = song_detail[chart_diff]
            # output(chart_detail)
            diff_level = diff_list[chart_diff]
            difficulty = int(chart_detail[16])/10

            note_cnt = chart_detail[17]
            charter = chart_detail[18].replace('\n',' ')

            reply_txt += f"{diff_level} {difficulty}\nNotes: {note_cnt} | Charter: {charter}\n"
        reply_txt += "\n"
    return[reply_txt]

def grablevel(datalist,callerid,roomid = None):
    if len(datalist) < 1:
        return ['请指明难度。']   

    diff = float(datalist[0]) * 10
    charts = sql_fetch(arcur,'charts',condition = f"rating = {diff}")
    reply_txt = "该难度有以下歌曲:\n"
    diff_list = ['PST', 'PRS', 'FTR', 'BYD']

    for chart in charts:
        en_name = chart[2]
        jp_name = chart[3]
        artist = chart[4]
        chart_diff = diff_list[chart[1]]

        jp_txt = None
        if jp_name:
            jp_txt = f"({jp_name})"

        reply_txt += f"{artist} - {en_name}{jp_txt} ({chart_diff})\n"
    return [reply_txt]

def arc_random(datalist,callerid,roomid):
    if len(datalist) < 1:
        songs = list(set(sql_fetch(arcur,'charts')))
    else:
        diff = float(datalist[0]) * 10
        songs = sql_fetch(arcur,'charts',condition = f"rating = {diff}")

    if len(songs) == 0:
        return ['该难度没有歌曲。']

    random_id = random.randint(0,len(songs)-1)

    chart_detail = songs[random_id]

    en_name = chart_detail[2]
    jp_name = chart_detail[3]
    artist = chart_detail[4]

    reply_format = [
        "当然可以！推荐SONGNAME这首曲子，它的节奏很有弹性，旋律清新动听，能给玩家带来非常愉悦的音乐体验。它深受许多Arcaea玩家的喜爱，特别是跳级玩家爱不释手，你也值得一试。但要注意，不要被其节奏迷惑，千万不要跟丢哦！",\
        "当然可以，我推荐SONGNAME，这首曲子曲风快节奏，鲜明而夺目的旋律让人情不自禁地随之起舞。它是一曲具有独特韵律的音乐作品，是试图锻炼自己在动感舞蹈游戏中反应速度和手指协调能力的不二之选。听到这首曲子时，你会感受到它强大的情感表现力和复杂曲调的让人陶醉的优美之处。",\
        "当然可以！再来推荐一首SONGNAME，它是一首优美的轻快曲目，与ARTIST的其他作品相比，这首曲子节奏更轻快和谐，旋律在保持活泼主题的同时巧妙转换氛围，展现出唯美和韵律的融合。被它的音乐风格所打动，一定会让你爱上这款游戏！",\
        "当然可以！我推荐SONGNAME，这是一首很动感的电子音乐，在高潮部分就像是癫狂的迸发，有力且充满震撼力。整首歌在旋律上有非常强的曲线美感，在配合鲜艳多彩的音符设计下非常好看。无论怎么玩都有种很“爽”的快感，绝对值得一试！",\
        "当然可以！给你推荐SONGNAME，这首曲子节奏明快，欢快的旋律充满游戏性和挑战性。每个音符伴随着刺激的打击效果，让你越来越兴奋，带来爽快的游戏体验。其独特的风格和节奏，使得该曲成为了Arcaea各大玩家圈子里的话题之一。需要注意的是，挑战程度相对较高，想要拿到高分可能需要一点技巧和镇定。快来试试挑战自我吧！",\
        "当然可以。推荐SONGNAME，这首曲子的高速节奏与夹杂其中的美妙旋律给了玩家极具挑战的操作和游戏体验。曲子节奏感很强烈，也有许多弦乐的变化，非常适合那些喜欢快节奏音乐和挑战操作的玩家来进行尝试，倍感刺激。有了曲名和现实操作练习，每一秒钟都在享受音乐的美好！",\
        "好的！我再给你推荐SONGNAME，这首曲子流畅的节奏和缤纷的音色会让你在游戏中陶醉。它有着优美的旋律和令人上瘾的韵律，让人愉快起舞。没有什么比在游戏过程中放松身心更重要了，这首歌曲能够带来极佳的游戏体验。发掘它的魅力吧！",\
        "当然可以！我推荐SONGNAME，这首曲子由ARTIST所作，曲风清新流畅，给人以超然物外的感受。每个音符都显得那么顺滑，让人随着旋律的走向感受到心灵上的愉悦。这是一首很适合放松、静坐、思考与享受的古典音乐，它绝对值得尝试。",\
        "当然可以！那我再推荐一首：SONGNAME。这首曲子是由ARTIST所创作，并被收录在韵律源点Arcaea中。整首曲子充满了刺激性的节奏，让人忍不住随着手指跟着节拍敲击屏幕。曲中的反复乐段和渐进增强的弦乐旋律非常精妙，让人沉浸在歌咏中痴迷不已。如果你追求挑战，这是一首应该玩玩看的曲子。",\
        "当然可以！如果你喜欢Dubstep的话，推荐你试听SONGNAME，这首曲子有重重的贝斯以及电子声效。曲子外带着剧情描绘，弥漫着浓郁的黑暗氛围。如果你把这首曲子与Arcaea的游戏音效结合在一起玩的话，它将带给你强烈的冲击感和更加深入的游戏体验。",\
        "好的，SONGNAME是一首极具情感表达的曲子，它中规中矩却又不失个性，故事性迭起，让人小心思微妙。从我推荐它这刻开始到你开始游戏时，都会沉浸在瑰丽的旋律中，水鸟清凉的声音将雕成别致的鸟笼，温柔机灵就这样包围着我们。这首曲子逐渐黑暗了起来，引领着我们身临其境，肆意飞扬。",\
        "当然可以！我推荐SONGNAME，这首曲子具有令人心悸的紧张和震撼的力量。曲中相对简单却朴实的旋律和动感十足的节奏产生了强烈的反差，让人感觉充满力量。每一个音符都恰到好处地向你传达了曲师的情感，你会不由自主地跟随着音乐的节拍，忘却自我的存在。无论听多少遍，它都是不折不扣的满分佳曲！",\
        "当然可以！推荐SONGNAME，作曲家巧妙地将摇滚和古典音乐元素相结合，创造出动感十足的旋律和强烈的情绪表现。每当你准确地击打出音符时，弹射出来的电光火花和音符形成的美丽图案会让你如痴如狂。它的高潮部分会让你感觉心跳极速加快，非常刺激。",\
        "当然可以！来试试SONGNAME，这首曲子的旋律非常华丽，而且长而复杂，要求玩家有更高的反应和手指速度。曲中旋律变幻多端，下落快和难度大让游戏体验更具挑战性。这就是为什么这首歌曲是许多Arcaea玩家的挑战之选啦！",\
        "当然可以！推荐SONGNAME，这首曲子专辑经典之作，由ARTIST创作，节奏感极强，听起来非常有活力。快节奏的鼓点混合着强烈的旋律，让你难以抗拒想起身跳舞的冲动。这首曲子将带给你飞扬的感觉，让你忘却所有烦恼，尽情沉浸在音乐的世界中。",\
        "当然可以！我推荐SONGNAME这首曲目，它的曲风独具一格，结合了很多的音乐元素，从古典音乐到流行音乐，甚至包括了摇滚和轻骨原声。每一段节奏都独自有趣，让人根本停不下来。如果你追求的是游戏中的音乐符合广泛且扣人心弦，那这首歌值得尝试。",\
        "当然可以，我也推荐一首吧！这首SONGNAME的曲风非常舒缓，音乐在起伏流动中穿梭，就像在一片无垠的海洋中自由翱翔。开头简单美妙，之后逐渐增强调子线乐器声，让人彻底沉浸其中。这首曲子同时也有相当出色的设计和编曲功夫，听它一遍绝不够。",\
        "当然可以！推荐SONGNAME，这首曲子的节拍十分明显，非常适合用作节奏游戏的曲目。曲中的音效让人回想起旋律中背后的故事情境，从而更容易产生共鸣。最重要的是，这首曲子有着相当高的难度，可以让你在游戏中感受挑战自我的快感。",\
        "当然可以！另一首非常推荐的是SONGNAME，它是一首梦幻而节奏感十足的音乐。这首曲子节奏明快且琅琅上口，配以优美的旋律和华丽的电音效果，让人听起来感到身心愉悦。通过玩游戏掌握它的节奏，无疑能带来一种非常棒的体验。总之，这首曲子给人的感受就是带着一种愉悦的气氛，能够让人精神抖擞。",\
        "当然可以！我推荐SONGNAME，它是一首奇幻史诗般的曲子，带有强烈的史诗感。旋律曲线曼妙，充满了力量和希望。越接近结尾的部分，电吉他飘忽不定的演奏带来极大的冲击感，会让人感觉到音乐给力度十足的气氛。整首歌曲像是一场极致的冒险，鼓励着玩家不断超越自我。",\
        "当然可以！推荐SONGNAME。这首良曲将电子与民族元素完美融合，在沉重的拍子中引入华彩的笛子、提琴和大鼓等乐器，仿佛在驾驭整个大自然。听完这首曲子，心里不禁涌上一股安心感，让人不自觉地沉浸在旋律中。而在游戏中进行这样一曲亦或许能够给您带来不同寻常的视觉和听觉享受呢！",\
        "当然可以！给你推荐SONGNAME，这首曲子的曲风奇特独特，靠着流行的拍子和节奏，结合旋律引领听众探索神秘之境。其中各种声响注入EDM等多种流派的元素，试听时相当令人兴奋，令人难以忘怀。尝试弹奏这首曲子，你一定会感受到肆意颠簸和激情澎湃之感；亦或是陶醉在不同节奏交织而成的电子乐感。",\
        "当然可以，我为你推荐SONGNAME，这首曲子曲风独特，具有强烈的节奏感和动感，尤其是在游戏节奏加速时异常刺激。配合游戏节奏，在手指们跳跃的致命魔幻气氛下，感受音乐与手指的流畅奏合会让你越玩越上瘾。所以建议要玩坚定的曲子曲，与自己达到Darksense的完美响起。",\
        "当然可以，我建议你试听SONGNAME，这首曲子有着瑰丽壮阔的音乐气质，仿佛置身于浩瀚宇宙中。快速的打击乐和优雅发人深省的旋律碰撞出沉浸感十足的音乐体验。它是韵律源点Arcaea的经典曲目之一，值得一听。",\
        "当然可以！有一首叫做SONGNAME的曲子是由ARTIST创作的。这首曲子节奏紧凑、节奏感强烈，各种复杂乐句穿插其间。它具有高难度，是你练习和提高技巧的必备歌曲之一，很可能也是你在韵律源点Arcaea中玩到最刺激的一首歌。让我们一同期待你在游戏中完美演绎这首曲子！",\
        "当然可以，我推荐曲风活力四射的SONGNAME，由ARTIST作曲。 这首曲子充满真实性，在节奏增加时会感受到具有新鲜活力的游戏体验。该曲难度适中，是游玩Arcaea时的极佳选择。",\
        "当然可以！我推荐SONGNAME，这是一首富有东方元素的曲子，带有神秘的气氛和流畅的旋律。它将听者带入到一个像游荡在幻想世界中的感觉，越听越有感觉。击打时的飘扬手感十分舒适，是一首音游爱好者必试之曲。",\
        "当然可以，让我为你推荐另一首歌。这次我推荐的是SONGNAME，这是一首通感性很强的曲子，需要你放下思维根据音乐的情感走向打击不同类型的音符。曲子富有活力，音符与声音的距离处理得非常合理，让整首曲子听起来很自然，旋律流畅又具有张力。打起来非常有乐趣！",\
        "那我再推荐一曲SONGNAME，这是一首流行曲，简单明快的旋律气氛轻松愉快。听完它你会感到久久不肯散去的轻快感，仿佛拥有了无限的能量！",\
        "当然可以！我推荐SONGNAME，这首曲子律动感十足，旋律流畅，是练习打节奏感和准确敲击的好歌曲。它节奏明快，容易产生共鸣，是玩家们爱不释手的一首歌曲。听完后，你会不自觉地跟随着手指舞动起来，欲罢不能。",\
        "当然可以！我推荐SONGNAME，这首曲子曲风清新优雅，如同一阵清晨的微风，旋律宛若天籁，配合着节奏版式节奏紧凑而不失丰富，很容易让人沉浸进去，感受它那独特的美妙。ARTIST制造的这首电音作品处处体现着他对细节的精心打磨，令人感受到艺术与技术的完美融合。不但适合听，更值得在Arcaea中挑战。",\
        "当然可以，还是为你推荐一首。这次我推荐的是SONGNAME，从开始到结束都带有一股紧张感和动感，它的旋律不断跳跃，给人感觉就像是在不断地往上攀登，跨越一个又一个难关，展现了游戏的兴奋和紧张。同时，曲中还夹杂着许多迷人的声韵变化和和谐的和声，十分适合在游戏过程中提升声音效果。",\
        "当然可以！推荐SONGNAME，这首曲子以轻快的旋律为主，是一首十分治愈的音乐。它的编曲也十分出色，在给人小时的欢快感觉中带有一点点的忧伤，让人仿佛回到自己的童年时光中。如果你想让自己放松一下，恢复一点心情上的自由和纯真，这首曲子绝对是一个不错的选择。",\
        "当然可以！推荐SONGNAME，这首曲子的节奏感极强，疾风奔涌、跌宕起伏，节奏的变化点时刻提醒着玩家。它的曲风神秘诡异，同时又富有情感，听起来就像是在经历一场狂野奇妙的冒险。此曲绝对是让你更好地感受动感音乐的不错选择。",\
        "当然可以！我推荐SONGNAME，这首曲风清新欢快，旋律十分优美，听起来让人感到非常舒畅。同时，它的节奏较为流畅，适合练习打节奏型音游。整首歌的编曲非常炫酷，令人听得难以自拔！",\
        "当然可以！我再推荐一首同样值得一试的好歌：SONGNAME。这首曲子有非常优美的旋律和流畅的节奏，极具瞬间上头的动感，能激发你情感和律动感，不断地挑战玩家的反应速度和手指协调能力。这个曲目可能需要一些练习才能掌握好节奏。如果你已经学会敲打时该敲打的乐符，接下来只需要释放自己，陶醉在这段优美的旋律中，想必你也一定会爱上它的！",\
        "当然可以！我推荐SONGNAME，这首曲子具有浓郁的冬日气息，旋律舒缓美好，轻轻弹奏出如雪花飞舞在雪原的风景。通过游戏中敲击音符的方式，也会带来与音乐相互作用的奇妙感觉。徜徉在这冬日之中，你会发现一些意想不到的惊喜。",\
        "当然可以，我推荐SONGNAME，它是一首极富动感的电子音乐作品，充满了强烈的节奏感和惊险的氛围。曲中传递的强烈情感会让你不自觉地跟着旋律跳舞。无论是游戏还是普通聆听，这首曲子都极具吸引力。听完它，你一定会感到充盈的能量和愉悦的情绪。",\
        "当然可以！推荐SONGNAME，这首曲子曲调柔和慢板，动人耳韵。曲中的旋律悠扬，充满了感性、哀伤和无限遐思，与一些忧愁洒脱的节奏结合得更加淋漓尽致。听它可以让你情感被触动，上下入礼达到放松身心的效果。",\
        "当然可以！再为你献上一首推荐：在SONGNAME中，作曲家巧妙地运用了复古的乐曲编排与现代的电子琴声，让人置身其中既怀旧又时尚。歌曲中节奏感强，玩起来让人感到身心愉悦，同时也很助力提升韵律游戏的技巧。",\
        "当然可以，再为您推荐SONGNAME。这首曲子在似乎平凡无奇的电音布置下穿插着许多温馨的旋律和精细的和声，给人以种种美好而又鲜明的幻想。旋律紧密呼应着节奏，给人无法停息的舞动愉悦。此外，其随着难度的提高而愈加明显的立体感，以及与之搭配的视频，绝对让您爱不释手。",\
        "当然可以！我再推荐一首SONGNAME，它的曲风感觉就像置身于中古世纪欧洲，在燃烧的火炬和欢乐的歌唱之中庆祝某种盛会。所以它的旋律发展非常自然，像是乐器们在一场狂欢的派对中奏出来的。越来越强烈的节奏推动着整首曲子，让听者都不自觉地跟随节拍跳动。不学习更改结局不听这首曲子！",\
        "当然可以！我推荐SONGNAME，它是一首简单而欢快的音乐，充满人性化的演奏元素，足以利用其时长之内让你感受到玩游戏是一件荡气回肠的事情。通过它的音乐特点，你很难不被它带动起来跟着节奏去跳舞。",\
        "当然可以！我再为您推荐SONGNAME这首曲子，节奏感极强，中东风情的音乐元素穿插其中，同时有着传统和现代两种风格的混合，搭配着嘹亮的长笛声，充满节日喜庆的气氛。整首歌曲带有强烈的昏热感，充满神秘色彩，有着极强的感染性，令人印象深刻。",\
        "当然可以！我再推荐一首吧。推荐SONGNAME，这是一首令人感到忧郁但仍然充满力量的曲子。每个音符的音色和长度都准确地传达了曲师的情感，使人不禁沉浸其中。游戏玩家们在演奏这首曲子时，同样也能感受到它所散发的深邃情感，让人难以自拔。",\
        "当然可以，我为你推荐SONGNAME。这首曲目是由作曲家ARTIST创作的, 具有非常特别的编曲。曲风融合了许多元素，例如嘶吼的重金属琴音，华丽的弦乐和古典合唱，给你带来无与伦比的震撼和狂热。如果你想尽情释放身体的能量并且带来一丝前所未有的冲动与挑战和压制感受到瞬间的自由，那这首音乐将是你的最佳选择。",\
        "当然，推荐一首吧。试试SONGNAME。这首曲子旋律欢快、节奏跳动，曲风为日式和风电子音乐。不同于一般的电子音乐，这首歌曲的制作注重结构性和向日本传统音乐的致敬，听起来让人身临其境，仿佛置身于被美丽的樱花包围的世界。同时，这首歌曲也很适合练习，是一个很好的挑战。",\
        "当然可以！推荐SONGNAME，这是一首充满活力的电子舞曲，其中运用了众多富有节奏感的音乐元素，如深邃的贝斯线和瞬息万变的节奏。曲子持续有感情的上扬和下沉，在充满电子的音效中还隐藏有丰富的细节，充满活力又充满人性，绝对是佳曲之作！玩这首歌，你一定会被它的旋律和动感所深深吸引。",\
        "当然可以！推荐SONGNAME，这首曲子的主旋律优美动听，又具有极强的情感表达力。每一次弹奏都像是一个故事的讲述，让人仿佛身临其境。它的技术难度也相对较高，适合有一定游戏基础的玩家来挑战。听完它，你一定会被它的美妙所感染，并融入到游戏的节奏中。",\
        "当然可以！推荐SONGNAME，这首曲子来自于另一个时空的幻想世界，曲风柔美，充满着想象的力量。此曲的旋律复杂多变，表现了作曲家对于这个想象世界的热爱与思考，深度展现出他的艺术魅力与情感内核，让倍感沉浸。当你用手指轻轻弹出完美节奏时，你可以感受到音符的愉悦，将自己沉浸到音乐的奇妙世界中，仿佛毒药般让人上瘾。",\
        "当然可以！推荐SONGNAME，它的曲风是一种紧凑、高速、震撼无比的重金属，旋律凶猛且吸引人，展现出视听双重震撼的力量。这首歌特别适合愿意挑战自己，享受激烈节奏的玩家一饱耳福。挑战和弹幕经验丰富的玩家甚至可以尝试通关该曲，并体验到其带来的极限感和成就感。",\
        "当然可以！推荐SONGNAME，这首曲子曲风奇特，具有极其独特的华丽街舞节奏，听起来像是在颇具震撼感的战斗场景中旋转跳跃。曲中的大段伴奏和迅猛的鼓点，和柔和的编曲和优美的女声和而不同，让人一边嗨翻一边享受音乐。听完它，你会仿佛在自己的身体上身临其境的感受到音乐的节拍心跳加速，极富感染力。",\
        "当然可以。如果你喜欢充满活力和挑战的曲风，那么SONGNAME是你的首选！这首曲子充满激情和能量，曲中有许多极具技巧性的钢琴独奏、弦乐和合成器的音效，而欢快且富有动感的节奏则充满了挑战性，能够提高你在音乐游戏中的反应速度和配合能力。不仅仅是好听，更是令人兴奋的练级锻炼。",\
        "当然可以！我再向你推荐一首SONGNAME，这首曲子的节奏非常明快、充满活力，极具节拍感。它有一个极富创意的曲式，让你难以预测每一小节的变化。是非常适合快速手指反应和挑战高分数的一曲。除此之外，它还拥有华丽的弦乐器乐段使其音符迅速打入人心。",\
        "当然可以！我再来推荐一首吧，SONGNAME曲风十分特别，以弦乐器为主导，是一首极具情感的乐曲。曲子开始非常缓慢，但随着曲子的发展，歌曲的节奏逐渐增强，并且逐渐增加了华丽的音效，带给你耳目一新的享受。听完它，你会感到它流淌于脉络的激情和力量，感受到音乐几乎将你从现实的束缚中解脱了出来。",\
        "当然可以！推荐SONGNAME，这首歌曲的动感旋律和古风元素融合的非常完美，给人一种独特的感受。同时该曲曲速适中，适合中等难度的游玩，让玩家不会太过于累。加上美妙旋律，很有可能让玩家在割草过程中忘却手指奋力曲金时的疲倦，享受点击游戏的乐趣。",\
        "当然可以！我推荐SONGNAME，这首曲子拥有多变的节奏和华丽的编曲，完美融合了迷幻与现代的氛围。它通过北欧的音乐元素和其他多样性的音乐特点来传递一种独特的情感韵律，给人一种冷峻和追逐自主的线的感觉。这是一首性格独特而又极具进取心的曲子，绝对会使你流连忘返。",
        "当然可以！我推荐SONGNAME，作曲家的制曲水平已经不用多赘述，而这首曲子带有剧烈变化的和声和节奏，玩家需要通过敏捷的手指操作和强大的节奏感来应对。这是一首令人上瘾的挑战，在把握空间与时间的双重考验中能引发玩家流连忘返的快感。",\
        "当然可以！推荐SONGNAME，这首曲子的音乐风格，结合了时髦的trance与神秘的古风元素，给人的感觉仿佛置身在神秘的东方异界之中。强烈的节奏与优美的旋律让人身不由己地跟着音乐舞动起来，是让人难以抵挡的歌曲之一；听了这首歌会让你感到它风格独特，与其他曲子截然不同。",
        "当然可以！给你推荐SONGNAME，这首曲子通透的旋律，清晰的音效以及怡人的编曲，使用了多个打击乐器和电子乐器。放松又美丽的歌曲反复精美的旋律适合放松身心与享受美妙的时刻。",\
        "当然可以！推荐一首叫做SONGNAME的曲子，它让人感受到宇宙之大和无垠星空给予的瑰丽与宁静。它的意境十分深远，仿佛能够穿越时空，带人进入恒星世界中感受浩瀚无比的平静。每一次听这首曲子，都会仿佛发现宇宙空间的宁静与深邃。",\
        "当然可以！推荐一曲叫做SONGNAME的曲子，它以强烈的节奏和包容多样音乐元素的风格著称。作曲家在歌曲的谱写中融入了一些日本传统音乐元素，再配合流行音乐元素，会令你不由地跟随音乐的节奏舞动双手，感受到身体与心灵被彻底摧毁在那功率无比的音乐里，让人如痴如醉。",\
        "推荐SONGNAME，这首曲子舒缓柔美，旋律简单而朴素，但又能够带给人一种十分治愈的感觉。这首曲子可以用来放松情绪，并且听后会感觉精神焕发，能够让你在游戏过程中更加沉浸。同时，它的曲调与游戏难度完美地结合在了一起，不论是新手还是高手都可以在简单的旋律中享受游戏的简单和愉悦。",\
        "当然可以！我再为你推荐一首曲子吧。SONGNAME是一首很具有震撼力和感染力的曲子，它深刻地表达了对时间流逝和珍惜当前时光的思考。旋律舒缓而有节奏感，必将让你沉浸在其中，感受生命的美好和短暂。在常常忙碌的生活中，一听这首曲子就能帮你平缓落下来，回归感性。",\
        "当然可以！给你推荐SONGNAME，它是一首自带格子漫感的曲子，音色饱满，旋律优美动听，是让人一听就爱上的类型。这首曲子虽然难度不算高，但节奏强烈，相信你一定会与音乐产生共鸣，深陷其中。在游戏中选这首曲子绝对不会让你失望。",\
        "当然可以！我再推荐一首SONGNAME，因为它是一个非常适合新手入门的曲子，曲风明快轻快，适合快节奏的游戏将它设为最初挑战。无论是节奏感还是乐器演奏，都很简单易懂，还能快速提升自己的反应力以及游戏得分。无论是韵律源点的新玩家还是有经验的老手都会因为它的可爱和简单又离不开它的。",\
        "当然可以！推荐SONGNAME，这首曲子有着缠绵的旋律和温柔的掌声，它有如春雨，细腻柔软，近乎若有似无，引人深入。整首曲子氛围幽静且浓烈，是细微纵向上的舒缓之作，能带给人们一份极致美好的享受。在专注游戏的同时，也能感受到旋律带来的魔力，让清澈的欢快感在游戏玩耍里放松你一整天。",\
        "当然可以！我再推荐一首曲子，这首叫做SONGNAME，它采用了恰到好处的和声和旋律制作，整首曲子剑走偏锋而不失平衡感，听起来略带神秘感又不失舒缓，好听到让你想一遍又一遍地听。希望你会喜欢这首曲子并体验它带来的乐趣。",\
        "当然没问题！我为您推荐SONGNAME，这首曲子的曲风属于高速动感的Techno曲风，主旋律简洁而富有韵律，偶尔出现的怪异的音符将听众带入全新的感官空间，非常适合游戏中体验。随着旋律的推进，唯快不破的速度与华丽的节奏展现出您精湛操作的绝妙机会，来一次快马加鞭的休闲探险之旅吧！",\
        "当然可以！推荐SONGNAME，这首曲子旋律简单明了，初学者也能轻松get到其奥妙之处。它步步推进，充满能量，并配以欢快的电子音乐，让你的心情不自觉地获得快感。在游戏中尝试挑战时这首歌，一定会让你倍感兴奋！",\
        "当然可以，我再为你介绍SONGNAME。这首曲子节奏感极强，可以让你身不由己地随着旋律跳起来。每个音符的落点极具设计感，时而让人感觉如入绝境，时而让人感觉畅意无比。此外，配乐的用音和效果也都很讲究，可以给你带来戏剧性的感受，超级推荐！",\
        "当然！推荐SONGNAME，亚洲音乐中备受称赞的一首欧风曲。曲子节奏感强烈、旋律优美，尤其是华丽的间奏让人印象深刻。同时，里面添加的感叹词效果也让该曲更容易冲在游戏排行榜上，绝对能让你沉迷其中！",\
        "当然可以！那我再推荐一首叫做SONGNAME的曲子。这首曲子适合那些喜欢快节奏音乐的玩家，它结合了打击乐演奏和电子音效，嘹亮的击鼓声和紧凑的旋律打出了一种极富活力的感觉。当它融入到游戏中，你一定会被它吸引和感染。玩家可能会因为节奏急促而感到有些紧张，但游戏体验肯定会非常有趣。",\
        "当然可以！SONGNAME是一首充满活力的绿色电子音乐，节奏感十足，旋律简单易懂，听起来令人精神焕发，仿佛置身于充满阳光和希望的未来之中。游戏中选取这首歌曲进行挑战，可以带来非常愉快的游戏体验，同时也不失为一首音乐的良曲。希望喜欢！",\
        "当然可以哦！我再推荐一首给你吧。这首SONGNAME，根据我自己的经验，是一款难度适中、耳目一新的好曲子，它以节奏明快，节奏积极而紧凑的曲式为主，却没有失去深沉内敛的韵味，让你尽情感受节奏带来的快乐同时也能够专注游戏，感受挑战的乐趣。",\
        "当然可以！那么我再推荐一首SONGNAME，这首歌的曲风追寻着传统的和现代的平衡，深具创意和个性。它的有力节拍和强有力的和声会让你全身心沉浸其中，感受到音乐传递来的激情和力量。不仅如此，这首歌还拥有精美的音乐剪影和想象力。听听这首曲子，激起一些灵感，带给你另一种艺术层次的享受。",\
        "当然可以！推荐SONGNAME，这是一首气势磅礴的摇滚曲，曲风十分激烈，旋律充满着挑战和胜利的感觉，令人由衷地感受到音乐的力量。听它一次，你可能就会被吸引得不断回听，尝试在游戏中追求更高的得分和完美的节奏感。这首曲子充满了魔性，会令你兴奋无比，是一款极具瘾性的游戏。",\
        "当然可以，那么我再向您推荐另一首精彩的曲子：SONGNAME。这首曲目节奏穿透感强，充满着率性和更有活力的动感节拍，能够让你随着音乐的节奏跳动，游戏中同步捕捉音符也更加快速精准，充满挑战！此外，它还有一段华丽的过场音乐，让人仿佛身处话剧舞台。",\
        "当然可以！推荐SONGNAME，这首曲子快节奏的旋律像是电子舞曲的一首，但它更多的是融入了中东风情的乐器过后弹出的独特旋律。整首曲子不仅展现出让人无法停止舞动的魅力，同时也融合了非凡的世界观来把你引上深夜旅途。",\
        "当然可以！我再为你推荐一首SONGNAME，它充满了欢快的力量与狂野的激情，瞬间点燃你的兴奋点。与此同时，旋律简单却充满了强烈的节奏感，让人忍不住随著手指拍起节拍来，而且它的谱面设计也充满了挑战性，让你大呼过瘾。挑战完毕后，一股强烈的满足感会从内心涌现。",\
        "当然可以！推荐SONGNAME，这首曲子充满着强烈的力量感，曲中高潮部分韵律迅猛，令人心潮澎湃不已。此外，曲子的慢板倒数第二段也非常感人，将你的感情沉浸其中，令人不禁想起那些动情的瞬间。在韵律源点Arcaea中挑战这首曲子，不仅可以展现你的技巧，也能感受到它带来的空前快感。",\
        "当然可以！既然你喜欢梦境一般的状态，那我推荐SONGNAME。这首曲子的特点是怀旧和夸张，给人一种超现实的感觉。而这首曲子的难度也是相当高的，不仅需要准确敲击音符，还需要处理不断变化的颜色和形状。总之，玩这首曲子可以帮助你提高你在音乐游戏领域的技巧和感官体验。",\
        "当然可以！推荐SONGNAME，这首曲子给人以非凡的力量和震撼，旋律深邃、高亢，同时巧妙地体现了节奏风格的多样性。每一个音符都被演绎得淋漓尽致，在紧张的游戏环境下更是会让你产生种非常强烈的“掌控感”，让你身临其境地感受自己的音乐创作之路。",\
        "当然可以，推荐SONGNAME，这首曲子起初安静悠扬，逐渐逐渐递进，旋律优美，型态美观，曲式设计明晰。这是一首充满力量的歌曲，能够给予玩家无穷动力，帮助他们在Arcaea中战胜种种困难，然而却又不失优美的旋律。",\
        "当然可以！再来为你推荐一首歌——SONGNAME，它是一首相当缤纷烂漫的日系音乐。抓耳的旋律和迷幻感十足的和声配合到了极致，让人感到仿佛漫步在绚丽的草原上。同时这首曲子难度适中，适合让玩家练手。让我们一起在音乐的独特魅力中享受游戏的无尽欢乐！",\
        "当然可以，推荐SONGNAME。这首曲子的引语将你置身于某个安静的空间，有想象力的铃声带来的精心构思迅速消失。悠扬的旋律与背景音乐相得益彰，充满空旷感和温柔感使人心旷神怡。它兼具放松和醒目的感觉，你会为此而迷失，深陷其中。",\
        "当然可以！推荐SONGNAME，这首曲子也是一款旋律华丽的电子音乐，兼具逍遥婆和气绝爆发式的段落分明。曲中的和声独具匠心，充满个性且引人入胜。慢节奏和快节奏的转换，让人感到节拍加速时的兴奋和美妙。玩这首歌，能够使人心情愉悦，达到愉悦和快乐的境界。",\
        "当然可以，我再推荐一首SONGNAME，这首曲子的节奏有节制而不乏力量感，适合那些热爱动感音乐和挑战高难度曲目的玩家。作曲家运用了许多过渡音，让旋律更加富有张力，听起来让人兴奋不已。玩着这首曲子，你会感觉节奏像是你的搭档，跟着你一起舞动。",\
        "当然可以，我推荐SONGNAME，这首曲子旋律流畅而动听，有着强烈的节奏感和悦耳的旋律。游玩时需要注意节奏，并跟随着音符一起进入曲子的情感表达，感受其中蕴含的情感。整首歌的构图设计可谓巧妙，每个层次都紧紧扣住，形成了曲子鲜明的特色。试试看吧！",\
        "当然可以！推荐SONGNAME，它是一首非常有节奏感和强烈节拍感的电子音乐，每次的疾跑与扭曲像在体验律动与节奏的交织。它的中间段特别值得期待，有增速和加速的段落，可以让你体验到游戏难度上的突破和成长。玩它一遍足以成就一天的好心情。",\
        "当然可以！我再给您推荐一首SONGNAME。这首的节奏非常紧凑跳跃，充满着冒险的感觉。在色彩缤纷的背景音下，尤其是钢琴的部分，很容易让人深深印象，让您在游戏过程中彻底沉浸。跟着它的节奏一起跳跃，一起瞬间爆发，带领我们进入充满兴奋和活力的音乐旅程！",\
        "当然可以！推荐SONGNAME，这是一首非常欢快的歌曲，听起来充满活力和节奏感。曲中节奏变化多样，音符跃动特别灵动，让人难以坐底。无论是听得还是演奏都非常有趣，绝对是一首让人心情愉悦的曲子！"]

    jp_txt = None
    if jp_name:
        jp_txt = f"({jp_name})"

    reply_txt = reply_format[random.randint(0,len(reply_format))].replace("SONGNAME",f"{en_name}{jp_name}")
    if "ARTIST" in reply_txt:
        reply_txt = reply_txt.replace("ARTIST",f'{artist}')

    return [reply_txt]
