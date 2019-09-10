import configparser
import socket
import threading
import re

from irc import irc
from channel import channel
from replyParser import replyParser

class main(irc):

	def __init__(self):
		irc.__init__(self)
		
		self.set_terminator('\r\n')
		self.set_pingPong('PING :tmi.twitch.tv\r\n', 'PONG :tmi.twitch.tv\r\n')
		self.bots = self.grabBotData()
		self.grabChannelData()
		self.replyParser = replyParser()
		self.setupBots()
		self.run(self.bots)
		
	def grabBotData(self):
	
		d = {}
		cfg = configparser.ConfigParser()
		cfg.read('config.ini')
		
		for n in cfg.sections():
			d[n.lower()] = {'nick': n.lower()}
			d[n.lower()]['outBuffer'] = []
			d[n.lower()]['password'] = cfg[n]['oauth']
			d[n.lower()]['channels'] = cfg[n]['channels'].split(',')
		return d
	
	def grabChannelData(self):
		channels = []
		self.channels = {}
		for b in self.bots:
			channels.extend(self.bots[b]['channels'])
		channels = list(set(channels))
		
		for c in channels:
			self.channels[c] = channel(c)		
	
	def setupBots(self):
		
		CAPREQ = 'CAP REQ :twitch.tv/membership twitch.tv/tags twitch.tv/commands\r\n'
		ADDRESS = ('irc.chat.twitch.tv', 6667)
		for bot in self.bots:
			self.create_client(socket.AF_INET, socket.SOCK_STREAM, ADDRESS, self.bots[bot], CAPREQ)
	
	def chat(self, bot, msg, channel):
		self.send(bot,'PRIVMSG #{0} : {1}\r\n'.format(channel, msg))
		
	def recv(self, line, bot):
		
		if 'PRIVMSG' not in line:
			print(line)
			return
		
		msg = re.search("(.*?user-type=.*?):(.*?)!.*PRIVMSG #(.*?) :(.*)", line)
		user=dict( item.split("=") for item in msg[1].split(";"))
		user['name'] = msg[2]
		channel = msg[3]
		print('{0}@{1} : {2}'.format(user['name'], channel, msg[4]))
		
		commands = self.channels[channel].data['commands']
		
		firstCmdPos=-1
		for cmd in commands:
			pos = msg[4].find(cmd)
			
			if pos == -1:
				continue
			
			if '{delcmd}' in commands[cmd]:
				firstCmdPos = pos
				firstCmd = cmd
				break
			if firstCmdPos == -1 or pos < firstCmdPos:
				firstCmdPos = pos
				firstCmd = cmd
				
		if firstCmdPos != -1:
			thread = threading.Thread(target=self.replyParser.parse, args=(bot, commands[firstCmd], msg, user, self.channels[channel]))
			thread.start()
			#reply = self.replyParser.parse(commands[firstCmd], msg, user, self.channels[channel])
			#self.chat(bot, reply, channel)

	def run_hook(self):
		for bot in self.bots:
			if len(self.bots[bot]['outBuffer'])>0:
				for message in self.bots[bot]['outBuffer']:
					self.chat(self.bots[bot], message[1], message[0].channel)
				self.bots[bot]['outBuffer'] = []












		
		
		
		
		
		
		
		
if __name__ == '__main__':
	bot = main()