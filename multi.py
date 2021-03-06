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
    
    # you may need to judge to continue loop:
    def has_something(self):
        return False
    # if you do, do something in single loop:
    def do_something(self):
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
    
    # call this before you calll this.work second times to do some initialize
    def renew(self):
        return True 
        
    
    # let spider running
    def work(self,asyn = False):
        pass
    
    # let spider stop running
    def poweroff(self):
        pass 
    
    # check if spider is really shutdown 
    def done(self):
        pass
    
    # tools to help do push:
    # mg = this.manager()
    # mg.add: using this same as Multi.push 
    # mg.commit()
    def manager(self):
        return None 
    
    # return how many jobs(threads) are in running( or done running but not release yet)
    def running_jobs(self):
        return 0

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
            remove_script="""
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
                exec(order)"""
            rp = func(*lst, **maps)
            succeed = True
        except Exception,e:
            if self.show:
                print("ERROR in thread run:",e)
                print("func is:",func,"parms is:",attrs)
                print("ORDER:",order)
                import traceback
                traceback.print_exc()
            succeed = False
            rp = func,attrs
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
    def __init__(self, multi_fc):
        threading.Thread.__init__(self)
        self.multi_fc =multi_fc 
    
    def run(self):
        self.multi_fc()

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
        self.accept = True
        self.__lock = threading.Lock()
        self.waiting = 0
    def push(self, obj):
        with self.product_ct:
            if not self.accept:
                return 
            if self.size > 0:
                with self.__lock:
                    num = len(self.products)
                while num >= self.size:
                    self.waiting += 1
                    self.product_ct.wait()
                    self.waiting -= 1
                    num = len(self.products)
            if not self.accept:
                return 
            with self.__lock:
                self.products.append(obj)
        with self.comsume_ct:
            self.comsume_ct.notify()
    def pop(self):
        with self.comsume_ct:
            with self.__lock:
                num = len(self.products)
            if num == 0:
                self.comsume_ct.wait(self.wait_time)
            with self.__lock:
                num = len(self.products)
            if num == 0:
                obj = None
            else:
                with self.__lock:
                    obj = self.products.pop()
        with self.product_ct:
            self.product_ct.notify()
        return obj 
    def empty(self):
        with self.__lock:
            return len(self.products) == 0
    def clean(self):
        with self.product_ct:
            self.products = []
        with self.product_ct:
            self.accept = False
            self.product_ct.notify_all()
    def init(self):
        self.products = []
        self.accept = True
class SingleFeedback(threading.Thread):
    def __init__(self, multi, container_size, wait_time = 1.0):
        threading.Thread.__init__(self)
        self.running = True 
        self.queue = ThreadSafeQueue(container_size, wait_time)
        self.__shutdown = False
        self.__ct = threading.Condition()
        self.has_obj = True
        self.multi = multi
    def push(self,obj):
        self.queue.push(obj)
    def push_bak(self,callback,response, remain,succeed):
        self.queue.push([callback,response,remain,succeed])
    def init(self):
        self.queue.init()
        self.has_obj = True
    def run(self):
        self.state = 0
        with self.__ct:
            self.running = True 
            self.__shutdown = False
        obj = None
        self.state = 1
        while self.running:
            self.state = 2
            with self.__ct:
                self.state = 2.5
                obj = self.queue.pop()
                self.state = 2.6
                self.has_obj = obj is not None
                self.state = 2.7
            self.state = 3
            if obj is None:
                continue
            self.state = 4
            callback,response,remain,succeed = obj 
            self.tmp = obj
            self.state = 4.3
            try:
                self.state = 4.5
                callback(response,remain,succeed)
                self.state = 4.7
            except Exception,e:
                self.state = 4.9
                if self.multi.show:
                    print("callback error:",e,e.message)
                    try:
                        import traceback
                        traceback.print_exc()
                    except:
                        print("Can't use module traceback to show details")
            self.state = 5
        self.state = 6
        self.queue.clean()
        self.state = 7
        with self.__ct:
            self.__shutdown = True
            self.__ct.notify()
        self.state = 8
    def empty(self):
        with self.__ct:
            if self.has_obj:
                return False
            return self.queue.empty()
    def shutdown(self):
        with self.__ct:
            self.running = False
        with self.__ct:
            if self.__shutdown == False:
                self.running = False
                self.__ct.wait()
