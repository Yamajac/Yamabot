import cmdTags.tags

class ErrorChecking(Exception):
    pass


class errorcmd(cmdTags.tags.tags):

    def __init__(self):
        cmdTags.tags.tags.__init__(self)
        self.tag = '{errorcmd}'
        self.errors['IndexError'] = self.handleIndexError
        self.errors['CommandDoesntExist'] = self.handleCommandDoesntExist
        self.errors['ErrorChecking'] = self.handleErrorChecking

    def reply(self, msg):
        query = msg.text[self.getTagPos(msg):].split(' ', 3)
        if len(query) == 2:
            cmd = msg.channel.get_command(query[1], msg.getCommand())
            print(cmd)
            tags = msg.parser.getTags(cmd['reply'])
            errors = {}
            for tag in tags:
                for e in msg.parser.cmdTags[tag].errors.keys():
                    error = 'default'
                    if 'errors' in cmd:
                        if e in cmd['errors']:
                            error = cmd['errors'][e]
                        errors.update({e: error})

            raise ErrorChecking({'Message':'Checking errors',  'cmd':msg.getCommand(),  'data':query,  'errors':errors})
        if len(query) < 4:
            msg.channel.remove_error(query[1], query[2], msg.getCommand())
            return msg.getCommand()['reply'].replace(self.getTag(), query[1])
        else:
            msg.channel.edit_error(query[1], query[2], query[3], msg.getCommand())
            return msg.getCommand()['reply'].replace(self.getTag(), query[1])

    def handleErrorChecking(self, error):
        error = error.args[0]
        command = error['data'][0]
        checkedCommand = error['data'][1]
        if 'errors' in error['cmd']:
            if 'ErrorChecking' in error['cmd']['errors']:
                pass
            return error['cmd']['errors']['ErrorChecking'].format(command, checkedCommand, error['errors'])
        else:
            return 'Valid errors are: {0}'.format(error['errors'])

    def handleIndexError(self, error):
        error = error.args[0]
        command = error['data'][0]
        new_command = '<commandName>'
        if len(error['data']) > 1:
            new_command = error['data'][1]
        err = '<error>'
        if len(error['data']) > 2:
            err = error['data'][2]
        reply = '<commandReply>'
        if 'errors' in error['cmd']:
            if 'IndexError' in error['cmd']['errors']:
                pass
            return error['cmd']['errors']['IndexError'].format(command, new_command, err, reply)
        else:
            return 'Proper syntax is: {0} {1} {2} {3}'.format(command, new_command, err, reply)

    def handleCommandDoesntExist(self, error):
        error = error.args[0]
        command = error['command']
        if 'errors' in error['cmd']:
            if 'CommandDoesntExist' in error['cmd']['errors']:
                pass
            return error['cmd']['errors']['CommandDoesntExist'].format(command)
        else:
            return 'The command "{0}" does not exist.'.format(command)


tag = errorcmd()