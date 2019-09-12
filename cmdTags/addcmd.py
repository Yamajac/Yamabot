import cmdTags.tags

class addcmd(cmdTags.tags.tags):

    def __init__(self):
        cmdTags.tags.tags.__init__(self)
        self.tag = '{addcmd}'
        
        self.errors['IndexError'] = self.handleIndexError
        self.errors['CommandExists'] = self.handleCommandExists
    
    def reply(self, msg):
        query = msg.text[self.getTagPos(msg):].split(' ',2)
        if len(query) < 3:
            raise IndexError({'Message': 'Missing command/reply', 'cmd': msg.getCommand(), 'data': query})
        msg.channel.add_command(query[1], query[2], msg.getCommand())
        return msg.getCommand()['reply'].replace(self.getTag(), query[1])
            
    def handleIndexError(self, error):
        error = error.args[0]
        command = error['data'][0]
        new_command = '<commandName>'
        if len(error['data']) == 2:
            new_command = error['data'][1]
        reply = '<commandReply>'
        
        if 'errors' in error['cmd'] and "IndexError" in error['cmd']['errors']:
            return error['cmd']['errors']['IndexError'].format(command, new_command, reply)
        return 'Proper syntax is: {0} {1} {2}'.format(command, new_command, reply)
        
    def handleCommandExists(self, error):
        error = error.args[0]
        command = error['command']
        
        if 'errors' in error['cmd'] and 'CommandExists' in error['cmd']['errors']:
            return error['cmd']['errors']['CommandExists'].format(command)
        return "{0} already exists.".format(command)
tag = addcmd()