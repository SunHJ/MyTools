#!/usr/bin/python
# coding: utf-8
'''
Created on 2018年5月7日

@author: SunHJ
'''
import re
import os
import sys
import json
import stat
import base64
import shutil
import urlparse
import smtplib
import datetime
import threading
import subprocess

from time import sleep
from email import encoders
from email.mime.base import MIMEBase 
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

gCodeStr = sys.getfilesystemencoding()

gConfig = None
gSubLoop = True

def sendMail(tMessages):
	if not gConfig.SmtpServer:
		return
	smtp = smtplib.SMTP()
	try:
		smtp.connect(gConfig.SmtpServer)
		smtp.login(gConfig.UserName, gConfig.PassWord)
		for itMail in tMessages:
			itMail['From'] = gConfig.FromAddr
			itMail['To'] = ','.join(gConfig.ToAddr)
			smtp.sendmail(gConfig.FromAddr, gConfig.ToAddr, itMail.as_string())
	except Exception as e:
		print e
	finally:
		smtp.quit()

def killServer(sParam):
	sPidCmd = "ps aux|grep '%s'|grep -v grep|awk '{print $2}'" % sParam
	sPid = os.popen(sPidCmd).read().strip()
	if sPid and sPid != '0':
		sKillCmd = "kill -9 %s" % sPid
		os.popen(sKillCmd).read()

class LogFile:
	def __init__(self, sName, sPath=""):
		self.fd = None
		self.memDate = None
		self.Path = sPath
		self.fullName = os.path.join(sPath, sName)
	
	def __del__(self):
		self.close()
	
	def createWrite(self, curDate=None):
		self.close()
		
		if not curDate:
			curDate = datetime.datetime.now().date()
	
		if not os.path.exists(self.Path):
			os.makedirs(self.Path)
		
		self.open(self.fullName, 'w')
		self.memDate = curDate
	
	def open(self, name, mode='r'):
		if self.fd != None:
			self.close()
		self.fd = open(name, mode)	
	
	def close(self):
		if self.fd != None:
			self.fd.close()
			self.fd = None
	
	def write(self, strWrite):
		if self.fd == None:
			return None
		
		curDate = datetime.datetime.now().date()
		if curDate != self.memDate:
			self.createWrite(curDate)
		
		return self.fd.write(strWrite)
	
	def read(self):
		if self.fd == None:
			return None
		return self.read()
	
	def tell(self):
		if self.fd == None:
			return None
		return self.fd.tell()
	
	def seek(self, offset, whence=os.SEEK_CUR):
		if self.fd == None:
			return None
		self.fd.seek(offset, whence)
	
	def flush(self):
		if self.fd == None:
			return None
		self.fd.flush()
   
	def fileno(self):
		if self.fd == None:
			return None
		return self.fd.fileno() 

class Config:
	def __init__(self, **entries):
		self.SmtpServer = ""
		self.UserName = ""
		self.PassWord = ""
		self.FromAddr = ""
		self.ToAddr = ""
		self.HostName = "TestName"
		self.ListenPort = 8000
	
	def load(self, sFileName):
		with open(sFileName) as jFile:
			jsonData = jFile.read()
		if not jsonData:
			return False
		
		conDict = json.loads(jsonData)
		self.__dict__.update(conDict)
		if not self.FromAddr:
			self.FromAddr = self.UserName
			
	def save(self, sFileName):
		with open(sFileName, "w") as jFile:
			json.dump(self.__dict__, jFile, indent=4)