class SingleFeedbackThread(threading.Thread):
    def __init__(self, single_feedback):
        threading.Thread.__init__(self)
        self.single_feedback = single_feedback
        self.single_feedback.init()
    def run(self):
        self.single_feedback.run()
class CallBack(object):
    def __init__(self,callback,container):
        self.callback = callback
        self.container = container
    def __call__(self,response, remain,succeed):
        if self.callback == Multi.not_callback:
            return 
        self.container.push([self.callback,response, remain,succeed])

class LinearContainer(object):
    def __init__(self, multi):
        self.multi = multi 
        self.ct = []
        self.push = self.add 
    def add(self,func, attrs, remain = None, callback = None):
        self.ct.append([func,attrs,remain,callback])
    def commit(self):
        if len(self.ct)==0:
            return 
        self.multi.pushs(self.ct)
        self.ct = []
class Multi(BaseMulti):
    @staticmethod
    def not_callback(response, remain, succeed):
        pass 
    mark_shows = False
    def __init__(self, single_thread_for_feedback = False):
        self.__mark_work = False
        self.__on_running = False
        self.__single_thread_for_feedback = single_thread_for_feedback
        if self.__single_thread_for_feedback:
            self.single_thread_container = SingleFeedback(self,300)
            #self.queue = ThreadSafeQueue(300)
    def __change_run_urls(self):
        self.__run_urls = self.__wait_urls[0]
        self.__wait_urls = self.__wait_urls[1:]
        if len(self.__wait_urls)==0:
            self.__wait_urls.append([])
    def manager(self):
        return LinearContainer(self)
    def __initz(self):
        self.__count_running = 0
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
            Multi.__inner_push(self, func, attrs, remain, callback)
        self.__change_run_urls()

    def init_objs(self):
        self.initobjs = []

    def init_push(self, func, attrs, remain = None, callback = None):
        if callback == None:
            callback = self.deal
        #if self.__single_thread_for_feedback:
        #   callback = CallBack(callback, self.single_thread_container)
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
        with self.__lock:
            self.__inner_push(func,args,remain,callback)
        return 
        if self.__single_thread_for_feedback and not locked_need:
            self.__inner_push(func,args,remain,callback)
            return 
    
    def __inner_pushs(self, list):
        for it in list:
            self.__inner_push(*it)

    def pushs(self, list, locked_need = False):
        with self.__lock:
            self.__inner_pushs(list)
        return 
        if self.__single_thread_for_feedback and not locked_need:
            self.__inner_pushs(list)
            return 
        with self.__lock:
            self.__inner_pushs(list)

    @staticmethod
    def attrs_(lst=[], maps=dict()):
        return [lst,maps]
    @staticmethod
    def attrs(*argv, **maps):
        return [argv, maps]
    def __start(self):
        if self.__on_running:
            return False
        self.__stop = False
        self.__on_running = True
        main_thread = MainThread(self.__run)
        main_thread.start()
        self.__main_thread = main_thread
        return self.__on_running
    def renew(self):
        if self.__on_running:
            print("You can not call this funcion when the thread is running!")
            print(" the thread is on running, wait until it done or call poweroff() to stop it")
            print(" call done() to check if the thread is done")
            return False 
        self.__mark_work = False
        return True 
    def work(self,asyn = True):
        if self.__mark_work:
            print("This function is already running or done run, to recall this, you should call function renew() first")
            return False 
        self.__mark_work = True
        if asyn:
            return self.__start()
        else:
            return self.__run()
    def poweroff(self):
        self.__stop=True
    
    def done(self):
        return self.__on_running==False
    
    def resume(self):
        if not self.__suspended:
            return True 
        self.__suspended = False 
        self.__suspend_lock.release()
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
    def running_jobs(self):
        return self.__count_running
    def __clear_threads(self):
        len_thd = len(self.__threads)
        cnt_thd = 0
        count_running = 0
        while cnt_thd < len_thd:
            if self.__threads[cnt_thd].done():
                self.__threads.pop(cnt_thd)
                len_thd -= 1
            else:
                cnt_thd += 1
                count_running +=1 
        self.__count_running = count_running
        return count_running
    def __run(self):
        self.__stop = False
        out = self.__inner_run()
        self.__on_running=False
        return out
    def has_something(self):
        return False
    def do_something(self):
        pass
    def __has_something(self):
        if self.has_something():
            return True 
        if len(self.__threads) > 0:
            return True
        if self.__single_thread_for_feedback:
            if not self.single_thread_container.empty():
                return True 
        with self.__lock:
            return len(self.__run_urls) + len(self.__wait_urls[-1]) + len(self.__threads) > 0 or len(self.__wait_urls) > 1
    def shows(self,s):
        if self.mark_shows:
            print("\n\n\n@@@@@@@@@@@@@@@@@@@@@@@@@@@\n\n\n"+s+"\n\n\n@@@@@@@@@@@@@@@@@@@@@@@@@@@n\n\n")
    def __build_thread(self, obj):
        func, attrs, remain, callback= obj 
        if threading.active_count() >= self.max_threads:
            return False 
        with self.__suspend_lock:
            try:
                newthread = SingleThread(func, attrs, remain, callback, self.show)
                newthread.start()
            except Exception,e:
                return False 
            self.__threads.append(newthread)
        return True 
    def __inner_run(self):
        self.__state = 0
        self.__initz()
        self.__threads = []
        global sleep_time
        #cnt=0
        self.__state = 1
        while self.__has_something() and not self.__stop:
            self.__state = 2
            if len(self.__run_urls) == 0:
                if self.sleep_time is not None:
                    time.sleep(self.sleep_time)
                else:
                    time.sleep(sleep_time)
            self.__state = 3
            self.shows("next run") 
            self.do_something()
            cls_cnt=0
            self.shows( "try __run_urls")
            self.__state = 4
            self.__count_state = 0
            for obj in self.__run_urls:
                self.__state = 4.4
                while self.__build_thread(obj) == False:
                    self.__state = 4.5
                    active_counts = self.__clear_threads()
                    cls_cnt = 0
                    if active_counts > self.max_threads:
                        if self.show:
                            print("sleep for active_counts"+str(active_counts))
                        if self.sleep_time is not None:
                            time.sleep(self.sleep_time)
                        else:
                            time.sleep(sleep_time)
                    self.__state = 4.6
                cls_cnt += 1
                self.__state = 4.7
                if cls_cnt>=self.max_threads:
                    self.__clear_threads()
                    cls_cnt=0
                self.__count_state += 1
                self.__state = 4.9
            self.__state = 5
            self.shows( "done __run_urls")
            with self.__lock:
                self.__change_run_urls()
            self.__state = 6
            self.shows( "done change_run_urls")
            count_running = self.__clear_threads()
            self.shows( "done clear_threads")
        self.__state = 7
        self.shows( "DONE RUNNING")
        if self.__single_thread_for_feedback:
            self.single_thread_container.shutdown()
        self.__state = 8
        while len(self.__threads)>0:
            th=self.__threads[0]
            th.join()
            if th.done():
                self.__threads.pop(0)
        self.shows( "DONE CLEAR")
        self.__state = 9
        try:
            return self.output()
        except Exception, e:
            print("Error code in your spider's function clean:", e )
            try:
                import traceback
                traceback.print_exc()
            except:
                print("Can't use module traceback to show details") 
        self.__state = 10
        return None


