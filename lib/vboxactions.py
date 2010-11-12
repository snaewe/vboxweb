"""

	$Id$
	Copyright (C) 2010 Ian Moore (imoore76 at yahoo dot com)

"""

import threading
import cache
import re
import math
import time
import types
import traceback
import hashlib
import os
from VBoxWebSrv import trans
from vboxapi import VirtualBoxManager
import VirtualBox_wrappers

class vboxactions(threading.local):

	# VBOX Constants
	resultcodes = {
		'0x80BB0001' : 'VBOX_E_OBJECT_NOT_FOUND',
		'0x80BB0002' : 'VBOX_E_INVALID_VM_STATE',
		'0x80BB0003' : 'VBOX_E_VM_ERROR',
		'0x80BB0004' : 'VBOX_E_FILE_ERROR',
		'0x80BB0005' : 'VBOX_E_IPRT_ERROR',
		'0x80BB0006' : 'VBOX_E_PDM_ERROR',
		'0x80BB0007' : 'VBOX_E_INVALID_OBJECT_STATE',
		'0x80BB0008' : 'VBOX_E_HOST_ERROR',
		'0x80BB0009' : 'VBOX_E_NOT_SUPPORTED',
		'0x80BB000A' : 'VBOX_E_XML_ERROR',
		'0x80BB000B' : 'VBOX_E_INVALID_SESSION_STATE',
		'0x80BB000C' : 'VBOX_E_OBJECT_IN_USE'
	}


	"""
	 Caching settings. Function : time in seconds. 0 == do not cache
	"""
	cacheSettings = {
			'getHostDetails' : 86400,
			'getGuestOSTypes' : 86400,
			'getSystemProperties' : 86400,
			'getHostNetworking' : 300,
			'getMediums' : 300, # 10 minutes
			'getVMs' : 2,
			'_getMachine' : 7200, # 2 hours
			'_getNetworkAdapters' : 7200,
			'_getStorageControllers' : 7200,
			'_getSharedFolders' : 7200,
			'_getUSBController' : 7200,
	}

	# Any exceptions generated
	errors = []

	# Not connected
	connected = False
	
	# No fatal error.. for starters
	fatal = False
	
	vbox = None
	vboxMgr = None
	cache = None
	session = None
	version = None
	progressCreated = False
	initialized = False
	vboxConnType = None
	progressOps = {}

	def __init__(self, ctx):

		if self.initialized:
			raise SystemError('__init__ called too many times in vboxconnector object')
		
		self.initialized = True
		
		self.errors = []
		self.progressOps = {}
		self.connected = self.fatal = self.progressCreated = False
		self.vbox = self.vboxMgr = self.cache = self.session = self.vboxConnType = self.ctx = None
		
		self.ctx = ctx

		# Set.. .. settings
		self.settings = self.ctx['config']
		
		if not self.settings.get('nicMax'):
			self.settings['nicMax'] = 4


		# Cache handler object.
		self.cache = cache.cache()
		self.cache.expire_multiplier = 1 # default
		
		
		# Connection type
		if self.settings.get('location'):
			self.vboxConnType = 'web'
		else:
			self.vboxConnType = 'xpcom'

		if(self.settings.get('disableCache')): self.cacheSettings = {}
		elif(self.settings.get('cacheExpireMultiplier')):
			self.cache.expire_multiplier = int(self.settings.get('cacheExpireMultiplier'))
			if(self.settings.get('cacheSettings')):
				self.cacheSettings.update(self.settings['cacheSettings'])
		if(self.settings.get('cachePath')): self.cache.path = self.settings.get('cachePath')
	
		self.cache.prefix = 'vbwc-'
		
		if self.settings.get('location'):
			self.cache.prefix = self.cache.prefix + str(hashlib.md5(self.settings.get('location')).hexdigest())
		else:
			# Handle both Win* And *nix
			self.cache.prefix = self.cache.prefix + str(hashlib.md5(str(os.environ.get('USERNAME',''))+str(os.environ.get('USER',''))).hexdigest())
		
		# Progress operation handling
		self.progressOps = ctx['progressOps']
		
		


	"""
	 
	  Connect to VirtualBox
	 
	"""
	def connect(self):

		# Already connected?
		if(self.connected): return True

		# Connect to webservice or?
		if self.vboxConnType == 'web':
			
			
			try:
				
				self.vboxMgr = VirtualBoxManager("WEBSERVICE",
							{'url':self.settings.get('location'),
								'user':self.settings.get('username'),
								'password':self.settings.get('password')})
				
				self.vbox = self.vboxMgr.vbox
				
				
			except Exception, e:				
				raise Exception("Error logging in or connecting to vboxwebsrv: " + str(e))
				
		else:
			self.vboxMgr = self.ctx['global']
			self.vbox = self.ctx['vbox']
		
		
		self.connected = True
		return True
	
	"""
	
		Cleanup
	
	"""
	def shutdown(self):

		# Do not logout if there is a progress operation associated
		# with this vboxweb session
		if self.connected and (not self.progressCreated) and self.vbox:

			if(self.session):
				try: self.session.unlockMachine()
				except: pass
			
			if self.vboxConnType == 'web': 
				self.vboxMgr.platform.disconnect()

		del self.errors, self.connected, self.fatal, self.progressCreated, self.ctx,self.progressOps, self.vbox, self.vboxMgr, self.session, self.vboxConnType
		
		self.cache.shutdown()
		del self.cache
	
	"""
		Return vbox type
	"""
	def vboxType(self,vbtype,conv):
		if type(conv) == types.InstanceType: conv = int(conv)
		exec "r = VirtualBox_wrappers."+vbtype+"(None,conv)"
		return r

	"""
		Return vbox type for setting values
	"""
	def vboxTypeSet(self,vbtype,conv):
		i = 0
		try:
			i = self.vboxType(vbtype,conv)
		except:
			pass
		return int(i)
	
	"""
		Return array of vbox items
	"""
	def vboxArray(self,obj,arrName):
		if self.vboxConnType == 'web':
			return getattr(obj,arrName)
		else:
			return self.vboxMgr.getArray(obj, arrName)
		
	"""
	 Return and / or set version
	"""
	def vboxVersion(self):

		if not self.version:

			self.connect()

			self.version = str(self.vbox.version)
			self.version = self.version.split('.')
			
			self.version = {
				'ose':(self.version[2].lower().find('ose') > 0),
				'string':'.'.join(self.version),
				'major':int(self.version.pop(0)),
				'minor':int(self.version.pop(0)),
				'sub':int(re.sub('[^\d]','',self.version.pop(0))),
				'revision':str(self.vbox.revision),
				'settingsFilePath' : str(self.vbox.settingsFilePath)
			}

		return self.version



	"""
	 
	 call overloader. Handles caching
	 
	"""
	def __call__(self,fn,req,response):


		"""
		 
		 Special Cases First
		 
		"""
		
		# Setting VM states
		if(fn.find('setStateVM') == 0):

			self.__setVMState(req['vm'],fn[10:],response)

		# Getting enumeration values
		elif(fn.find('getEnum') == 0):

			self._getEnumerationMap(fn[7:],response)

		# Access to other methods goes through caching
		elif(hasattr(self, fn+'Cached') and callable(getattr(self, fn+'Cached'))):

			# do not cache
			if(not self.cacheSettings.get(fn)):
				
				getattr(self, fn+'Cached')(req,response)

			# cached data exists ? return it : get data, cache data, return data
			elif(req.get('force_refresh') or (self.cache.get(fn,self.cacheSettings[fn],response) == False)):
	
					lock = self.cache.lock(fn)
	
					# file was modified while attempting to lock.
					# file data is returned
					if(lock == None):
						self.cache.get(fn,self.cacheSettings[fn],response)
	
					# lock obtained
					else:
						
						getattr(self, fn+'Cached')(req,response)

						if(self.cache.store(fn,response['data']) == False and response['data'] != False):
							raise Exception, "Error storing cache for " + fn
						
						
		# No caching method exists
		elif(hasattr(self, fn) and callable(getattr(self, fn))):
			getattr(self, fn)(req,response)
			
		# Not found
		else:
			raise Exception, 'Undefined method: '+ str(fn)

		
		response['errors'] = self.errors
		
		return response
	

	"""
		Enumerate guest properties of vm.
	"""
	def enumerateGuestProperties(self,args,response):

		self.connect()

		m = self.vbox.findMachine(args['vm'])

		response['data'] = m.enumerateGuestProperties(args['pattern'])

		return True


	"""	
		Get / Set Extra data functions
	"""
	def setExtraData(self,args,response):
		self.connect()
		self.vbox.setExtraData(str(args['key']),str(args['value']))
		response['data'] = 1
		return True

	def getExtraData(self,args,response):
		self.connect()
		response['data'] = str(self.vbox.setExtraData(str(args['key'])))
		return True

	"""
	
		Save all VM settings
		
	 """
	def saveVM(self,args,response):

		self.connect()
				
		# create session and lock machine
		machine = self.vbox.findMachine(args['id'])
		self.session = self.vboxMgr.platform.getSessionObject(self.vbox)
		machine.lockMachine(self.session, self.vboxType('LockType','Write'))

		# Version (OSE) checks below
		version = self.vboxVersion()

		# Cache items to expire
		expire = []

		# Shorthand
		m = self.session.machine

		# General machine settings
		m.name = str(args['name'])
		m.description = str(args['description'])
		m.OSTypeId = str(args['OSTypeId'])
		m.CPUCount = int(args['CPUCount'])
		m.memorySize = int(args['memorySize'])
		if self.vboxConnType == 'web':
			m.firmwareType = str(self.vboxType('FirmwareType',str(args['firmwareType'])))
		else:
			m.firmwareType = int(self.vboxType('FirmwareType',str(args['firmwareType'])))
		
		# Debug input
		#print args
		
		if(str(m.snapshotFolder) != str(args['snapshotFolder'])):
			m.snapshotFolder = str(args['snapshotFolder'])

		m.VRAMSize = int(args['VRAMSize'])

		""" Unsupported at this time
		m.monitorCount = max(1,int(args['monitorCount']))
		m.accelerate3DEnabled = args['accelerate3DEnabled']
		m.accelerate2DVideoEnabled = args['accelerate2DVideoEnabled']
		"""
		
		# Only if acceleration configuration is enabled
		if(self.settings['enableAccelerationConfig']):
			
			if int(args.get('HWVirtExProperties[Enabled]')): m.setHWVirtExProperty(self.vboxType('HWVirtExPropertyType','Enabled'),1)
			else: m.setHWVirtExProperty(self.vboxType('HWVirtExPropertyType','Enabled'),0)
			
			if int(args.get('HWVirtExProperties[NestedPaging]')): m.setHWVirtExProperty(self.vboxType('HWVirtExPropertyType','NestedPaging'), 1)
			else: m.setHWVirtExProperty(self.vboxType('HWVirtExPropertyType','NestedPaging'), 0)

		if int(args.get('RTCUseUTC')): m.RTCUseUTC = 1
		else: m.RTCUseUTC = 0

		if int(args.get('CpuProperties[PAE]')): m.setCPUProperty(self.vboxType('ProcessorFeature','PAE'), 1)
		else: m.setCPUProperty(self.vboxType('ProcessorFeature','PAE'),0)
		
		if args.get('GUI[SaveMountedAtRuntime]') == 'no':
			m.setExtraData('GUI/SaveMountedAtRuntime', 'no')
		else:
			m.setExtraData('GUI/SaveMountedAtRuntime', 'yes')

		# IOAPIC
		if int(args.get('BIOSSettings[IOAPICEnabled]')): m.BIOSSettings.IOAPICEnabled = 1
		else: m.BIOSSettings.IOAPICEnabled = 0

		# VRDE settings
		if(not version['ose']):
			if args.get('VRDEServer[enabled]'): m.VRDEServer.enabled = 1
			else: m.VRDEServer.enabled = 0
			m.VRDEServer.setVRDEProperty('TCP/Ports',str(args.get('VRDEServer[ports]')))
			if args.get('VRDEServer[authType]'): m.VRDEServer.authType = args.get('VRDEServer[authType]')
			else: m.VRDEServer.authType = int(self.vboxType('AuthType','Null'))
			m.VRDEServer.authTimeout = int(args.get('VRDEServer[authTimeout]'))
			if args.get('VRDEServer[allowMultiConnection]'): m.VRDEServer.allowMultiConnection = 1
			else: m.VRDEServer.allowMultiConnection = 0		

		# Audio controller settings
		if int(args.get('audioAdapter[enabled]')) > 0: m.audioAdapter.enabled = 1
		else: m.audioAdapter.enabled = 0
		m.audioAdapter.audioController = self.vboxTypeSet('AudioControllerType',args['audioAdapter[audioController]'])
		m.audioAdapter.audioDriver = self.vboxTypeSet('AudioDriverType',args['audioAdapter[audioDriver]'])

		# Boot order
		for i in range(self.vbox.systemProperties.maxBootPosition):
			if i < len(args['bootOrder[]']) and args['bootOrder[]'][i]:
				m.setBootOrder((i + 1),self.vboxTypeSet('DeviceType',args['bootOrder[]'][i]))
			else:
				m.setBootOrder((i + 1),self.vboxTypeSet('DeviceType','Null'))

		# Expire machine cache
		expire.append('_getMachine'+args['id'])


		# Storage Controllers
		attachedEx = attachedNew = {}
		for sc in self.vboxArray(m,'storageControllers'):
			mas = m.getMediumAttachmentsOfController(sc.name)
			for ma in mas:
				if type(ma.medium) != types.NoneType and str(ma.medium):
					attachedEx[str(sc.name)+str(ma.port)+str(ma.device)] = str(ma.medium.id)
				else: attachedEx[str(sc.name)+str(ma.port)+str(ma.device)] = None
				if(str(ma.controller)):
					m.detachDevice(ma.controller,ma.port,ma.device)

			scname = sc.name
			m.removeStorageController(scname)


		# Add New
		for i in range(10):
			
			name = args.get('storageControllers['+str(i)+'][name]')
			if not name: break;
			name = str(name).strip()
			
			if not name:
				name = str(args.get('storageControllers['+str(i)+'][bus]'))+' Controller'

			bust = self.vboxType('StorageBus',args.get('storageControllers['+str(i)+'][bus]'))
			c = m.addStorageController(name,bust)
			c.controllerType = self.vboxTypeSet('StorageControllerType',args.get('storageControllers['+str(i)+'][controllerType]'))
			
			if args.get('storageControllers['+str(i)+'][useHostIOCache]'): c.useHostIOCache = 1
			else: c.useHostIOCache = 0
			
			# Medium attachments
			for a in range(50):
				
				mtype = args.get('storageControllers['+str(i)+'][mediumAttachments]['+str(a)+'][type]')
				
				if not mtype: break

				device = int(args.get('storageControllers['+str(i)+'][mediumAttachments]['+str(a)+'][device]'))
				port = int(args.get('storageControllers['+str(i)+'][mediumAttachments]['+str(a)+'][port]'))
				medium = (str(args.get('storageControllers['+str(i)+'][mediumAttachments]['+str(a)+'][medium][id]')) if args.get('storageControllers['+str(i)+'][mediumAttachments]['+str(a)+'][medium][id]') else None)
				
				attachedNew[name+str(port)+str(device)] = medium

				if medium:
					med = self.vbox.findMedium(medium,self.vboxType('DeviceType',mtype))
				else:
					med = ('' if self.vboxConnType == 'web' else None)
				
				m.attachDevice(name,port,device,self.vboxType('DeviceType',mtype),med)
				
				if(str(mtype) == 'DVD'):
					if args.get('storageControllers['+str(i)+'][mediumAttachments]['+str(a)+'][passthrough]'): passthrough= True
					else: passthrough = False
					m.passthroughDevice(name,port,device,passthrough)
					
		# Expire storage
		expire.append('_getStorageControllers'+str(args['id']))
		expire.append('getMediums')


		"""
		 *
		 * When changing the following items, try our best to preserve existing
		 * cache at the expense of some processing. For vboxwebsrv connections only
		 *
		 """
		 
		# Network Adapters
		netchanged = False
		netprops = ['adapterType','MACAddress','hostInterface','internalNetwork','NATNetwork','cableConnected','attachmentType','enabled']
		netpropTypes = ['NetworkAdapterType',None,None,None,None,None,'NetworkAttachmentType',None]
		adapters = self._getCachedMachineData('_getNetworkAdapters',args['id'],self.session.machine)

		for i in range(self.settings['nicMax']):

			# Is there a property diff?
			if self.vboxConnType == 'web':
				ndiff = False
				for p in netprops:
					if(str(args.get('networkAdapters['+str(i)+']['+str(p)+']')) == str(adapters[i][p])): continue
					ndiff = True
					break
	
				# Check for redirection rules diff
				ndiff = (ndiff or (args.get('networkAdapters['+str(i)+'][redirects]') != adapters[i]['redirects']))
			else:
				ndiff = True
			
			if(not ndiff): continue
			netchanged = True


			n = m.getNetworkAdapter(i)
			for p in range(len(netprops) - 1):
				# Attachment type is set below
				if netprops[p] == 'attachmentType': continue
				# Internal network required
				if netprops[p] == 'internalNetwork' and not str(args.get('networkAdapters['+str(i)+']['+netprops[p]+']')): continue
				# Cast to vbox type
				setting = str(args.get('networkAdapters['+str(i)+']['+netprops[p]+']'))
				if netpropTypes[p]: setting = self.vboxTypeSet(netpropTypes[p], setting)
				setattr(n,netprops[p],setting)
			n.enabled = int(args.get('networkAdapters['+str(i)+'][enabled]'))


			if args.get('networkAdapters['+str(i)+'][attachmentType]') == 'Bridged':
					n.attachToBridgedInterface()
			elif args.get('networkAdapters['+str(i)+'][attachmentType]') == 'Internal':
					n.attachToInternalNetwork()
			elif args.get('networkAdapters['+str(i)+'][attachmentType]') == 'HostOnly':
					n.attachToHostOnlyInterface()
			elif args.get('networkAdapters['+str(i)+'][attachmentType]') == 'NAT':
				
					n.attachToNAT()

					for r in self.vboxArray(n.natDriver,'redirects'):
						n.natDriver.removeRedirect(str(r).split(',').pop(0))

					
					# Check for array with no idex
					if args.get('networkAdapters['+str(i)+'][redirects][]'):
						r = args.get('networkAdapters['+str(i)+'][redirects][]')
						if type(r) == type(list()):
							for a in range(len(r)):
								args['networkAdapters['+str(i)+'][redirects]['+str(a)+']'] = r[a]
						else:
							args['networkAdapters['+str(i)+'][redirects][0]'] = r
					
					# Add redirects
					for a in range(50):
						r = args.get('networkAdapters['+str(i)+'][redirects]['+str(a)+']')
						if not r: break
						r = str(r).split(',')
						n.natDriver.addRedirect(r[0],r[1],r[2],int(r[3]),r[4],int(r[5]))

			else:
					n.detach()

		# Expire network info?
		if(netchanged):
			expire.append('_getNetworkAdapters'+args['id'])
			expire.append('getHostNetworking')


		# Shared Folders
		sharedchanged = False
		sharedEx = {}
		sharedNew = {}
		for s in self._getCachedMachineData('_getSharedFolders',args['id'],m):
			sharedEx[s['name']] = {'name':s['name'],'hostPath':s['hostPath'],'autoMount':int(s['autoMount']),'writable':int(s['writable'])}
		
		for i in range(50):
			if not args.get('sharedFolders['+str(i)+'][name]'): break
			
			sfname = args.get('sharedFolders['+str(i)+'][name]')
			hostPath = args.get('sharedFolders['+str(i)+'][hostPath]')
			autoMount = int(args.get('sharedFolders['+str(i)+'][autoMount]'))
			writable = int(args.get('sharedFolders['+str(i)+'][writable]'))
			
			sharedNew[sfname] = {'name':sfname,'hostPath':hostPath,'autoMount':autoMount,'writable':writable}
		
		# Compare if we are trying to preserve cache
		if(self.vboxConnType != 'web' or (len(sharedEx) != len(sharedNew) or (sharedEx != sharedNew))):
			sharedchanged = True
			for k,s in sharedEx.iteritems(): m.removeSharedFolder(s['name'])
			for k,s in sharedNew.iteritems():
				m.createSharedFolder(s['name'],s['hostPath'],int(s['writable']),int(s['autoMount']))
		
		# Expire shared folders?
		if(sharedchanged): expire.append('_getSharedFolders'+args['id'])


		# USB Filters
		if(not version['ose'] or 1 == 1):

			usbchanged = False
			usbEx = {}
			usbNew = {}

			usbc = self._getCachedMachineData('_getUSBController',args['id'],self.session.machine)

			# controller properties
			if(self.vboxConnType != 'web' or (int(usbc['enabled']) != int(args.get('USBController[enabled]')) or int(usbc['enabledEhci']) != int(args.get('USBController[enabledEhci]')))):
				usbchanged = True
				m.USBController.enabled = int(args.get('USBController[enabled]'))
				m.USBController.enabledEhci = int(args.get('USBController[enabledEhci]'))

			# usb filter properties to change / check
			usbProps = ['vendorId','productId','revision','manufacturer','product','serialNumber','port','remote']
			
			# filters
			args['USBController'] = {}
			args['USBController']['deviceFilters'] = []
			for a in range(50):
				name = args.get('USBController[deviceFilters]['+str(a)+'][name]')
				if not name: break
				f = {'name':name,
					'active':int(args.get('USBController[deviceFilters]['+str(a)+'][active]')),
					'vendorId':re.sub('[^abcdef0-9]','',str(args.get('USBController[deviceFilters]['+str(a)+'][vendorId]')).lower()[0:4]),
					'productId':re.sub('[^abcdef0-9]','',str(args.get('USBController[deviceFilters]['+str(a)+'][productId]')).lower()[0:4]),
					'revision':re.sub('[^abcdef0-9]','',str(args.get('USBController[deviceFilters]['+str(a)+'][revision]')).lower()[0:4]),
					'port':(int(re.sub('[^0-9]','',args.get('USBController[deviceFilters]['+str(a)+'][port]'))) if args.get('USBController[deviceFilters]['+str(a)+'][port]') and re.sub('[^0-9]','',args.get('USBController[deviceFilters]['+str(a)+'][port]')) else None)
				}
				for b in usbProps:
					if f.get(b): continue
					f[b] = str(args.get('USBController[deviceFilters]['+str(a)+']['+str(b)+']')) if args.get('USBController[deviceFilters]['+str(a)+']['+str(b)+']') else None
				args['USBController']['deviceFilters'].append(f)
				
			if(self.vboxConnType != 'web' or (len(usbc['deviceFilters']) != len(args['USBController']['deviceFilters']) or usbc['deviceFilters'] != args['USBController']['deviceFilters'])):

				usbchanged = True


				# Remove and Add filters
				maxLen = max(len(usbc['deviceFilters']),len(args['USBController']['deviceFilters']))
				offset = 0
				
				# Remove existing
				for i in range(maxLen):

					# Only if filter differs
					if((i >= len(usbc['deviceFilters'])) or (i >= len(args['USBController']['deviceFilters'])) or (usbc['deviceFilters'][i] != args['USBController']['deviceFilters'][i])):

						# Remove existing?
						if(i < len(usbc['deviceFilters'])):
							m.USBController.removeDeviceFilter((i - offset))
							offset = offset + 1

						# Exists in new?
						if(i < len(args['USBController']['deviceFilters'])):

							# Create filter
							f = m.USBController.createDeviceFilter(args['USBController']['deviceFilters'][i]['name'])
							f.active = int(args['USBController']['deviceFilters'][i]['active'])

							for p in usbProps:
								if args['USBController']['deviceFilters'][i].get(p):
									setattr(f,p,str(args['USBController']['deviceFilters'][i][p]))

							m.USBController.insertDeviceFilter(i,f)
							
							offset = offset - 1


			# Expire USB info?
			if(usbchanged): expire.append('_getUSBController'+args['id'])
	


		self.session.machine.saveSettings()
		self.session.unlockMachine()
		self.session = None

		# Expire cache
		for ex in expire:
			self.cache.expire(ex)

		response['data']['result'] = 1

		return True


	"""
	 * Return cached result from machine request
	 """
	def _getCachedMachineData(self,fn,key,item,force_refresh=False):

		# do not cache
		if(not self.cacheSettings.get(fn) or not key):
			return getattr(self, fn)(item)

		
		# Cached data exists?
		result = {}
		if not force_refresh and (self.cache.get(fn+key,self.cacheSettings[fn],result) != False):
			return result['data']

		lock = self.cache.lock(fn+key)

		# file was modified while attempting to lock.
		# file data is returned
		if(lock == None):
			return self.cache.get(fn+key,self.cacheSettings[fn])

		result = getattr(self, fn)(item)
		
		if(self.cache.store(fn+key,result) == False and result != False):
			raise Exception("Error storing cache.")
			return False

		return result



	"""
	 * Get progress for operation.
	 """
	def getProgress(self,args,response):

		args['progress'] = str(args['progress'])
		
		pop = self.cache.get('ProgressOperations',False)
		pop = pop.get(args['progress'])
		
		if(not pop):
			raise Exception('Could not obtain progress operation: '+ args['progress'])

		# Connect to vboxwebsrv
		self.connect()
		session = progress = None

		try:

			try:

				# vboxwebsrv method of obtaining objects
				if self.vboxConnType == 'web':
					
					# Keep session from timing out
					vbox = VirtualBox_wrappers.IVirtualBox(self.vboxMgr.platform.wsmgr, pop['session']);
					
					session = self.vboxMgr.platform.getSessionObject(vbox)
					
					# Force call
					if str(session.state):
						pass
					
					progress = VirtualBox_wrappers.IProgress(self.vboxMgr.platform.wsmgr,args['progress'])
	
				# XPCOM method
				else:
					gpop = self.progressOps.get('get')(args['progress'])
					
					progress = gpop['progress']
					
					session = gpop['session']
					

			except Exception, e:
				self.errors.append(
					{'errno':0,
					'error':str(type(e)) + ": " + str(e),
					'details':traceback.format_exc()
					}
				)				
				raise Exception('Could not obtain progress operation: '+args['progress'])
			
			
			response['data']['progress'] = args['progress']

			response['data']['info'] = {
				'completed' : bool(progress.completed),
				'canceled' : bool(progress.canceled),
				'description' : str(progress.operationDescription),
				'timeRemaining' : self.__splitTime(int(progress.timeRemaining)),
				'timeElapsed' : self.__splitTime((time.time() - pop['started'])),
				'percent' : int(progress.percent)
			}

			# Completed? Do not return. Fall to __destroyProgress() called later
			if(response['data']['info']['completed'] or response['data']['info']['canceled']):

				try:
					if(not response['data']['info']['canceled'] and progresss and progress.errorInfo.text):
						self.errors.append(
							{'errno':0,
							'error':str(progress.errorInfo.text),
							'details':traceback.format_exc()
							}
						)				
				except:
					pass


			else:

				response['data']['info']['cancelable'] = bool(progress.cancelable)

				return True


		except Exception, e:

			# Force progress dialog closure
			response['data']['info'] = {'completed':1}

			# Does an exception exist?
			try:
				if(progress and progress.errorInfo):
					self.errors.append(
						{'errno':0,
						'error':str(progress.errorInfo.text),
						'details':traceback.format_exc()
						}
					)				

			except:
				pass

			# Some progress operations seem to go away after completion
			# probably the result of automatic session closure
			if not (session and str(self.vboxType('SessionState',session.state)) == 'Unlocked'):
				self.errors.append(
					{'errno':0,
					'error':str(type(e)) + ": " + str(e),
					'details':traceback.format_exc()
					}
				)				



		self.__destroyProgress(args['progress'],response)


	"""
	 * Get progress for operation.
	 """
	def cancelProgress(self,args,response):

		pop = self.cache.get('ProgressOperations',False)
		pop = pop[args['progress']]
		
		if(not pop):
			raise Exception('Could not obtain progress operation: '+args['progress'])

		# Connect to vboxwebsrv
		self.connect()

		try:
			if self.vboxConnType == 'web':
				progress = VirtualBox_wrappers.IProgress(self.client,args['progress'])
			else:
				pop = self.progressOps.get('get')(args['progress'])
				progress = pop['progress']
				
			if(not (progress.completed or progress.canceled)):
				progress.cancel()
				
		except Exception, e:
			self.errors.append(
				{'errno':0,
				'error':str(type(e))+": "+str(e),
				'details':traceback.format_exc()
				}
			)				

		response['data']['progress'] = str(args['progress'])
		response['data']['result'] = 1
		return True

	"""
	 *
	 * Destroy a progress reference
	 *
	 """
	def __destroyProgress(self,p,response):

		pops = self.cache.get('ProgressOperations',False)
		pop = pops[p]
		
		if(not pop):
			raise Exception('Could not destroy progress operation: '+p)

		# Expire cache item?
		if pop['expire'] and type(pop['expire']) == type(list()):
			for e in pop['expire']: self.cache.expire(e)

		# Connect to vbox
		self.connect()

		try:
			
			# vboxwebsrv connectino
			if self.vboxConnType == 'web':
	
				try:
					progress = VirtualBox_wrappers.IProgress(self.client,p)
				except:
					pass
				
				# Recreate vbox interface and close session
				vbox = VirtualBox_wrappers.IVirtualBox(self.vboxMgr, pop['session'])
	
				session = self.vboxMgr.platform.getSessionObject(vbox)
	
				if(session and str(session.state) != 'Unlocked'):
					session.unlockMachine()
	
			# Non-web connection
			else:
				
				pop = self.progressOps.get('get')(p)
				session = pop['session']
				
				self.progressOps.get('delete')(p)

				if session and str(self.vboxType('SessionState',session.state)) != 'Unlocked':
					session.unlockMachine()
					
				
		except Exception, e:
			self.errors.append(
				{'errno':0,
				'error':str(type(e))+": "+str(e),
				'details':traceback.format_exc()
				}
			)				
			
		# Remove progress reference from cache
		self.cache.lock('ProgressOperations')
		inprogress = self.cache.get('ProgressOperations',False)
		if(not inprogress): inprogress = {}
		elif inprogress.get(p): del inprogress[p]
		self.cache.store('ProgressOperations',inprogress)

		return True


	"""
	 * Get enumeration maps
	 """
	def _getEnumerationMap(self,classname, response):
		response['data'] = []
		exec('c = VirtualBox_wrappers.'+classname)
		keys = c._NameMap.keys()
		keys.sort()
		for i in range(len(keys)):
			response['data'].append(str(c._NameMap.get(i)))

	"""
	 * Save system properties
	 """
	def saveSystemProperties(self,args,response):

		# Connect to vboxwebsrv
		self.connect()

		self.vbox.systemProperties.defaultMachineFolder = str(args['SystemProperties[defaultMachineFolder]'])
		self.vbox.systemProperties.VRDEAuthLibrary = str(args['SystemProperties[VRDEAuthLibrary]'])

		self.cache.expire('getSystemProperties')

		response['data']['result'] = 1
		
		return True


	"""
	 * Import appliance
	 """
	def applianceImport(self,args,response):

		# Connect to vboxwebsrv
		self.connect()


		app = self.vbox.createAppliance()
		progress = app.read(str(args['file']))

		# Does an exception exist?
		try:
			if(progress.errorInfo):
				self.errors.append(
					{'errno':0,
					'error':str(progress.errorInfo.text),
					'details':traceback.format_exc()
					}
				)				
				
				return False
			
		except: pass

		progress.waitForCompletion(-1)

		app.interpret()

		a = 0
		for d in list(self.vboxArray(app,'virtualSystemDescriptions')):
			# Replace with passed values
			for b in range(len(args['descriptions['+str(a)+'][0][]'])):
				args['descriptions['+str(a)+'][5][]'][b] = bool(args['descriptions['+str(a)+'][5][]'][b])
			d.setFinalValues(args['descriptions['+str(a)+'][5][]'],args['descriptions['+str(a)+'][3][]'],args['descriptions['+str(a)+'][4][]'])
			a+=1

		
		progress = app.importMachines()

		# Save progress
		pid = self.__storeProgress(progress,'getMediums')
		if not pid: return False

		response['data']['progress'] = pid

		return True


	"""
	 * Get list of VMs available for export
	 """
	def getVMsExportable(self,args,response):

		# Connect to vboxwebsrv
		self.connect()
		
		response['data'] = []
		for machine in self.vboxArray(self.vbox,'machines'):

			response['data'].append({
				'name' : str(machine.name),
				'state' : str(self.vboxType('MachineState',machine.state)),
				'OSTypeId' : str(machine.OSTypeId),
				'id' : str(machine.id),
				'description' : str(machine.description)
			})
			
		return True


	"""
	 * Read and interpret appliance
	 """
	def applianceReadInterpret(self,args,response):

		# Connect to vboxwebsrv
		self.connect()

		app = self.vbox.createAppliance()
		progress = app.read(str(args['file']))

		# Does an exception exist?
		try:
			if(progress.errorInfo):
				self.errors.append(
					{'errno':0,
					'error':str(progress.errorInfo.text),
					'details':traceback.format_exc()
					}
				)								
				return False
		except: pass
		
		progress.waitForCompletion(-1)

		app.interpret()

		response['data']['warnings'] = list(app.getWarnings())
		response['data']['descriptions'] = []
				
		# Each virtual machine (description in interpreted file)
		for d in list(self.vboxArray(app,'virtualSystemDescriptions')):
			
			descItemsOut = []
			descItems = d.getDescription()
			
			# Each list
			for a in range(len(descItems)):

				descSubItemsOut = []
				
				# Cast description types
				if a == 0 and self.vboxConnType != 'web':
					for b in range(len(descItems[0])):
						descSubItemsOut.append(str(self.vboxType('VirtualSystemDescriptionType',int(descItems[0][b]))))
				else:					
					for b in range(len(descItems[a])):
						descSubItemsOut.append(str(descItems[a][b]))
				
				descItemsOut.append(descSubItemsOut)
				
			response['data']['descriptions'].append(descItemsOut)
			
		app=None
		
		response['data']['result'] = 1
		
		return True


	"""
	 * Export an appliance
	 """
	def applianceExport(self,args,response):

		# Connect to vboxwebsrv
		self.connect()

		app = self.vbox.createAppliance()
		
		appProps = {
			'name' : 'Name',
			'description' : 'Description',
			'product' : 'Product',
			'vendor' : 'Vendor',
			'version' : 'Version',
			'product-url' : 'ProductUrl',
			'vendor-url' : 'VendorUrl',
			'license' : 'License'}
		
		# Compile a list of vms
		vms = {}
		for k in args.keys():
			m = re.search('vms\[(.*?)\]',str(k))
			if m:
				vms[str(m.group(1))] = True

		
		# For each VM in list
		for vmk in vms.keys():
			
			# VM Id
			vm = args.get('vms['+str(vmk)+'][id]')
			if not vm: continue
			
			# Get VM
			m = self.vbox.findMachine(str(vm))
			desc = m.export(app)
			descItems = desc.getDescription()
			
			props = []
			for a in range(len(descItems)):
				subProps = []
				for b in range(len(descItems[a])):
					subProps.append(str(descItems[a][b]))
				props.append(subProps)
			
			
			ptypes = []
			for p in props[0]:
				if self.vboxConnType == 'web':
					ptypes.append(str(p))
				else:
					ptypes.append(str(self.vboxType('VirtualSystemDescriptionType',int(p))))
			
			for k,v in appProps.iteritems():
				# Check for existing property
				try:
					idx = ptypes.index(str(v))
					props[3][idx] = str(args.get('vms['+str(vmk)+']['+str(k)+']'))
				except:
					desc.addDescription(self.vboxType('VirtualSystemDescriptionType',v),str(args.get('vms['+str(vmk)+']['+str(k)+']')),'')
					props[3].append(str(args.get('vms['+str(vmk)+']['+str(k)+']')))
					props[4].append('')

			enabled = []
			for i in range(len(props[3])):
				enabled.append(True)
							
			desc.setFinalValues(enabled,props[3],props[4])
			
		if not args.get('format'):
			args['format'] = 'ovf-1.0'
		
		progress = app.write(str(args['format']),1,str(args['file']))

		# Save progress
		pid = self.__storeProgress(progress)
		if not pid: return False

		response['data']['progress'] = pid

		return True

	"""
	 * Get host networking info
	 """
	def getHostNetworkingCached(self,args,response):

		# Connect to vboxwebsrv
		self.connect()

		"""
		 * NICs
		 """
		if type(response['data']) != type(dict()):
			response['data'] = {}
			
		response['data']['networkInterfaces'] = []
		for d in self.vboxArray(self.vbox.host,'networkInterfaces'):
			response['data']['networkInterfaces'].append({
				'name' : str(d.name),
				'interfaceType' : str(self.vboxType('HostNetworkInterfaceType',d.interfaceType)),
			})

		"""
		 * Existing Networks
		 """
		networks = {}
		for machine in self.vboxArray(self.vbox,'machines'):

			for i in range(self.settings['nicMax']):

				try:
					h = machine.getNetworkAdapter(i)
	
					if(bool(h.enabled) and str(h.internalNetwork)):
						networks[str(h.internalNetwork)] = 1
				except:
					break

		response['data']['networks'] = networks.keys()
		return True


	"""
	 * Get host-only networking info
	 """
	def getHostOnlyNetworkingCached(self,args,response):

		# Connect to vboxwebsrv
		self.connect()

		"""
		 * NICs
		 """
		response['data'] = {'networkInterfaces':[]}
		response['data']['networkInterfaces'] = []
		for d in self.vboxArray(self.vbox.host,'networkInterfaces'):

			if(str(self.vboxType('HostNetworkInterfaceType',d.interfaceType)) != 'HostOnly'): continue

			# Get DHCP Info
			try:
				dhcp = self.vbox.findDHCPServerByNetworkName(d.networkName)
			except:
				dhcp = None

			if dhcp :
				dhcp = {
					'enabled' : int(dhcp.enabled),
					'IPAddress' : str(dhcp.IPAddress),
					'networkMask' : str(dhcp.networkMask),
					'networkName' : str(dhcp.networkName),
					'lowerIP' : str(dhcp.lowerIP),
					'upperIP' : str(dhcp.upperIP)
				}
			else:
				dhcp = {}
			
			response['data']['networkInterfaces'].append({
				'id' : str(d.id),
				'IPV6Supported' : int(d.IPV6Supported),
				'name' : str(d.name),
				'IPAddress' : str(d.IPAddress),
				'networkMask' : str(d.networkMask),
				'IPV6Address' : str(d.IPV6Address),
				'IPV6NetworkMaskPrefixLength' : int(d.IPV6NetworkMaskPrefixLength),
				'dhcpEnabled' : int(d.dhcpEnabled),
				'networkName' : str(d.networkName),
				'dhcpServer' : dhcp
			})

		return True


	"""
	 * Save Host-only interface configuration
	 """
	def saveHostOnlyInterfaces(self,args,response):

		# Connect to vboxwebsrv
		self.connect()

		for i in range(50):

			if not args.get('networkInterfaces['+str(i)+'][id]'): break
			
			nicIn = {}
			
			nic = self.vbox.host.findHostNetworkInterfaceById(str(args.get('networkInterfaces['+str(i)+'][id]')))
			for a in ['IPAddress','networkMask','IPV6Address','IPV6NetworkMaskPrefixLength','id','name']:
				try:
					nicIn[a] = str(args.get('networkInterfaces['+str(i)+']['+a+']'))
				except: nicIn[a] = ''
			nicIn['dhcpServer'] = {}
			for a in ['enabled','IPAddress','networkMask','lowerIP','upperIP']:
				try:
					nicIn['dhcpServer'][a] = args.get('networkInterfaces['+str(i)+'][dhcpServer]['+a+']')
				except: nicIn['dhcpServer'][a] = ''
			
			# Common settings
			if(nic.IPAddress != nicIn['IPAddress'] or nic.networkMask != nicIn['networkMask']):
				nic.enableStaticIpConfig(nicIn['IPAddress'],nicIn['networkMask'])
			
			if(nic.IPV6Supported and
				(nic.IPV6Address != nicIn['IPV6Address'] or nic.IPV6NetworkMaskPrefixLength != nicIn['IPV6NetworkMaskPrefixLength'])):
				nic.enableStaticIpConfigV6(nicIn['IPV6Address'],int(nicIn['IPV6NetworkMaskPrefixLength']))

			# Get DHCP Info
			try:
				dhcp = self.vbox.findDHCPServerByNetworkName(nic.networkName)
			except: dhcp = None

			# Create DHCP server?
			if(bool(nicIn['dhcpServer']['enabled']) and not dhcp):
				dhcp = self.vbox.createDHCPServer(nic.networkName)

			if(dhcp):
				dhcp.enabled = bool(nicIn['dhcpServer']['enabled'])
				dhcp.setConfiguration(nicIn['dhcpServer']['IPAddress'],nicIn['dhcpServer']['networkMask'],nicIn['dhcpServer']['lowerIP'],nicIn['dhcpServer']['upperIP'])


		response['data']['result'] = 1
		return True


	"""
	 * Add Host-only interface
	 """
	def createHostOnlyInterface(self,args,response):

		# Connect to vboxwebsrv
		self.connect()

		progress = self.vbox.host.createHostOnlyNetworkInterface()

		if(not (progress and progress[0])): return False
		progress = progress[0]

		# Save progress
		pid = self.__storeProgress(progress)
		if not pid: return False
		
		response['data']['progress'] = pid

		return True



	"""
	 * Remove network interface
	 """
	def removeHostOnlyInterface(self,args,response):

		# Connect to vboxwebsrv
		self.connect()

		progress = self.vbox.host.removeHostOnlyNetworkInterface(str(args['id']))

		if(not progress): return False

		# Save progress
		pid = self.__storeProgress(progress)
		if not pid:
			return False

		response['data']['result'] = 1
		response['data']['progress'] = pid

		return True

	"""
	 * Populate a list of Guest OS types
	 """
	def getGuestOSTypesCached(self,args,response):

		# Connect to vboxwebsrv
		self.connect()

		# get* attr problem
		if self.vboxConnType == 'web':
			osTypes = self.vbox.getGuestOSTypes()
		else:
			osTypes = self.vboxArray(self.vbox, 'GuestOSTypes')
			
		response['data'] = []
		for g in osTypes:

			response['data'].append({
				'familyId' : str(g.familyId),
				'familyDescription' : str(g.familyDescription),
				'id' : str(g.id),
				'description' : str(g.description),
				'is64Bit' : bool(g.is64Bit),
				'recommendedRAM' : str(g.recommendedRAM),
				'recommendedHDD' : (int(g.recommendedHDD) / 1024) / 1024
			})
		return True



	"""
	 * Set VM state
	 *
	 *
	 """
	def __setVMState(self, vm, state, response):


		states = {
			'powerDown' : {'result':'PoweredOff','progress':2},
			'reset' : {'passGetTest':True},
			'saveState' : {'result':'Saved','progress':2},
			'powerButton' : {'acpi':True},
			'sleepButton' : {'acpi':True},
			'pause' : {'result':'Paused','progress':False},
			'resume' : {'result':'Running','progress':False},
			'powerUp' : {'result':'Running'},
			'discardSavedState' : {'result':'poweredOff','lock':'shared','force':True}
		}

		# Check for valid state
		if not states.get(state):
			response['data']['result'] = 0
			raise Exception('Invalid state: ' + state)

		# Connect to vboxwebsrv
		self.connect()

		# Machine state
		machine = self.vbox.findMachine(vm)
		mstate = str(self.vboxType('MachineState',machine.state))

		# If state has an expected result, check
		# that we are not already in it
		if(states[state].get('result')):
			if(mstate == states[state]['result']):
				response['data']['result'] = 0
				raise Exception('Machine is already in requested state.')

		# Special case for power up
		if(state == 'powerUp' and mstate == 'Paused'):
			return self.__setVMState(vm,'resume',response)
		elif(state == 'powerUp'):
			return self.__launchVMProcess(machine,response)

		# Open session to machine
		self.session = self.vboxMgr.platform.getSessionObject(self.vbox)

		# Lock machine
		if states[state].get('lock'): stype = 'Write'
		else: stype = 'Shared'
		
		machine.lockMachine(self.session,self.vboxType('LockType',stype))

		# If this operation returns a progress object save progress
		progress = None
		if(states[state].get('progress')):

			progress = getattr(self.session.console,state)()

			if(not progress):

				# should never get here
				try:
					self.session.unlockMachine()
					self.session = None
				except: pass

				response['data']['result'] = 0
				raise Exception('Unknown error settings machine to requested state.')

			# Save progress
			pid = self.__storeProgress(progress,None)
			if not pid:
				return False
			

			response['data']['progress'] = pid

		# Operation does not return a progress object
		# Just call the function
		else:
		
			if states[state].get('force'):
				getattr(self.session.console,state)(states[state].get('force'))
			else:
				getattr(self.session.console,state)()


		# Check for ACPI button
		if(states[state].get('acpi') and not self.session.console.getPowerButtonHandled()):
			self.session.unlockMachine()
			self.session = None
			raise Exception(trans('ACPI event not handled'))


		if(not progress):
			self.session.unlockMachine()
			self.session=None
		

		response['data']['result'] = 1
		return True


	"""
	 *
	 * This starts a VM
	 *
	 """
	def __launchVMProcess(self, machine, response):

		# Connect to vboxwebsrv
		self.connect()

		# Try opening session for VM
		self.session = self.vboxMgr.platform.getSessionObject(self.vbox)

		# VRDE is not (currently) supported in OSE
		version = self.vboxVersion()
		if(version['ose']): sessionType = 'headless'
		else: sessionType = 'vrdp'

		progress = machine.launchVMProcess(self.session, sessionType, ('' if self.vboxConnType == 'web' else None))


		pid = self.__storeProgress(progress)
		
		if not pid:
			return False

		response['data']['progress'] = pid
		response['data']['result'] = 1
		
		return True


	"""
	 *  Array containing details about the VirtualBox host.
	 """
	def getHostDetailsCached(self,args,response):

		# Connect to vboxwebsrv
		self.connect()

		"""
		 * Generic Host system details
		 """
		host = self.vbox.host
		response['data'] = {
			'id' : 'host',
			'operatingSystem' : str(host.operatingSystem),
			'OSVersion' : str(host.OSVersion),
			'memorySize' : str(host.memorySize),
			'cpus' : [],
			'networkInterfaces' : {},
			'DVDDrives' : {},
			'floppyDrives' : {}
		}

		"""
		 * Processors
		 """
		for i in range(host.processorCount):
			response['data']['cpus'].append(str(host.getProcessorDescription(i)))

		"""
		 * NICs
		 """
		response['data']['networkInterfaces'] = []
		for d in self.vboxArray(host,'networkInterfaces'):
			response['data']['networkInterfaces'].append({
				'name' : str(d.name),
				'IPAddress' : str(d.IPAddress),
				'networkMask' : str(d.networkMask),
				'IPV6Address' : str(d.IPV6Address),
				'IPV6NetworkMaskPrefixLength' : int(d.IPV6NetworkMaskPrefixLength),
				'status' : str(self.vboxType('HostNetworkInterfaceStatus',d.status)),
				'mediumType' : str(self.vboxType('HostNetworkInterfaceMediumType',d.mediumType)),
				'interfaceType' : str(self.vboxType('HostNetworkInterfaceType',d.interfaceType)),
				'hardwareAddress' : str(d.hardwareAddress),
				'networkName' : str(d.networkName),
			})


		"""
		 * Medium types (DVD and Floppy)
		 """
		response['data']['DVDDrives'] = []
		for d in self.vboxArray(host,'DVDDrives'):

			response['data']['DVDDrives'].append({
				'id' : str(d.id),
				'name' : str(d.name),
				'location' : str(d.location),
				'description' : str(d.description),
				'deviceType' : 'DVD',
				'hostDrive' : True,
			})

		response['data']['floppyDrives'] = []
		for d in self.vboxArray(host,'floppyDrives'):

			response['data']['floppyDrives'].append({
				'id' : str(d.id),
				'name' : str(d.name),
				'location' : str(d.location),
				'description' : str(d.description),
				'deviceType' : 'Floppy',
				'hostDrive' : True,
			})

		return True

	
	"""
	 * Get a list of connected USB devices
	 """
	def getHostUSBDevices(self,args,response):

		# Connect to vboxwebsrv
		self.connect()

		response['data'] = []

		for d in self.vboxArray(self.vbox.host,'USBDevices'):
			response['data'].append({
				'id' : str(d.id),
				'vendorId' : str(d.vendorId),
				'productId' : str(d.productId),
				'revision' : str(d.revision),
				'manufacturer' : str(d.manufacturer),
				'product' : str(d.product),
				'serialNumber' : str(d.serialNumber),
				'address' : str(d.address),
				'port' : str(d.port),
				'version' : str(d.version),
				'portVersion' : str(d.portVersion),
				'remote' : str(d.remote),
				'state' : str(d.state),
				})
				
		return True


	"""
	 *
	 *
	 * Return an array containing details of the virtual
	 * machine specified by vm
	 *
	 *
	 """
	def getVMDetails(self,args,response,snapshot=None):

		# Host instead of vm info
		if(args.get('vm') == 'host'):
			return self('getHostDetails',args, response)


		# Connect to vboxwebsrv
		self.connect()

		version = self.vboxVersion()

		# Get registered machine or snapshot machine
		if(snapshot):

			machine = snapshot

		else:

			machine = self.vbox.findMachine(args.get('vm'))

			# For correct caching, always use id
			args['vm'] = str(machine.id)

			# Check for accessibility
			if(not machine.accessible):

				response['data'] = {
					'name' : str(machine.id),
					'state' : 'Inaccessible',
					'OSTypeId' : 'Other',
					'id' : str(machine.id),
					'sessionState' : 'Inaccessible',
					'accessible' : 0,
					'accessError' : {
						# BUG: Bug in API. IVirtualBoxErrorInfo::resultCode is an int in bindings
						# where it should be a long. Can't hold entire resultCode value. 
						#'resultCode' : self.resultcodes.get(str(hex(machine.accessError.resultCode))),
						'resultCode' : 'UNKNOWN',
						'component' : str(machine.accessError.component),
						'text' : str(machine.accessError.text)}
				}

				return True


		# Basic data
		data = self._getCachedMachineData('_getMachine',args.get('vm'),machine,args.get('force_refresh'))

		# Network Adapters
		data['networkAdapters'] = self._getCachedMachineData('_getNetworkAdapters',args.get('vm'),machine,args.get('force_refresh'))

		# Storage Controllers
		data['storageControllers'] = self._getCachedMachineData('_getStorageControllers',args.get('vm'),machine,args.get('force_refresh'))

		# Shared Folders
		data['sharedFolders'] = self._getCachedMachineData('_getSharedFolders',args.get('vm'),machine,args.get('force_refresh'))


		# USB Filters
		#if(not version['ose']):
		data['USBController'] = self._getCachedMachineData('_getUSBController',args.get('vm'),machine,args.get('force_refresh'))


		# Non-cached items when not obtaining
		# snapshot machine info
		if(not snapshot):

			data['state'] = str(self.vboxType('MachineState',machine.state))
			if machine.currentSnapshot:
				data['currentSnapshot'] = {'id':str(machine.currentSnapshot.id),'name':str(machine.currentSnapshot.name)}
			data['snapshotCount'] = int(machine.snapshotCount)
			data['sessionState'] = str(self.vboxType('SessionState',machine.sessionState))
			data['currentStateModified'] = bool(machine.currentStateModified)

			mdlm = (int(machine.lastStateChange)/1000)

			# Get current console port

			if(not version['ose'] and data['state'] == 'Running'):
				console = self.cache.get('__consolePort'+args.get('vm'),False)
				if(console == False or console['lastStateChange'] < mdlm):
					self.session = self.vboxMgr.platform.getSessionObject(self.vbox)
					machine.lockMachine(self.session, self.vboxType('LockType','Shared'))
					data['consolePort'] = int(self.session.console.VRDEServerInfo.port)
					self.session.unlockMachine()
					self.session = None
					console = {
						'consolePort':data['consolePort'],
						'lastStateChange':mdlm
					}
					self.cache.store('__consolePort'+data['id'],console)
				else:
					data['consolePort'] = console['port']


		data['accessible'] = 1
		response['data'] = data

		return True


	"""
	 *
	 * Register a VM from its settings file
	 *
	 """
	def registerVM(self,args,response):

		# Connect to vboxwebsrv
		self.connect()

		vm = self.vbox.openMachine(args['file'])
		self.vbox.registerMachine(vm)

		response['data']['result'] = 1
		
		return True


	"""
	 *
	 * Remove a Virtual Machine
	 *
	 """
	def removeVM(self, args, response):

		# Connect to vboxwebsrv
		self.connect()

		machine = self.vbox.findMachine(args['vm'])

		cache = ['__consolePort'+args['vm'],'_getMachine'+args['vm'],'_getNetworkAdapters'+args['vm'],'_getStorageControllers'+args['vm'],
			'_getSharedFolders'+args['vm'],'_getUSBController'+args['vm'],'getMediums']

		# Only unregister or delete?
		if(args.get('unregister')):

			machine.unregister('Full')

			# Clear caches
			for ex in cache:
				self.cache.expire(ex)
				
			response['data']['result'] = 1
			
			return True

		else:

			hds = []
			delete = machine.unregister(self.vboxType('CleanupMode','DetachAllReturnHardDisksOnly'))
			
			if(args.get('delete')):
				for hd in delete:
					if hd: hds.append(hd)
			else:
				hds = []

			progress = machine.delete(hds)

			pid = self.__storeProgress(progress,cache)
			if not pid:
				return False

			response['data']['progress'] = pid
			response['data']['result'] = 1
			
			return True


	"""
	 *
	 * Create a new Virtual Machine
	 *
	 """
	def createVM(self,args, response):

		# Connect to vboxwebsrv
		self.connect()

		version = self.vboxVersion()

		# create machine
		m = self.vbox.createMachine(args['name'],args['ostype'],'','',False)

		# Set memory
		m.memorySize = int(args['memory'])


		# Save and register
		m.saveSettings()
		self.vbox.registerMachine(m)
		vm = str(m.id)

		try:

			self.session = self.vboxMgr.platform.getSessionObject(self.vbox)

			# Lock VM
			machine = self.vbox.findMachine(vm)
			machine.lockMachine(self.session,self.vboxType('LockType','Write'))

			# OS defaults
			defaults = self.vbox.getGuestOSType(str(args['ostype']))


			# Always set
			self.session.machine.setExtraData('GUI/SaveMountedAtRuntime', 'yes')
			self.session.machine.USBController.enabled = True
			self.session.machine.USBController.enabledEhci = True
			if(not version['ose']):
				self.session.machine.VRDEServer.authTimeout = 5000

			# Other defaults
			self.session.machine.BIOSSettings.IOAPICEnabled = defaults.recommendedIOAPIC
			self.session.machine.setHWVirtExProperty(self.vboxType('HWVirtExPropertyType','Enabled'),int(defaults.recommendedVirtEx))
			self.session.machine.setCPUProperty(self.vboxType('ProcessorFeature','PAE'),int(defaults.recommendedPae))
			self.session.machine.RTCUseUTC = defaults.recommendedRtcUseUtc
			self.session.machine.chipsetType = defaults.recommendedChipset
			self.session.machine.firmwareType = str(defaults.recommendedFirmware)
			if(int(defaults.recommendedVRAM) > 0):
				self.session.machine.VRAMSize = int(defaults.recommendedVRAM)

			"""
			 * Hard Disk and DVD/CD Drive
			 """
			DVDbusType = defaults.recommendedDvdStorageBus
			DVDconType = defaults.recommendedDvdStorageController

			# Attach harddisk?
			if(args['disk']):

				HDbusType = defaults.recommendedHdStorageBus
				HDconType = defaults.recommendedHdStorageController

				sc = self.session.machine.addStorageController(trans(str(self.vboxType('StorageBus',HDbusType))+' Controller'),HDbusType)
				sc.controllerType = HDconType
				sc.useHostIOCache = bool(self.vbox.systemProperties.getDefaultIoCacheSettingForStorageController(HDconType))

				m = self.vbox.findMedium(args['disk'],self.vboxType('DeviceType','HardDisk'))

				self.session.machine.attachDevice(trans(str(self.vboxType('StorageBus',HDbusType))+' Controller'),0,0,self.vboxType('DeviceType','HardDisk'),m)




			# Attach DVD/CDROM
			if(DVDbusType):

				if(not args['disk'] or (str(HDbusType) != str(DVDbusType))):

					sc = self.session.machine.addStorageController(trans(str(self.vboxType('StorageBus',DVDbusType))+' Controller'),DVDbusType)
					sc.controllerType = DVDconType
					sc.useHostIOCache = bool(self.vbox.systemProperties.getDefaultIoCacheSettingForStorageController(DVDconType))

				self.session.machine.attachDevice(trans(str(self.vboxType('StorageBus',DVDbusType))+' Controller'),1,0,self.vboxType('DeviceType','DVD'),('' if self.vboxConnType == 'web' else None))


			self.session.machine.saveSettings()
			self.session.unlockMachine()
			self.session = None

			if(args['disk']): self.cache.expire('getMediums')

		except Exception, e:
			self.errors.append(
				{'errno':0,
				'error':str(type(e))+": "+str(e),
				'details':traceback.format_exc()
				}
			)				
			return False

		response['data']['result'] = 1
		
		return True


	"""
	 *
	 * Return a list of guest attached network adapters
	 *
	 """
	def _getNetworkAdapters(self,m):

		adapters = []

		for i in range(self.settings['nicMax']):
			n = m.getNetworkAdapter(i)
			adapters.append(self._getNetworkAdapter(n))

		return adapters


	"""
	 *
	 *
	 * Return a list of VMs along with their
	 *
	 * states and basic info
	 *
	 """
	def getVMsCached(self,args,response):

		# Connect to vboxwebsrv
		self.connect()

		# Get a list of registered machines
		#machines = self.vbox.machines
		machines = self.vboxArray(self.vbox,'machines')
		
		response['data'] = []

		for machine in machines:

			try:
				if machine.currentSnapshot:
					sname = str(machine.currentSnapshot.name)
				else:
					sname = ''

				response['data'].append({
					'name' : str(machine.name),
					'state' : str(self.vboxType('MachineState',machine.state)),
					'OSTypeId' : str(machine.OSTypeId),
					'id' : str(machine.id),
					'lastStateChange' : int(machine.lastStateChange),
					'sessionState' : str(self.vboxType('SessionState',machine.sessionState)),
					'currentSnapshot' : sname
				})

			except Exception, e:


				if(machine):

					response['data'].append({
						'name' : str(machine.id),
						'state' : 'Inaccessible',
						'OSTypeId' : 'Other',
						'id' : str(machine.id),
						'sessionState' : 'Inaccessible',
						'lastStateChange' : 0,
						'currentSnapshot' : ''
					})
					
				if(machine and machine.accessible):
					self.errors.append(
						{'errno':0,
						'error':str(type(e))+": "+str(e),
						'details':traceback.format_exc()
						}
					)
				
		
	
		if(not response['data'] or not len(response['data'])):
			response['data'] = {'empty':1}
			
		return True


	"""
	 * Debug input array
	 *
	 """
	def debugInput(self,args,response):
		self.errors.append(
				{'errno':0,
				'error':"debugInput",
				'details':str(args)
				}
			)				
		response['data']['result'] = 1
		return True

	"""
	 *
	 *
	 * Get all mediums registered with this vbox installation
	 *
	 *
	 """
	def getMediumsCached(self,args,response):

		# Connect to vboxwebsrv
		self.connect()
		
		response['data'] = []
		mds = [self.vboxArray(self.vbox,'hardDisks'),self.vboxArray(self.vbox,'DVDImages'),self.vboxArray(self.vbox,'floppyImages')]
		for i in range(2):
			for m in mds[i]:
				response['data'].append(self._getMedium(m))
				
		return True


	"""
	 *
	 * Fill network adapter info
	 *
	 """
	def _getNetworkAdapter(self,n):

		redirects = []
		if str(self.vboxType('NetworkAttachmentType',n.attachmentType)) == 'NAT':
			r = list(self.vboxArray(n.natDriver,'redirects'))
			for i in range(len(r)):
				redirects.append(str(r[i]))
			
		return {
			'adapterType' : str(self.vboxType('NetworkAdapterType',n.adapterType)),
			'slot' : str(n.slot),
			'enabled' : int(n.enabled),
			'MACAddress' : str(n.MACAddress),
			'attachmentType' : str(self.vboxType('NetworkAttachmentType',n.attachmentType)),
			'hostInterface' : str(n.hostInterface),
			'internalNetwork' : str(n.internalNetwork),
			'NATNetwork' : str(n.NATNetwork),
			'cableConnected' : int(n.cableConnected),
			'redirects' : redirects
			}

	"""
	 *
	 * Fill USB Controller data
	 *
	 """
	def _getUSBController(self,m):

		deviceFilters = []
		for df in self.vboxArray(m.USBController,'deviceFilters'):
			deviceFilters.append({
				'name' : str(df.name),
				'active' : int(df.active),
				'vendorId' : str(df.vendorId),
				'productId' : str(df.productId),
				'revision' : str(df.revision),
				'manufacturer' : str(df.manufacturer),
				'product' : str(df.product),
				'serialNumber' : str(df.serialNumber),
				'port' : str(df.port),
				'remote' : str(df.remote)
			})

		return {
			'enabled' : int(m.USBController.enabled),
			'enabledEhci' : int(m.USBController.enabledEhci),
			'deviceFilters' : deviceFilters
			}

	"""
	 *
	 *
	 * Fill Machine data
	 *
	 """
	def _getMachine(self, m):

		version = self.vboxVersion()
		
		if(version['ose']): VRDEServer = None
		else:
			VRDEServer = {
				'enabled' : bool(m.VRDEServer.enabled),
				'ports' : str(m.VRDEServer.getVRDEProperty('TCP/Ports')),
				'netAddress' : str(m.VRDEServer.getVRDEProperty("TCP/Address")),
				'authType' : str(m.VRDEServer.authType),
				'authTimeout' : int(m.VRDEServer.authTimeout),
				'allowMultiConnection' : int(m.VRDEServer.allowMultiConnection)
			}

		return {
			'name' : str(m.name),
			'description' : str(m.description),
			'id' : str(m.id),
			'OSTypeId' : str(m.OSTypeId),
			'CPUCount' : int(m.CPUCount),
			'memorySize' : str(m.memorySize),
			'VRAMSize' : str(m.VRAMSize),
			'accelerate3DEnabled' : bool(m.accelerate3DEnabled),
			'accelerate2DVideoEnabled' : bool(m.accelerate2DVideoEnabled),
			'BIOSSettings' : {
				'ACPIEnabled' : bool(m.BIOSSettings.ACPIEnabled),
				'IOAPICEnabled' : bool(m.BIOSSettings.IOAPICEnabled)
				},
			'firmwareType' : str(self.vboxType('FirmwareType',m.firmwareType)),
			'snapshotFolder' : str(m.snapshotFolder),
			'monitorCount' : int(m.monitorCount),
			'VRDEServer' : VRDEServer,
			'audioAdapter' : {
				'enabled' : bool(m.audioAdapter.enabled),
				'audioController' : str(self.vboxType('AudioControllerType',m.audioAdapter.audioController)),
				'audioDriver' : str(self.vboxType('AudioDriverType',m.audioAdapter.audioDriver)),
				},
			'RTCUseUTC' : bool(m.RTCUseUTC),
			'HWVirtExProperties' : {
				'Enabled' : int(m.getHWVirtExProperty(self.vboxType('HWVirtExPropertyType','Enabled'))),
				'NestedPaging' : int(m.getHWVirtExProperty(self.vboxType('HWVirtExPropertyType','NestedPaging')))
				},
			'CpuProperties' : {
				'PAE' : int(m.getCPUProperty(self.vboxType('ProcessorFeature','PAE')))
				},
			'bootOrder' : self._getBootOrder(m),
			'GUI' : {'SaveMountedAtRuntime' : str(m.getExtraData('GUI/SaveMountedAtRuntime'))},

		}
		
		
	"""
	 *
	 * Fill boot order
	 *
	 """
	def _getBootOrder(self,m):
		returnval = []
		mbp = self.vbox.systemProperties.maxBootPosition
		for i in range(self.vbox.systemProperties.maxBootPosition):
			b = str(self.vboxType('DeviceType',m.getBootOrder(i + 1)))
			if(b == 'Null'): continue
			returnval.append(b)
		return returnval

	
	"""
	 *
	 * Fill shared folders
	 *
	 """
	def _getSharedFolders(self,m):
		returnval = []
		for sf in self.vboxArray(m,'sharedFolders'):
			returnval.append({
				'name' : str(sf.name),
				'hostPath' : str(sf.hostPath),
				'accessible' : bool(sf.accessible),
				'writable' : bool(sf.writable),
				'autoMount' : bool(sf.autoMount),
				'lastAccessError' : str(sf.lastAccessError)
			})
		return returnval

	"""
	 *
	 * Fill medium attachments
	 *
	 """
	def _getMediumAttachments(self,mas,mid=None):

		returnval = []

		for ma in mas:
			
			if(ma.medium): m = {'id':str(ma.medium.id)}
			else: m = None
			
			returnval.append({
				'medium' : m,
				'controller' : str(ma.controller),
				'port' : int(ma.port),
				'device' : int(ma.device),
				'type' : str(self.vboxType('DeviceType',ma.type)),
				'passthrough' : bool(ma.passthrough)
			})
			
		return returnval


	"""
	 * Save snapshot name and description
	 """
	def saveSnapshot(self,args,response):

		# Connect to vboxwebsrv
		self.connect()

		vm = self.vbox.findMachine(args['vm'])

		snapshot = vm.findSnapshot(args['snapshot'])
		snapshot.name = str(args['name'])
		snapshot.description = str(args['description'])

		response['data']['result'] = 1
		return True


	"""
	 * Return full snapshot details
	 """
	def getSnapshotDetails(self,args,response):

		# Connect to vboxwebsrv
		self.connect()

		vm = self.vbox.findMachine(args['vm'])
		snapshot = vm.findSnapshot(args['snapshot'])
		machine = {}
		self.getVMDetails({},machine,snapshot.machine)

		response['data'] = self._getSnapshot(snapshot,False)
		response['data']['machine'] = machine['data']

		response['data']['result'] = 1
		
		return True


	"""
	 * Restore snapshot of machine
	 """
	def snapshotRestore(self, args, response):

		# Connect to vboxwebsrv
		self.connect()

		progress = self.session = None

		try:

			# Open session to machine
			self.session = self.vboxMgr.platform.getSessionObject(self.vbox)

			machine = self.vbox.findMachine(args['vm'])
			machine.lockMachine(self.session,self.vboxType('LockType','Write'))

			snapshot = self.session.machine.findSnapshot(str(args['snapshot']))

			progress = self.session.console.restoreSnapshot(snapshot)
			
			
			pid = self.__storeProgress(progress,['_getMachine'+args['vm'],'getMediums','_getStorageControllers'+args['vm']])
			if not pid:
				return False

		except Exception, e:

			self.errors.append(
				{'errno':0,
				'error':str(type(e))+": "+str(e),
				'details':traceback.format_exc()
				}
			)				

			if(self.session):
				try:
					self.session.unlockMachine()
				except:
					pass
			response['data']['result'] = 0
			return False

		response['data']['progress'] = pid
		response['data']['result'] = 1
		
		return True


	"""
	 * Delete snapshot of machine
	 """
	def snapshotDelete(self,args, response):

		# Connect to vboxwebsrv
		self.connect()

		progress = self.session = None

		try:

			# Open session to machine
			self.session = self.vboxMgr.platform.getSessionObject(self.vbox)

			machine = self.vbox.findMachine(args['vm'])
			machine.lockMachine(self.session, self.vboxType('LockType','Write'))

			progress = self.session.console.deleteSnapshot(args['snapshot'])

			pid = self.__storeProgress(progress,['_getMachine'+args['vm'],'getMediums','_getStorageControllers'+args['vm']])
			if not pid:
				return False


		except Exception, e:

			self.errors.append(
				{'errno':0,
				'error':str(type(e))+": "+str(e),
				'details':traceback.format_exc()
				}
			)				

			if(self.session):
				try:
					self.session.unlockMachine()
					self.session=None
				except: pass

			response['data']['result'] = 0
			return False

		response['data']['progress'] = pid
		response['data']['result'] = 1
		
		return True


	"""
	 * Take snapshot of machine
	 """
	def snapshotTake(self, args, response):

		# Connect to vboxwebsrv
		self.connect()

		machine = self.vbox.findMachine(args['vm'])

		progress = self.session = None

		try:

			# Open session to machine
			self.session = self.vboxMgr.platform.getSessionObject(self.vbox)
			if str(self.vboxType('SessionState',machine.sessionState)) == 'Unlocked':
				stype = 'Write'
			else:
				stype = 'Shared'
			machine.lockMachine(self.session, self.vboxType('LockType',stype))

			progress = self.session.console.takeSnapshot(args['name'],args['description'])

			pid = self.__storeProgress(progress,['_getMachine'+args['vm'],'getMediums','_getStorageControllers'+args['vm']])
			if not pid:				
				try:
					self.session.unlockMachine()
					self.session=None
				except: pass
				return False
			
		except Exception, e:

			self.errors.append(
				{'errno':0,
				'error':str(type(e))+": "+str(e),
				'details':traceback.format_exc()
				}
			)				

			#response['data']['error'][] = e.getMessage()
			response['data']['progress'] = pid
			response['data']['result'] = 0

			if(not progress and self.session):
				try:
					self.session.unlockMachine()
					self.session=None
				except: pass

			return False

		response['data']['progress'] = pid
		response['data']['result'] = 1
		
		return True


	"""
	 * Return a list of Snapshots for machine
	 """
	def getSnapshots(self,args, response):

		# Connect to vboxwebsrv
		self.connect()

		machine = self.vbox.findMachine(args['vm'])

		""" No snapshots? Empty array """
		if(int(machine.snapshotCount) < 1):
			response['data'] = []
		else:
			s = machine.findSnapshot(('' if self.vboxConnType == 'web' else None))
			response['data'] = self._getSnapshot(s,True)
		
		return True


	"""
	 *
	 * Fill snapshot info
	 *
	 """
	def _getSnapshot(self,s,sninfo=False):

		children = []

		if(sninfo):
			for c in self.vboxArray(s,'children'):
				children.append(self._getSnapshot(c, True))

		timestamp = int(int(s.timeStamp)/1000)

		resp = {
			'id' : str(s.id),
			'name' : str(s.name),
			'description' : str(s.description),
			'timeStamp' : timestamp,
			'timeStampSplit' : self.__splitTime(int(time.time()) - timestamp),
			'online' : bool(s.online),
			'machine' : (str(s.machine.id) if sninfo else None)
		}
		
		if sninfo:
			resp.update({'children' : children})
		
		return resp

	"""
	 *
	 * Fill Storage Controllers
	 *
	 """
	def _getStorageControllers(self,m):

		sc = []

		for c in self.vboxArray(m,'storageControllers'):
			sc.append({
				'name' : str(c.name),
				'maxDevicesPerPortCount' : int(c.maxDevicesPerPortCount),
				'useHostIOCache' : bool(c.useHostIOCache),
				'minPortCount' : int(c.minPortCount),
				'maxPortCount' : int(c.maxPortCount),
				'instance' : str(c.instance),
				'portCount' : int(c.portCount),
				'bus' : str(self.vboxType('StorageBus',c.bus)),
				'controllerType' : str(self.vboxType('StorageControllerType',c.controllerType)),
				'mediumAttachments' : self._getMediumAttachments(m.getMediumAttachmentsOfController(c.name), str(m.id))
			})
		return sc

	"""
	 * Clone a medium
	 """
	def mediumCloneTo(self,args,response):

		# Connect to vboxwebsrv
		self.connect()

		
		format = re.sub('.*\.','',args['file'].upper())
		if(format != 'VDI' and format != 'VMDK'):
			format = 'VDI'
		target = self.vbox.createHardDisk(format,args['file'])

		src = self.vbox.findMedium(args['id'],self.vboxType('DeviceType','HardDisk'))

		if args['type'] == 'fixed': type = 'Fixed'
		else: args['type'] = 'Standard'
		type = self.vboxType('MediumVariant', args['type'])

		progress = src.cloneTo(target,type,('' if self.vboxConnType == 'web' else None))

		pid = self.__storeProgress(progress,'getMediums')
		if not pid:
			return False

		response['data'] = {'progress' : pid}

		return True


	"""
	 * Make a medium immutable
	 """
	def mediumSetType(self,args,response):

		# Connect to vboxwebsrv
		self.connect()

		m = self.vbox.findMedium(args['id'],self.vboxType('DeviceType','HardDisk'))
		m.type = self.vboxTypeSet('MediumType',args['type'])

		self.cache.expire('getMediums')

		response['data'] = {'result' : 1,'id' : args['id']}

		return True


	"""
	 * Add existing medium
	 """
	def mediumAdd(self,args,response):

		# Connect to vboxwebsrv
		self.connect()

		m = self.vbox.openMedium(args['path'],self.vboxType('DeviceType',args['type']),self.vboxType('AccessMode','ReadWrite'))

		self.cache.expire('getMediums')
		response['data']['result'] = 1
		
		return True


	"""
	 * Create base storage medium
	 """
	def mediumCreateBaseStorage(self,args,response):

		# Connect to vboxwebsrv
		self.connect()

		format = re.sub('.*\.','',args['file'].upper())
		if(format != 'VDI' and format != 'VMDK'): format = 'VDI'
		hd = self.vbox.createHardDisk(format,args['file'])

		if args.get('type') == 'fixed': variant = 'Fixed'
		else: variant = 'Standard'

		progress = hd.createBaseStorage(int(args.get('size')),self.vboxType('MediumVariant',variant))

		pid = self.__storeProgress(progress,'getMediums')
		if not pid:
			return False

		response['data'] = {'progress' : pid,'id' : hd.id}

		return True


	"""
	 * Release medium from all attachments
	 """
	def mediumRelease(self,args,response):

		# Connect to vboxwebsrv
		self.connect()

		m = self.vbox.findMedium(args['id'],self.vboxType('DeviceType',args['type']))

		# connected to...
		for uuid in self.vboxArray(m,'machineIds'):

			# Find medium attachment
			try:
				mach = self.vbox.findMachine(uuid)
			except:
				# TODO: error message indicating machine no longer exists?
				continue
			
			remove = []
			for a in self.vboxArray(mach,'mediumAttachments'):
				if(a.medium and a.medium.id == args['id']):
					remove.append({
						'controller' : a.controller,
						'port' : a.port,
						'device' : a.device
					})
					break

			# save state
			state = str(self.vboxType('SessionState',mach.sessionState))

			if(not len(remove)): continue

			# create session
			self.session = self.vboxMgr.platform.getSessionObject(self.vbox)

			# Hard disk requires machine to be stopped
			if(args['type'] == 'HardDisk' or state == 'Unlocked'):
				mach.lockMachine(self.session, self.vboxType('LockType','Write'))
			else:
				mach.lockMachine(self.session, self.vboxType('LockType','Shared'))


			for r in remove:
				if(args['type'] == 'HardDisk'):
					self.session.machine.detachDevice(r['controller'],int(r['port']),int(r['device']))
				else:
					self.session.machine.mountMedium(r['controller'],int(r['port']),int(r['device']),('' if self.vboxConnType == 'web' else None),True)
				

			self.session.machine.saveSettings()
			self.session.unlockMachine()

			self.cache.expire('_getStorageControllers'+str(uuid))

		self.cache.expire('getMediums')

		response['data']['result'] = 1
		
		return True


	"""
	 * Remove medium
	 """
	def mediumRemove(self,args,response):

		# Connect to vboxwebsrv
		self.connect()

		if(not args.get('type')): args['type'] = 'HardDisk'
		m = self.vbox.findMedium(args['id'],self.vboxType('DeviceType',args['type']))

		if(args.get('delete') and self.settings.get('deleteOnRemove') and str(self.vboxType('DeviceType',m.deviceType)) == 'HardDisk'):

			progress = m.deleteStorage()

			pid = self.__storeProgress(progress,'getMediums')
			if not pid:
				return False
			
			response['data']['progress'] = pid

		else:
			m.close()
			self.cache.expire('getMediums')
		
		response['data']['result'] = 1
		
		return True
	

	"""
	 * Mount a medium on a given medium attachment (port/device)
	 """
	def mediumMount(self,args,response,save=False):

		# Connect to vboxwebsrv
		self.connect()

		# Find medium attachment
		machine = self.vbox.findMachine(args['vm'])
		state = str(self.vboxType('SessionState',machine.sessionState))
		save = (save or machine.getExtraData('GUI/SaveMountedAtRuntime'))

		# create session
		self.session = self.vboxMgr.platform.getSessionObject(self.vbox)

		if(state == 'Unlocked'):
			machine.lockMachine(self.session,self.vboxType('LockType','Write'))
			save = True # force save on closed session as it is not a "run-time" change
		else:
			machine.lockMachine(self.session, self.vboxType('LockType','Shared'))

		self.session.machine.mountMedium(args['controller'],int(args['port']),int(args['device']),args['medium'],True)

		if(save): self.session.machine.saveSettings()

		self.session.unlockMachine()

		self.cache.expire('getMediums')
		self.cache.expire('_getStorageControllers'+args['vm'])

		response['data']['result'] = 1
		
		return True


	"""
	 *
	 *  Fill medium data
	 *
	 """
	def _getMedium(self,m):

		children = []
		attachedTo = []
		machines = self.vboxArray(m,'machineIds')
		hasSnapshots = 0

		for c in self.vboxArray(m,'children'):
			children.append(self._getMedium(c))

		if not machines: machines = []
		
		for mid in machines:
			
			sids = m.getSnapshotIds(mid)
						
			mid = self.vbox.findMachine(mid)
			
			c = len(sids)
			
			hasSnapshots = max(hasSnapshots,c)
			snapshots = []
			for i in range(c):
				if str(mid.id) != str(sids[i]):
					snapshots.append(str(mid.findSnapshot(str(sids[i])).name))

			if(len(snapshots)): hasSnapshots = 1
			else: hasSnapshots = 0

			attachedTo.append({'machine':str(mid.name),'snapshots':snapshots})

		m.refreshState()
		return {
				'id' : str(m.id),
				'description' : str(m.description),
				'state' : str(self.vboxType('MediumState',m.state)),
				'location' : str(m.location),
				'name' : str(m.name),
				'deviceType' : str(self.vboxType('DeviceType',m.deviceType)),
				'hostDrive' : bool(m.hostDrive),
				'size' : str(m.size),
				'format' : str(m.format),
				'type' : str(self.vboxType('MediumType',m.type)),
				'parent' : str(m.parent.id) if (str(self.vboxType('DeviceType',m.deviceType)) and m.parent) else None,
				'children' : children,
				'base' : str(m.base.id) if(str(self.vboxType('DeviceType',m.deviceType)) and m.base) else None,
				'readOnly' : bool(m.readOnly),
				'logicalSize' : str((int(m.logicalSize) / 1024) / 1024),
				'autoReset' : bool(m.autoReset),
				'hasSnapshots' : bool(hasSnapshots),
				'lastAccessError' : str(m.lastAccessError),
				'machineIds' : [],
				'attachedTo' : attachedTo
			}


	"""
	 * Store a progress operation for later use
	 """
	def __storeProgress(self,progress,expire=None):
		
		# Does an exception exist?
		try:
			if progress.errorInfo:
				self.errors.append(
					{'errno':0,
					'error':str(progress.errorInfo.text),
					'details':traceback.format_exc()
					}
				)
				return False

		except: pass

		""" Store progress operation """
		self.cache.lock('ProgressOperations')
		inprogress = self.cache.get('ProgressOperations',False)
		if type(inprogress) != type(dict()):
			inprogress = {}
		if expire and (not type(expire) == type(list())):
			expire = [expire]

		# If progress is unaccessible, let getProgress()
		# handle it. Try / catch used and errors ignored.
		try: cancelable = progress.cancelable
		except: pass

		""" Generate interface ids """
		if self.vboxConnType == 'web':
			progressid = str(progress)
			vboxid = str(self.vbox)
		else:
			progressid = self.progressOps['store'](progress,self.session)
			vboxid = '' # Unused in non-web connections
			
		inprogress[str(progressid)] = {
			'session':vboxid,
			'progress':progressid,
			'cancelable':bool(cancelable),
			'expire': expire,
			'started': int(time.time())
		}

		self.cache.store('ProgressOperations',inprogress)

		""" Do not destroy login session / reference to progress operation """
		self.progressCreated = True

		return progressid


	"""
	 *
	 * Get information about this vbox installation
	 *
	 """
	def getSystemPropertiesCached(self,args,response):

		# Connect to vboxwebsrv
		self.connect()

		response['data'] = {
			'minGuestRAM' : str(self.vbox.systemProperties.minGuestRAM),
			'maxGuestRAM' : str(self.vbox.systemProperties.maxGuestRAM),
			'minGuestVRAM' : str(self.vbox.systemProperties.minGuestVRAM),
			'maxGuestVRAM' : str(self.vbox.systemProperties.maxGuestVRAM),
			'minGuestCPUCount' : str(self.vbox.systemProperties.minGuestCPUCount),
			'maxGuestCPUCount' : str(self.vbox.systemProperties.maxGuestCPUCount),
			'infoVDSize' : str(self.vbox.systemProperties.infoVDSize),
			'networkAdapterCount' : int(self.vbox.systemProperties.networkAdapterCount),
			'maxBootPosition' : str(self.vbox.systemProperties.maxBootPosition),
			'defaultMachineFolder' : str(self.vbox.systemProperties.defaultMachineFolder),
			'homeFolder' : str(self.vbox.homeFolder),
			'defaultHardDiskFormat' : str(self.vbox.systemProperties.defaultHardDiskFormat),
			'VRDEAuthLibrary' : str(self.vbox.systemProperties.VRDEAuthLibrary),
			'defaultAudioDriver' : str(self.vbox.systemProperties.defaultAudioDriver),
			'maxGuestMonitors' : str(self.vbox.systemProperties.maxGuestMonitors)
		}
		return True


	"""
	 *
	 * Return vm log names
	 *
	 """
	def getVMLogFileNames(self,args,response):

		# Connect to vboxwebsrv
		self.connect()

		m = self.vbox.findMachine(args['vm'])
		logs = []
		i = 0
		l = 'True'
		while(str(l)):
			l = m.queryLogFilename(i)
			if not str(l): break
			logs.append(str(l))
			i+=1
			
		response['data'] = logs
		
		return True


	"""
	 *
	 * Return vm log contents
	 *
	 """
	def getVMLogFile(self,args,response):

		# Connect to vboxwebsrv
		self.connect()

		m = self.vbox.findMachine(args['vm'])
		
		try:
			o = 0
			s = 8192 * 2# 16k chunks
			response['data']['log'] = ''
			while True:
				l = m.readLog(int(args['log']),o,s)
				if len(l) == 0: break
				response['data']['log'] += (''.join(map(chr,l)) if self.vboxConnType == 'web' else l)
				o+=len(l)
			
		except: pass
		
		return True


	"""
	 *
	 * Format a time
	 *
	 """
	def __splitTime(self,t):

		spans = [
			{'days' : 86400},
			{'hours' : 3600},
			{'minutes' : 60},
			{'seconds' : 1}
		]

		time = {}
		for i in range(len(spans)):
			k,v = spans[i].popitem()
			if(not int(math.floor(t / v)) > 0): continue
			time[k] = int(math.floor(t / v))
			t -= math.floor(time[k] * v)
		

		return time
	


