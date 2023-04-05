import json,requests,time
# from ..sqlHelper import *

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

def animelookup(datalist,callerid,roomid = None):
    model = 'anime'
    mode = 0
    files = {
        'image': open('/Users/windsun/Downloads/1.png','rb')
    }
    content = requests.post(f"https://aiapiv2.animedb.cn/ai/api/detect?model={model}&force_one={mode}",data = None,files = files)
    print(content.text)
    content = json.loads(content.text)
    print(content)
    return ['']

def search_by_url(url):
    API_URL = 'https://api.trace.moe/search?url=' + url
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
    with open("result.mp4", 'wb') as f:
        for chunk in downloader.iter_content(chunk_size = 1024*1024):
            if chunk:
              f.write(chunk)

    # print(reply_txt)
    return [reply_txt]

def anilist_fetchfromid(query:str,vars_: dict):
    url = "https://graphql.anilist.co"
    headers = None
    return requests.post(url,
        json={"query": query,"variables": vars_},
        headers=headers).json()

def search_by_img(img):
    API_URL = 'https://api.trace.moe/search'
    s = requests.Session()
    res = s.get(API_URL)

# search_by_url("https://transfer.sh/Sw7vid/67531677548059_.pic.jpg")

