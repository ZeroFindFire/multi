#coding=utf-8

import multi 
import socket 
"""

python
from multi import scan 
from testz.test import time
s = scan.TCPScan('172.0.0.0/20',22)
s = scan.TCPScan('182.0.0.0/12',22)
s.mark_shows = False 
s = scan.TCPScan('192.168.0.1/19',22)
ips = time(s.work,False)[0]
ssh = scan.SSHScan(ips)
ssh.mark_shows = False 
logins = time(ssh.work,False)[0]


"""
class SSHScan(multi.Multi):
	def __init__(self, ips, user = 'root', pwd = 'jcb410', loop_size = -1):
		super(SSHScan,self).__init__(True)
		size = len(ips)
		self.size = size
		self.user = user 
		self.pwd = pwd 
		self.ips = ips 
		if loop_size > 0:
			size = min(loop_size,size)
		for i in xrange(size):
			ip = ips[i]
			attrs = self.attrs([ip,user,pwd])
			self.init_push(ssh_check, attrs, ip)
		self.index = i + 1
		self.logins =[]
	def deal(self, response, remain, succeed):
		if self.index < self.size:
			ip = self.ips[self.index]
			attrs = self.attrs([ip,self.user, self.pwd])
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
class TCPScan(multi.Multi):
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


def tcp_open(ip,port):
	server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server.settimeout(5.0)
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

