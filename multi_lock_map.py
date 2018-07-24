
class Multi:
	__lock: lock
	__suspend_lock: lock
	
	push():
		__lock
	pushs():
		__lock: ?
	suspend():
		__suspend_lock
	resume():
		__suspend_lock
	
	build_thread(): 
		__suspend_lock:
			SingleThread.run()

	__has_something():
		SingleFeedback.empty()
		__lock

	threading inner_run():
		while True:
			__has_something()
			build_thread()
			__lock: ?
		SingleFeedback.shutdown()
	callback():
		pushs()

class SingleFeedback:
	__ct: condition
	
	threading run():
		__ct: ?
		while running:
			__ct:
				ThreadSafeQueue.pop()
			Multi.callback()
		ThreadSafeQueue.clean()
		__ct: notify
	
	empty():
		__ct: ?
		ThreadSafeQueue.empty()

	shutdown():
		__ct
		__ct: wait



class ThreadSafeQueue:
	comsume_ct: condition
	product_ct: condition
	__lock: lock

	push():
		product_ct:
			__lock: ?
			product_ct.wait()
			__lock: ?
		comsume_ct:
			comsume_ct.notify()

	pop():
		comsume_ct:
			__lock: ?
			comsume_ct.wait(time)
			__lock: ?
			__lock: ?
		product_ct:
			product_ct.notify()
		
	empty():
		__lock: ?
	
	clean():
		product_ct: ?
		product_ct: notify_all()









class SingleThread:
	
	threading run(): 
		SingleFeedback.push()
