"""
	Simple data -> filesystem caching class
	
	$Id$
	Copyright (C) 2010 Ian Moore (imoore76 at yahoo dot com)
 
"""

import os
import time
import hashlib
import pickle
import portalocker
import threading

class cache(threading.local):

	path = '/tmp'
	ext = 'dat'
	prefix = 'vbw'
	force_refresh = False
	expire_multiplier = 60 # 1 minute
	open = {}
	locked = {}
	logfile = None #'/tmp/cache.log'
	initialized = False

	"""
	
		init() set up temp path
		
	"""
	def __init__(self):
		
		if self.initialized:
			raise SystemError('__init__ called too many times in cache object')
		
		self.initialized = True

		if(os.environ.get('TEMP') and os.access(os.environ['TEMP'], os.W_OK)):
			self.path = os.environ['TEMP']
		elif(os.environ.get('TMP') and os.access(os.environ['TMP'], os.W_OK)):
			self.path = os.environ['TMP']
		
		self.open = {}
		self.locked = {}
		

	"""
		
		Shutdown. Do our best to ensure all filehandles are closed
		and flocks removed.
		
	"""
	def shutdown(self):
		self.__log("Entered shutdown")
		self.__log("Open: " + str(self.open))
		for k in self.open.keys():
			self.__log("Unlocking " + str(k))
			self.unlock(k)
			

	"""
	
		get cached data
		
	"""
	def get(self,key,expire,data=None):
		# Is file cached?
		if(not self.cached(key,expire)):
			return False
		else:
			d = self.__getCachedData(key)
			if(self.logfile): self.__log("Returning cached data for: "+key +" data: " + str(d))
			
			if data != None:
				data['data'] = d
				
		return d

	
	"""
	
		get date last modified for cache item
		
	"""
	def getDLM(self,key,expire):
		if(not self.cached(key,expire)): return int(time.time())
		return self.__filemtime(self.__fname(key)) or int(time.time())
	


	"""
	
		Blocking lock on cache item
		
	"""
	def lock(self,key):

		fname = self.__fname(key)

		prelock = int(self.__filemtime(fname))

		fp = open(fname, "ab")
		
		self.open[key] = fp

		os.chmod(fname, 0600)

		portalocker.lock(fp,portalocker.LOCK_EX)


		# Written while blocking ?
		if(prelock > 0 and self.__filemtime(fname) > prelock):
			if(self.logfile): self.__log(key+" prelock: " + str(prelock) + " postlock: "+str(self.__filemtime(fname))+" NOT writing.")
			self.unlock(key)
			del self.open[key]
			return None
		

		if(self.logfile):
			 self.__log(key+" prelock: " + str(prelock) + " postlock: "+ str(self.__filemtime(fname)) +" writing.")

		self.locked[key] = fp

		return True
	

	"""
	
	 Store locked cache item
	 
	"""
	def store(self,key,data):

		self.__log("Locked returns" + str(self.locked.get(key)) + " for " + str(key));
		
		if(not self.locked.get(key)): return False

		if(self.logfile): self.__log(key+" writing at "+str(int(time.time())))

		self.locked[key].seek(0)
		self.locked[key].truncate(0)
		try: pickle.dump(data, self.locked[key])
		except: pass
		self.unlock(key)
		return data
	

	"""
	
		Remove exclusive lock
		
	"""
	def unlock(self,key):
		try: portalocker.unlock(self.locked[key])
		except: print "Cache error unlocking file with key " + key
		try: self.locked[key].close()
		except: print "Cache error closing file with key " + key
		del self.open[key]
		del self.locked[key]
	

	"""
	
		Determine if file is cached and has not expired
		
	"""
	def cached(self,key,expire=60):
		return (not self.force_refresh and os.path.exists(self.__fname(key)) and (expire == False or (self.__filemtime(self.__fname(key)) > (int(time.time()) - (self.expire_multiplier * expire)))))
	


	"""
	
		Expire (unlink) cached item
		
	"""
	def expire(self,key):
		
		if self.locked.get(key):
			self.unlock(key)
		
		if not os.path.exists(self.__fname(key)): return
		
		while(os.path.exists(self.__fname(key))):
			try:
				os.unlink(self.__fname(key))
			except Exception, e:
				print "Exception " + str(e)
				time.sleep(1)
	

	"""
	
		Logging used for debugging
		
	"""
	def __log(self,s):
		if(not self.logfile): return
		f = open(self.logfile,'a')
		f.write(s+"\n")
		f.close()
	

	"""
	
		Lock aware file read
		
	"""
	def __getCachedData(self,key):

		fname = self.__fname(key)

		# Pre-existing locked read
		if(self.locked.get(key)):
			self.locked[key].seek(0)
			try: str = pickle.load(self.locked[key])
			except: str = False
			self.locked[key].seek(0)
			return str
		

		fp=open(fname, "r")
		self.open[key] = fp
		portalocker.lock(fp,portalocker.LOCK_SH)
		
		# The following 2 lines handle cases where open (above) was called
		# on an empty file that was created by cache::lock()
		fp.seek(0)
		
		try: str = pickle.load(fp)
		except: str = False
		
		try: portalocker.unlock(fp)
		except: print "Cache error unlocking file with key " + key
		try: fp.close()
		except: print "Cache error closing file with key " + key
			
		del self.open[key]
		return str
	

	# Generate file name
	def __fname(self,key):
		return self.path+'/'+self.prefix+hashlib.md5(key).hexdigest()+'.'+self.ext


	# Return mtime of file
	def __filemtime(self,file):
		try:
			return int(os.path.getmtime(file))
		except:
			return 0



