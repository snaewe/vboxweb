#!/usr/bin/env python
#
# Copyright (C) 2009 Sun Microsystems, Inc.

# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:

# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

import cherrypy
import os
import socket
import sys
import urllib
import hashlib

if sys.version_info < (2, 6):
    import simplejson
    isSimpleJson = True
else:
    import json
    isSimpleJson = False

from cherrypy.lib.static import serve_file

if sys.platform == 'win32':
    import pythoncom

# VirtualBox API
import vboxapi

# VBoxWeb modules
sys.path.insert(0,'modules')
import vboxRDPWeb

SESSION_KEY = '_cp_username'

def require(*conditions):
    """A decorator that appends conditions to the auth.require config
    variable."""
    def decorate(f):
        if not hasattr(f, '_cp_config'):
            f._cp_config = dict()
        if 'auth.require' not in f._cp_config:
            f._cp_config['auth.require'] = []
        f._cp_config['auth.require'].extend(conditions)
        return f
    return decorate

def convertObjToJSON(obj):
    # print 'default(', repr(obj), ')'
    # Convert objects to a dictionary of their representation
    d = { '__class__':obj.__class__.__name__}
    d.update(obj.__dict__)
    return d

if isSimpleJson:
    class ConvertObjToJSONClass(simplejson.JSONEncoder):
        def default(self, obj):
            return convertObjToJSON(obj)

#
# @todo write autowrapper for attributes main-like classes below.
#       Currently this involves too much copying around.
#
class jsHeader:
    def __init__(self, ctx, arrMach, type, statusMessage = ""):
        self.magic = "jsVBxWb"
        self.ver = 1

        self.username = cherrypy.request.login
        self.sessionID = cherrypy.session.id
        self.numMach = len(arrMach)
        self.updateType = type
        self.statusMessage = statusMessage

class jsVirtualBox:
    def __init__(self, ctx):
        arrOSTypes = ctx['global'].getArray(ctx['vb'], 'guestOSTypes')
        self.arrGuestOSTypes = []
        for type in arrOSTypes:
            self.arrGuestOSTypes.append(jsGuestOSType(type))
        self.numGuestOSTypes = len(self.arrGuestOSTypes)

class jsVRDPServer:
    def __init__(self, ctx, vrdp):
        self.enabled = vrdp.enabled
        self.port = vrdp.port

        self.netAddress = vrdp.netAddress
        if not self.netAddress:
            self.netAddress = ctx['serverAdr']

        self.authType = vrdp.authType
        self.allowMultiConnection = vrdp.allowMultiConnection
        self.reuseSingleConnection = vrdp.reuseSingleConnection

class jsGuestOSType:
    def __init__(self, guestOSType):
        self.familyId = guestOSType.familyId
        self.familyDescription = guestOSType.familyDescription
        self.id = guestOSType.id
        self.description = guestOSType.description
        self.is64Bit = guestOSType.is64Bit
        self.recommendedIOAPIC = guestOSType.recommendedIOAPIC
        self.recommendedVirtEx = guestOSType.recommendedVirtEx
        self.recommendedRAM = guestOSType.recommendedRAM
        self.recommendedVRAM = guestOSType.recommendedVRAM
        self.recommendedHDD = guestOSType.recommendedHDD

class jsHardDiskAttachment:
    def __init__(self, attachment):
        self.hardDisk = jsHardDisk(attachment.hardDisk)
        self.controller = attachment.controller
        self.port = attachment.port
        self.device = attachment.device

class jsHardDisk:
    def __init__(self, hardDisk):
        self.id = hardDisk.id
        self.name = hardDisk.name
        self.type = hardDisk.type
        self.logicalSize = hardDisk.logicalSize

class jsMachine:
    def __init__(self, ctx, machine):
        self.accessible = machine.accessible
        self.name = machine.name
        self.desc = machine.description
        self.id = machine.id
        self.OSTypeId = machine.OSTypeId
        self.CPUCount = machine.CPUCount
        self.bootOrder = []
        self.memorySize = machine.memorySize
        self.VRAMSize = machine.VRAMSize
        self.accelerate3DEnabled = machine.accelerate3DEnabled
        self.HWVirtExEnabled = machine.HWVirtExEnabled
        self.HWVirtExNestedPagingEnabled = machine.HWVirtExNestedPagingEnabled
        self.VRDPServer = jsVRDPServer(ctx, machine.VRDPServer)
        self.state = machine.state
        self.sessState = machine.sessionState

        self.hardDiskAttachments = []
        arrAtt = ctx['global'].getArray(machine, 'hardDiskAttachments')
        for i in arrAtt:
            self.hardDiskAttachments.append(jsHardDiskAttachment(i))

        maxBootPosition = ctx['vb'].systemProperties.maxBootPosition
        for i in range(1, maxBootPosition + 1):
            self.bootOrder.append(machine.getBootOrder(i))

