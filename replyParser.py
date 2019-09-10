import cmdTags.__init__
import sys

class replyParser(object):

	def __init__(self):
		self.cmdTags = {}
		cmdTags.__init__.__load_all__(self.cmdTags)
		
	def parse(self, bot, reply, msg, user, channel):
		for tag in self.cmdTags:
			if tag in reply:
				try:
					reply = self.cmdTags[tag].reply(bot, reply, msg, user, channel)
				except Exception as e:
					reply = self.cmdTags[tag].errorHandler(e)
		bot['outBuffer'].append([channel, reply])
		
		