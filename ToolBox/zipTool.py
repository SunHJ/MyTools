#!/usr/bin/python
# coding:utf-8

import os
import sys
import json
import zipfile
from zipfile import ZIP_DEFLATED

def is644file(name):
	f644 = [".go", ".lua", ".h", ".c", ".cpp", ".json", ".pb", ".proto", ".so", ".dll"]
	for it in f644:
		if name.endswith(it):
			return True
	return False

def fmt644Mod(path):
	if os.path.isfile(path):
		name = os.path.basename(path)
		if is644file(name):
			os.chmod(path, 0644)
	if os.path.isdir(path):
		os.chmod(path, 0755)

def dict2obj(vDict):
	class _obj:
		def __init__(self, **props):
			self.__dict__.update(props)
	return _obj(**vDict)

def ZipAll(conf):
	dstfile = conf.get(u"dst", None)
	if not dstfile:
		print(u"conf not `dst`")
		return
	
	dstpath = os.path.dirname(dstfile)
	if not dstpath: dstpath = "./"
	if not os.path.isdir(dstpath):
		os.makedirs(dstpath, 0755)

	path = conf.get(u"root", None)
	if not path:
		print(u"conf not `root`")
		return

	arcName = conf.get(u"name", None)
	if not arcName:
		arcName = os.path.basename(path)

	ziplist = conf.get(u"ziplist", {})
	if not ziplist:
		print(u"conf `ziplist` is empty")
		return
	
	with zipfile.ZipFile(dstfile, mode='w', compression=ZIP_DEFLATED) as zipF:
		zipDict(zipF, path, ziplist, arcName)

	return dstfile

def zipString(zFd, curPath, strPatern, arcName):
	if strPatern == u"all":
		appendAll(zFd, curPath, arcName)
	elif strPatern == u"file":
		appendOne(zFd, curPath, arcName)

def zipList(zFd, curPath, fList, arcName):
	for it in fList:
		tarPath = os.path.join(curPath, it)
		tarArc = os.path.join(arcName, it)
		appendOne(zFd, tarPath, tarArc)

def zipDict(zFd, curPath, fMap, arcName):
	for key, val in fMap.items():
		newPath = os.path.join(curPath, key)
		newArc = os.path.join(arcName, key)
		vType = type(val)
		if vType == unicode:
			zipString(zFd, newPath, val, newArc)
		elif vType == list:
			zipList(zFd, newPath, val, newArc)
		elif vType == dict:
			zipDict(zFd, newPath, val, newArc)

def appendOne(dst, path, arcname=""):
	print(arcname)
	fmt644Mod(path)
	dst.write(path, arcname)

def appendAll(dst, path, arcname=""):
	for it in os.listdir(path):
		arc = os.path.join(arcname, it)
		fullIt = os.path.join(path, it)
		appendOne(dst, fullIt, arc)

		if os.path.isdir(fullIt):
			appendAll(dst, fullIt, arc)

def UnZip(srczip, dstpath=""):
	if not zipfile.is_zipfile(srczip):
		print("`%s` is not zipfile")
		return
	
	if not dstpath:
		dstpath = os.path.dirname(srczip)
	
	if not os.path.isdir(dstpath):
		os.makedirs(dstpath, 0755)

	with zipfile.ZipFile(srczip, mode='r', compression=ZIP_DEFLATED) as zipF:
		zipF.extractall(dstpath)

if __name__ == "__main__":
	jsonCfg = u"./zipConfig.json"
	config = {}
	with open(jsonCfg, u'r') as rf:
		config = json.load(rf)

	zipCfg = config.keys()

	if len(sys.argv) < 2:
		print("please input pack key or -all(will pack all)\n\tOptKeys:[%s]" % ", ".join(zipCfg))
		sys.exit()
	else:
		zipKeys = []
		for it in sys.argv[1:]:
			if it not in zipCfg:
				if it == u"-all":
					zipKeys = zipCfg[:]
					break
				else:
					print("zipConfig ha't `%s`" % it)
					sys.exit()
			else:
				zipKeys.append(it)
		zipCfg = zipKeys[:]
	
	for it in zipCfg:
		print("`%s` packing..." % it)
		lfile = ZipAll(config.get(it, {}))
		if not lfile:
			print("`%s` pack faild" % it)
