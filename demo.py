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

"""
need implement:
fc_sim :
rule:
key_words to key_words
html2urls 
robots check
"""

s = """
爬虫 0.322882357397
url 0.23752647481
广度 0.131058550601
深度 0.131058550601
deepth 0.128684257297
seeds 0.128684257297
种子 0.128684257297
优先 0.11266019461
抓取 0.096978431194
http 0.090078980108
队列 0.0822981462228
HTML 0.0772105543783
"""

"""

python
from multi import demo 
url = "https://www.cnblogs.com/wangshuyi/p/6734523.html"
keys = demo.keys(url,30)

python
from multi import demo 
s = demo.s
sr=s.split("\n")
keys = []
for s in sr:
	kw=s.split(" ")
	if len(kw)!=2:
		continue
	key, weight = kw
	key = key.decode("utf-8")
	weight = float(weight)
	keys.append([key,weight])


lnks = []
lnks.append([u'http://book.zongheng.com/book/144244.html',1.0])
fc_sim = demo.Sim(keys)
spd = demo.Demo(lnks,fc_sim)
spd.show=False
spd.work(asyn=True)


python
from multi import demo 
keys = []
words = u"恐怖小说,恐怖,惊悚,  鬼, 尸体, 死亡, 小说"
values = [     0.1, 0.1, 0.1, 0.1,  0.1,  0.1,  0.01]
words = ''.join(words.split(" "))
words = words.split(',')
if len(values)!=len(words):
	print "ERROR  LEN"

for i in xrange(len(words)):
	keys.append([words[i],values[i]])

lnks = []
lnks.append([u'http://book.zongheng.com/book/144244.html',1.0])
lnks.append([u'http://www.biquge.com.tw/2_2497/',1.0])
lnks.append([u'http://www.biquge.com.tw/2_2556/',3.0])
lnks.append([u'http://www.biquge.com.tw/0_278/',3.0])
lnks.append([u'http://www.biquge.com.tw/0_278/',2.0])
lnks.append([u'http://www.biquge.com.tw/0_270/',2.0])
fc_sim = demo.Sim(keys)
spd = demo.Demo(lnks,fc_sim)
spd.work(asyn=True)

"""
from spider import robots,url_base,cut
import random 
def keys(url, num = 10):
	import requests 
	rp = requests.get(url)
	url_base.rq_encode(rp)
	html = rp.text
	cts = cut.contents(html)
	rstkeys = cut.tf_idfs(cts,num)
	return rstkeys
class Sim(object):
	# key_words: list of [word,value]
	def __init__(self,key_words, alpha = 0.0001):
		self.key_words = key_words
		self.alpha = alpha
	def __call__(self,contents):
		l = len(contents)
		l = l>>1
		l = 1.0 / l
		rst = 1.0
		keys = self.key_words 
		for k in keys:
			key = k[0]
			c = contents.count(key)
			n = 1.0 * c * l 
			rst *= (n * k[1] + self.alpha)
		return rst 
