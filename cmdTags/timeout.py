import cmdTags.tags

class timeout(cmdTags.tags.tags):

	def __init__(self):
		cmdTags.tags.tags.__init__(self)
		self.tag = '{timeout}'
	
	def reply(self, bot, reply, msg, user, channel):
		bot['outBuffer'].append([channel, '/timeout {0} 1'.format(user['name'])])
		return reply.replace(self.getTag(), "")
			
tag = timeout()
