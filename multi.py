#coding=utf-8

import time
import threading
sleep_time=1.0
# A description, notes: the class that you should inherit is Spider, not BaseSpider
class BaseMulti(object):
	# init urls to spiding 
	initobjs = []
	sleep_time = 1.0
	# max threads limit 
	max_threads = 300

	# time seperate of each spiding 
	seperate_time = 0
	show = True
	container_size = 300
	# you should implement this by yourself
	def deal(self, response, remain, succeed):
		pass
	
	# you can implement this 
	def clean(self):
		pass
	
	# 
	def suspend(self):
		pass 
	
	# 
	def resume(self):
		pass
	
	# append url to spider
	def push(self, func, attrs, remain = None, callback = None):
		pass
		
	# let spider running
	def start(self):
		pass

	# let spider running
	def work(self,asyn = False):
		pass
	
	# let spider stop running
	def poweroff(self):
		pass 
	
	# check if spider is really shutdown 
	def done(self):
		pass
	
	# inner function, you should not call this 
	def run(self):
		pass 
	

class SingleThread(threading.Thread):
	def __init__(self, func, attrs, remain, callback, show):
		threading.Thread.__init__(self)
		self.attrs = attrs 
		self.callback = callback
		self.func = func
		self.__done = False 
		self.remain = remain
		self.show = show
	def done(self):
		return self.__done
	
	def run(self):
		try:
			attrs = self.attrs 
			func = self.func
			#print "attrs:",attrs
			maps = attrs[1]
			lst = attrs[0]
			order = "none"
			#print "lst:",lst
			if len(maps) == 0:
				rp = func(*lst)
			else:
				order = "rp=func("
				for i in xrange(len(lst)):
					order += "lst[" + str(i) + "], "
				for key in maps:
					order += ""+key+"=maps['"+key+"'], "
				order = order[:-1]
				order+=")"
				exec(order)
			succeed = True
		except Exception,e:
			if self.show:
				print "ERROR in thread run:",e
				print "ORDER:",order
				import traceback
				traceback.print_exc()
			succeed = False
			rp = None
		try:
			self.callback(rp,self.remain,succeed)
		except Exception,e:
			print "There are Error in your codes:", e
			try:
				import traceback
				traceback.print_exc()
			except:
				print "Can't use module traceback to show details"
		self.__done = True
	
class MainThread(threading.Thread):
	def __init__(self, spider):
		threading.Thread.__init__(self)
		self.spider =spider 
	
	def run(self):
		self.spider.inner_run()
		self.spider.thd_done()


class Multi(BaseMulti):
	def __init__(self):
		self.__on_running = False
	def change_run_urls(self):
		self.__run_urls = self.__wait_urls[0]
		self.__wait_urls = self.__wait_urls[1:]
		if len(self.__wait_urls)==0:
			self.__wait_urls.append([])
	def has_something(self):
		return len(self.__run_urls) + len(self.__wait_urls[-1]) + len(self.__threads) > 0 or len(self.__wait_urls) > 1

	def __initz(self):
		self.__suspended=False
		self.__lock = threading.Lock()
		self.__suspend_lock = threading.Lock()
		self.__run_urls = []
		self.__wait_urls = [[]]
		for urlobj in self.initobjs:
			tp = type(urlobj)
			remain = None
			if tp not in [list,tuple]:
				func = urlobj 
				attrs = self.attrs()
				remain = None
				callback = None
			else:
				func = urlobj[0]
				attrs = self.attrs() if len(urlobj) <2 else urlobj[1]
				remain = None if len(urlobj)<3 else urlobj[2]
				callback = None if len(urlobj)<4 else urlobj[3]
			Multi.push(self, func, attrs, remain, callback)
		self.change_run_urls()

	def push(self,func, args = [],remain = None, callback = None):
		if callback == None:
			callback = self.deal
		with self.__lock:
			if len(self.__wait_urls[-1])>= self.container_size:
				self.__wait_urls.append([])
			if type(args) == dict:
				args = [[],args]
			elif len(args)==0:
				args = [[],dict()]
			elif len(args)==1:
				args.append(dict())
			self.__wait_urls[-1].append((func, args, remain, callback))

	@staticmethod
	def attrs(lst=[], maps=dict()):
		return [lst,maps]

	def start(self):
		if self.__on_running:
			return False
		self.__stop = False
		self.__on_running = True
		main_thread = MainThread(self)
		main_thread.start()
		self.__main_thread = main_thread
		return self.__on_running

	def work(self,asyn = True):
		if asyn:
			return self.start()
		else:
			return self.run()
	
	def poweroff(self):
		self.__stop=True
	
	def done(self):
		return self.__on_running==False
	
	def thd_done(self):
		self.__on_running=False
	
	def resume(self):
		if not self.__suspended:
			return True 
		self.__suspend_lock.release()
		self.__suspended = False 
		return True
	
	def suspend(self):	
		if self.__suspended:
			return True
		self.__suspend_lock.acquire()
		while len(self.__threads)>0:
			th=self.__threads[0]
			th.join()
			if th.done():
				self.__threads.pop(0)
		self.__suspended = True
		return True

	def clear_threads(self):
		len_thd = len(self.__threads)
		cnt_thd = 0
		while cnt_thd < len_thd:
			if self.__threads[cnt_thd].done():
				self.__threads.pop(cnt_thd)
				len_thd -= 1
			else:
				cnt_thd += 1
	def run(self):
		self.__stop = False
		out = self.inner_run()
		self.__on_running=False
		return out

	def inner_run(self):
		self.__initz()
		self.__threads = []
		global sleep_time
		#cnt=0
		while self.has_something() and not self.__stop:
			cls_cnt=0
			if len(self.__run_urls) == 0:
				if self.sleep_time is not None:
					time.sleep(self.sleep_time)
				else:
					time.sleep(sleep_time)
				
			for obj in self.__run_urls:
				if self.seperate_time>0:
					if self.show:
						print "sleep for seperate_time"
					time.sleep(self.seperate_time)
				func, attrs, remain, callback= obj 
				while threading.active_count() >= self.max_threads:
					if self.show:
						print "sleep for active_count()"
					if self.sleep_time is not None:
						time.sleep(self.sleep_time)
					else:
						time.sleep(sleep_time)
				cls_cnt+=1
				if cls_cnt>=self.max_threads:
					self.clear_threads()
					cls_cnt=0
				newthread=None
				with self.__suspend_lock:
					while newthread is None:
						try:
							newthread = SingleThread(func, attrs, remain, callback, self.show)
							newthread.start()
						except Exception,e:
							if self.show:
								print "create or start thread error:",e,e.message
							newthread=None 
							time.sleep(sleep_time)
					if newthread is not None:
						self.__threads.append(newthread)
			with self.__lock:
				self.change_run_urls()
			self.clear_threads()
		while len(self.__threads)>0:
			th=self.__threads[0]
			th.join()
			if th.done():
				self.__threads.pop(0)
		try:
			return self.clean()
		except Exception, e:
			print "Error code in your spider's function clean:", e 
			try:
				import traceback
				traceback.print_exc()
			except:
				print "Can't use module traceback to show details"
		return None

