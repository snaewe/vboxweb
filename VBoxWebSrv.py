#!/usr/bin/env python
"""
	$Id$
	Copyright (C) 2010 Ian Moore (imoore76 at yahoo dot com)
"""
import cherrypy
from cherrypy.lib.static import serve_file
import os
import socket
import sys
import threading
import urllib
import hashlib
import math
import time
import inspect
import traceback
import re
import StringIO
import types
import md5
import random
import uuid
import gc
from email.utils import parsedate_tz

# Enable garbage collection
gc.enable()
gc.set_debug(gc.DEBUG_UNCOLLECTABLE)

if sys.platform == 'win32':
	try:
		import pythoncom
	except Exception, e:
		print str(e)
		print "Please install Python for Windows extensions found at\nhttp://sourceforge.net/projects/pywin32/files/"
		quit()
	import win32com

	try:
		import vboxapi # Main VirtualBox API
	except Exception, e:
		print "\n"
		print str(e)
		print "\nPlease run the vboxapisetup.py python script found in\n<VirtualBox Installation folder>\\sdk\\install\n\n"
		print "'cd' into the folder and run " + str(os.path.abspath(sys.executable)) + " vboxapysetup.py install"
		quit()
else:
	import vboxapi # Main VirtualBox API

# VBoxWeb modules
sys.path.insert(0,'lib')
sys.path.insert(0,'languages')

# Load vbox connector
import vboxactions


"""

	JSON imports and helpers
	
"""

if sys.version_info < (2, 6):
	try:
		import simplejson
		jsonType = 'simplejson'
	except:
		print "Warning: using internal JSON encoder. Installing simplejson for python (usually a package named python-simplejson) will improve performance."
		jsonType = 'internal'
else:
    import json
    jsonType = 'json'

def convertObjToJSON(obj):
    d = { '__class__':obj.__class__.__name__}
    d.update(obj.__dict__)
    return d

if jsonType == 'simplejson':
    class ConvertObjToJSONClass(simplejson.JSONEncoder):
        def default(self, obj):
			return convertObjToJSON(obj)

def jsonEncode(data):
	""" Last resort JSON encoder """
	if type(data) == type(dict()):
		l = []
		for k in data.keys():
			l.append(jsonEncode(str(k))+": "+jsonEncode(data[k]))
		return str('{ ' + ', '.join(l) + ' }')
	elif type(data) == type(list()):
		l = []
		for i in range(len(data)):
			l.append(jsonEncode(data[i]))
		return str('[' + ', '.join(l) + ']')
	elif type(data) == types.NoneType:
		return str("null")
	elif type(data) == type(int()):
		return str(int(data))
	elif type(data) == type(bool()):
		return str('true' if data else 'false')
	elif type(data) == types.InstanceType and data.__class__.__name__ == 'Boolean':
		return str(jsonEncode(bool(data)))
	else:
		return str('"' + str(data).replace('\\', '\\\\').replace('"','\\"').replace("\r","\\r").replace("\n","\\n") + '"')




"""

	Global vars
	
"""
g_vboxManager = None
g_threadPool = {}
g_logLevel = 99
g_serverTerminated = False
g_progressOps = {}

def trans(str):
	"""Language translation"""
	strt = None
	import VBoxWebConfig
	c = VBoxWebConfig.VBoxWebConfig()
	exec("import " + c.language)
	exec("strt = "+c.language+".trans.get('"+str+"')")
	
	return strt if strt else str


"""

	Progress operations MUST persist accross requests
	
"""
def progressObjStore(progress,session):
	# Generate progress ID
	pid = str(uuid.uuid4())
	g_progressOps[pid] = {
			'progress':progress,
			'session':session
	}
	return pid


def progressObjGet(pid):
	try:
		return g_progressOps.get(pid)
	except:
		return None

def progressObjDel(pid):
	try:
		pop = g_progressOps.get(pid)
		# remove session
		try:
			s = pop.get('session')
			if s: s.unlockMachine()
		except:
			pass
		del g_progressOps[pid]
	except:
		pass


def perThreadInit(threadIndex):
	if g_vboxManager:
		g_vboxManager.initPerThread()

