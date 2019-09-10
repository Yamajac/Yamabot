import socket

class irc(object):
	
	def __init__(self):
		self.set_pingPong('ping', 'pong')
	
	def create_client(self, family, type, address, client, extra=False):
		sock = socket.socket(family, type)
		sock.connect(address)
		sock.setblocking(0)
		client['sock'] = sock
		if extra:
			sock.send(extra.encode('utf-8'))
		self.join_channels(client)
		
	def join_channels(self, client):
		client['sock'].send('PASS {0}\r\n'.format(client['password']).encode('utf-8'))
		client['sock'].send('NICK {0}\r\n'.format(client['nick']).encode('utf-8'))
		for channel in client['channels']:
			client['sock'].send('JOIN #{0}\r\n'.format(channel).encode('utf-8'))
		
	def set_terminator(self, terminator):
		self.terminator=terminator
		
	def set_pingPong(self, ping, pong):
		self.ping=ping
		self.pong=pong
	
	def send(self, client, msg):
		client['sock'].send(msg.encode('utf-8'))
	
	def recv(self, msg, client):
		print(msg)
		
	def run_hook(self):
		pass
		
	def run(self, clients):
		msg=''
		while 1:
			for k, client in clients.items():
				try:
					msg = client['sock'].recv(1024).decode('utf-8')
					if msg==self.ping:
						self.send(client, self.pong)
						
				except socket.error:
					msg=False
					
				if msg:
					for line in msg.split(self.terminator):
						if line: self.recv(line, client)
			self.run_hook()
