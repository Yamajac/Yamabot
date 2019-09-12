import cmdTags.__init__
import sys
import os
import importlib

class replyParser(object):

    def __init__(self):
        self.cmdTags = {}
        cmdTags.__init__.__load_all__(self.cmdTags)
        
    def parse(self, msg):
    
        reply = msg.getCommand()['reply']
        for tag in self.cmdTags:
            if tag in msg.getCommand()['reply']:
                try:
                    reply = self.cmdTags[tag].reply(msg)
                except Exception as e:
                    reply = self.cmdTags[tag].errorHandler(e)
                    
        if reply:
            msg.bot['outBuffer'].append([msg.channel, reply])
    
    def getTags(self, reply):
        
        return {d for d in self.cmdTags if d in reply}
            

            
        