def perThreadDeinit(threadIndex):
	if g_vboxManager:
		g_vboxManager.deinitPerThread()

def onShutdown():
    global g_serverTerminated
    g_serverTerminated = True
    if g_vboxManager:
    	
    	if hasattr(g_vboxManager, 'interruptWaitEvents'):
			g_vboxManager.interruptWaitEvents()
			
    	if sys.platform == 'win32':
    		from win32api import PostThreadMessage
    		from win32con import WM_USER
    		PostThreadMessage(g_vboxManager.platform.tid, WM_USER, None, None)
			

"""

	VBoxWeb - Request handler class
	
"""
class VBoxWeb:
    
	config = {}
	initCOM = False
	
	# Fatal connection error number
	VBWEB_ERRNO_FATAL = 32
	
	# Web session cookie
	session_cookie = ''
	
	def __init__(self, ctx):
        
		print "VBoxWeb init ..."
        
		self.ctx = ctx
		
		self.initCOM = False
		
		if sys.platform == 'win32':
			self.vbox_stream = pythoncom.CoMarshalInterThreadInterfaceInStream(pythoncom.IID_IDispatch, self.ctx['vbox'])


		# Init JSON printer
		self.jsonPrinter = None
		if jsonType == 'simplejson':
			self.jsonPrinter = simplejson.dumps
		elif jsonType != 'internal':
			if hasattr(json, "dumps"):
				self.jsonPrinter = json.dumps
			elif hasattr(json, "write"):
				self.jsonPrinter = json.write



		import VBoxWebConfig
		c = VBoxWebConfig.VBoxWebConfig()
        
		self.ctx['config'] = {}
		for v in inspect.getmembers(c):
			self.ctx['config'][v[0]] = v[1]
        
		# Progress functions access to global progressOps var
		self.ctx['progressOps'] = {'get':progressObjGet,'store':progressObjStore,'delete':progressObjDel}
		
		# generate session_cookie name. Not very secure, but better than a static / predictable key.
		self.session_cookie = md5.md5(os.path.abspath(os.path.dirname(__file__))).hexdigest()


		print "started."
		
	"""
		Setup win32 com object
	"""		
	def prepareCOM(self):
		if self.initCOM is False:
			if sys.platform == 'win32':
				# Get the "real" VBox interface from the stream created in the class constructor above
				i = pythoncom.CoGetInterfaceAndReleaseStream(self.vbox_stream, pythoncom.IID_IDispatch)
				self.ctx['vbox'] = win32com.client.Dispatch(i)
			self.initCOM = True
	
	
	
	"""
		Check authentication
	"""
	def checkAuth(self, debug=False):
		
		# TODO: Implement outside of vbox for vboxwebsrv
		return True
	
		# check cookie first
		if cherrypy.session.get('authed'):
			return True

		# check username / password
		if cherrypy.request.params.get('username') and cherrypy.request.params.get('password'):

			username = str(cherrypy.request.params['username'])
			password = str(cherrypy.request.params['password'])
						
			h = hashlib.new('sha1')
			h.update(password)
			password = h.hexdigest()

			if str(password) == str(self.ctx['vbox'].getExtraData("vboxwebc/users/" + username)):
				cherrypy.session['authed'] = True
				return True

		return False

	"""
        Return data as JSON data
    """
	def toJSON(self, data):
		if jsonType == 'simplejson':
			return self.jsonPrinter(data, cls=ConvertObjToJSONClass)
		elif jsonType == 'internal':
			return jsonEncode(data)
		else:
			return self.jsonPrinter(data, default=convertObjToJSON)
        
                       


	"""
		Return language data in JavaScript consumable format
	"""
	def getLangData(self):
		exec("import " + self.ctx['config']['language'])
		cherrypy.response.headers['Content-Type'] = 'text/javascript'
		return "var vboxLangData = " + self.toJSON(en_us.trans) + ";"
    
	getLangData.exposed = True


	"""
		Return RDP file
	"""
	def rdpFile(self, **kw):

		# Require authentication
		if not self.checkAuth():
			# Auth failed. Send 401.
			raise cherrypy.HTTPError(401, "Authentication is required to access the requested resource on this server.")
		
		# Init win32 com
		self.prepareCOM()

		if re.match('[^\d]', cherrypy.request.params.get('port')):
			response = {'errors':[],'data':{},'fn':'getVMDetails' }
			try:
				cherrypy.thread_data.vbox = vboxactions.vboxactions(self.ctx)
				req = {'vm':cherrypy.request.params.get('vm')}
				cherrypy.thread_data.vbox('getVMDetails',req,response)
			finally:
				if cherrypy.thread_data.vbox:
					cherrypy.thread_data.vbox.shutdown()
				del cherrypy.thread_data.vbox
			port = response['data'].get('consolePort')
		else:
			port = cherrypy.request.params.get('port')

		cherrypy.response.headers['Content-Type'] = "application/x-rdp"
		cherrypy.response.headers['Content-Disposition'] = "attachment; filename=\""+ cherrypy.request.params.get('vm') +".rdp\""
		
		return str("auto connect:i:1\nfull address:s:"+cherrypy.request.params.get('host')+( str(port+":") if port else '')+"\ncompression:i:1\ndisplayconnectionbar:i:1\n")

	rdpFile.exposed = True

	
	"""
		Used by jquery FileTree plugin to browse files / folders
	"""
	def jqueryFileTree(self, **kw):

		from jqueryFileTree import jqueryFileTree
		
		# Require authentication
		if not self.checkAuth():
			# Auth failed. Send 401.
			raise cherrypy.HTTPError(401, "Authentication is required to access the requested resource on this server.")

		# Init win32 com
		self.prepareCOM()
		
		rstr = ''
		
		allowedFiles = {}
		if self.ctx['config'].get('browserRestrictFiles'):
			allowedList = self.ctx['config']['browserRestrictFiles'].lower().split(',')
			for i in allowedList: allowedFiles[i] = i
        
		allowedFolders = {}
		if self.ctx['config'].get('browserRestrictFolders'):
			allowedList = self.ctx['config']['browserRestrictFolders'].lower().split(',')
			for i in allowedList: allowedFolders[i] = i
        
		localBrowser = bool(self.ctx['config'].get('browserLocal') or g_vboxManager)

		try:       
			cherrypy.thread_data.vbox = vboxactions.vboxactions(self.ctx)
            
			cherrypy.thread_data.vbox.connect()
            
			if str(cherrypy.thread_data.vbox.vbox.host.operatingSystem).lower().find('windows') == -1:
				strDSEP = '/'
			else:
				strDSEP = '\\'
    		
			ft = jqueryFileTree()
    		
			if localBrowser:
				if cherrypy.thread_data.vbox:
					cherrypy.thread_data.vbox.shutdown()
					del cherrypy.thread_data.vbox
				ft.mode = 'local'
			else:
				ft.mode = 'remote'
				ft.vbox = cherrypy.thread_data.vbox.vbox
    		
    		
			if cherrypy.request.params.get('fullpath'):
				ft.fullpath = int(cherrypy.request.params.get('fullpath'))
			if cherrypy.request.params.get('dirsOnly'):
				ft.dirsOnly = int(cherrypy.request.params.get('dirsOnly'))
			ft.strDSEP = strDSEP
			ft.allowedFiles = allowedFiles
			ft.allowedFolders = allowedFolders
    		
			rstr = ft.getdir(cherrypy.request.params.get('dir'))

		except Exception, e:
			print e
			print traceback.format_exc()
			
		finally:
			try:
				if cherrypy.thread_data.vbox:
					cherrypy.thread_data.vbox.shutdown()
					del cherrypy.thread_data.vbox
			except:
				pass
				
		return rstr
		
		
		
	jqueryFileTree.exposed = True
	
	"""
		Return screen shot
	"""
	def screen(self, **kw):
    	
    	# Require authentication
		if not self.checkAuth():
			# Auth failed. Send 401.
			raise cherrypy.HTTPError(401, "Authentication is required to access the requested resource on this server.")

		# Init win32 com
		self.prepareCOM()
    	
		width = cherrypy.request.params.get('width')
		vm = cherrypy.request.params.get('vm')
		if not vm: return ''

		try:
			cherrypy.thread_data.vbox = vboxactions.vboxactions(self.ctx)
    
			machine = cherrypy.thread_data.vbox._getMachineRef(vm)
			machineState = str(cherrypy.thread_data.vbox.vboxType('MachineState',machine.state))
    		
			if str(machineState) != 'Running' and str(machineState) != 'Saved':
				machine.releaseRemote()
				raise Exception('The specified virtual machine is not in a Running state.')
            
    		# Date last modified
			dlm = math.floor(int(machine.lastStateChange)/1000)
    
    		# Running screen shot
			if str(machineState) == 'Running':
    
				cherrypy.thread_data.vbox.session = cherrypy.thread_data.vbox.vboxMgr.platform.getSessionObject(cherrypy.thread_data.vbox.vbox)
				machine.lockMachine(cherrypy.thread_data.vbox.session,cherrypy.thread_data.vbox.vboxType('LockType','Shared'))
    
				res = cherrypy.thread_data.vbox.session.console.display.getScreenResolution(0)
    
				screenWidth = int(res[0])
				screenHeight = int(res[1])
    
				if width and int(width) > 0:
					factor  = float(float(width) / float(screenWidth))
					screenWidth = width
					if factor > 0:screenHeight = factor * screenHeight
					else:screenHeight = (screenWidth * 3.0/4.0)
    			
				cherrypy.response.headers["Expires"] = "Mon, 26 Jul 1997 05:00:00 GMT"
				cherrypy.response.headers['Last-Modified'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
				cherrypy.response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0"
				cherrypy.response.headers["Pragma"] = "no-cache"
    
				imageraw = [cherrypy.thread_data.vbox.session.console.display.takeScreenShotPNGToArray(0,int(screenWidth), int(screenHeight))]				
				cherrypy.thread_data.vbox.session.unlockMachine()
    			
    
			else:
    
    			# Set last modified header
				cherrypy.response.headers['Last-Modified'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(dlm))
    			
    		  	# Let the browser cache images
			  	if cherrypy.request.headers.get('If-Modified-Since') and time.mktime(parsedate_tz(cherrypy.request.headers.get('If-Modified-Since'))).time() >= dlm:
			  		raise cherrypy.HTTPRedirect([], 304)
          		
				if cherrypy.request.params.get('full'):
					imageraw = machine.readSavedScreenshotPNGToArray(0);
				else:
					imageraw = machine.readSavedThumbnailPNGToArray(0);
    
			cherrypy.response.headers['Content-Type'] = 'image/png'
    		
			imgdata = ''
    
    		# Non-web data is printed directly
			if cherrypy.thread_data.vbox.vboxConnType != 'web':
				for i in range(len(imageraw)):
					if len(imageraw[i]):
						imgdata = imageraw[i]
						break
			else:
    			
				for i in range(len(imageraw)):
					if type(imageraw[i]) == types.InstanceType:
						for b in imageraw[i]:
							imgdata += chr(b)
    		    		
		finally:
			if cherrypy.thread_data.vbox:
				cherrypy.thread_data.vbox.shutdown()
				del cherrypy.thread_data.vbox
			
		imgdata = StringIO.StringIO(imgdata)
		return cherrypy.lib.file_generator(imgdata)
	
	screen.exposed = True
        
	"""
    
        
        ALL ajax calls
        
         
    """
	def ajax(self,fn, **kw):

		# Require authentication
		if not self.checkAuth():
			# Auth failed. Send 401.
			raise cherrypy.HTTPError(401, "Authentication is required to access the requested resource on this server.")

		# Init win32 com
		self.prepareCOM()
        
		response = {'errors':[],'data':{},'fn':fn }
        
		cherrypy.thread_data.vbox = None
		
		try:
			
			##########################
			#
    		# Configuration request
    		#
    		#########################
			if fn == 'getConfig':
    
				response['data'] = self.ctx['config']
    

				try:              
				
					cherrypy.thread_data.vbox = vboxactions.vboxactions(self.ctx)
    				
					response['data']['VBWEB_ERRNO_FATAL'] = self.VBWEB_ERRNO_FATAL
    
					response['data']['version'] = cherrypy.thread_data.vbox.vboxVersion()
            		
					response['data']['hostOS'] = str(cherrypy.thread_data.vbox.vbox.host.operatingSystem)
					if response['data']['hostOS'].lower().find('windows') == -1:
						response['data']['DSEP'] = '/'
					else:
						response['data']['DSEP'] = '\\'
            				
				except:
					pass
        		
				if response['data'].get('username'): del response['data']['username']
				if response['data'].get('password'): del response['data']['password']
        		
				# Get host
				if response['data'].get('location'):
					
					try:
						from urlparse import urlparse
						url = urlparse(response['data'].get('location'))
					except:
						url = urllib.parse(response['data'].get('location'))
					response['data']['host'] = url.hostname

					if not response['data'].get('servers') or type(response['data']['servers']) != type(list()):
						response['data']['servers'] = [
    						{'name' : response['data']['host'],
    						'location' : response['data']['location']
    						}
    					]
					response['data']['servername'] = response['data']['servers'][0]['name']
                
				else:
					response['data']['host'] = 'localhost'
					response['data']['servers'] = []
        
				if not response['data'].get('consoleHost'):
					response['data']['consoleHost'] = response['data']['host']


			##############################
			#
			# Other AJAX requests
			#
			##############################
			else:
                
				cherrypy.thread_data.vbox = vboxactions.vboxactions(self.ctx)
    
				cherrypy.thread_data.vbox(fn,cherrypy.request.params, response)
				
                
			try:
				if cherrypy.thread_data.vbox and len(cherrypy.thread_data.vbox.errors):
					response['errors'] = cherrypy.thread_data.vbox.errors
			except:
				pass
            
		except Exception, e:
			
			errno = 0
			error = str(e)
			details = traceback.format_exc()
			
			try:
				errno = self.VBWEB_ERRNO_FATAL if cherrypy.thread_data.vbox and not cherrypy.thread_data.vbox.connected else 0
			except:
				pass
				
			response['errors'].append(
				{'errno':errno,
				'error':error,
				'details':details
				}
			)				
		
		
		# make sure vbox.shutdown() is called
		finally:
			#response = self.toJSON(response)
			try:
				if cherrypy.thread_data.vbox:
					cherrypy.thread_data.vbox.shutdown()
    				del cherrypy.thread_data.vbox
			except:pass
        
		# Debug output
		if len(response['errors']):
			print response['errors']
		if len(g_progressOps):
			print g_progressOps
		        
		cherrypy.response.headers['Content-Type'] = 'text/javascript'

		return self.toJSON(response)
	
	ajax.exposed = True
         
	def index(self,**kw):

		# Require authentication
		if self.checkAuth():
			if cherrypy.request.params.get('vbwlogin'):
				raise cherrypy.HTTPRedirect('/')
			file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'www/static/index.html')
		else:
			file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'www/static/login.html')
			
		cherrypy.response.headers["Expires"] = "Mon, 26 Jul 1997 05:00:00 GMT"
		cherrypy.response.headers['Last-Modified'] = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
		cherrypy.response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0"
		cherrypy.response.headers["Pragma"] = "no-cache"
					
		return serve_file(file, content_type='text/html')
    
	index.exposed = True


