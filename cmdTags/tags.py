class tags(object):
    
    def __init__(self):    
        self.tag = 'base'
        self.errors={}

    def getTag(self):
        return self.tag
    
    def getTagPos(self, msg):
        return msg.text.find(msg.firstCmd[0])
        
    def reply(self, msg):
        return "{0} hasn't been configured properly. Please contact Yamajac.".format(self.getTag()) 
        
    def errorHandler(self, error):
        try:
            return self.errors[error.__class__.__name__](error)
        except:
            raise error
    