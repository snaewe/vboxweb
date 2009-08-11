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

import cgi
import cherrypy
import os
import socket
import sys
import time
import traceback

if sys.version_info < (2, 6):
    import simplejson
    isSimpleJson = True
else:
    import json
    isSimpleJson = False

from cherrypy.lib.static import serve_file

if sys.platform == 'win32':
    import pythoncom

import vboxapi

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

class jsHeader:
    def __init__(self, ctx, arrMach, type):
        self.magic = "jsVBxWb"
        self.ver = 1

        self.sessionID = cherrypy.session.id
        self.numMach = len(arrMach)
        self.updateType = type

#
# @todo write autowrapper for attributes main-like classes below.
#       Currently this involves too much copying around.
#
class jsVRDPServer:
    def __init__(self, ctx, machine):
        global g_serverAddress

        self.enabled = machine.VRDPServer.enabled
        self.port = machine.VRDPServer.port

        self.netAddress = machine.VRDPServer.netAddress
        if not self.netAddress:
            self.netAddress = ctx['serverAdr']

        self.authType = machine.VRDPServer.authType
        self.allowMultiConnection = machine.VRDPServer.allowMultiConnection
        self.reuseSingleConnection = machine.VRDPServer.reuseSingleConnection

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
        self.ostype = jsGuestOSType(ctx['vb'].getGuestOSType(machine.OSTypeId))
        self.CPUCount = machine.CPUCount
        self.bootOrder = []
        self.memorySize = machine.memorySize
        self.VRAMSize = machine.VRAMSize
        self.accelerate3DEnabled = machine.accelerate3DEnabled
        self.HWVirtExEnabled = machine.HWVirtExEnabled
        self.HWVirtExNestedPagingEnabled = machine.HWVirtExNestedPagingEnabled
        self.VRDPServer = jsVRDPServer(ctx, machine)
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
        self.forceUpdate = False
        self.init = False
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

    def initPage(self):
        if self.init is False:
            if sys.platform == 'win32':
                # Get the "real" VBox interface from the stream created in the class constructor above
                import win32com
                i = pythoncom.CoGetInterfaceAndReleaseStream(self.vbox_stream, pythoncom.IID_IDispatch)
                self.ctx['vb'] = win32com.client.Dispatch(i)

            # We're done now
            self.init = True

    @cherrypy.expose
    def vboxGetUpdates(self):

        arrJSON = []
        arrMach = []

        # Add all machines that have changed (are dirty) to arrMach
        for m in self.arrMach:
            if (m.isDirty is True) or (self.forceUpdate is True):
                arrMach.append(m)
                m.isDirty = False

        if len(arrMach) is len(self.arrMach):
            updateType = 0 # Full
        else:
            updateType = 1 # Differential

        # Add header
        arrJSON.append(jsHeader(self.ctx, arrMach, updateType))

        # Add arrMach to the final JSON array
        for m in arrMach:
            arrJSON.append(jsMachine(self.ctx, m.mach))

        self.forceUpdate = False

        print "type %d, %d machines modified" %(updateType, len(arrMach))
        if isSimpleJson:
            return self.jsonPrinter(arrJSON, cls=ConvertObjToJSONClass)
        else:
            return self.jsonPrinter(arrJSON, default=convertObjToJSON)

    @cherrypy.expose
    def vboxVMAction(self, operation, uuid):
        print "vboxVMAction called with operation " + operation + " and uuid " + uuid

        if operation == "startvm":
            session = self.ctx['mgr'].getSessionObject(self.ctx['vb'])
            progress = self.ctx['vb'].openRemoteSession(session, uuid, "headless", "")
            # todo we shouldn't wait here, perform asynchronously
            progress.waitForCompletion(-1)
            session.close()

        # Commands requiring an open session
        elif (operation == "pausevm" or
             operation == "resumevm" or
             operation == "savestatevm" or
             operation == "poweroff" or
             operation == "acpipoweroffvm"):
            session = self.ctx['mgr'].getSessionObject(self.ctx['vb'])
            progress = self.ctx['vb'].openExistingSession(session, uuid)
            console = session.console;
            if operation == "pausevm":
                console.pause()
            elif operation == "resumevm":
                console.resume()
            elif operation == "savestatevm":
                pass
            elif operation == "poweroff":
                console.powerDown()
            elif operation == "acpipoweroff":
                console.powerButton()

        elif operation == "discardvm":
            pass
        else:
            print "vboxVMAction: unknown operation"

        # todo easier way to return "no updates"?
        arrJSON = []
        arrJSON.append(jsHeader(self.ctx, [], 1))
        if isSimpleJson:
            return self.jsonPrinter(arrJSON, cls=ConvertObjToJSONClass)
        else:
            return self.jsonPrinter(arrJSON, default=convertObjToJSON)

    @cherrypy.expose
    def vboxStartVM(self, uuid):
        print "vboxStartVM called with uuid " + uuid
        session = self.ctx['mgr'].getSessionObject(self.ctx['vb'])
        progress = self.ctx['vb'].openRemoteSession(session, uuid, "headless", "")
        # todo we shouldn't wait here, perform asynchronously
        progress.waitForCompletion(-1)
        session.close()
        # todo easier way to return "no updates"?
        arrJSON = []
        arrJSON.append(jsHeader(self.ctx, [], 1))
        if isSimpleJson:
            return self.jsonPrinter(arrJSON, cls=ConvertObjToJSONClass)
        else:
            return self.jsonPrinter(arrJSON, default=convertObjToJSON)

    @cherrypy.expose
    def index(self):

        self.initPage()

        # Register IVirtualBox (global) callback
        self.callbackVBox = self.ctx['global'].createCallback('IVirtualBoxCallback', VBoxMonitor, self)
        self.ctx['vb'].registerCallback(self.callbackVBox)

        self.populateVMList()
        self.forceUpdate = True

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

