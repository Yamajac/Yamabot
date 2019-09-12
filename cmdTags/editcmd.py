import cmdTags.tags

class editcmd(cmdTags.tags.tags):
    
    def __init__(self):
        cmdTags.tags.tags.__init__(self)
        self.tag = '{editcmd}'
        
        self.errors['IndexError'] = self.handleIndexError
        self.errors['CommandDoesntExist'] = self.handleCommandDoesntExist
    
    def reply(self, msg):
        query = msg.text[self.getTagPos(msg):].split(' ',2)
        if len(query) < 3:
            raise IndexError({'Message': 'Missing command/reply', 'cmd': msg.getCommand(), 'data': query})
        msg.channel.edit_command(query[1], query[2], msg.getCommand())
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
        
    def handleCommandDoesntExist(self, error):
        error = error.args[0]
        command = error['command']
        
        if 'errors' in error['cmd'] and 'CommandDoesntExist' in error['cmd']['errors']:
            return error['cmd']['errors']['CommandDoesntExist'].format(command)
        return "{0} doesn't exist.".format(command)
        
tag = editcmd()
