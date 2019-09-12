import cmdTags.tags
import random

class rand(cmdTags.tags.tags):

    def __init__(self):
        cmdTags.tags.tags.__init__(self)
        self.tag = '{rand}'
       
    
    def reply(self, msg):
        
        customRange = msg.firstCmd[1]['reply'][msg.firstCmd[1]['reply'].find(self.tag)+len(self.tag):].split(" ")[0].split(",")
        if len(customRange) > 1:
            number = random.randint(int(customRange[0]), int(customRange[1]))
            tag = "{0}{1},{2}".format(self.getTag(),customRange[0], customRange[1])
        else:
            number = random.randint(1,101)
            tag = self.getTag()
        return msg.firstCmd[1]['reply'].replace(tag, str(number))
            
        
tag = rand()