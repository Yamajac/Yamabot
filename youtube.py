import urllib.request, urllib, json
YTKEY = ''

def GetData(URL, replacements):
    Request = urllib.request.Request((URL.format)(*replacements), headers={'User-Agent':'YamaBot /0.1', 
     'Accept':'application/json'})
    URL = urllib.request.urlopen(Request)
    Data = URL.read()
    encoding = URL.info().get_content_charset('utf-8')
    JSON = json.loads(Data.decode(encoding))
    URL.close()
    return JSON


def GetVideo(ID):
    return GetData('https://www.googleapis.com/youtube/v3/videos?part=snippet&id={0}&key={1}', (ID, YTKEY))


def GetSearch(QUERY):
    return GetData('https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=25&q={0}&key={1}', (urllib.parse.quote(QUERY), YTKEY))