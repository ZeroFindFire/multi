#coding=utf-8
import pyperclip
import sys 
l = len(sys.argv)
addparm = '*.py'
msg = 'update'
if l > 1:
	addparm = sys.argv[1]
	if l > 2:
		msg = sys.argv[2]
user = 'asdf'
token = 'tmp'
pyperclip.copy("git add %s\r\ngit commit -m '%s'\r\ngit push\r\n%s\r\n%s\r\n"%(addparm,msg,user,token))
