#coding=utf-8


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

类BaseMulti是格式定义，实际使用需要继承或者使用类Multi
主要参数与函数有：
max_threads: 一次运行的最多线程数
init_objs: 初始化
init_push: 设置初始运行的多线程函数
push: 运行中添加其它函数（将创建线程运行）
deal: 默认回调函数，可改写
clean: 所有线程函数结束后调用
work(asyn): 开始运行，参数asyn=True时，将在主线程进行运行管理与调度程序，运行结束后返回clean的返回值
					参数asyn=True时，将创建新线程进行运行管理与调度程序，返回None

"""

import time
import threading
sleep_time=1.0

# A demo class just for description, notes: the class that you should inherit is Multi, not BaseMulti
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

	# if single_thread_for_feedback is True
	# the function deal (or other callback function) will run in linear order, so don't need to care about lock and ect
	def __init__(self, single_thread_for_feedback = False):
		pass
	# you should implement this by yourself
	def deal(self, response, remain, succeed):
		pass
	
	# you can implement this 
	def clean(self):
		pass

	# or this
	def output(self):
		return self.clean()
	# 
	def suspend(self):
		pass 
	
	# 
	def resume(self):
		pass

	def init_objs(self):
		pass

	def init_push(self, func, attrs, remain = None, callback = None):
		pass

	# append url to spider
	def push(self,func, args = [], remain = None, callback = None, locked_need = False):
		pass
	# single lock for multi obj push
	# the obj in list should be in structure like parameters in function push
	def pushs(self, list, locked_need = False):
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
				print("ERROR in thread run:",e)
				print("ORDER:",order)
				import traceback
				traceback.print_exc()
			succeed = False
			rp = None
		try:
			self.callback(rp,self.remain,succeed)
		except Exception,e:
			print("There are Error in your codes:", e)
			try:
				import traceback
				traceback.print_exc()
			except:
				print("Can't use module traceback to show details")
		self.__done = True
	
class MainThread(threading.Thread):
	def __init__(self, multi):
		threading.Thread.__init__(self)
		self.multi =multi 
	
	def run(self):
		self.multi.inner_run()
		self.multi.thd_done()

class RingQueue(object):
	def __init__(self, size = 100, auto_wait = False, wait_time = 0.1):
		size += 1
		self.products = [None for i in xrange(size)]
		self.first = 0
		self.last = 0
		self.size = size
		self.wait_time = wait_time
		self.auto_wait = auto_wait
	def full(self):
		nxt = (self.last + 1)% self.size
		return nxt == self.first
	def push(self, obj):
		while self.auto_wait and self.full():
			time.sleep(self.wait_time)
		nxt = (self.last + 1)% self.size
		self.products[self.last]=obj 
		self.last = self.nxt
	def empty(self):
		return self.first == self.last
	def pop(self):
		while self.auto_wait and self.empty():
			time.sleep(self.wait_time)
		obj = self.products[self.first]
		self.products[self.first] = None 
		self.first = (self.first + 1) % self.size
		return obj 

class ThreadSafeQueue(object):
	def __init__(self, size = -1, wait_time = 1.0):
		self.products = []
		self.size = size
		self.comsume_ct = threading.Condition()
		self.product_ct = threading.Condition()
		self.wait_time = wait_time
	def push(self, obj):
		with self.product_ct:
			if self.size > 0:
				if len(self.products) >= self.size:
					self.product_ct.wait()
			self.products.append(obj)
		with self.comsume_ct:
			self.comsume_ct.notify()
	def pop(self):
		with self.comsume_ct:
			if len(self.products) == 0:
				self.comsume_ct.wait(self.wait_time)
			if len(self.products) == 0:
				return None 
			obj = self.products.pop()
		with self.product_ct:
			self.product_ct.notify()
		return obj 
	def clean(self):
		self.products = []
class SingleFeedback(threading.Thread):
	def __init__(self, container_size, wait_time = 1.0):
		threading.Thread.__init__(self)
		self.running = True 
		self.queue = ThreadSafeQueue(container_size)
		self.__shutdown = False
		self.__ct = threading.Condition()
		pass
	def push(self,callback,response, remain,succeed):
		self.queue.push([callback,response,remain,succeed])
	def run(self):
		with self.__ct:
			self.running = True 
			self.__shutdown = False
		obj = None
		while self.running or obj is not None:
			obj = self.queue.pop()
			if obj is None:
				continue
			callback,response,remain,succeed = obj 
			callback(response,remain,succeed)
		self.queue.clean()
		with self.__ct:
			self.__shutdown = True
			self.__ct.notify()
	def shutdown(self):
		with self.__ct:
			self.running = False
		with self.__ct:
			if self.__shutdown == False:
				self.__ct.wait()
class SingleFeedbackThread(threading.Thread):
	def __init__(self, single_feedback):
		threading.Thread.__init__(self)
		self.single_feedback = single_feedback
	def run(self):
		self.single_feedback.run()
class CallBack(object):
	def __init__(self,callback,container):
		self.callback = callback
		self.container = container
	def __call__(self,response, remain,succeed):
		self.container.push(self.callback,response, remain,succeed)
class Multi(BaseMulti):
	def __init__(self, single_thread_for_feedback = False):
		self.__on_running = False
		self.__single_thread_for_feedback = single_thread_for_feedback
		if self.__single_thread_for_feedback:
			self.single_thread_container = SingleFeedback(300)
	def change_run_urls(self):
		self.__run_urls = self.__wait_urls[0]
		self.__wait_urls = self.__wait_urls[1:]
		if len(self.__wait_urls)==0:
			self.__wait_urls.append([])
	def has_something(self):
		return len(self.__run_urls) + len(self.__wait_urls[-1]) + len(self.__threads) > 0 or len(self.__wait_urls) > 1

	def __initz(self):
		if self.__single_thread_for_feedback:
			self.single_thread_container_thread = SingleFeedbackThread(self.single_thread_container)
			self.single_thread_container_thread.start()
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

	def init_objs(self):
		self.initobjs = []

	def init_push(self, func, attrs, remain = None, callback = None):
		if callback == None:
			callback = self.deal
		if self.__single_thread_for_feedback:
			callback = CallBack(callback, self.single_thread_container)
		self.initobjs.append([func,attrs,remain,callback])

	def __inner_push(self,func, args = [], remain = None, callback = None):
		if callback == None:
			callback = self.deal
		if self.__single_thread_for_feedback:
			callback = CallBack(callback, self.single_thread_container)
		if len(self.__wait_urls[-1])>= self.container_size:
			self.__wait_urls.append([])
		if type(args) == dict:
			args = [[],args]
		elif len(args)==0:
			args = [[],dict()]
		elif len(args)==1:
			args.append(dict())
		self.__wait_urls[-1].append((func, args, remain, callback))

	def push(self,func, args = [], remain = None, callback = None, locked_need = False):
		if self.__single_thread_for_feedback and not locked_need:
			self.__inner_push(func,args,remain,callback)
			return 
		with self.__lock:
			self.__inner_push(func,args,remain,callback)

	def __inner_pushs(self, list):
		for it in list:
			self.__inner_push(*it)

	def pushs(self, list, locked_need = False):
		if self.__single_thread_for_feedback and not locked_need:
			self.__inner_pushs(list)
			return 
		with self.__lock:
			self.__inner_pushs(list)

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
						print("sleep for seperate_time")
					time.sleep(self.seperate_time)
				func, attrs, remain, callback= obj 
				while threading.active_count() >= self.max_threads:
					if self.show:
						print("sleep for active_count()")
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
								print("create or start thread error:",e,e.message)
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
		if self.__single_thread_for_feedback:
			self.single_thread_container.shutdown()
		try:
			return self.output()
		except Exception, e:
			print("Error code in your spider's function clean:", e )
			try:
				import traceback
				traceback.print_exc()
			except:
				print("Can't use module traceback to show details") 
		return None

