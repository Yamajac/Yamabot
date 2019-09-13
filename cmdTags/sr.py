import cmdTags.tags
import re
import youtube

class sr(cmdTags.tags.tags):
    YTRE = re.compile('((?:https?:)?\\/\\/)?((?:www|m)\\.)?((?:youtube\\.com|youtu.be))(\\/(?:[\\w\\-]+\\?v=|embed\\/|v\\/)?)([\\w\\-]+)(\\S+)')

    def __init__(self):
        cmdTags.tags.tags.__init__(self)
        self.tag = '{sr}'

    def reply(self, msg):
        query = msg.text[self.getTagPos(msg):].split(' ', 1)[1]
        YTURL = self.YTRE.search(query)
        if YTURL == None:
            video = youtube.GetSearch(query)
        else:
            video = youtube.GetVideo(YTURL.group(5))
        return msg.getCommand()['reply'].replace(self.getTag(), video['items'][0]['snippet']['title']).format(video['items'][0]['snippet']['channelTitle'])


tag = sr()