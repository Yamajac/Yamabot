import cmdTags.tags

class delcmd(cmdTags.tags.tags):
    
    def __init__(self):
        cmdTags.tags.tags.__init__(self)
        self.tag = '{delcmd}'
        
        self.errors['IndexError'] = self.handleIndexError
        self.errors['CommandDoesntExist'] = self.handleCommandDoesntExist
    
    def reply(self, msg):
        query = msg.text[self.getTagPos(msg):].split(' ',2)
        if len(query) < 2:
            raise IndexError({'Message': 'Missing command', 'cmd': msg.getCommand(), 'data': query})
        msg.channel.remove_command(query[1], msg.getCommand())
        return msg.getCommand()['reply'].replace(self.getTag(), query[1])
            
    def handleIndexError(self, error):
        error = error.args[0]
        command = error['data'][0]
        new_command = '<commandName>'
        
        if 'errors' in error['cmd'] and "IndexError" in error['cmd']['errors']:
            return error['cmd']['errors']['IndexError'].format(command, new_command)
        return 'Proper syntax is: {0} {1}'.format(command, new_command)
        
    def handleCommandDoesntExist(self, error):
        error = error.args[0]
        command = error['command']
        
        if 'errors' in error['cmd'] and 'CommandDoesntExist' in error['cmd']['errors']:
            return error['cmd']['errors']['CommandDoesntExist'].format(command)
        return "The command \"{0}\" does not exist.".format(command)
        
tag = delcmd()
