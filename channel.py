import json

class CommandExists(Exception):
	pass
class CommandDoesntExist(Exception):
	pass
	
class channel(object):
	
	def __init__(self, channel):
		self.channel = channel
		self.get_commands()
	
	def get_commands(self):
		try:
			with open('channels/{0}.json'.format(self.channel)) as channel_file:
				channel_data = json.load(channel_file)
		except FileNotFoundError:
			channel_data = {'commands': {'!ac': 'The command {addcmd} has been added.'}}
			self.save_data()
			
		self.data = channel_data
		
	def save_data(self):
		with open('channels/{0}.json'.format(self.channel), 'w') as channel_file:
			json.dump(self.data, channel_file, indent=4, sort_keys=True, ensure_ascii=False)
	
	def add_command(self, command, reply):
		if command in self.data['commands']:
			raise CommandExists({"message": "Command already exists", "command": command})
		self.data['commands'][command] = reply
		self.save_data()
			
	def remove_command(self, command):
		if command not in self.data['commands']:
			raise CommandDoesntExist({"message": "Command doesn't exist", "command": command})
		del self.data['commands'][command]
		self.save_data()
		
	def edit_command(self, command, reply):
		if command not in self.data['commands']:
			raise CommandDoesntExist({"message": "Command doesn't exist", "command": command})
		self.data['commands'][command] = reply
		self.save_data()
	