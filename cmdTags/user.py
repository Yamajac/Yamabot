import cmdTags.tags

class user(cmdTags.tags.tags):

    def __init__(self):
        cmdTags.tags.tags.__init__(self)
        self.tag = '{user}'
    
    def reply(self, msg):
        return msg.getCommand()['reply'].replace(self.getTag(), msg.user['display-name'])
            
tag = user()
