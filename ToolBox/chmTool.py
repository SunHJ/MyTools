#!/usr/bin/python
# coding:utf-8

import os
import sys
import stat

exeFile = ["lua", "luac", "skynet", "clientbot", "luaclientbot"]
#srcStuff = [".h", ".c", ".cpp", ".go", ".lua", ".json", ".py"]

def chmodAll(path):
	if os.path.isfile(path):
		name = os.path.basename(path)
		if name in exeFile or \
		name.endswith(".out") or \
		name.endswith(".py") or \
		name.endswith(".sh"):
			os.chmod(path, 0744)
		else:
			os.chmod(path, 0644)
	elif os.path.isdir(path):
		os.chmod(path, 0755)
		for it in os.listdir(path):
			newpath = os.path.join(path, it)
			chmodAll(newpath)

if __name__ == "__main__":
	if len(sys.argv) < 2:
		print("Please input path or file")
		sys.exit()
	
	for it in sys.argv[1:]:
		chmodAll(it)