"""
	
	Web Server Thread starts cherrypy
	
"""
class WebServerThread(threading.Thread):
	
    def __init__(self, ctx):
    	
		threading.Thread.__init__(self)
		self.ctx = ctx
        
		if g_vboxManager:
			self.ctx['vbox'] = g_vboxManager.vbox
		
		if sys.platform == 'win32':
			self.vbox_stream = pythoncom.CoMarshalInterThreadInterfaceInStream(pythoncom.IID_IDispatch, self.ctx['vbox'])

    def finish(self):
        cherrypy.engine.exit()

    def run(self):

		if sys.platform == 'win32':
			i = pythoncom.CoGetInterfaceAndReleaseStream(self.vbox_stream, pythoncom.IID_IDispatch)
			self.ctx['vbox'] = win32com.client.Dispatch(i)

		cherrypy.quickstart(VBoxWeb(self.ctx), '/', {
				'/rdpweb': {
					'tools.staticdir.on': True,
					'tools.staticdir.dir': 'www/static/rdpweb'},													
                '/images': {
                    'tools.staticdir.on': True,
                    'tools.staticdir.dir': 'www/static/images'},
                '/panes': {
                    'tools.staticdir.on': True,
                    'tools.staticdir.dir': 'www/static/panes'},
                '/css': {
                    'tools.staticdir.on': True,
                    'tools.staticdir.dir': 'www/css'},
                '/js': {
                    'tools.staticdir.on': True,
                    'tools.staticdir.dir': 'www/static/js'},                    
                }
        )