class RunAgent:
	def __init__(self, sPath, sServerName, tParamList=[], sUpdatePath=""):
		self.Path = sPath
		self.ServerName = sServerName
		self.ParamList = tParamList
		self.Process = None
		self.RunCmd = ' '.join([sServerName] + tParamList)
		self.UpdatePath = sUpdatePath

		sErrFileName = ''.join(['Error_', sServerName] + tParamList)
		sErrFileName = re.sub(r'[\<=>:*?"\'|\n\r\t /]', "_", sErrFileName)
		self.errFile = LogFile(sErrFileName + '.log', sys.path[0] + "/log")
		self.Id = sErrFileName
	
	def __del__(self):
		if self.getStatus() == None:
			self.stopServer()
	   
	def getStatus(self):
		"""
			-9: 外部Kill结束
			2: 程序出现异常
			0: 已经正常结束
			None: 正在运行...
		"""
		if not self.Process:
			return False

		return self.Process.poll()
	
	def startServer(self):
		fullName = os.path.join(self.Path, self.ServerName)
		if not os.path.isfile(fullName):
			print "Path:%s Not Exists or Server:%s Not Exists." % (self.Path, self.ServerName)
			return 
		
		os.chdir(self.Path)
		if self.Process:
			self.stopServer()
		
		sRunCmd = "./" + self.RunCmd
		self.errFile.createWrite()
		print(os.getcwd(), sRunCmd)
		self.Process = subprocess.Popen(sRunCmd, shell=True, stdin=subprocess.PIPE, stdout=None, stderr=self.errFile) #
 
	def getShellOut(self):
		if not self.Process:
			return ""
		
		out = self.Process.stdout.read()
		return out
	
	def getErrorOut(self):
		if not self.Process:
			return ""
		
		err = self.Process.stderr.read()
		return err
	
	def setShellIn(self, *params):
		print(params)
		if not params:
			return

		strcmd = " ".join(params)
		print(strcmd)

		self.Process.stdin.write(strcmd)
		#print(self.Process.stdout.read())

	def stopServer(self):
		if not self.RunCmd:
			return
		killServer(self.RunCmd)
		print self.RunCmd
		self.Process = None
	
	def updateBinFile(self):
		if not os.path.exists(self.UpdatePath):
			return False
		
		srcFile = os.path.join(self.UpdatePath, self.ServerName)
		if not os.path.isfile(srcFile):
			return False
		
		if self.getStatus() != False:
			self.stopServer()
		
		dstFile = os.path.join(self.Path, self.ServerName)
		shutil.copyfile(srcFile, dstFile)
		os.chmod(dstFile, stat.S_IEXEC)
		return True
		
	def showStatus(self):
		sPidCmd = "ps aux|grep '%s'|grep -v 'grep'" % self.RunCmd
		return os.popen(sPidCmd).read().strip()
	
	def genMailBody(self, errCode):
		msg = MIMEMultipart()
		msg['Subject'] = u'%s[%s]宕机通知' % (gConfig.HostName, self.ServerName)
		
		sContent = u"ServerPath:%s\nStartCmd:%s\nErrorCode:%s" % (self.Path, self.RunCmd, errCode)
		mailContent = MIMEText(sContent, _subtype='plain', _charset='utf-8')
		msg.attach(mailContent)
		
		self.errFile.flush()
		with open(self.errFile.fullName, 'rb') as fd:
			errAttach = MIMEBase('application', 'octet-stream')
			errAttach.set_payload(fd.read())
			encoders.encode_base64(errAttach)
			errAttach.add_header('Content-Disposition', 'attachment', filename=os.path.basename(self.errFile.fullName))
			msg.attach(errAttach)
		
		return msg

