import cmdTags.tags

class nextsong(cmdTags.tags.tags):

    def __init__(self):
        cmdTags.tags.tags.__init__(self)
        self.tag = '{nextsong}'
        self.errors['KeyError'] = self.handleKeyError
    
    def reply(self, msg):
        video = msg.channel.get_song('next_song', msg.getCommand())
        return msg.getCommand()['reply'].replace(self.getTag(), "youtu.be/{0}".format(video['id'])).format(video['title'])
     
    def handleKeyError(self, error):
        error = error.args[0]
        song = error['song']
        
        if 'errors' in error['cmd'] and 'KeyError' in error['cmd']['errors']:
            return error['cmd']['errors']['KeyError'].format(song)
        return "{0} not found".format(song)    
        
tag = nextsong()