class Demo(multi.Multi):
	def __init__(self,lnks_with_weight,fc_sim, weight_remain = 0.5):
		multi.Multi.__init__(self, True)
		self.urls = lnks_with_weight[:]
		self.sim=fc_sim 
		self.set = set()
		self.waitset = set()
		self.done_urls = []
		self.init_objs()
		self.max_container_urls = 300
		self.push_urls = 10
		self.deal_urls = 600
		self.total_urls = 3000
		self.robots = robots.Robots(False)
		self.weight_remain = weight_remain
		self.on_running_count = 0
		for url in self.urls:
			parm = self.attrs([url[0]],{})
			self.init_push(requests.get,parm,url[1],self.deal)
	def check_urls(self):
		if self.on_running_count > self.deal_urls:
			mx_len = self.push_urls+self.max_container_urls
			if len(self.urls) > mx_len*2:
				self.urls.sort(key=lambda x:x[1], reverse=True)
				print "check_urls cut",len(self.urls),"to",mx_len
				self.urls = self.urls[:mx_len]
			print "check_urls too many in run:",self.on_running_count
			return 
		self.urls.sort(key=lambda x:x[1], reverse=True)
		l = min(len(self.urls), self.push_urls)
		for i in xrange(l):
			urlobj = self.urls[i] 
			url = urlobj[0]
			uhost = url_base.http_base(url)
			parm=self.attrs([url],{'headers':url_base.header(uhost)})
			self.push(requests.head,parm,urlobj[1],self.deal)
			self.on_running_count+=1
			#print "		check url push head",urlobj[0]
			#self.waitset.add(url)
		
		print "done push ",l," requests.head",len(self.urls)
		self.urls = self.urls[l:]
		print "current url lens:",len(self.urls)
		if len(self.urls) > self.max_container_urls:
			print "do remove from set:",self.max_container_urls,len(self.urls),len(self.urls)-self.max_container_urls
			for urlboj in self.urls[self.max_container_urls:]:
				url  =urlobj[0]
				if url in self.waitset:
					self.waitset.remove(url)
			self.urls = self.urls[:self.max_container_urls]
			print "done remove from set"
		print "finish check_urls",len(self.urls)
	def robots_deal(self,response,remain,succeed):
		url,chd_sim,lurls, count_obj = remain
		count_obj[0]+=1
		if response == True:
			self.waitset.add(url)
			self.urls.append([url,chd_sim])
		self.check_urls()
		return 
		if count_obj[0] == lurls:
			self.check_urls()
			print "finish check_urls"
		elif random.random() > 0.9:
			self.check_urls()
	def deal(self, response, remain, succeed):
		self.on_running_count-=1
		if not succeed:
			print "failed to get url:",response 
			return 
		url = response.url 
		print "deal on ",url
		if url in self.set:
			return
		method = response.request.method # 'HEAD', 'GET', 'POST', ...
		if method == 'HEAD':
			ct_type = response.headers['Content-Type']
			if ct_type.lower().find('text/html')<0 :
				print "not text/html:",ct_type
				return 
			uhost = url_base.http_base(url)
			parm=self.attrs([url],{'headers':url_base.header(uhost)})
			self.push(requests.get,parm,remain,self.deal)
			self.on_running_count+=1
			print "finish head ",url
			return 
		elif method == '':
			print "error request.method in here:",url 
			return 
		url_base.rq_encode(response)
		self.check_urls()
		self.set.add(url)
		self.waitset.add(url)
		text = response.text
		sim = self.sim(text)
		self.done_urls.append([url,sim])
		if len(self.done_urls)>self.total_urls:
			print "catched enough url:", len(self.set)
			return 
		chd_sim = self.weight_remain * remain + sim 
		urls = url_base.html2urls(text, url)
		print "urls in ",url,": ",len(urls)
		#cnt = 0
		lurls = len(urls)
		#for turl in urls:
		count_object = [0]
		for i in xrange(lurls):
			turl = urls[i]
			if not url_base.maybe_html(turl) or turl in self.waitset:
				if not url_base.maybe_html(turl):
					#print "mabe not url:",turl 
					pass 
				if not self.robots.allow(turl):
					#print "robots not allow:",turl
					pass
				continue 
			self.push(self.robots.allow,self.attrs([turl]),[turl, chd_sim,lurls,count_object],self.robots_deal)
			continue
			if  not self.robots.allow(turl):
				pass
			#self.waitset.add(turl)
			#if len(self.urls) > self.max_container_urls:
			#	continue 
			self.waitset.add(turl)
			self.urls.append([turl,chd_sim])
		#print "push count in url",url,":",cnt
		
		print "finish get ",url
	def output(self):
		self.on_running_count = 0
		print "DONE WORK"
		self.done_urls.sort(key=lambda x:x[1], reverse=True)
		return self.done_urls[:10]