# Implementation of IConsoleCallback
class GuestMonitor:
    def __init__(self, mach):
        self.mach = mach

    def onMousePointerShapeChange(self, visible, alpha, xHot, yHot, width, height, shape):
        print  "%s: onMousePointerShapeChange: visible=%d" %(self.mach.name, visible)

    def onMouseCapabilityChange(self, supportsAbsolute, needsHostCursor):
        print  "%s: onMouseCapabilityChange: needsHostCursor=%d" %(self.mach.name, needsHostCursor)

    def onKeyboardLedsChange(self, numLock, capsLock, scrollLock):
        print  "%s: onKeyboardLedsChange capsLock=%d"  %(self.mach.name, capsLock)

    def onStateChange(self, state):
        print  "%s: onStateChange state=%d" %(self.mach.name, state)

    def onAdditionsStateChange(self):
        print  "%s: onAdditionsStateChange" %(self.mach.name)

    def onDVDDriveChange(self):
        print  "%s: onDVDDriveChange" %(self.mach.name)

    def onFloppyDriveChange(self):
        print  "%s: onFloppyDriveChange" %(self.mach.name)

    def onNetworkAdapterChange(self, adapter):
        print  "%s: onNetworkAdapterChange" %(self.mach.name)

    def onSerialPortChange(self, port):
        print  "%s: onSerialPortChange" %(self.mach.name)

    def onParallelPortChange(self, port):
        print  "%s: onParallelPortChange" %(self.mach.name)

    def onStorageControllerChange(self):
        print  "%s: onStorageControllerChange" %(self.mach.name)

    def onVRDPServerChange(self):
        print  "%s: onVRDPServerChange" %(self.mach.name)

    def onUSBControllerChange(self):
        print  "%s: onUSBControllerChange" %(self.mach.name)

    def onUSBDeviceStateChange(self, device, attached, error):
        print  "%s: onUSBDeviceStateChange" %(self.mach.name)

    def onSharedFolderChange(self, scope):
        print  "%s: onSharedFolderChange" %(self.mach.name)

    def onRuntimeError(self, fatal, id, message):
        print  "%s: onRuntimeError fatal=%d message=%s" %(self.mach.name, fatal, message)

    def onCanShowWindow(self):
        print  "%s: onCanShowWindow" %(self.mach.name)
        return True

    def onShowWindow(self, winId):
        print  "%s: onShowWindow: %d" %(self.mach.name, winId)

# Implementation of IVirtualBoxCallback, simply re-routes to page object (parent)
class VBoxMonitor:
    def __init__(self, parent):
        self.parent = parent

    def onMachineStateChange(self, id, state):
        print "onMachineStateChange: %s %d" %(id, state)
        self.parent.onMachineStateChange(id, state)

    def onMachineDataChange(self,id):
        print "onMachineDataChange: %s" %(id)
        self.parent.onMachineDataChange(id)

    def onExtraDataCanChange(self, id, key, value):
        print "onExtraDataCanChange: %s %s=>%s" %(id, key, value)
        #bRet = self.parent.onExtraDataCanChange(id, key, value)
        bRet = True

        # Witty COM bridge thinks if someone wishes to return tuple, hresult
        # is one of values we want to return
        if sys.platform == 'win32':
            return "", 0, bRet

        return "", bRet

    def onExtraDataChange(self, id, key, value):
        print "onExtraDataChange: %s %s=>%s" %(id, key, value)
        self.parent.onExtraDataChange(id, key, value)

    def onMediaRegistered(self, id, type, registred):
        print "onMediaRegistred: %s" %(id)
        self.parent.onMediaRegistered(id, type, registred)

    def onMachineRegistered(self, id, registred):
        print "onMachineRegistred: %s" %(id)
        self.parent.onMachineRegistered(id, registred)

    def onSessionStateChange(self, id, state):
        print "onSessionStateChange: %s %d" %(id, state)
        self.parent.onSessionStateChange(id, state)

    def onSnapshotTaken(self, mach, id):
        print "onSnapshotTaken: %s %s" %(mach, id)
        self.parent.onSnapshotTaken(mach, id)

    def onSnapshotDiscarded(self, mach, id):
        print "onSnapshotDiscarded: %s %s" %(mach, id)
        self.parent.onSnapshotDiscarded(mach, id)

    def onSnapshotChange(self, mach, id):
        print "onSnapshotChange: %s %s" %(mach, id)
        self.parent.onSnapshotChange(mach, id)

    def onGuestPropertyChange(self, id, name, newValue, flags):
        print "onGuestPropertyChange: %s: %s=%s" %(id, name, newValue)
        self.parent.onGuestPropertyChange(id, name, newValue, flags)

