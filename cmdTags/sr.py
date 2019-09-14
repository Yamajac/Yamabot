import cmdTags.tags
import re
import youtube

class sr(cmdTags.tags.tags):
    YTRE = re.compile('((?:https?:)?\\/\\/)?((?:www|m)\\.)?((?:youtube\\.com|youtu.be))(\\/(?:[\\w\\-]+\\?v=|embed\\/|v\\/)?)([\\w\\-]+)(\\S+)')

    def __init__(self):
        cmdTags.tags.tags.__init__(self)
        self.tag = '{sr}'
        
        self.errors['TooManySongs'] = self.handleTooManySongs
        
    def reply(self, msg):
        query = msg.text[self.getTagPos(msg):].split(' ', 1)[1]
        if "soundcloud" in query:
            return "Soundcloud not currently available. Tell Yamajac to stop being lazy."
        YTURL = self.YTRE.search(query)
        if YTURL == None:
            video = youtube.GetSearch(query)
        else:
            video = youtube.GetVideo(YTURL.group(5))
            
        song = {
            "title":        video['items'][0]['snippet']['title'], 
            "uploader":     video['items'][0]['snippet']['channelTitle'],
            "id":           video['items'][0]['id'] if 'videoId' not in video['items'][0]['id'] else video['items'][0]['id']['videoId'],
            "requester":    msg.user['display-name']
        }
        msg.channel.add_song(song, False, msg.getCommand())
        return msg.getCommand()['reply'].replace(self.getTag(), video['items'][0]['snippet']['title']).format(video['items'][0]['snippet']['channelTitle'])

    def handleTooManySongs(self, error):
        error = error.args[0]
        cmd = error['cmd']
        song = error['song']
        limit = error['limit']
        if 'errors' in error['cmd'] and 'TooManySongs' in error['cmd']['errors']:
            return error['cmd']['errors']['TooManySongs'].format(song['title'], song['uploader'], song['id'], song['requester'], limit)
        return "Song queue is full, please try again later.".format(command)

tag = sr()