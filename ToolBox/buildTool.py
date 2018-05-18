#! /usr/bin/env python
# encoding: utf-8
'''
Created on Aug 16, 2016

@author: shj
'''
import os
import sys
import json
import stat
import time
import subprocess

if sys.version_info.major == 2:
	from xmlrpclib import Fault
else:
	from xmlrpc.client import Fault

class BuildError(Fault):
	"""
	参数错误
	"""
	def __init__(self, message="Build Error."):
		Fault.__init__(self, 10, message)
		
class BuildTool():
	def __init__(self, sGoRoot, lGoPaths):
		self.goRoot = sGoRoot
		self.goPath = ":".join(lGoPaths)
		if sys.platform == "win32":
			self.goPath = ";".join(lGoPaths)
		
	def setGoBuildEnv(self):
		os.environ["GOROOT"] = self.goRoot
		os.environ["GOPATH"] = self.goPath
		oldPath = os.environ["PATH"]
		
		goBin = os.path.join(self.goRoot, "bin")
		if sys.platform != "win32":
			os.environ["PATH"] = goBin + ":" + oldPath
		else:
			os.environ["PATH"] = goBin + ";" + oldPath

	def clearBin(self, binPath):
		fileList = os.listdir(binPath)
		
		for it in fileList:
			fullPath = os.path.join(binPath, it)
			os.remove(fullPath)
		
		return len(fileList)

	def _checkResult(self, sResult):
		if sResult.find('# ') != -1:
			return False
		return True

	def buildSigle(self, strBuildArg, strBuildPath):
		print("Begin Build `%s`..." % strBuildPath)  #
		oldPath = os.getcwd()
		os.chdir(strBuildPath)

		cmdGoBuild = "go build " + strBuildArg
		#cmdGoBuild = "%s [%s]" % (strBuildCmd, strBuildPath)
		strCurTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
		print (">>>>>%s `%s`\n" % (strCurTime, cmdGoBuild))
		
		logFile = "build.log"
		if os.path.exists(logFile):
			os.remove(logFile)
		
		with open(logFile, 'w+') as log:
			subprocess.call(cmdGoBuild, stdout=log, stderr=log, shell=True)
			log.seek(0, 0)
			buildOut = log.read()
		
		os.chdir(oldPath)

		print (buildOut)
		if not self._checkResult(buildOut):
			raise BuildError("Build `%s` Error." % strWorkName)
		
	def BuildProject(self, proConfig):
		# 检查工程是否存在
		buildPath = proConfig.get("Path", "")
		if not buildPath:
			print("[GoProjects] config has’t `Path` key")
			return False
		
		if not os.path.isdir(buildPath):
			print("[GoProjects] config Path:`%s` not exist" % buildPath)
			return False

		self.setGoBuildEnv()

		buildArgs = proConfig.get("BuildArg", "")
		try:
			self.buildSigle(buildArgs, buildPath)
		except BuildError as e:
			print(e.faultString)
			return False

		return True

if __name__ == "__main__":
	jsonCfg = u"./buildConfig.json"
	config = {}
	with open(jsonCfg, u'r') as rf:
		config = json.load(rf)

	# go 安装根目录
	GoRoot = config.get("GoRoot", "")
	if not GoRoot:
		print("buildConfig.json has't key:`GoRoot`")
		sys.exit()
	if not os.path.isdir(GoRoot):
		print("GoRoot:`%s` is not exist" % GoRoot)
		sys.exit()

	# Go库目录 
	GoPaths = config.get("GoPaths", [])
	if not GoPaths:
		print("buildConfig.json has't key:`GoPaths`")
		sys.exit()
	
	for iGoPath in GoPaths:
		if not os.path.isdir(iGoPath):
			print("GoPath:`%s` is not exist" % iGoPath)
			sys.exit()

	build = BuildTool(GoRoot, GoPaths)
	
	GoProjects = config.get("GoProjects", {})
	bulids = GoProjects.keys()
	if len(sys.argv) < 2:
		print("please input build project or -all(will build all)\n\tOptProject:[%s]" % ", ".join(bulids))
		sys.exit()
	else:
		keys = []
		for it in sys.argv[1:]:
			if it not in bulids:
				if it == u"-all":
					keys = bulids[:]
					break
				else:
					print("GoProjects has't `%s`" % it)
					sys.exit()
			else:
				keys.append(it)

		bulids = keys[:]
	
	for it in bulids:
		proConfig = GoProjects.get(it, {})
		if not proConfig: continue
		build.BuildProject(proConfig)