class VBoxMachine:
    def __init__(self, mach):
        self.mach = mach
        self.isDirty = True

class VBoxPage:
    def __init__(self, ctx):
        self.ctx = ctx

        # Ugly COM stuff
        self.initCOM = False
        if sys.platform == 'win32':
            self.vbox_stream = pythoncom.CoMarshalInterThreadInterfaceInStream(pythoncom.IID_IDispatch, self.ctx['vb'])

        # Init JSON printer
        self.jsonPrinter = None
        if isSimpleJson:
            self.jsonPrinter = simplejson.dumps
        else:
            if hasattr(json, "dumps"):
                self.jsonPrinter = json.dumps
            elif hasattr(json, "write"):
                self.jsonPrinter = json.write
        self.arrMach = []

        # Register authentication check handler
        cherrypy.tools.auth = cherrypy.Tool('before_handler', self.checkAuth)

    def prepareCOM(self):
        if self.initCOM is False:
            if sys.platform == 'win32':
                # Get the "real" VBox interface from the stream created in the class constructor above
                import win32com
                i = pythoncom.CoGetInterfaceAndReleaseStream(self.vbox_stream, pythoncom.IID_IDispatch)
                self.ctx['vb'] = win32com.client.Dispatch(i)
            self.initCOM = True

    def checkAuth(self, *args, **kwargs):
        """A tool that looks in config for 'auth.require'. If found and it
        is not None, a login is required and the entry is evaluated as alist of
        conditions that the user must fulfill"""
        conditions = cherrypy.request.config.get('auth.require', None)
        # format GET params
        get_parmas = urllib.quote(cherrypy.request.request_line.split()[1])
        if conditions is not None:
            username = cherrypy.session.get(SESSION_KEY)
            if username:
                cherrypy.request.login = username
                for condition in conditions:
                    # A condition is just a callable that returns true orfalse
                    if not condition():
                        # Send old page as from_page parameter
                        raise cherrypy.HTTPRedirect("/login?from_page=%s" % get_parmas)
            else:
                # Send old page as from_page parameter
                raise cherrypy.HTTPRedirect("/login?from_page=%s" %get_parmas)

    def check_credentials(self, username, password):
        """Verifies credentials for username and password.
        Returns None on success or a string describing the error on failure"""
        pwdDigest = self.ctx['vb'].getExtraData("vboxweb/users/" + username)
        h = hashlib.new('sha1')
        h.update(password)
        if h.hexdigest() == pwdDigest:
            return None
        else:
            return u"Incorrect username or password."

    def on_login(self, username):
        """Called on successful login"""

    def on_logout(self, username):
        """Called on logout"""

    def get_loginform(self, username, msg="Enter login information", from_page="/"):
        return """<html><body>
            <form method="post" action="/login">
            <input type="hidden" name="from_page" value="%(from_page)s" />
            %(msg)s<br />
            Username: <input type="text" name="username" value="%(username)s" /><br />
            Password: <input type="password" name="password" /><br />
            <input type="submit" value="Log in" /><p>
            Use <code>VBoxWebSrv.py adduser myuser mypassword</code> to create user accounts.
        </body></html>""" % locals()

    @cherrypy.expose
    def login(self, username=None, password=None, from_page="/"):
        self.prepareCOM()
        if username is None or password is None:
            return self.get_loginform("", from_page=from_page)

        error_msg = self.check_credentials(username, password)
        if error_msg:
            return self.get_loginform(username, error_msg, from_page)
        else:
            cherrypy.session[SESSION_KEY] = cherrypy.request.login = username
            self.on_login(username)
            raise cherrypy.HTTPRedirect(from_page or "/")

    @cherrypy.expose
    def logout(self, from_page="/"):
        self.prepareCOM()
        sess = cherrypy.session
        username = sess.get(SESSION_KEY, None)
        sess[SESSION_KEY] = None
        if username:
            cherrypy.request.login = None
            self.on_logout(username)
        raise cherrypy.HTTPRedirect(from_page or "/")

    def populateVMList(self):
        vboxVMList=self.ctx['global'].getArray(self.ctx['vb'], 'machines')
        self.arrMach = []
        for m in vboxVMList: # Append all machines
            self.arrMach.append(VBoxMachine(m))

    def getMachine(self, id):
        for m in self.arrMach: # @todo slow, speed this up
            if cmp(m.mach.id, id) == 0:
                return m
        return None

    def machineSetDirty(self, id):
        m = self.getMachine(id)
        if m <> None:
            m.isDirty = True

    def onMachineStateChange(self, id, state):
        self.machineSetDirty(id)

    def onMachineDataChange(self,id):
        self.machineSetDirty(id)

    def onExtraDataCanChange(self, id, key, value):
        # Allow all at the moment
        return True

    def onExtraDataChange(self, id, key, value):
        self.machineSetDirty(id)

    def onMediaRegistered(self, id, type, registred):
        self.machineSetDirty(id)

    def onMachineRegistered(self, id, registered):
        self.populateVMList() # Just re-build internal list from scratch

    def onSessionStateChange(self, id, state):
        self.machineSetDirty(id)

    def onSnapshotTaken(self, mach, id):
        self.machineSetDirty(id)

    def onSnapshotDiscarded(self, mach, id):
        self.machineSetDirty(id)

    def onSnapshotChange(self, mach, id):
        self.machineSetDirty(id)

    def onGuestPropertyChange(self, id, name, newValue, flags):
        # Don't react on this event - generated too much unused traffic atm
        pass

