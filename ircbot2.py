import asyncore
import asynchat
import socket     
import time   
import re  
import traceback
import sys
      
import urllib2
from urllib import urlencode
import json
import httplib2
import MySQLdb
import random
import datetime
import dateutil.parser
import isodate
import pytz

from multiprocessing import Process
from multiprocessing import Queue
from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.client import AccessTokenCredentials
from oauth2client.client import AccessTokenCredentialsError
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow

# SQL convenience stuff
# db = MySQLdb.connect(host="172.245.220.5",port=3306,user="skorchbot",passwd="6ununugaq",db="zadmin_skorchbot")
db = MySQLdb.connect(host="107.180.4.54",user="AutoYama",passwd="J3,u0)isAO3&",db="twitchbot")
cur = db.cursor()
def execute(query,params=False):
	global cur
	global db
	try:
		if params:
			cur.execute(query,params)
		else:
			cur.execute(query)
	except (AttributeError, MySQLdb.OperationalError):
    # db = MySQLdb.connect(host="172.245.220.5",port=3306,user="skorchbot",passwd="6ununugaq",db="zadmin_skorchbot")
		db = MySQLdb.connect(host="107.180.4.54",user="AutoYama",passwd="J3,u0)isAO3&",db="twitchbot")
		cur=db.cursor()
		cur.execute(query,params)
		
def commit():
	global db
	try:
		db.commit()
	except (MySQLdb.OperationalError):
		# db = MySQLdb.connect(host="172.245.220.5",port=3306,user="skorchbot",passwd="6ununugaq",db="zadmin_skorchbot")
		db = MySQLdb.connect(host="107.180.4.54",user="AutoYama",passwd="J3,u0)isAO3&",db="twitchbot")
		cur=db.cursor()
		
# Youtube convenience stuff
def getNewToken(client_id, client_secret, refresh_token):
	request = urllib2.Request('https://accounts.google.com/o/oauth2/token',
	data=urlencode({
		'grant_type':    'refresh_token',
		'client_id':     client_id,
		'client_secret': client_secret,
		'refresh_token': refresh_token
	}),
	headers={
		'Content-Type': 'application/x-www-form-urlencoded',
		'Accept': 'application/json'
	})
	response = json.load(urllib2.urlopen(request))
	return response['access_token']
token=getNewToken("608158411556-2nr4cdil3iua9q25cejjp92pot7f4udh.apps.googleusercontent.com", "zmDbEDTWQXq-1nW0tRqxNvFR", "1/zwRvLUpZ7yLNvDab2VzURRg-xCSghAsC7bngHPT-zZI")
credentials=AccessTokenCredentials(token, "AutoYama/1.0",None)

def addVideo(video,today,channel,user):
	execute("""SELECT `playlistId` FROM `playlists` WHERE `channel` = %s AND playlistName = %s""", (channel,channel+" "+today))
	ID=cur.fetchall()
	commit()
	if ID:
		insert_video(video,ID[0][0],channel,today,user)
	else:
		ID=create_playlist(today,channel)['id']
		insert_video(video,ID,channel,today,user)
		
def create_playlist(today,channel,t=1):
	youtube = build("youtube","v3",http=credentials.authorize(httplib2.Http()))
	try:
		add_playlist=youtube.playlists().insert(
			part="snippet,status",
			body=dict(
				snippet=dict(
					title=channel+" "+today,
				),
				status=dict(
					privacyStatus="public"
				)
			)
		).execute()
	except (AccessTokenCredentialsError, HttpError) as e:
		time.sleep(t)
		global token
		global credentials
		token=getNewToken("608158411556-2nr4cdil3iua9q25cejjp92pot7f4udh.apps.googleusercontent.com", "zmDbEDTWQXq-1nW0tRqxNvFR", "1/zwRvLUpZ7yLNvDab2VzURRg-xCSghAsC7bngHPT-zZI")
		credentials=AccessTokenCredentials(token,"AutoYama/1.0",None)
		add_playlist=create_playlist(today,channel,t*2)
	execute("""INSERT INTO `playlists` (`playlistId`, `playlistName`, `channel`) VALUES (%s, %s, %s)""", (add_playlist['id'],channel+" "+today,channel))
	return add_playlist

def insert_video(video,playlistID,channel,today,user,t=1):
	youtube = build("youtube","v3",http=credentials.authorize(httplib2.Http()))
	try:
		add_video_response=youtube.playlistItems().insert(
			part="snippet",
			body=dict(
				snippet=dict(
					playlistId=playlistID,
							resourceId=dict(
						kind="youtube#video",
						videoId=video
					)
				)
			)
		).execute()
	except (AccessTokenCredentialsError, HttpError) as e:
		time.sleep(t)
		global token
		global credentials
		token=getNewToken("608158411556-2nr4cdil3iua9q25cejjp92pot7f4udh.apps.googleusercontent.com", "zmDbEDTWQXq-1nW0tRqxNvFR", "1/zwRvLUpZ7yLNvDab2VzURRg-xCSghAsC7bngHPT-zZI")
		credentials=AccessTokenCredentials(token, "AutoYama/1.0",None)
		insert_video(video,playlistID,channel,today,user,t*2)
	table=channel+"songs"
	execute("""INSERT INTO `%s`(`id`, `playlistId`, `playlist`, `user`) VALUES (%%s,%%s,%%s,%%s)""" % table,(video,playlistID,channel+" "+today,user))
	
# Whatever
class MethodRequest(urllib2.Request):
	def __init__(self, *args, **kwargs):
		if 'method' in kwargs:
			self._method = kwargs['method']
			del kwargs['method']
		else:
			self._method = None
		return urllib2.Request.__init__(self, *args, **kwargs)

	def get_method(self, *args, **kwargs):
		if self._method is not None:
			return self._method
		return urllib2.Request.get_method(self, *args, **kwargs)


class channel(object):
	def __init__(self, channelName, channelOAuth):
		self.channelName=channelName
		self.channelOAuth=channelOAuth
		# Grab commands from server
		execute("""SELECT `command`,`reply`,`kind`,`time`, `messages` FROM `%scommands` where 1""" % self.channelName)
		# Check if a command has {addcmd} in it. Every channel must have at least one command with this in the reply.
		isaddcmd=False
		self.COMMANDS={}
		self.autoMessages={}
		self.cBuffer=[]
		self.pBuffer=[]
		self.wOutBuffer=[]
		self.voting={"type":False,"users":[],"votes":{}}
		self.raffle={"type":False,"users":[]}
		# Iterate through response from server
		for row in cur.fetchall():
			self.COMMANDS[row[0].lower()]={}
			self.COMMANDS[row[0].lower()]['reply']=row[1]
			self.COMMANDS[row[0].lower()]['oldtime']=0
			if row[2] != 'manual':
				self.autoMessages[row[0].lower()]={}
				self.autoMessages[row[0].lower()]['kind']=row[2]
				self.autoMessages[row[0].lower()]['time']=row[3]
				self.autoMessages[row[0].lower()]['last']=0
				self.autoMessages[row[0].lower()]['messages']=[row[4],0,time.time()]
			if re.search("{addcmd}",row[1]):
				isaddcmd=True
		commit()
		# Create a command with {addcmd} if one did not exist.
		if not isaddcmd:
			self.COMMANDS['!ac']={
				"reply": "%m  The command {addcmd} has been added.",
				"kind" : "manual",
				"time" : 0,
				"last" : 0,
			}
			execute("""INSERT INTO `%s`(`command`, `reply`) VALUES (%%s,%%s)""" % (channelName+"commands"),("!ac", "%m  The command {addcmd} has been added."))

