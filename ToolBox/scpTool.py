#!/usr/bin/python
# coding:utf-8

import os
import sys
import json
import stat
import paramiko

def dict2obj(vDict):
	class _obj:
		def __init__(self, **props):
			self.__dict__.update(props)
	return _obj(**vDict)

def ssh_scp_put(ip, user, pwd, localfile, remotefile):
	trans = paramiko.Transport((ip, 22))
	trans.connect(username=user, password=pwd)
	sftp = paramiko.SFTPClient.from_transport(trans)
	sftp.put(localfile, remotefile)
	trans.close()

	#ssh = paramiko.SSHClient()
	#ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	#ssh.connect(ip, 22, user, password)
	#stdin, stdout, stderr = ssh.exec_command(u'date')
	#print(stdout.read())
	#sftp = paramiko.SFTPClient.from_transport(ssh.get_transport())

def showProcess(sent, total):
	percent = 1.0*sent/total
	num_count = 50
	num_arrow = int(num_count * percent)
	num_line = num_count - num_arrow
	process_bar = "\r    [%s%s]%.2f%%" % (">"*num_arrow, " "*num_line, percent*100)
	sys.stdout.write(process_bar)
	sys.stdout.flush()
	#print process_bar ,

def scpFileToRemote(hostKey, param):
	hostCfg = config.get(hostKey, {})
	cfg = dict2obj(hostCfg)
	sendKeys = cfg.sendConfig.keys()
	if param not in sendKeys:
		if param != "-all":
			print("unknown send key for `%s`" % hostKey)
			return
	else:
		sendKeys = [param]
	
	trans = paramiko.Transport((cfg.host, 22))
	trans.connect(username=cfg.user, password=cfg.pwd)
	sftp = paramiko.SFTPClient.from_transport(trans)
	if not sftp:
		print("[%s] host`%s` send faild" % (hostKey, cfg.host))
		return

	for it in sendKeys:
		sCfg = cfg.sendConfig.get(it, {})
		sc = dict2obj(sCfg)
		if not sc.name: continue

		localfile = os.path.join(sc.local, sc.name)
		remotefile = os.path.join(sc.remote, sc.name)
		if not os.path.exists(localfile):
			print("`%s` `%s` local is not exists" % (hostKey, it))
			continue

		print("send `%s` to [%s]:%s" % (localfile, hostKey, sc.remote))
		sftp.put(localfile, remotefile, callback=showProcess)
		print ""

	trans.close()

if __name__ == "__main__":
	jsonCfg = u"./scpConfig.json"
	config = {}
	with open(jsonCfg, u'r') as rf:
		config = json.load(rf)
	
	if len(sys.argv) < 3:
		print("please input hostkey(-all) sendkey(-all)")
		sys.exit()
	
	hosts = config.keys()
	param1 = sys.argv[1]
	if param1 not in hosts:
		if param1 != "-all":
			print("scpConfig has't host key`%s`" % param1)
			sys.exit()
	else:
		hosts = [param1]
	
	param2 = sys.argv[2]
	for it in hosts:
		scpFileToRemote(it, param2)