import cmdTags.tags

class timeout(cmdTags.tags.tags):

    def __init__(self):
        cmdTags.tags.tags.__init__(self)
        self.tag = '{timeout}'
    
    def reply(self, msg):
        msg.bot['outBuffer'].append([msg.channel, '.timeout {0} 1'.format(msg.user['name'])])
        return msg.firstCmd[1]['reply'].replace(self.getTag(), "")
            
tag = timeout()