def rdpWebControlDownloadCallback(blocks, blockSize, size):
    percentage = (blockSize * blocks * 100) / size
    if percentage > 100:
        percentage = 100
    print "Status: %d%%" % (percentage)

def rdpWebControlDownload(forceUpdate = False, url = None, dest = None, proxies = None):

    import zipfile
    if sys.version_info < (3, 0):
        import urllib
        url_open = urllib.urlopen
    else:
        import urllib.request
        import urllib.error
        url_open = urllib2.urlopen

    try:

        # @todo add local/remote version comparison to update to a newer version
        #       if necessary.

        fhFileLocal = None
        fhFileVer = None
        ret = False

        # Set default URL
        if url is None:
            url = "http://download.virtualbox.org/virtualbox/rdpweb/"

        if dest is None:
            dest = os.path.abspath(os.path.dirname(__file__)) + "/www/static/"

        # Check for already installed object
        bRDPInstalled = os.path.isfile(dest + "rdpweb.swf")
        if bRDPInstalled and (forceUpdate is False):
            return

        # Get latest version information
        strVersion = ""
        print "Looking up latest version of Sun RDP Web Control (from %s) ..." %(url)
        fhFileVer = url_open(url + "LATEST.TXT", None, proxies)

        # Parse version and let the user know
        strLine = fhFileVer.readline().rstrip("\n")
        fVersion = float(strLine)
        if hasattr(fVersion, '__int__'):
            print "Latest version is: ",fVersion
        else:
            raise IOError("No version information found!")

        # Download the ZIP
        print "Downloading Sun RDP Web Control ..."
        rdpFile = "rdpweb_" + strLine + ".zip"
        urllib.urlretrieve(url + rdpFile, dest + rdpFile, rdpWebControlDownloadCallback)
        print "Download complete."

        # Extract from ZIP
        print "Extracting Sun RDP Web Control ..."
        fhFileLocal = zipfile.ZipFile(dest + rdpFile, "r")

        if fhFileLocal.testzip() <> None:
            raise IOError("File is corrupted!")
        if fhFileLocal is None:
            raise IOError("Could not decompress file!")

        for i, name in enumerate(fhFileLocal.namelist()):
            print "Extracting %s" % name
            if not name.endswith('/'):
                outfile = open(os.path.join(dest, name), 'wb')
                outfile.write(fhFileLocal.read(name))
                outfile.flush()
                outfile.close()

        fhFileLocal.close()

        print "Cleaning up ..."
        os.remove(dest + rdpFile)
        os.rename(dest + "rdpweb_" + strLine + ".swf", dest + "rdpweb.swf")

        print "Installation successful."
        ret = True

    except Exception, e:
        print e

    finally:
        if fhFileVer <> None:
            fhFileVer.close()
        if fhFileLocal <> None:
            fhFileLocal.close()

        return ret

def main(argv):

    # Why subscribe() doesn't take callback argument, having global vboxMgr is a bit ugly
    cherrypy.engine.subscribe('start_thread', perThreadInit)
    cherrypy.engine.subscribe('stop_thread',  perThreadDeinit)

    print "VirtualBox Version:", g_virtualBoxManager.vbox.version[:3]

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
    rdpWebControlDownload()

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
