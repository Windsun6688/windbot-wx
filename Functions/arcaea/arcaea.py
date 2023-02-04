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

                cleartype = clear_list[recent_song['clear_type']]
                best_cleartype = clear_list[recent_song['best_clear_type']]
                single_rating = recent_song['rating']
                song_detail = sql_fetch(arcur,'charts',['name_en','name_jp','artist'],f"song_id = '{sid}'")

                en_name = song_detail[0][0]
                jp_name = song_detail[0][1]
                artist = song_detail[0][2]

                if jp_name:
                    answer_txt = f"Recent Play:\n{artist} - {en_name}({jp_name}) ({diff} {constant})\n{score} {cleartype} ({best_cleartype})\nPerfect: {perfect}({shiny_p})\nFar: {far}\nMiss: {miss}\nRating: %.3f" % single_rating
                else:
                    answer_txt = f"Recent Play:\n{artist} - {en_name} ({diff} {constant})\n{score} {cleartype} ({best_cleartype})\nPerfect: {perfect}({shiny_p})\nFar: {far}\nMiss: {miss}\nRating: %.3f" % single_rating

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

        if jp_name:
            reply_txt += f"{artist} - {en_name}({jp_name}), BPM {bpm}, 时长 {mins}分{secs}秒, 是{side}侧歌曲, 来自{pack}包, SongID为: {sid}\n"
        else:
            reply_txt += f"{artist} - {en_name}, BPM {bpm}, 时长 {mins}分{secs}秒, 是{side}侧歌曲, 来自{pack}包, SongID为: {sid}\n"

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
        if bg:
            bg_txt = f", 有特殊背景{bg}"
        else:
            bg_txt = None

        if jp_name:
            reply_txt += f"{artist} - {en_name}({jp_name}), BPM {bpm}, 时长 {mins}分{secs}秒, 是{side}侧歌曲, 来自{pack}包, {world_unlock}爬梯获得, 封面绘师{jacket_designer}{bg_txt}\n"
        else:
            reply_txt += f"{artist} - {en_name}, BPM {bpm}, 时长 {mins}分{secs}秒, 是{side}侧歌曲, 来自{pack}包, {world_unlock}爬梯获得, 封面绘师{jacket_designer}{bg_txt}\n"

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

        if jp_name:
            reply_txt += f"{artist} - {en_name}({jp_name}) ({chart_diff})\n"
        else:
            reply_txt += f"{artist} - {en_name} ({chart_diff})\n"
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

    if jp_name:
        reply_txt = f"随机到的歌曲是:\n{artist} - {en_name}({jp_name})"
    else:
        reply_txt = f"随机到的歌曲是:\n{artist} - {en_name}"

    return [reply_txt]