class AgentManager:
	def __init__(self):
		self.AllAgent = {}
		self.CheckKeyList = []
		self.MailCount = {}
		
	def LoadConfig(self, tConfig):
		cKeys = sorted(tConfig.ServerConfig.keys())
		for itKey in cKeys:
			tServerConfig = tConfig.ServerConfig.get(itKey, {})
			sPath = tServerConfig.get("Path", "")
			mapServer = tServerConfig.get("ServerMap", {})

			if not sPath or not mapServer: continue 
			
			scrPath = tServerConfig.get("UpdatePath", "")
			for sName, tParam in mapServer.iteritems():
				agent = RunAgent(sPath, sName, tParam, scrPath)
				aId = agent.Id
				if self.AllAgent.has_key(aId):
					self.CheckKeyList.remove(aId)
					oldAgent = self.AllAgent[aId]
					if oldAgent.getStatus() == None:
						print oldAgent.RunCmd + " is Running..."
						continue

				self.AllAgent[aId] = agent
		print len(self.AllAgent)
		
	def StartOneAgent(self, nId):
		idList = sorted(self.AllAgent.keys())
		if nId < 0 or nId >= len(idList):
			return False
		
		self.AddCheck(nId)
		
		agent = self.AllAgent.get(idList[nId], None)
		if not agent:
			return False
		agent.startServer()
		return True
	
	def StopOneAgent(self, nId):
		idList = sorted(self.AllAgent.keys())
		if nId < 0 or nId >= len(idList):
			return False
		
		self.DelCheck(nId)
		
		agent = self.AllAgent.get(idList[nId], None)
		if not agent:
			return False
		agent.stopServer()
		return True

	def CheckAllAgents(self):
		mailList = []
		for it in self.CheckKeyList:
			agent = self.AllAgent.get(it, None)
			if not agent:
				continue

			if not self.MailCount.has_key(agent.RunCmd):
				self.MailCount[agent.RunCmd] = 0

			reErrorCode = agent.getStatus()
			if reErrorCode == None:
				self.MailCount[agent.RunCmd] = 0
			else:
				self.MailCount[agent.RunCmd] += 1
				if self.MailCount[agent.RunCmd] == 1:
					tMsg = agent.genMailBody(reErrorCode)
					mailList.append(tMsg)

				# 尝试重启
				agent.startServer()
		return mailList
	
	def ShowAllAgent(self):
		idList = sorted(self.AllAgent.keys())
		nId = 0
		strStatus = "%-6s%-32s%-8s%-10s" % ("ID", "Server", "Check", "Status")
		for it in idList:
			agent = self.AllAgent.get(it, None)
			if not agent: continue
			sId = "[%2d]" % nId
			sServer = agent.RunCmd
			sCheck = "False"
			if it in self.CheckKeyList:
				sCheck = "True"
			sStatus = "Stop"
			if agent.getStatus() == None:
				sStatus = "Running"

			strItem = "\n%-6s%-32s%-6s%-10s" % (sId, sServer, sCheck, sStatus)
			strStatus += strItem
			nId += 1
		print strStatus
	
	def DelCheck(self, nId):
		idList = sorted(self.AllAgent.keys())
		if nId < 0 or nId >= len(idList):
			return False
		strId = idList[nId]
		if strId in self.CheckKeyList:
			self.CheckKeyList.remove(strId)
		return True
	
	def AddCheck(self, nId):
		idList = sorted(self.AllAgent.keys())
		if nId < 0 or nId >= len(idList):
			return False
		strId = idList[nId]
		if strId not in self.CheckKeyList:
			self.CheckKeyList.append(strId)
		return True
	
	def SendCmd(self, nId, *params):
		idList = sorted(self.AllAgent.keys())
		if nId < 0 or nId >= len(idList):
			return False

		agent = self.AllAgent.get(idList[nId], None)
		if not agent:
			return False

		if agent.getStatus() != None:
			print agent.RunCmd + " has't running..."
			return False

		agent.setShellIn(*params)
		
	
	def UpdateOneBin(self, nId):
		idList = sorted(self.AllAgent.keys())
		if nId < 0 or nId >= len(idList):
			return False
		agent = self.AllAgent.get(idList[nId], None)
		if not agent:
			return False
		if agent.getStatus() == None:
			print agent.RunCmd + " is Running..."
			return False
		agent.updateBinFile()
		return True
	
	def StartAllAgent(self):
		self.CheckKeyList = []
		for key, agent in self.AllAgent.iteritems():
			agent.startServer()
			self.CheckKeyList.append(key)
		
	def StopAllAgent(self):
		self.CheckKeyList = []
		for _, agent in self.AllAgent.iteritems():
			agent.stopServer()
	
	def _getAgentStatus(self):
		reData = []
		idList = sorted(self.AllAgent.keys())
		nId = -1
		for it in idList:
			nId += 1
			agent = self.AllAgent.get(it, None)
			if not agent: continue
			tItem = {}
			tItem['Id'] = nId
			tItem["Name"] = agent.ServerName
			tItem["Path"] = agent.Path
			tItem["Status"] = agent.getStatus() == None
			reData.append(tItem)
		return reData
		
	def RequestHandle(self, qData, reMsg):
		qAction = qData.get("action", "")
		if not qAction: return
		if qAction == "GetAllStatus":
			pass
		elif qAction == "Stop":
			nId = qData.get('param', -1)
			self.StopOneAgent(nId)
		elif qAction == "Start":
			nId = qData.get('param', -1)
			self.StartOneAgent(nId)
		elif qAction == "UpBin":
			nId = qData.get('param', -1)
			self.UpdateOneBin(nId)
		
		reMsg.data = self._getAgentStatus()

class ReMessage():
	def __init__(self):
		self.msg = ""
		self.code = 0
		self.data = None
	
	def getReMsgString(self):
		tMsg = {}
		tMsg['msg'] = self.msg
		tMsg['code'] = self.code
		if self.data:
			tMsg['data'] = json.dumps(self.data)
		return json.dumps(tMsg)

