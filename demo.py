#coding=utf-8
import multi
import requests

"""

init_push必须调用
如果你只需要一次性进行所有多线程运行，你只需要调用init_push
如果你需要分批运行多线程，第一批需要调用init_push，剩下的需要调用push

init_push 和 push 的参数格式都为：
func, attrs, remain, callback
	func为需要运行的函数，
	attrs是传递给func的参数，需要用Multi.attrs函数创建
	比如你想运行的是 test(6,"name", age=10, healthy = True)
	attrs需要如此创建：
		attrs = Multi.attrs([6,"name"],dict(age=10,healthy=True))
	remain为保留值，将传递给callback，可为空
	callback为回调函数，可为空，空时调用类的默认函数deal，callback形式为： 
		callback(response, remain, succeed)
		response 为函数func的返回值
		succeed用来判断函数是否运行成功，如果func中抛出异常，则succeed为False

"""
import time
import random
class Test(multi.Multi):
	def __init__(self, single_thread_for_feedback=False):
		multi.Multi.__init__(self, single_thread_for_feedback)
		self.init_objs()
		list_attrs = ["http://www.baidu.com"]
		map_attrs = {"timeout":10}
		attrs = self.attrs(list_attrs,map_attrs)
		self.init_push(requests.get,attrs,0,self.deal)
	def deal(self, response, remain, succeed):
		# succeed == Flase if Excepitoin happen
		print "remain:",remain
		if not succeed:
			print "error"
		else:
			response.encoding = 'utf-8'
			print "get:",response.url,len(response.text)
		if remain == 0:
			attrs = self.attrs(["http://www.baidu.com"])
			self.push(requests.get, attrs, 1, callback = self.deal)

			attrs = self.attrs(["http://fanyi.baidu.com/"])
			self.push(requests.get, attrs, 2)
		for i in xrange(10):
			slp = random.random()
			print response.url,":",i,"sleep:",slp
			time.sleep(slp)
	def clean(self):
		print "work done"
		return 123

"""
python
from multi import demo
tst = demo.Test()
# tst.work(asyn = True)
# or:
rst =tst.work(asyn = False)
print "rst:",rst
"""