class Root(VBoxPage):

    def registerCallbacks(self):
        # Register IVirtualBox (global) callback
        self.callbackVBox = self.ctx['global'].createCallback('IVirtualBoxCallback', VBoxMonitor, self)
        self.ctx['vb'].registerCallback(self.callbackVBox)

    @cherrypy.expose
    @require()
    def vboxGetUpdates(self):
        print "Page: vboxGetUpdates"

        arrJSON = []
        arrMach = []

        # Add all machines that have changed (are dirty) to arrMach
        for m in self.arrMach:
            if (m.isDirty is True):
                arrMach.append(m)
                m.isDirty = False

        if (len(arrMach) is len(self.arrMach)):
            updateType = 0 # Full
        else:
            updateType = 1 # Differential

        # Add header (must always come first atm)
        arrJSON.append(jsHeader(self.ctx, arrMach, updateType))

        # Add global VirtualBox object on full update
        if updateType is 0:
            arrJSON.append(jsVirtualBox(self.ctx))

        # Add arrMach to the final JSON array
        for m in arrMach:
            arrJSON.append(jsMachine(self.ctx, m.mach))

        print "%s update, %d machines modified" %("full" if updateType is 0 else "differential", len(arrMach))
        if isSimpleJson:
            return self.jsonPrinter(arrJSON, cls=ConvertObjToJSONClass)
        else:
            return self.jsonPrinter(arrJSON, default=convertObjToJSON)

    @cherrypy.expose
    @require()
    def vboxVMAction(self, operation, uuid):
        statusMessage = ""
        print "Page: vboxVMAction called with operation " + operation + " and uuid " + uuid
        # Close session if opened
        if operation == "startvm":
            session = self.ctx['mgr'].getSessionObject(self.ctx['vb'])
            progress = self.ctx['vb'].openRemoteSession(session, uuid, "headless", "")
            # todo we shouldn't wait here, perform asynchronously
            progress.waitForCompletion(-1)
            session.close()
            statusMessage = "Started VM with ID " + uuid

        # Commands requiring an open session
        elif (operation == "pausevm" or
             operation == "resumevm" or
             operation == "savestatevm" or
             operation == "poweroffvm" or
             operation == "acpipoweroffvm" or
             operation == "discardvm"):
            session = self.ctx['mgr'].getSessionObject(self.ctx['vb'])
            progress = self.ctx['vb'].openExistingSession(session, uuid)
            console = session.console;
            if operation == "pausevm":
                console.pause()
                statusMessage = "Paused VM with ID " + uuid
            elif operation == "resumevm":
                console.resume()
                statusMessage = "Resumed VM with ID " + uuid
            elif operation == "savestatevm":
                console.saveState()
                statusMessage = "Saving state of VM with ID " + uuid
            elif operation == "poweroffvm":
                console.powerDown()
                statusMessage = "Powering off VM with ID " + uuid
            elif operation == "acpipoweroffvm":
                console.powerButton()
                statusMessage = "Sent ACPI power button signal to VM with ID " + uuid
            elif operation == "discardvm":
                console.discardCurrentState()
                statusMessage = "Discarded saved state for VM with ID " + uuid
        else:
            print "vboxVMAction: unknown operation"

        arrJSON = []
        arrJSON.append(jsHeader(self.ctx, [], 1, statusMessage))
        if isSimpleJson:
            return self.jsonPrinter(arrJSON, cls=ConvertObjToJSONClass)
        else:
            return self.jsonPrinter(arrJSON, default=convertObjToJSON)

    # Entry point when browser loads the whole page
    @cherrypy.expose
    @require()
    def index(self):
        print "Page: init"

        self.prepareCOM()
        self.registerCallbacks()
        self.populateVMList()

        file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'www/templates/index.html')
        return serve_file(file, content_type='text/html')