class Multi_Backup(BaseMulti):
    mark_shows = True
    def __init__(self, single_thread_for_feedback = False):
        self.__mark_work = False
        self.__on_running = False
        self.__single_thread_for_feedback = single_thread_for_feedback
        if self.__single_thread_for_feedback:
            #self.single_thread_container = SingleFeedback(300)
            self.queue = ThreadSafeQueue(300)
    def change_run_urls(self):
        self.__run_urls = self.__wait_urls[0]
        self.__wait_urls = self.__wait_urls[1:]
        if len(self.__wait_urls)==0:
            self.__wait_urls.append([])
    
    def __initz(self):
        self.__count_running = 0
        if self.__single_thread_for_feedback:
            pass
            #self.single_thread_container_thread = SingleFeedbackThread(self.single_thread_container)
            #self.single_thread_container_thread.start()
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
            callback = CallBack(callback, self.queue)
        self.initobjs.append([func,attrs,remain,callback])

    def __inner_push(self,func, args = [], remain = None, callback = None):
        if callback == None:
            callback = self.deal
        if self.__single_thread_for_feedback:
            callback = CallBack(callback, self.queue)
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
    def renew(self):
        if self.__on_running:
            print("You can not call this funcion when the thread is running!")
            print(" the thread is on running, wait until it done or call poweroff() to stop it")
            print(" call done() to check if the thread is done")
            return
        self.__mark_work = False
    def work(self,asyn = True):
        if self.__mark_work:
            print("This function is already running or done run, to recall this, you should call function renew() first")
        self.__mark_work = True
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
        self.__suspended = False 
        self.__suspend_lock.release()
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
    def running_threads(self):
        return self.__count_running
    def clear_threads(self):
        len_thd = len(self.__threads)
        cnt_thd = 0
        count_running = 0
        while cnt_thd < len_thd:
            if self.__threads[cnt_thd].done():
                self.__threads.pop(cnt_thd)
                len_thd -= 1
            else:
                cnt_thd += 1
                count_running +=1 
        self.__count_running = count_running
        return count_running
    def run(self):
        self.__stop = False
        out = self.inner_run()
        self.__on_running=False
        return out
    def has_something(self):
        return False
    def do_something(self):
        print("next run")
    def __has_something(self):
        if self.has_something():
            return True 
        if len(self.__threads) > 0:
            return True
        if self.__single_thread_for_feedback:
            if not self.queue.empty():
                return True 
        return len(self.__run_urls) + len(self.__wait_urls[-1]) + len(self.__threads) > 0 or len(self.__wait_urls) > 1
    def shows(self,s):
        if self.mark_shows:
            print("\n\n\n@@@@@@@@@@@@@@@@@@@@@@@@@@@\n\n\n"+s+"\n\n\n@@@@@@@@@@@@@@@@@@@@@@@@@@@n\n\n")
    def build_thread(self, obj):
        func, attrs, remain, callback= obj 
        if threading.active_count() >= self.max_threads:
            return False 
        with self.__suspend_lock:
            try:
                newthread = SingleThread(func, attrs, remain, callback, self.show)
                newthread.start()
            except Exception,e:
                return False 
            self.__threads.append(newthread)
        return True 
    def inner_run(self):
        self.__initz()
        self.__threads = []
        global sleep_time
        #cnt=0
        while self.__has_something() and not self.__stop:
            self.shows("next run") 
            self.do_something()
            cls_cnt=0
            if len(self.__run_urls) == 0:
                if self.sleep_time is not None:
                    time.sleep(self.sleep_time)
                else:
                    time.sleep(sleep_time)
            self.shows( "try __run_urls")
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
            self.shows( "done __run_urls")
            with self.__lock:
                self.change_run_urls()
            self.shows( "done change_run_urls")
            count_running = self.clear_threads()
            self.shows( "done clear_threads")

            if self.__single_thread_for_feedback:
                cobj = self.queue.pop()
                self.cobj = cobj
                while cobj is not None:
                    callback,response,remain,succeed = cobj 
                    try:
                        callback(response,remain,succeed)
                    except Exception,e:
                        if self.show:
                            print("callback error:",e,e.message)
                            try:
                                import traceback
                                traceback.print_exc()
                            except:
                                print("Can't use module traceback to show details")
                    count_running -= 1
                    if count_running <= 0:
                        break 
                    cobj = self.queue.pop()
                    self.cobj = cobj
            self.shows( "done __single_thread_for_feedback")
        self.shows( "DONE RUNNING")
        while len(self.__threads)>0:
            th=self.__threads[0]
            th.join()
            if th.done():
                self.__threads.pop(0)
        if self.__single_thread_for_feedback:
            self.queue.clean()
        self.shows( "DONE CLEAR")
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

