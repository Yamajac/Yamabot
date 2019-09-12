import json
import os

class CommandExists(Exception):
    pass
class CommandDoesntExist(Exception):
    pass
    
class channel(object):
    
    def __init__(self, channel):
        self.channel = channel
        self.commandsLastUpdated = 0
        self.getCommands()
        
    def getCommands(self):
        try:
            if self.commandsLastUpdated == os.stat('channels/{0}.json'.format(self.channel)).st_mtime:
                return self.data['commands']
            print("Reloading commands for channel: {0}".format(self.channel))
            with open('channels/{0}.json'.format(self.channel)) as channel_file:
                self.data = json.load(channel_file)
        except FileNotFoundError:
            self.data = {'commands': {'!ac': {'reply': 'The command {addcmd} has been added.'}}}
            self.save_data() 
            
        self.commandsLastUpdated = os.stat('channels/{0}.json'.format(self.channel)).st_mtime
        return self.data['commands']
        
    def save_data(self):
        with open('channels/{0}.json'.format(self.channel), 'w') as channel_file:
            json.dump(self.data, channel_file, indent=4, sort_keys=True, ensure_ascii=False)
        self.commandsLastUpdated = os.stat('channels/{0}.json'.format(self.channel)).st_mtime

    def get_command(self, command, cmd=False):
        if command in self.data['commands']:
            return self.data['commands'][command]
        else:
            raise CommandDoesntExist({"message": "Command doesn't exist", "cmd": cmd, "command": command})
    
    def add_command(self, command, reply, cmd=False):
        if command in self.data['commands']:
            raise CommandExists({"message": "Command already exists", "cmd": cmd, "command": command})
        self.data['commands'][command] = {'reply': reply}
        self.save_data()
            
    def remove_command(self, command, cmd=False):
        if command not in self.data['commands']:
            raise CommandDoesntExist({"message": "Command doesn't exist", "cmd": cmd, "command": command})
        del self.data['commands'][command]
        self.save_data()
        
    def edit_command(self, command, reply, cmd=False):
        if command not in self.data['commands']:
            raise CommandDoesntExist({"message": "Command doesn't exist", "cmd": cmd, "command": command})
        self.data['commands'][command]['reply'] = reply
        self.save_data()
     
    def edit_error(self, command, error, reply, cmd=False):
        if command not in self.data['commands']:
            raise CommandDoesntExist({"message": "Command doesn't exist", "cmd": cmd, "command": command})
        if 'errors' not in self.data['commands'][command]:
            self.data['commands'][command]['errors'] = {}
        self.data['commands'][command]['errors'][error] = reply
        self.save_data()   
    
    def remove_error(self, command, error, cmd=False):
        if command not in self.data['commands']:
            raise CommandDoesntExist({"message": "Command doesn't exist", "cmd": cmd, "command": command})
        del self.data['commands'][command]['errors'][error]
        self.save_data()   
    