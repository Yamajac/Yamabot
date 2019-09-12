import re
from replyParser import replyParser
import threading

class message(object):
    parser = replyParser()
    
    def __init__(self, line, channels, bot):
        msg = re.search("(.*?user-type=.*?):(.*?)!.*PRIVMSG #(.*?) :(.*)", line)
        self.user = dict( item.split("=") for item in msg[1].split(";"))
        self.user['name'] = msg[2]
        self.channel = channels[msg[3]]
        self.text = msg[4]	
        self.bot = bot
        
    def getCommand(self):
        return self.channel.data['commands'][self.firstCmd]
    
    def parseMessage(self):
        commands = self.channel.getCommands()

        firstCmdPos = -1
        firstCmd = False
        for cmd in commands:
            pos = self.text.find(cmd)
            
            if pos == -1:
                continue
            if firstCmdPos == -1 or pos < firstCmdPos:
                firstCmdPos = pos
                firstCmd = cmd
                
        if not firstCmd:
            return firstCmd
            
        self.firstCmd = firstCmd
        return firstCmd
        
    def parseReply(self):
        thread = threading.Thread(target=self.parser.parse, args=(self,))
        thread.start()