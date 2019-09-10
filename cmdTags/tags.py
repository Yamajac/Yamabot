class tags(object):
	
	def __init__(self):	
		self.tag = 'base'
		self.errors={}

	def getTag(self):
		return self.tag
		
	def reply(self, reply, message, user, channel):
		return "{0} hasn't been configured properly. Please contact Yamajac.".format(self.getTag()) 
		
	def errorHandler(self, error):
		try:
			return self.errors[error.__class__.__name__](error)
		except:
			raise error
	