class WebRequestHandler(BaseHTTPRequestHandler):
	Handler = None
	def do_POST(self):
		nDataLen = int(self.headers['content-length'])
		srcDatas = self.rfile.read(nDataLen)
		# 检查参数
		qParam = urlparse.parse_qs(srcDatas)
		qEntry = qParam.get('entry', ['hippie'])[0]
		if qEntry != "hippie":
			self.sendResponse(404, "")
			return
		
		_sData = base64.decodestring(qParam.get('data', [''])[0])
		qData = json.loads(_sData)
		
		reMsg = ReMessage()
		if self.Handler and hasattr(self.Handler, "RequestHandle"):
			self.Handler.RequestHandle(qData, reMsg)
		
		self.sendResponse(200, reMsg.getReMsgString())
	
	def sendResponse(self, nCode, strMessage):
		self.send_response(nCode)
		self.end_headers()
		self.wfile.write(strMessage)
		
def monitorThread(_id, manger):
	while gSubLoop:
		mailList = manger.CheckAllAgents()
		if mailList:
			print len(mailList)
			sendMail(mailList)
			
		sleep(gConfig.Interval)

def serviceThread(nPort, manager):
	WebRequestHandler.Handler = manager
	server = HTTPServer(('0.0.0.0', nPort), WebRequestHandler)
	print "StrRunHelperUrl: http://127.0.0.1:%d" % nPort
	server.serve_forever()

def updateResource():
	tResource = gConfig.ServerConfig.get("Resource", {})
	if tResource:
		srcPath = tResource.get("SrcPath", "")
		if not os.path.exists(srcPath):
			return

		copyMap = tResource.get("CopyMap", {})
		if not copyMap:
			return
		
		dstPath = tResource.get("DstPath", "")
		if not os.path.exists(dstPath):
			os.makedirs(dstPath)
	
		for src, dst in copyMap.iteritems():
			srcResource = os.path.join(srcPath, src)
			if not os.path.exists(srcResource):
				continue
			
			dstRespurce = os.path.join(dstPath, dst)
			if os.path.isdir(dstRespurce):
				shutil.rmtree(dstPath)
			elif os.path.isfile(dstRespurce):
				os.remove(dstRespurce)
			
			shutil.copytree(srcResource, dstRespurce)

def getAgentId(sId):
	try:
		return type(eval(sId))(sId)
	except Exception:
		return -1

def showHelp():
	strHelp = """Available commands:
	help		--print all cmd
	show		--print all server status
	startall	--start all server
	stopall		--stop all server
	stop id		--stop a server specified  by id
	start id	--start a server specified  by id
	upbin id	--update binfile. Need stop first!!!
"""
	print strHelp

def main(sConfigName):
	global gConfig
	global gSubLoop
	
	gConfig = Config()
	gConfig.load(sConfigName)
	
	mAgent = AgentManager()
	mAgent.LoadConfig(gConfig)

	mThread = threading.Thread(target=monitorThread, args=(0, mAgent))
	mThread.setDaemon(True)
	mThread.start()
	
	# sThread = threading.Thread(target=serviceThread, args=(gConfig.ListenPort, mAgent))
	# sThread.setDaemon(True)
	# sThread.start()
	
	while True:
		srcCmdIn = raw_input("Wait CMD->")
		cmdInList = srcCmdIn.lower().strip().split()
		if not cmdInList: continue
		
		sCmd = cmdInList[0]
		if sCmd == "q" or sCmd == "exit" or sCmd == "quit":  # 退出
			gSubLoop = False
			mAgent.StopAllAgent()
			break

		elif sCmd == "help":
			showHelp()
			
		elif sCmd == "show":
			mAgent.ShowAllAgent()
		
		elif sCmd == "startall":
			mAgent.StartAllAgent()
		
		elif sCmd == "stopall":
			mAgent.StopAllAgent()
		
		elif sCmd == "start":
			if len(cmdInList) < 2:
				print "Please input serverId"
				continue
			nId = getAgentId(cmdInList[1])
			mAgent.StartOneAgent(nId)
			
		elif sCmd == "stop":
			if len(cmdInList) < 2:
				print "Please input serverId"
				continue
			nId = getAgentId(cmdInList[1])
			mAgent.StopOneAgent(nId)
		
		elif sCmd == "cmd":
			if len(cmdInList) < 3:
				print "Please input `serverid cmd`"
				continue
			nId = getAgentId(cmdInList[1])
			mAgent.SendCmd(nId, *cmdInList[2:])
		
		elif sCmd == "upbin":
			if len(cmdInList) < 2:
				print "Please input serverId"
				continue
			nId = getAgentId(cmdInList[1])
			mAgent.UpdateOneBin(nId)
			
		#elif sCmd == "upre":
		#	updateResource()
			
		else:
			print("UnKnown CMD:" + srcCmdIn)
	
if __name__ == "__main__":
	conf = "config.json"
	if len(sys.argv) > 1:
		conf = sys.argv[1]
	main(conf)