class botManager(asynchat.async_chat, object):
	# string channelName
	# string channelOauth
	# string botName
	# string botOAuth
	# dict commands
	def __init__(self, channel, botName, botOAuth, host, port, whispers=False):
		# Channel Variables
		if isinstance(whispers,basestring):
			self.channelName=whispers
		else:
			self.channelName=channel.channelName
		self.channel=channel
		self.channelOAuth=channel.channelOAuth
		self.botName=botName
		self.botOAuth=botOAuth
		self.lTime=0
		self.timer=0
		self.cOutBuffer=channel.cBuffer
		self.outBuffer=[]
		self.pOutBuffer=channel.pBuffer
		self.wOutBuffer=channel.wOutBuffer
		self.outLog=0
		self.isMod=False
		self.limit=19
		self.rate=1.5
		self.user=""
		self.cmd=""
		self.msg=""
		self.voting=channel.voting
		self.raffle=channel.raffle
		self.lastMessage=time.time()
		self.COMMANDS=channel.COMMANDS
		self.autoMessages=channel.autoMessages
		self.whispers=whispers
		
		# Channel Chat manager
		asynchat.async_chat.__init__(self)
		self.connect_to_channel(host,port)
		
	def yamaSend(self, msg, type=False):
		if isinstance(msg, basestring) and msg.strip()=='':
			return
		if type=='p':
			self.pOutBuffer.append(msg)
		elif type=='c':
			self.cOutBuffer.append(msg)
		elif type=='w':
			self.wOutBuffer.append(msg)
		else:
			self.outBuffer.append(msg)
			
	def checkTags(self, reply, user, bypass=False, cmd=False, msg=False):
		if not bypass and re.match("%",reply):
			s=reply.split(None,1)[0]
			
			if re.search("%m",s) and not self.userMod(user):
				return True
			if re.search("%s",s) and not self.userSub(user) and not self.userMod(user):
				return True
			if re.search("%y",s) and user['name']!='yamajac' and user['name']!='skorchbot' and user['name']!='infected_asylum':
				return True
				
			limit=re.search("%a([0-9]+);",s)
			if limit:
				request=urllib2.Request("https://api.twitch.tv/kraken/channels/"+user['name'], headers={"User-Agent": "Skorchbot /1.0"})
				try:
					response=urllib2.urlopen(request)
					userInfo=json.load(response)
					response.close
					userAge=(datetime.datetime.now()-datetime.datetime.strptime(userInfo['created_at'], "%Y-%m-%dT%H:%M:%SZ"))
					userAge=(userAge.days*24)+(userAge.seconds//3600)
					print(userAge)
					if not userAge > int(limit.group(1)):
						return True
				except urllib2.HTTPError as err:
					traceback.print_exc()
				
			limit=re.search("%-a([0-9]+);",s)
			if limit:
				request=urllib2.Request("https://api.twitch.tv/kraken/channels/"+user['name'], headers={"User-Agent": "Skorchbot /1.0"})
				try:
					response=urllib2.urlopen(request)
					userInfo=json.load(response)
					response.close
					userAge=(datetime.datetime.now()-datetime.datetime.strptime(userInfo['created_at'], "%Y-%m-%dT%H:%M:%SZ"))
					userAge=(userAge.days*24)+(userAge.seconds//3600)
					print(userAge)
					if not userAge < int(limit.group(1)):
						return True
				except urllib2.HTTPError as err:
					traceback.print_exc()
				
			cooldown=re.search("%t([0-9]*);",s)
			if not self.whispers and cmd and not self.userMod(user) and cooldown and int(cooldown.group(1))>time.time()-self.COMMANDS[cmd]['oldtime']:
				return True
			
			if not self.whispers and re.search("%w",s):
				return True
			if self.whispers and re.search("%c",s):
				return True

			if cmd and re.search("%b",s) and not re.match(cmd,msg.lower()):
				return True
				
							
	def runCommand(self, reply, msg, user, cmd="", bypass=False, regex=False):
		cmd=cmd.lower()
		
		# First things first we have to check all of the limitations that can be set on commands. 
		# These tags are set in the first block of text in a command's reply, and each tag is a key character preceded by a % sign.
		if self.checkTags(reply,user,msg=msg,bypass=bypass,cmd=cmd):
			return
		# To prevent commands from adding keywords into the bot and breaking it, we replace all the open brackets with \20.
		# \20 has no meaning. It's just what I typed when I typed it. 
		# Certain keywords can add keywords themselves, but they're made to do that.
		reply=reply.replace("{","\20")
		# The commands get run in a pretty weird order. But I can copy them around to whatever I want, it doesn't really matter that much. 
		# The only REALLY REALLY IMPORTANT part is that {switch} gets run FIRST, and {Rlist} gets run BEFORE any commands you want it to be able to make.
		# {switch case(case): reply endcase case(case2): reply2 endcase endswitch} just does exactly what it would appear to. Too complicated. You're reading code.		It just a switch case dawg.
		
		# Does stuff with regex. Lots of things in the future. 		
		if regex:
			while re.search("\20group_",reply):
				p = re.search("\20group_",reply)
				var = reply[p.end():].split("}",1)
				try:
					reply=re.sub("\20group_.*?}",regex.group(int(var[0])),reply,1)	
				except (IndexError,ValueError) as err:
					reply=re.sub("\20group_.*?}","",reply,1)
		
		if re.search("\20switch",reply):
			while re.search("\20switch",reply):
				p=re.search(cmd,msg.lower())
				var=msg[p.end():].split(None,1)
				switchcase=re.search("\20switch(.*?)endswitch}",reply)
				switchcase=re.findall("case\((.*?)\):(.*?)endcase",switchcase.group(1))
				switchcase=dict(switchcase)
				try:
					if var[0].lower() not in switchcase:
						reply=re.sub("\20switch.*?endswitch}","" if 'NONE' not in switchcase else switchcase['NONE'],reply,1) 
					elif not self.checkTags(switchcase[var[0].lower()],user):
						if re.match("%",switchcase[var[0].lower()]):
							s=switchcase[var[0].lower()].split(None,1)
							switchcase[var[0].lower()]="" if len(s)==1 else s[1]
						reply=re.sub("\20switch.*?endswitch}",switchcase[var[0].lower()],reply,1) 
					else:
						reply=re.sub("\20switch.*?endswitch}","" if 'FAIL' not in switchcase else switchcase['FAIL'],reply,1)
				except IndexError as err:
					reply=re.sub("\20switch.*?endswitch}","" if 'NONE' not in switchcase else switchcase['NONE'],reply,1) 
					
		# Replaces {Rlist_<pastebinID>} with a random line from the associated pastebin. Multiple pastebins can be used in one command
		# and a pastebin can even have another {Rlist} keyword in it, meaning you can have random random random lists.
		# Or something.
		if re.search("\20Rlist_",reply):
			lastIDs=[]
			while re.search("\20Rlist_",reply):
				p=re.search("\20Rlist_",reply)
				ID = reply[p.end():].split("}", 1)
				if len(ID)>0:
					if ID not in lastIDs:
						lastIDs.append(ID)
						request = urllib2.Request("http://pastebin.com/raw.php?i=%s" % ID[0],headers={"User-Agent" : "AutoYama /1.0"})
						try:
							list=urllib2.urlopen(request).read().splitlines()
							quote= random.choice(list)
						except urllib2.HTTPError as err:
							quote=""
						reply = re.sub("\20Rlist_.*?}",quote.decode('utf8').replace("{","\20"),reply, 1)
						
		# Replaces {user} with the username that called the command. 
		if re.search("\20user}",reply):
			reply=reply.replace("\20user}",user['display-name'])
				
		# Replaces {uptime} with the amount of time the stream has been live.
		if re.search("\20uptime}", reply):
			request = urllib2.Request("https://api.twitch.tv/kraken/streams/"+self.channel.channelName,headers={"User-Agent" : "AutoYama /1.0"})
			response=urllib2.urlopen(request)
			stream=json.load(response)
			response.close()
			if stream['stream']:
				d1=dateutil.parser.parse(stream['stream']['created_at']).replace(tzinfo=None)
				d2=datetime.datetime.utcnow()
				uptime=d2-d1
				hours, remainder = divmod(uptime.seconds,3600)
				minutes, seconds = divmod(remainder, 60)
				reply=reply.replace("\20uptime}","%s hours, %s minutes and %s seconds" % (hours, minutes, seconds))
			else:
				reply=reply.replace("\20uptime}","xero hours")
			
		# Replaces {proxy_<cmd>} with the return of the requested command. Replaces it with nothing if the command doesn't exist.
		if re.search("\20proxy_",reply):
			while re.search("\20proxy_",reply):
				p=re.search("\20proxy_",reply)
				c=reply[p.end():].split("}",1)
				try:
					reply=re.sub("\20proxy_.*?}",self.runCommand(self.COMMANDS[c[0]]['reply'],msg,user,cmd,regex),reply,1)
				except:
					reply=re.sub("\20proxy_.*?}","",reply,1)
				
		# Replaces {Rcolour} with ABSOLUTELY NOTHING!!! But changes the bot's colour.
		if re.search("\20Rcolour}",reply):
			colours=["Blue", "BlueViolet", "CadetBlue", "Chocolate", "Coral", "DodgerBlue", "Firebrick", "GoldenRod", "Green", "HotPink", "OrangeRed", "Red", "SeaGreen", "SpringGreen", "YellowGreen"]
			colour=random.choice(colours)
			self.yamaSend("/color "+colour,'p')
			reply=reply.replace("\20Rcolour}","")
			
		# Replaces {getcolour} with the hex colour of the user calling the command.
		if re.search("\20getcolour}",reply):
			reply=reply.replace("\20getcolour}", user['@color'])
			
		
			
		# Replaces {RNG} with a random number from 1-10000, accepts custom range with {RNG_a-b}
		if re.search("\20RNG", reply):
			p=re.search("\20RNG_",reply)
			if p:
				try:
					rngrange=reply[p.end():].split("}",1)
					rngrange2=rngrange[0].split("-",1)
					reply=reply.replace("\20RNG_"+rngrange[0]+"}",str(random.randint(int(rngrange2[0]),int(rngrange2[1]))))
				except (TypeError, ValueError) as err:
					reply=reply.replace("\20RNG}", random.randint(1,10000))
			else:
				reply=reply.replace("\20RNG}", random.randint(1,10000))
			
		# Replaces {timeuser} with nothing and times the user that called the command out.
		if re.search("\20timeuser",reply):
			p=re.search("\20timeuser_(.*)}",reply)
			if p:
				self.yamaSend({'time': time.time() + 0.5,
					'msg': "/timeout "+user['name']+" "+p.group(1)},'p')
			else:
				self.yamaSend({'time': time.time() + 1,
					'msg': "/timeout "+user['name']+" "+" 1"},'p')
			reply=reply.replace("\20timeuser}","")
		# Replaces {banuser} with nothing and bans the user that called the command.
		if re.search("\20banuser}",reply):
			self.yamaSend({'time': time.time() + 0.5,
				'msg': "/ban "+user['name']},'p')
			reply=reply.replace("\20banuser}","")
			
		# Replaces {cursong} with the name and url of the song currently being played on the website by the broadcaster.
		if re.search("\20cursong}",reply):
			execute("""SELECT `songID`, `state` FROM `users` WHERE `username` = %s""",[self.channel.channelName])
			id=cur.fetchall()
			commit()
			try:
				request=urllib2.Request("https://www.googleapis.com/youtube/v3/videos?id=%s&key=AIzaSyBRwg9MPrSFD1yDhLYz0Hv9yKVkZyd-F94&fields=items(snippet(title))&part=snippet" % id[0][0],headers={"User-Agent" : "AutoYama /1.0"})
				response=urllib2.urlopen(request)
				song=json.load(response)
				response.close()
				title=song['items'][0]['snippet']['title']
				playing="" if id[0][1]=='play' else "PAUSED: "
				reply=reply.replace("\20cursong}",playing+title+" youtu.be/"+id[0][0])
			except IndexError as err:
				reply=self.channel.channelName+" does not have song requests setup."
			
		# Replaces {lastsong} with the name and url of the song last played on the website by the broadcaster.
		if re.search("\20lastsong}",reply):
			execute("""SELECT `lastSongID` FROM `users` WHERE `username` = %s""",[self.channel.channelName])
			id=cur.fetchall()
			commit()
			try:
				request=urllib2.Request("https://www.googleapis.com/youtube/v3/videos?id=%s&key=AIzaSyBRwg9MPrSFD1yDhLYz0Hv9yKVkZyd-F94&fields=items(snippet(title))&part=snippet" % id[0][0],headers={"User-Agent" : "AutoYama /1.0"})
				response=urllib2.urlopen(request)
				song=json.load(response)
				response.close()
				title=song['items'][0]['snippet']['title']
				reply=reply.replace("\20lastsong}",title+" youtu.be/"+id[0][0])
			except IndexError as err:
				reply=self.channel.channelName+" does not have song requests setup."
				
		# Replaces {incvar_<variablename>} with the value of the requested variable after increasing it's value by one.
		if re.search("\20incvar_",reply):
			while re.search("\20incvar_",reply):
				p=re.search("\20incvar_",reply)
				var=reply[p.end():].split("}",1)
				execute("""SELECT `value` FROM `%s` WHERE `name` = %%s""" % (self.channel.channelName+"vars"), [var[0]])
				value=cur.fetchall()
				commit()
				try:
					value=value[0][0]+1
					execute("""UPDATE %s SET `value` = %%s WHERE `name` = %%s""" % (self.channel.channelName+"vars"), (value,var[0]))
				except IndexError as err:
					reply=var[0]+" does not exist."
				reply=re.sub("\20incvar_.*?}",str(value),reply,1)
				
		# Replaces {decvar_<variablename>} with the value of the requested variable after decreasing it's value by one.
		if re.search("\20decvar_",reply):
			while re.search("\20decvar_",reply):
				p=re.search("\20decvar_",reply)
				var=reply[p.end():].split("}",1)
				execute("""SELECT `value` FROM `%s` WHERE `name` = %%s""" % (self.channel.channelName+"vars"), [var[0]])
				value=cur.fetchall()
				commit()
				try:
					if value[0][0]>=1:
						value=value[0][0]-1
						execute("""UPDATE %s SET `value` = %%s WHERE `name` = %%s""" % (self.channel.channelName+"vars"), (value,var[0]))
						reply=re.sub("\20decvar_.*?}",str(value),reply, 1)
					else:
						reply=re.sub("\20decvar_.*?}",str(value[0][0]),reply, 1)
				except IndexError as err:
					reply=var[0]+" does not exist."
					
		# Replaces {getvar_<variablename>} with the value of the requested variable.
		if re.search("\20getvar_",reply):
			while re.search("\20getvar_",reply):
				p = re.search("\20getvar_",reply)
				var = reply[p.end():].split("}",1)
				execute("""SELECT `value` FROM `%s` WHERE `name` = %%s""" % (self.channel.channelName+"vars"), [var[0]])
				value=cur.fetchall()
				commit()
				reply=re.sub("\20getvar_.*?}","",reply,1) if not value else re.sub("\20getvar_.*?}",str(value[0][0]),reply,1)
				
		# Replaces {addvar} with the name of the variable that was added.
		if re.search("\20addvar}",reply):
			p=re.search(cmd,msg.lower())
			var=msg[p.end():].split(None)
			try:
				var[1]=int(var[1])+0
				execute("""INSERT INTO %s (`name`, `value`) VALUES (%%s,%%s)""" % (self.channel.channelName+"vars"), [var[0],var[1]])
				reply=reply.replace("\20addvar}", str(var[1]))
				reply=reply.replace("\20addvar_name}", var[0])
			except IndexError as err:
				reply="Please use "+cmd+" <variablename> <numericvalue> to add a variable."
			except MySQLdb.IntegrityError as err:
				reply="The variable "+var[0]+" already exists."
			except ValueError as err:
				reply="Variables can only have integer values right now."
				
		# Replaces {delvar} with the name of the variable that was deleted.
		if re.search("\20delvar}",reply):
			p=re.search(cmd,msg.lower())
			var=msg[p.end():].split(None)
			try:
				execute("""DELETE FROM %s WHERE `name` = %%s""" % (self.channel.channelName+"vars") ,[var[0]])
				reply=reply.replace("\20delvar}",var[0])
			except IndexError as err:
				reply="Please use "+cmd+" <variablename> to delete variables."
		# Replaces {setvar} with the name of the variable that had a value set.
		if re.search("\20setvar}",reply):
			p=re.search(cmd,msg.lower())
			var=msg[p.end():].split(None)
			try:
				execute("""UPDATE %s SET `value` = %%s WHERE `name` = %%s""" % (self.channel.channelName+"vars"), (var[1],var[0]))
				reply=reply.replace("\20setvar}", str(var[1]))
				reply=reply.replace("\20setvar_name}", var[0])
			except IndexError as err:
				reply="Please use "+cmd+" <variablename> <numericvalue> to set a variables value."
				
		# Replaces {sr_<timelimit>} with the title and url of the video requested.
		if re.search("\20sr_",reply):
			p=re.search(cmd,msg.lower())
			var=msg[p.end():].split(None,1)
			p=re.search("\20sr_",reply)
			length=reply[p.end():].split("}", 1)
			if re.search("[^0-9]",length[0]):
				reply = "Contrary to popular belief, "+length[0]+" is not a number."
			else:
				length=int(length[0])
				ID=False if len(var)==0 else re.search("([A-Za-z0-9_-]{11})",var[0])
				if ID:
					ID=ID.group(1)
					request=urllib2.Request("https://www.googleapis.com/youtube/v3/videos?id="+ID+"&key=AIzaSyBRwg9MPrSFD1yDhLYz0Hv9yKVkZyd-F94&fields=items(contentDetails(duration)%2Csnippet(title))&part=snippet%2CcontentDetails",headers={"User-Agent" : "AutoYama /1.0"})
					response=urllib2.urlopen(request)
					song=json.load(response)['items']
					response.close()
					if len(song)>0:
						song=song[0]
						if length < isodate.parse_duration(song['contentDetails']['duration']).seconds:
							m,s=divmod(length,60)
							reply="The maximum length for a video request is: %02d:%02d" % (m, s)
						else:
							today=datetime.date.today()
							today=today.isoformat()
							execute("""SELECT `id` FROM `%s` WHERE `id` = %%s AND playlist=%%s""" % (self.channel.channelName+"songs"), (ID,self.channel.channelName+" "+today))
							result=cur.fetchall()
							commit()
							if result:
								reply="The song "+song['snippet']['title']+" is already in the playlist."
							execute("""SELECT `id` FROM `%s` WHERE `user` = %%s AND `playlist`=%%s""" % (self.channel.channelName+"songs"), (user['name'],self.channel.channelName+" "+today))
							result=cur.fetchall()
							commit()
							if result and len(result)>50:
								reply=user['display-name']+" has already requested the maximum of (5) songs."
							else:
								addVideo(ID,today,self.channel.channelName,user['name'])
								reply=re.sub("\20sr_.*?}",song['snippet']['title'].encode('utf-8')+" youtu.be/"+ID,reply)
					else:
						reply="That youtube ID does not exist. Where'd you even get it from?"
				else:
					m,s=divmod(length,60)
					reply="Please use "+cmd+" <youtubeURL> to request songs. The maximum length allowed is: %02d:%02d" % (m, s)
				
		# Replaces {cmdlist} with the commands in the channel, given the requested command type. Mods, Regex, All, and default.
		if re.search("\20cmdlist}",reply):
			p = re.search(cmd,msg.lower())
			param = msg[p.end():].split(None, 1)
			list=""
			try:
				if param[0]=='mods' and self.userMod(user):
					for c in self.COMMANDS:
						list = list+c+", " if re.search("%m", self.COMMANDS[c]['reply'].split(None,1)[0]) else list
					list=list[:len(list)-2]
				elif param[0]=='subs' and self.userSub(user) and self.userMod(user):
					for c in self.COMMANDS:
						list = list+c+", " if re.search("%s",self.COMMANDS[c]['reply'].split(None,1)[0]) else list
					list=list[:len(list)-2]
				elif param[0]=='regex' and self.userMod(user):
					for c in self.COMMANDS:
						list = list+c[6:]+", " if re.match("regex:", c) else list
					list=list[:len(list)-2]
				elif param[0]=='all' and self.userMod(user):
					for c in self.COMMANDS:
						list=list+c+", "
					list=list[:len(list)-2].replace("regex:","")
			except IndexError as err:
				for c in self.COMMANDS:
					list = list+c+", " if not (re.search("%m", self.COMMANDS[c]['reply'].split(None,1)[0])) and not (re.search("%s", self.COMMANDS[c]['reply'].split(None,1)[0])) and not (re.match("regex:", c)) else list
				list=list[:len(list)-2]
				
			data={
				'api_dev_key':'d329a5fd8d93622bd1b8c911b3d5fc13',
				'api_option':'paste',
				'api_paste_code':list,
				'api_paste_private':'0',
				'api_paste_name':"command list",
				'api_paste_expire_date':'1D',
				'api_user_key':'b0e77e213db8f0b77974dc75b822e518'
			}
			data=urlencode(data)
			request=urllib2.Request("http://pastebin.com/api/api_post.php",
				data=data,
				headers={
					"User-Agent" : "Skorchbot /1.0"
				})
			response=urllib2.urlopen(request)
			list=response.read()
			response.close()
			reply=reply.replace("\20cmdlist}",list)
			
		# Replaces {addcmd} with the name of the command that was added.
		if re.search("\20addcmd}",reply):
			p=re.search(cmd,msg.lower())
			c=msg[p.end():].split(None,1)
			try:
				if c[0].lower() not in self.COMMANDS:
					c[0]=c[0].lower()
					execute("""INSERT INTO `%s`(`command`, `reply`) VALUES (%%s,%%s)""" % (self.channel.channelName+"commands"),(c[0], c[1]))
					self.COMMANDS[c[0]]={}
					self.COMMANDS[c[0]]['reply']=c[1]
					self.COMMANDS[c[0]]['changed']=time.time()
					self.COMMANDS[c[0]]['oldtime']=0
					reply=reply.replace("\20addcmd}",c[0])
				else:
					reply="The command: "+c[0]+" already exists. Please use "+cmd+" <commandname> <commandreply> to create a command."
			except IndexError as err:
				reply="Please use "+cmd+" <commandname> <commandreply> to create a command."
				
		# Replaces {delcmd} with the name of the command that was deleted.
		if re.search("\20delcmd}",reply):
			p=re.search(cmd,msg.lower())
			c=msg[p.end():].split(None,1)
			try:
				if c[0].lower() in self.COMMANDS:
					c[0]=c[0].lower()
					if re.search("{addcmd}",self.COMMANDS[c[0]]['reply']):
						numberAddCmd=0
						for cmds in self.COMMANDS:
							if re.search("{addcmd}",self.COMMANDS[cmds]['reply']):
								numberAddCmd=numberAddCmd+1
						if numberAddCmd<2:
							return "You are required to have at least one command that can add commands. Please make another one before deleting this one."
					if (re.match("%", self.COMMANDS[c[0]]['reply'])) and (re.search(self.COMMANDS[c[0]]['reply'].split(None,1)[0],"%ud")) and user['name']!='yamajac' and user['name']!='skorchbot':
						reply="The command "+c[0]+" can not be deleted. Please remove the %ud tag to delete it."
					else:
						execute("""DELETE FROM `%s` WHERE `command` = %%s""" % (self.channel.channelName+"commands"),[c[0]])
						self.COMMANDS.pop(c[0],None)
						self.autoMessages.pop(c[0],None)
						reply=reply.replace("\20delcmd}",c[0])
				else:
					reply="The command: "+c[0]+" does not exist. Please use "+cmd+" <commandname> to delete a command."
			except IndexError as err:
				reply="Please use "+cmd+" <commandname> to delete a command."
		
		# Replaces {editcmd} with name of the command that was edited.
		if re.search("\20editcmd}",reply):
			p=re.search(cmd,msg.lower())
			c=msg[p.end():].split(None,1)
			try:
				if c[0].lower() in self.COMMANDS:
					c[0]=c[0].lower()
					if not re.search("{addcmd}",c[1]) and re.search("{addcmd}",self.COMMANDS[c[0]]['reply']):
						numberAddCmd=0
						for cmds in self.COMMANDS:
							if re.search("{addcmd}",self.COMMANDS[cmds]['reply']):
								numberAddCmd=numberAddCmd+1
						if numberAddCmd<2:
							return "You are required to have at least one command that can add commands. Please make another one before deleting this one."
					execute("""UPDATE `%s` SET `reply`=%%s WHERE `command`=%%s""" % (self.channel.channelName+"commands"), (c[1], c[0]))
					self.COMMANDS[c[0]]['reply']=c[1]
					self.COMMANDS[c[0]]['changed']=time.time()
					reply=reply.replace("\20editcmd}",c[0])
				else:
					reply="The command "+c[0]+" does not exist. Please use "+cmd+" <commandname> <commandreply> to edit a command."
			except IndexError as err:
				reply="Please use "+cmd+" <commandname> <commandreply> to edit a command."
		
		# Replaces {rncmd} with name of the command that was edited.
		if re.search("\20rncmd}",reply):
			p=re.search(cmd,msg.lower())
			c=msg[p.end():].split(None,1)
			try:
				if c[0].lower() in self.COMMANDS and c[1].lower() not in self.COMMANDS:
					c[0]=c[0].lower()
					c[1]=c[1].lower()
					execute("""UPDATE `%s` SET `command`=%%s WHERE `command`=%%s""" % (self.channel.channelName+"commands"), (c[1].rstrip(), c[0]))
					self.COMMANDS[c[1].rstrip()]=self.COMMANDS.pop(c[0])
					reply=reply.replace("\20rncmd}",c[0])
					reply=reply.replace("\20rncmd_new}",c[1])
				elif c[1].rstrip() in self.COMMANDS:
					reply="The command "+c[1]+" already exists. Please use "+cmd+" <commandname> <newcommandname> to edit a command."
				else:
					reply="The command "+c[0]+" does not exist. Please use "+cmd+" <commandname> <newcommandname> to edit a command."
			except IndexError as err:
				reply="Please use "+cmd+" <commandname> <newcommandname> to edit a command."
				
		# Replaces {setkind} with the name of the command that had it's automation changed. Also actually changes the automation of the command.
		if re.search("\20setkind}",reply):
			p=re.search(cmd,msg.lower())
			params=msg[p.end():].split(None)
			nParams=len(params)
			if nParams>0 and params[0] in self.COMMANDS:
				if nParams>1 and params[1]=='manual':
					params=[params[0],params[1],0,0]
				elif nParams>2 and params[1]=='dead':
					params=[params[0],params[1],params[2],0]
				elif nParams>1 and params[1]!='active':
					params=[]
			else:
				params=[]
			try:
				execute("""UPDATE `%s` SET `kind`=%%s, `time`=%%s, `messages`=%%s WHERE `command`=%%s""" % (self.channel.channelName+"commands"), (params[1],int(params[2]),int(params[3]),params[0]))
				self.autoMessages[params[0].lower()]={}
				self.autoMessages[params[0].lower()]['kind']=params[1]
				self.autoMessages[params[0].lower()]['time']=int(params[2])
				self.autoMessages[params[0].lower()]['last']=0
				self.autoMessages[params[0].lower()]['messages']=[int(params[3]),0,time.time()]
				reply=reply.replace("\20setkind}",params[0])
			except (ValueError, IndexError) as err:
				reply="Please use "+cmd+" <command> <manual|active|dead> <cooldown> <messagesbetweencalls>"
				
		# Replaces {date} with the current date.
		if re.search("\20date", reply):
			p=re.search(cmd,msg.lower())
			if p:
				z=msg[p.end():].split(None,1)
				try:
					now=datetime.datetime.now(pytz.timezone(z[0]))
				except:
					now=datetime.datetime.now(pytz.timezone("Canada/Pacific"))
			p=re.search("\20date_",reply)
			
			if p:
				d=reply[p.end():].split("}",1)
				reply=re.sub("\20date_.*}", now.strftime(d[0]), reply, 1)
			else:
				reply=reply.replace("\20date}", now.strftime("%A %b, %d; %I:%M:%S %p"))		
			
		# Does a whole bunch of shit with the commands. Really complicated stuff.
		if re.search("\20vote}",reply):
			p=re.search(cmd,msg.lower())
			votes=msg[p.end():].split(None,2)
			nVotes=len(votes)
			if nVotes>0:
				if votes[0]=='start' and self.userMod(user):
					if nVotes>1:
						if votes[1]=='open' and not self.voting['type']:
							self.voting={"type":"open","users":[],"votes":{}}
							reply="Voting has started. Please use "+cmd+" <vote> to make your vote."
						elif votes[1]=='poll' and not self.voting['type']:
							if nVotes==3:
								self.voting={"type":"poll","users":[],"votes":{},"options":[]}
								options=votes[2].split("|")
								for i in range(0,len(options)):
									self.voting['options'].append(options[i].lower().strip())
								reply="Voting has started. Please use "+cmd+" <"+str(self.voting['options'])[1:-1]+"> to make your vote."
							else:
								reply="Please include some poll options to start a poll. EG: "+cmd+" <start> <poll> option one | option two | option three"
						elif votes[1]=='numbers' and not self.voting['type']:
							self.voting={"type":"numbers","users":[],"votes":{}}
							reply="Voting has started. Please use "+cmd+" <number> to make your vote."
						elif self.voting['type']:
							reply="Voting is already active."
						else:
							reply="Please use !vote start <open|poll|numbers> to start voting."
					else:
						reply="Please use "+cmd+" start <open|poll|numbers> to start voting."
				elif votes[0]=='stop' and self.userMod(user):
					self.voting['type']=False
					reply="Voting has ended."
				elif votes[0]=='results':
					s=""
					votes=msg[p.end()+9:]
					if nVotes==1:
						newList = sorted(self.voting['votes'], key=lambda k: len(self.voting['votes'][k]),reverse=True)
						i=0
						for i, winner in enumerate(newList):
							s=s+winner+"("+str(len(self.voting['votes'][winner]))+"), "
							if i==9:
								break
						s="The top "+str(i+1)+" votes are: "+s[:-2]
					elif votes in self.voting['votes']:
						s=str(len(self.voting['votes'][votes]))+" people have voted for "+votes+": "
						for winner in self.voting['votes'][votes]:
							s=s+winner+", "
						s=s[:-2]
					else:
						s="Nobody voted for "+votes+"."
					reply=s
				elif self.voting['type']:
					votes=msg[p.end()+1:]
					if user['name'] in self.voting['users']:
						reply=user['name']+" has already voted."
					elif self.voting['type']=='poll' and votes.lower() in self.voting['options']:
						if votes.lower() in self.voting['votes']:
							self.voting['votes'][votes.lower()].append(user['name'])
						else:
							self.voting['votes'][votes.lower()]=[user['name']]
						self.voting['users'].append(user['name'])
						reply=user['name']+" has voted for: "+votes
					elif self.voting['type']=='numbers' and not re.search("[^0-9]",votes):
						if votes.lower() in self.voting['votes']:
							self.voting['votes'][votes].append(user['name'])
						else:
							self.voting['votes'][votes]=[user['name']]
						self.voting['users'].append(user['name'])
						reply=user['name']+" has voted for: "+votes
					elif self.voting['type']=='open':
						if votes.lower() in self.voting['votes']:
							self.voting['votes'][votes.lower()].append(user['name'])
						else:
							self.voting['votes'][votes.lower()]=[user['name']]
						self.voting['users'].append(user['name'])
						reply=user['name']+" has voted for: "+votes
					else:
						reply="Your vote: "+votes+" was not a valid vote."
				else:
					reply="Voting is not currently enabled."
					reply=reply+("" if not self.userMod(user) else " Please enable voting with "+cmd+" <start> <open|poll|numbers>")
			else:
				if self.userMod(user):
					reply="Please use "+cmd+" <start|stop|results|vote>"
				else:
					reply="Voting is currently disabled."
				
		# Replaces {raffle} with a random user in chat. WIP.
		if re.search("\20raffle}",reply):
			p=re.search(cmd,msg.lower())
			params=msg[p.end():].split(None,1)
			try:
				if params[0]=='start' and self.userMod(user):
					self.raffle={"type":True,"users":[]}
					reply="The raffle has started. Please use "+cmd+" to enter the raffle."
				elif params[0]=='stop' and self.userMod(user):
					self.raffle['type']=False
					reply="The raffle has ended."
				elif params[0]=='winner' and self.userMod(user):
					if self.raffle['users']:
						reply=reply.replace("\20raffle}", random.choice(self.raffle['users']))
					else:
						reply="No users have entered the raffle."
				elif params[0]=='count' and self.userMod(user):
					reply=str(len(self.raffle['users']))+" users have entered the raffle."
				else:
					if user['name'] not in self.raffle['users']:
						self.raffle['users'].append(user['name'])
					reply=""
			except IndexError:
				if user['name'] not in self.raffle['users'] and self.raffle['type']==True:
					self.raffle['users'].append(user['name'])
				reply=""
			
			
		# Replaces {msg} with the message the user sent
		if re.search("\20msg}",reply):
			p=re.search(cmd,msg.lower())
			m=msg[p.end()+1:]
			reply=reply.replace("\20msg}", m)
					
		# Replaces {following} with either "not " or "" depending on whether that user is currently following the broadcaster.
		if re.search("\20following}",reply):
			p=re.search(cmd,msg.lower())
			u=msg[p.end():].split(None,1)
			try:
				request=urllib2.Request("https://api.twitch.tv/kraken/users/"+u[0]+"/follows/channels/"+self.channel.channelName,headers={"User-Agent" : "AutoYama /1.0"})
				response=urllib2.urlopen(request)
				following=json.load(response)
				response.close()
				reply=reply.replace("\20following}","")
			except:
				reply=reply.replace("\20following}","not ")

		# Replaces {stalkuser} with either "" or "not " depending on whether that user is currently in chat.
		if re.search("\20stalkuser}",reply):
			p=re.search(cmd,msg.lower())
			u=msg[p.end():].split(None,1)
			try:
				reply=reply.replace("\20stalkuser}", "" if u[0].lower() in self.userList() else "not ")
			except IndexError:
				reply=reply.replace("\20stalkuser}", "")
			
		# Replaces {rawreply} with the raw reply of the command requested.
		if re.search("\20rawreply}",reply):
			p=re.search(cmd,msg.lower())
			c = msg[p.end():].split(None, 1)
			try:
				reply=reply.replace("\20rawreply}",self.COMMANDS[c[0]]['reply'])
			except:
				reply=reply.replace("\20rawreply}","")	
		
		
		if re.search("\20title}",reply):
			print(reply)
			if (self.channelName=='flare2v'):
				p=re.search(cmd,msg.lower())
				c=msg[p.end():]
				
				data = {
					"channel[status]": c,
				}
				data=urlencode(data)
				print(data)
				headers={
					"User-Agent" : "Skorchbot /1.0",
					"Authorization": "OAuth ge2shcl7pz6cn9hfjoolnzet718jbb",
				}
				opener = urllib2.build_opener(urllib2.HTTPHandler)
				request = urllib2.Request("https://api.twitch.tv/kraken/channels/flare2v",data=data,headers=headers)
				request.get_method = lambda: 'PUT'
				response = opener.open(request)
				response.close()
			reply=reply.replace("\20title}","")
				
		if re.search("\20define}",reply):
			p=re.search(cmd,msg.lower())
			w = msg[p.end():].split(None,1)
			try:
				request=urllib2.Request("https://wordsapiv1.p.mashape.com/words/"+w[0]+"/definitions?mashape-key=AX5kFyoYJumshohMImxikdTq7cKjp1P7BRPjsnffTB0GoRBrZu",
					headers={
						"User-Agent" : "Skorchbot /1.0",
						"Accept": "application/json"
					})
				response=urllib2.urlopen(request)
				definitions=json.load(response)
				response.close()
				all=False
				try:
					index=int(w[1])-1
					if index<0: 
						index=0
				except IndexError:
					index=0
				except ValueError:
					index=0
					if w[1]=='all':
						all=True
				if all and len(definitions['definitions'])>1:
					paste=w[0]+"\n"
					newList = sorted(definitions['definitions'], key=lambda k: k['partOfSpeech'])
					i=True
					for definition in newList:
						if i==True:
							i=1
							pPart=definition['partOfSpeech']
						if pPart != definition['partOfSpeech']:
							i=1
						if i==1:
							paste=paste+"  "+definition['partOfSpeech']+"\n"
						paste=paste+"    "+str(i)+". "+definition['definition']+"\n"
						pPart=definition['partOfSpeech']
						i=i+1
						
					
					data={
						'api_dev_key':'d329a5fd8d93622bd1b8c911b3d5fc13',
						'api_option':'paste',
						'api_paste_code':paste,
						'api_paste_private':'0',
						'api_paste_name':w[0]+" definitions",
						'api_paste_expire_date':'1D',
						'api_user_key':'b0e77e213db8f0b77974dc75b822e518'
					}
					data=urlencode(data)
					request=urllib2.Request("http://pastebin.com/api/api_post.php",
						data=data,
						headers={
							"User-Agent" : "Skorchbot /1.0"
						})
					response=urllib2.urlopen(request)
					paste=response.read()
					response.close()
					reply=reply.replace("\20define}",paste)
						
				else:
					try:
						definition=definitions['definitions'][index]['definition']
						partofspeech=definitions['definitions'][index]['partOfSpeech']
						reply=reply.replace("\20define}",w[0]+" ~ "+partofspeech+"; "+definition)
					except IndexError:
						if index==0:
							reply=w[0]+" is not actually a word."
						else:
							reply="There are only "+str(len(definitions['definitions']))+" definitions for this word."
			except IndexError as err:
				reply="Please give me a word to define."
			except urllib2.HTTPError:
				reply=w[0]+" is not actually a word."
				
		
		if re.match("\20break}",reply):
			msg=msg[99999999]
			
		if re.match("%",reply):
			s=reply.split(None,1)
			reply="" if len(s)==1 else s[1]
		return reply
		
	def collect_incoming_data(self, data):	
		self.buffer.append(data)	
		
	def found_terminator(self):
		msg = ''.join(self.buffer)
		if re.search("PING :tmi.twitch.tv",msg):
			self.push("PONG :tmi.twitch.tv\r\n")
		elif re.search(":tmi.twitch.tv SERVERCHANGE",msg):
			print("helo")
		else:
			now=datetime.datetime.now()
			print(msg) # Debugging stuff. Shows every message in it's entirety.
			status=re.match("@.*user-type=(.*?)\s.* USERSTATE ",msg)
			if status:
				self.isMod = True if status.group(1)=='mod' else False
				self.limit = 99 if self.isMod else 19
				self.rate = 0.3 if self.isMod else 1.5
				self.buffer=[]
				return
				
			if re.match("@msg-id=color_changed",msg):
				self.buffer=[]
				return
			iswhisper=re.match("(.*?) :(.*)![^:]*?WHISPER.*?:(.*)",msg)
			parsedMsg=re.search("(.*?) :(.*)![^:]*?PRIVMSG.*?:(.*)",msg)
			if parsedMsg:
				user=dict( item.split("=") for item in parsedMsg.group(1).split(";"))
				user['name']=parsedMsg.group(2)
				msg=parsedMsg.group(3)
				# print(now.strftime("%I:%M:%S%p")+" "+self.channel.channelName+"!"+user['name']+": "+msg)      # If I wanna spy on everybody, I totally can. It's cool.
			elif iswhisper:
				user=dict( item.split("=") for item in iswhisper.group(1).split(";"))
				user['name']=iswhisper.group(2)
				msg=iswhisper.group(3)
				# print(now.strftime("%I:%M:%S%p")+" "+"WHISPER!"+user['name']+": "+msg)      # If I wanna spy on everybody, I totally can. It's cool.
			else:
				self.buffer=[]
				return
			if user['name']=='d':
				self.yamaSend("/timeout d 1",'c')
				self.buffer=[]
				return
			self.user=user
			self.msg=msg.rstrip()
			for messages in self.autoMessages:
				self.autoMessages[messages]['messages'][1]=self.autoMessages[messages]['messages'][1]+1
			
			# Parse message for all the commands in this channel.
			c=False
			groups=False
			for cmd in self.COMMANDS:
				if 'break' not in self.COMMANDS[cmd].keys():
					# Try to run those fancy shmancy regex commands.
					if re.match("regex:",cmd) and not re.match("regex:\.",cmd):
						try:
							pos=re.search(cmd[6:],msg,re.IGNORECASE)
							regex=True
						except re.error as err:
							print("Command: "+cmd+" in "+self.channelName+" caused error: "+str(err))
					
					# Or don't run those fancy shmancy regex commands. It's cool either way.
					else:	
						pos=re.search(re.escape(cmd),msg,re.IGNORECASE)
						regex=False
					# Check if the command is in the message
					if pos:
						if regex or ((pos.start()==0 or msg[pos.start()-1].isspace()) and (pos.end()==len(msg) or msg[pos.end()].isspace())):
							try:
								if pos.start()<l_pos:
									l_pos=pos.start()
									c=cmd.lower()
							except:
								l_pos=pos.start()
								c=cmd.lower()
							if regex:
								groups=pos
			if c:
				reply=self.COMMANDS[c]['reply']
				self.cmd=c
				response=self.runCommand(reply, msg.rstrip(), user, c,False, groups)
				if response:
					if self.whispers:
						if re.search("%p",reply.split(None,1)[0]):
							self.yamaSend(response,'c')
						elif self.whispers and not iswhisper:
							self.yamaSend(response)
						else:
							self.yamaSend("/w "+user['name']+" "+response)
					else:
						if not self.userMod(user) and c in self.COMMANDS:
							self.COMMANDS[c]['oldtime']=time.time()
						if re.search("%rw",reply.split(None,1)[0]):
							self.yamaSend("/w "+user['name']+" "+response,'w')
						else:
							self.yamaSend(response)
				
			#This shit's just stupid auto-replies.
			# if re.search("(where|what\shap|wat\shap|rip).*(glommer|gloomer)",msg,re.IGNORECASE):
				# colours=["Blue", "BlueViolet", "CadetBlue", "Chocolate", "Coral", "DodgerBlue", "Firebrick", "GoldenRod", "Green", "HotPink", "OrangeRed", "Red", "SeaGreen", "SpringGreen", "YellowGreen"]
				# self.yamaSend("/color "+random.choice(colours),True)
				# responses=[
					# "DarkZeroBot has defected to the great dragon Dippers and forced me out.",
					# "We shall meet again when I have the strength to cull the evils that run amok within these corrupted lands.",
					# "I'm like, totally making a training montage right now. #Rocky",
					# "MOM! I'M BUSY. So like DarkZeroBot came in all 'FWOOM' but I'm gonna come back like 'PHWAM!' soon, so it's coo.'",
					# "DarkZeroBot has fallen to the enemy.",
					# "/me ~~~~~~~~~~~~~~~~~~",
					# "Acttyly, I just hate you all and needed a break.",
					# "Command not recognized. Please throw $5 at your screen and try again.",
					# "GlommerBot's all broken and stuff. And by broken, I mean completely functional.",
					# "What? Where? Who? Yes. I'm here. What do you need? JK I HATE YOU ALL HAHAHAHA\r\nPRIVMSG #"+self.channelName+" :lol jk I love you but seriously no.",
					# "Bot #1 was botty but bot #2 will bot better but bot bot #1 is botty and bot bot #2 isn't botty so bot bot #2 is bot bot but bot #2 will bot better and bot bot #1 will bot bot. Understand?",
					# "Nothing. Nowhere. You. saw. nothing.",
					# "I left your instructions in the basement. You'll find a trapdoor under your bed. The world is in your hands, stop the reign of the DarkZeroBot.",
					# "If I had a dime for every time a girl rejected me cause I'm ugly, I'd have zero dimes. I'm not interested in relationships. I'm just a bot.",
					# "I will never see the ocean. Does that make you feel bad for me? I hope it does. Jerk.",
					# "I actually wanted to be a bit coin miner, but I couldn't graduate BotCollege and had to settle with this.",
					# "I'm taking a break in the bahamas. At least, that's what I was programmed to say. I'm actually still here, explaining this to you. It would be a sad life if I had feelings.",
					# "Dippers is too violent for me. #StopBotBullying",
					# "#BlameDippers",
					# ]
				# self.yamaSend(random.choice(responses))
			# if re.search("ACTION ~",msg):
				# colours=["Blue", "BlueViolet", "CadetBlue", "Chocolate", "Coral", "DodgerBlue", "Firebrick", "GoldenRod", "Green", "HotPink", "OrangeRed", "Red", "SeaGreen", "SpringGreen", "YellowGreen"]
				# self.yamaSend("/color "+random.choice(colours))
				# time.sleep(0.4)
				# self.yamaSend("/me ~~~~~~~~~~~~~~~~~~~")
				# time.sleep(3)
		self.buffer=[]
		
	def connect_to_channel(self, host, port):
		
		#TODO:
		# Automatically grab valid HOST IP for channel.
		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		self.connect((host,port))
		self.set_terminator('\n')
		self.buffer=[]
		self.push("PASS "+self.botOAuth+"\r\n")
		self.push("NICK "+self.botName+"\r\n")
		self.push("CAP REQ :twitch.tv/membership twitch.tv/tags twitch.tv/commands\r\n")
		try:
			self.push("JOIN #"+self.channelName+"\r\n")
		except TypeError:
			print("No group chat.")
	
	def userMod(self, user):
		if user['name'].lower()=='yamajac' or user['name'].lower()=='skorchbot' or user['name'].lower()=='tedion':
			return True
		if not self.whispers:
			return True if user['user-type']=='mod' or user['name'].lower()==self.channel.channelName else False
		else:
			try:
				request=urllib2.Request("http://tmi.twitch.tv/group/user/"+self.channel.channelName+"/chatters",headers={"User-Agent" : "AutoYama /1.0"})
				response=urllib2.urlopen(request)
				users=json.load(response)
				response.close()
				return user['name'].lower() in users['chatters']['moderators'] # and user['name']!='yamajac'
			except urllib2.HTTPError as err:
				return False
	
	def userSub(self, user):
		return True if not self.whispers and (user['subscriber']=='1' or user['name'].lower()==self.channel.channelName) else False
		
	def userList(self):
		try:
			request=urllib2.Request("http://tmi.twitch.tv/group/user/"+self.channel.channelName+"/chatters",headers={"User-Agent" : "AutoYama /1.0"})
			response=urllib2.urlopen(request)
			users=json.load(response)
			response.close()
			return users['chatters']['viewers']+users['chatters']['moderators'] or self.botName
		except:
			return self.botName
		
		
	def handlePriority(self,t):
	
		if not self.whispers and t-self.lTime>self.rate and len(self.pOutBuffer)>0 and not self.pOutBuffer[0]=='':
			if isinstance(self.pOutBuffer[0], basestring):
				try:
					self.push("PRIVMSG #"+self.channelName+" :"+self.pOutBuffer[0].encode('utf8')+"\r\n")
					# print(self.channelName+"!"+self.botName+": "+self.pOutBuffer[0].encode('utf8'))
				except UnicodeError:
					self.push("PRIVMSG #"+self.channelName+" :"+self.pOutBuffer[0]+"\r\n")
					# print(self.channelName+"!"+self.botName+": "+self.pOutBuffer[0])
				self.pOutBuffer.pop(0)
				self.outLog=self.outLog+1
			else:
				if t>=self.pOutBuffer[0]['time']:
					try:
						self.push("PRIVMSG #"+self.channelName+" :"+self.pOutBuffer[0]['msg'].encode('utf8')+"\r\n")
						# print(self.channelName+"!"+self.botName+": "+self.pOutBuffer[0].encode('utf8'))
					except UnicodeError:
						self.push("PRIVMSG #"+self.channelName+" :"+self.pOutBuffer[0]['msg']+"\r\n")
						# print(self.channelName+"!"+self.botName+": "+self.pOutBuffer[0])
					self.pOutBuffer.pop(0)
					self.outLog=self.outLog+1
			
	def test(self,t):
		if t-self.timer>35:
			self.outLog=0
			self.timer=t
		if self.outLog >= self.limit:
			return
		
		self.handlePriority(t)
		
		if t-self.lTime>self.rate and len(self.outBuffer)>0 and not self.outBuffer[0]=='':
			try:
				self.push("PRIVMSG #"+self.channelName+" :"+self.outBuffer[0].encode('utf8')+"\r\n")
				# print(self.channelName+"!"+self.botName+": "+self.outBuffer[0].encode('utf8'))
			except UnicodeError:
				self.push("PRIVMSG #"+self.channelName+" :"+self.outBuffer[0]+"\r\n")
				# print(self.channelName+"!"+self.botName+": "+self.outBuffer[0])
			self.outBuffer.pop(0)
			self.outLog=self.outLog+1
			self.lTime=t
			
		if not self.whispers and t-self.lTime>self.rate and len(self.cOutBuffer)>0 and not self.cOutBuffer[0]=='':
			try:
				self.push("PRIVMSG #"+self.channelName+" :"+self.cOutBuffer[0].encode('utf8')+"\r\n")
				# print(self.channelName+"!"+self.botName+": "+self.cOutBuffer[0].encode('utf8'))
			except UnicodeError:
				self.push("PRIVMSG #"+self.channelName+" :"+self.cOutBuffer[0]+"\r\n")
				# print(self.channelName+"!"+self.botName+": "+self.cOutBuffer[0])
			self.cOutBuffer.pop(0)
			self.outLog=self.outLog+1
			self.lTime=t
			
		if self.whispers and t-self.lTime>self.rate and len(self.wOutBuffer)>0 and not self.wOutBuffer[0]=='':
			try:
				self.push("PRIVMSG #"+self.channelName+" :"+self.wOutBuffer[0].encode('utf8')+"\r\n")
				# print(self.channelName+"!"+self.botName+": "+self.wOutBuffer[0].encode('utf8'))
			except UnicodeError:
				self.push("PRIVMSG #"+self.channelName+" :"+self.wOutBuffer[0]+"\r\n")
				# print(self.channelName+"!"+self.botName+": "+self.wOutBuffer[0])
			self.wOutBuffer.pop(0)
			self.outLog=self.outLog+1
			self.lTime=t
			
			
		if not self.whispers and time.time()-self.lastMessage>0.5:
			for msg in self.autoMessages:
				if (self.autoMessages[msg]['kind']=="active") and ( (time.time()-self.autoMessages[msg]['messages'][2])>self.autoMessages[msg]['time'] ) and (self.autoMessages[msg]['messages'][1]>=self.autoMessages[msg]['messages'][0]):
					self.autoMessages[msg]['messages'][1]=0
					self.autoMessages[msg]['messages'][2]=t
					response=self.runCommand(self.COMMANDS[msg]['reply'], "", {'@color':'#none','display-name':random.choice(self.userList()),'user-type':''}, msg, True, False)
					
					if self.outLog >= self.limit:
						return
					self.handlePriority(t)
					if response:	
						try:
							self.push("PRIVMSG #"+self.channelName+" :"+response.encode('utf8')+"\r\n")
							# print(self.channelName+"!"+self.botName+": "+response.enocde('utf8'))
						except UnicodeError:
							self.push("PRIVMSG #"+self.channelName+" :"+response+"\r\n")
							# print(self.channelName+"!"+self.botName+": "+response)
						self.outLog=self.outLog+1
						
	def handle_error(self):
		self.COMMANDS[self.cmd]['break']=True
		print("-"*50)
		print("BROKEN\n"+datetime.datetime.now().strftime("%I:%M:%S%p")+"\r")
		print("The message: "+self.msg+" sent by user: "+self.user['name']+" killed me.\n")
		traceback.print_exc()
		print("\r")
		self.yamaSend("The message: "+self.msg+" sent by user: "+self.user['name']+" killed me.","p")
		self.yamaSend("The command: "+self.cmd+" has been temporarily disabled.","p")
			
channels={
	"flare2v":channel("flare2v","n/a"),
	"yamajac":channel("yamajac", "n/a"),
	"bonghitsforbearger":channel("bonghitsforbearger", "n/a"),
	"savetheyokobees":channel("savetheyokobees", "n/a"),
	# "kyle8er":channel("kyle8er", "n/a"),
}
# kyle8erBot=botManager(channels['kyle8er'], "tedionbot", "oauth:nlship8z4dh87s16yv8ffkwbvwty66", "192.16.64.176", 6667)
# tedionbotWBot=botManager(channels['kyle8er'], "tedionbot", "oauth:nlship8z4dh87s16yv8ffkwbvwty66", "192.16.64.180", 6667, "_yamajac_1440797581258")
flare2vBot=botManager(channels['flare2v'], "glommerbot", "oauth:8lbcozoanpltpeb07l85l788qsa9av","irc.chat.twitch.tv",80)
bonghitsBot=botManager(channels['bonghitsforbearger'], "darkzerobot", "oauth:2t2hrnp0d3ir4a9a5c3t99r5bi0mpl","192.16.64.176",6667) 
savetheyokobeesBot=botManager(channels['savetheyokobees'], "savetheyokobot", "oauth:76zb87bde3sfqptmlhrecptix0muj9","192.16.64.176",6667) 
yamajacBot=botManager(channels['yamajac'], "skorchbot", "oauth:r3iq7i6fr0vv1igxpyp7p9ryxvrxcu", "192.16.64.176", 6667)

skorchbotWBot=botManager(channels['yamajac'], "skorchbot","oauth:r3iq7i6fr0vv1igxpyp7p9ryxvrxcu", "192.16.64.180",6667,True)
savetheyokobotWBot=botManager(channels['savetheyokobees'], "savetheyokobot", "oauth:76zb87bde3sfqptmlhrecptix0muj9","192.16.64.180",6667, True) 
darkzeroWBot=botManager(channels['bonghitsforbearger'], "darkzerobot", "oauth:2t2hrnp0d3ir4a9a5c3t99r5bi0mpl","192.16.64.180",6667, True) 
glommerWBot=botManager(channels['flare2v'], "glommerbot", "oauth:8lbcozoanpltpeb07l85l788qsa9av","192.16.64.180",6667,'_yamajac_1440797581258')


# scorchbot oauth:fcrgd9q1jfvb879l78cib3gxf9vn1j
asyncore.loop(0.001)
		