def main(argv = sys.argv):

	global g_vboxManager
	
    # For proper UTF-8 encoding / decoding
	reload(sys)
	sys.setdefaultencoding('utf8')
	
	print "VBoxWebSrv Platform: %s"%sys.platform

	# Load config file
	import VBoxWebConfig
	config = VBoxWebConfig.VBoxWebConfig()
	
	# Determine connection type
	try:
		if config.location or len(config.servers):
			print "Connection type: vboxwebsrv"
	except:
		g_vboxManager = vboxapi.VirtualBoxManager(None, None)
		print "Connection type: local; VirtualBox Version: %s" %g_vboxManager.vbox.version
	

    # Check command line args
	if len(argv) > 1:
		
		if argv[1] == "adduser":
			if len(argv) <> 4:
				print "Syntax: " + argv[0] + " adduser <username> <password>"
				print "\t\t(also used to change user's password)"
				return
			h = hashlib.new('sha1')
			h.update(argv[3])
			g_vboxManager.vbox.setExtraData(
				"vboxwebc/users/" + argv[2], h.hexdigest())
			return
		elif argv[1] == "deluser":
			if len(argv) <> 3:
				print "Syntax: " + argv[0] + " deluser <username>"
				return
			g_vboxManager.vbox.setExtraData("vboxwebc/users/" + argv[2], "")
			return
		elif argv[1] == "help":
			print """
VBoxWeb Command Usage:

    adduser <username> <password>
        - Add a new user to VBoxWeb (also used to change <username's> password)

    deluser <username>
        - Delete an existing user

    help
        -Display this message
"""
			return
		else:
			print "\nUnknown command '%s'. See '%s help' for available commands" % (argv[1], argv[0])
			return

	cherrypy.engine.subscribe('start_thread', perThreadInit)
	cherrypy.engine.subscribe('stop_thread',  perThreadDeinit)

	cherrypy.config.update(VBoxWebConfig.WebServerConfig)
	cherrypy.config.update({
						'tools.sessions.storage_path' : os.path.abspath(os.path.dirname(__file__)) + '/.sessions',
						'tools.staticdir.root': os.path.abspath(os.path.dirname(__file__))
    })

	ctx = {'global':g_vboxManager,'vbox':None}

	cherrypy.engine.subscribe('stop', onShutdown)

    # Start the webserver thread
	ws = WebServerThread(ctx)
	ws.start()

    # Events loop, wait for keyboard interrupt
	global g_serverTerminated

    # Loop for local connections
	if g_vboxManager:
		try:
          # Darwin-specific uglyness
		  if sys.platform == 'darwin':
		  	while not g_serverTerminated:
                # We have no timed waits on Darwin, and waitForEvents(-1)
                # blocks signal delivery for some reasons, thus we cannot send
                # wait interrupt notifcation.
                # Instead we cheat a bit and just sleep() between events
				g_vboxManager.waitForEvents(0)
				time.sleep(0.3)
		  else:
		  	while not g_serverTerminated:
		  		g_vboxManager.waitForEvents(-1)
  		except KeyboardInterrupt:
  			pass

	# Loop for vboxwebsrv connections
	else:
		try:
			while not g_serverTerminated:
				time.sleep(0.3)
			print "Terminating..."
		except KeyboardInterrupt:
			print "Caught interrupt"
			pass
					
    # Shut down
	ws.finish()

	
if __name__ == '__main__':
    main(sys.argv)
