#coding=utf-8
import multi
import requests
class Test(multi.Multi):
	def __init__(self):
		multi.Multi.__init__(self)
		self.initobjs =  []
		list_attrs = ["http://www.baidu.com"]
		map_attrs = {"timeout":10}
		attrs = self.attrs(list_attrs,map_attrs)
		obj = [requests.get,attrs,0]
		self.initobjs.append(obj)
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
	def clean(self):
		print "work done"
		return 123
tst = Test()
# tst.work(asyn = True)
# or:
rst =tst.work(asyn = False)
print "rst:",rst