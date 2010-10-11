
class VBoxWebConfig:

	# See languages folder for more language options
	language = 'en_us'

	"""
	
		vboxwebsrv style config. Only use if you are
		connecting to VirtualBox through vboxwebsrv.
		
	"""
	
	""" Single vboxwebsrv server example. """
	# Username / password for system user that runs VirutalBox 
	location = 'http://127.0.0.1:18083/'
	username = 'vbox'
	password = 'pass'

	""" Multiple vboxwebsrv server example. """
	"""
	servers = [
		{
			name : 'London',
			username: 'user1',
			password: 'password1',
			location: 'http://192.168.0.1:18083'
		},
		{
			name : 'New York',
			username: 'user2',
			password: 'password2',
			location: 'http://192.168.33.1:18083'
		},		
	]
	"""
	
	# Default host/ip to use for console
	#consoleHost = '192.168.1.40'
	
	# Disable "preview" box
	#noPreview = True
	
	# Default preview box update interval in seconds
	#previewUpdateInterval = 30
	
	# Preview box pixel width
	previewWidth = 180
	
	"""
	Allow to prompt deletion harddisk files on removal from Virtual Media Manager.
	If this is not set, files are always kept. If this is set, you will be PROMPTED
	to decide whether or not you would like to delete the harddisk file(s) when you
	remove a harddisk from virtual media manager. You may still choose not to delete
	the file when prompted.
	"""
	deleteOnRemove = True
	
	"""
	 * File / Folder browser settings
	 """
	
	# Restrict file types
	browserRestrictFiles = '.iso,.vdi,.vmdk,.img,.bin,.vhd,.hdd,.ovf,.ova'
	
	# Restrict locations / folders
	#browserRestrictFolders = 'D:\\,C:\\Users\\Ian' # Or something like '/home/vbox,/var/ISOs'
	
	# Force use of local, webserver based file browser instead of going through vboxwebsrv
	#browserLocal = True
	
	# Disable file / folder browser.
	#browserDisable = True
	
	"""
	 * Misc
	"""
	
	""" Disable any of VirtualBox Web Console's main tabs """
	#disableTabVMSnapshots = True # Snapshots tab
	#disableTabVMConsole = True # Console tab
	
	""" Screen resolutions for console tab """
	consoleResolutions = '640x480,800x600,1024x768'
	
	""" Max number of network cards per VM. Do not set above VirtualBox's limit (typically 8) or below 1 """
	nicMax = 4
	
	""" Enable Acceleration configuration (normally hidden in the VirtualBox GUI) """
	enableAccelerationConfig = True
	
	""" Custom VMList sort function in JavaScript """
	""" This places running VMs at the top of the list"""
	"""
	vmListSort = 'function(a,b) {\
		if(a.state == "Running" && b.state != "Running") return -1\
		if(b.state == "Running" && a.state != "Running") return 1\
		return strnatcasecmp(a.name,b.name)\
	}'
	"""
	
	
	"""
	 * Cache tweeking.
	 *
	 * Not a good idea to set any of these unless asked to do so.
	 """
	#cachePath = '/tmp'
	
	"""
	 * Cache timings
	
	cacheExpireMultiplier = 1
	cacheSettings = {
			'getHostDetails' : 86400, # "never" changes
			'getGuestOSTypes' : 86400,
			'getSystemProperties' : 86400,
			'getInternalNetworks' : 86400,
			'getMediums' : 600,
			'getVMs' : 3,
			'__getMachine' : 7200,
			'__getNetworkAdapters' : 7200,
			'__getStorageControllers' : 7200,
			'__getSharedFolders' : 7200,
			'__getUSBController' : 7200,
	}
	"""
	
	
"""
	Web Server (cherry.py) Config
"""
WebServerConfig = {
	
	'server.socket_host' : "0.0.0.0",
	'server.socket_port' : 8080,
	'server.thread_pool' : 10,
	'server.environment' : "production",  # development

	'tools.encode.on' : True,
	'tools.encode.encoding' : "utf-8",

	'tools.response_headers.on' : True,

	'tools.sessions.on' : True,
	'tools.sessions.timeout' : 60,
	'tools.sessions.storage_type' : "file",
	
	'tools.gzip.on' : True,
	'tools.gzip.compress_level' : 9,
	'tools.gzip.mime_types' : "['text/html', 'text/xml', 'text/css', 'text/javascript', 'application/x-javascript', 'application/x-shockwave-flash']",

	'tools.decode.on' : True,

	'tools.trailing_slash.on' : True,
	'tools.log_headers.on' : False,

	'log.error_file' : "VBoxWeb.log",
	'log.screen' : False,

}