g_virtualBoxManager = vboxapi.VirtualBoxManager(None, None)
g_threadPool = {}
g_logLevel = 99
g_sessionNum = 0

def log(level, str):
    if g_logLevel >= level:
        print str

def perThreadInit(threadIndex):
    g_virtualBoxManager.initPerThread()

def perThreadDeinit(threadIndex):
    g_virtualBoxManager.deinitPerThread()

def main(argv = sys.argv):

    print "VirtualBox Version: %s, Platform: %s" %(g_virtualBoxManager.vbox.version, sys.platform)

    bRDPWebForceUpdate = False

    # Check command line args
    if len(argv) > 1:
        if argv[1] == "adduser":
            if len(argv) <> 4:
                print "Syntax: " + argv[0] + " adduser <username> <password>"
                return
            h = hashlib.new('sha1')
            h.update(argv[3])
            g_virtualBoxManager.vbox.setExtraData(
                "vboxweb/users/" + argv[2], h.hexdigest())
            return
        elif argv[1] == "deluser":
            if len(argv) <> 3:
                print "Syntax: " + argv[0] + " deluser <username>"
                return
            g_virtualBoxManager.vbox.setExtraData("vboxweb/users/" + argv[2], "")
            return
        elif argv[1] == "rdpweb":
            if len(argv) <> 3:
                print "Syntax: " + argv[0] + " rdpweb update"
                return
            bRDPWebForceUpdate = True

    # Why subscribe() doesn't take callback argument, having global vboxMgr is a bit ugly
    cherrypy.engine.subscribe('start_thread', perThreadInit)
    cherrypy.engine.subscribe('stop_thread',  perThreadDeinit)

    fileConfig = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'VBoxWeb.conf')
    print "Using config file:", fileConfig

    cherrypy.config.update(fileConfig)
    cherrypy.config.update({
        'tools.staticdir.root': os.path.abspath(os.path.dirname(__file__))
    })

    # Lookup our external IP
    print "Getting external IP (google.com) ..."
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("google.com", 80))
    serverAdr, serverPort = s.getsockname()[:2]
    s.close
    print "External IP is:", serverAdr

    # Init config
    ctx = {'global':g_virtualBoxManager,
           'mgr':g_virtualBoxManager.mgr,
           'vb':g_virtualBoxManager.vbox,
           'ifaces':g_virtualBoxManager.constants,
           'remote':g_virtualBoxManager.remote,
           'type':g_virtualBoxManager.type,
           'serverAdr':serverAdr,
           'serverPort':serverPort
           }

    # Download the RDP web control
    bRDPForceUpdate = False
    vboxRDPWeb.checkForUpdate(
        "http://download.virtualbox.org/virtualbox/rdpweb/",
        os.path.abspath(os.path.dirname(__file__)) + "/www/static/",
        None,
        bRDPWebForceUpdate)

    # Run web server
    cherrypy.quickstart(Root(ctx), '/', {
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'www/static'},
        '/images': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'www/static/images'}}
        )

    # Shut down

if __name__ == '__main__':
    main(sys.argv)
