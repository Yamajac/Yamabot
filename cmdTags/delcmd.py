import cmdTags.tags

class delcmd(cmdTags.tags.tags):
	
	def __init__(self):
		cmdTags.tags.tags.__init__(self)
		self.tag = '{delcmd}'
		
		self.errors['IndexError'] = self.handleIndexError
		self.errors['CommandDoesntExist'] = self.handleCommandDoesntExist
	
	def reply(self, bot, reply, msg, user, channel):
		query = msg[4].split(' ',2)
		if len(query) < 2:
			raise IndexError({'Message': 'Missing command', 'data':query})
		channel.remove_command(query[1])
		return reply.replace(self.getTag(), query[1])
			
	def handleIndexError(self, error):
		error = error.args[0]
		command = error['data'][0]
		new_command = '<commandName>'
			
		return 'Proper syntax is: {0} {1}'.format(command, new_command)
		
	def handleCommandDoesntExist(self, error):
		error = error.args[0]
		command = error['command']
		return "{0} doesn't exist.".format(command)
		
tag = delcmd()
