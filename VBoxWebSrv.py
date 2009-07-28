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

import sys, os
import socket
import traceback
import cherrypy
import cgi

if sys.version_info < (2, 6):
    import simplejson as json
else:
    import json

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

class jsHeader:
    def __init__(self, ctx, vmList):
        self.magic = "jsVBxWb"
        self.ver = 1

        self.numMach = len(vmList)
#
# @todo write autowrapper for attributes main-like classes below.
#       Currently this involves too much copying around.
#
class jsVRDPServer:
    def __init__(self, ctx, machine):
        global g_serverAddress

        self.enabled = machine.VRDPServer.enabled;
        self.port = machine.VRDPServer.port;

        self.netAddress = machine.VRDPServer.netAddress
        if not self.netAddress:
            self.netAddress = ctx['serverAdr']

        self.authType = machine.VRDPServer.authType;
        self.allowMultiConnection = machine.VRDPServer.allowMultiConnection;
        self.reuseSingleConnection = machine.VRDPServer.reuseSingleConnection;

class jsMachine:
    def __init__(self, ctx, machine):
        self.accessible = machine.accessible
        self.name = machine.name
        self.desc = machine.description
        self.id = machine.id
        self.ostype = machine.OSTypeId
        self.CPUCount = machine.CPUCount
        self.memorySize = machine.memorySize
        self.VRAMSize = machine.VRAMSize
        self.accelerate3DEnabled = machine.accelerate3DEnabled
        self.HWVirtExEnabled = machine.HWVirtExEnabled
        self.HWVirtExNestedPagingEnabled = machine.HWVirtExNestedPagingEnabled
        self.VRDPServer = jsVRDPServer(ctx, machine)
        self.state = machine.state
        self.sessState = machine.sessionState

class VBoxPage:
    def __init__(self, ctx):
        self.ctx = ctx
        if sys.platform == 'win32':
            self.vbox_stream = pythoncom.CoMarshalInterThreadInterfaceInStream(pythoncom.IID_IDispatch, self.ctx['vb'])
        self.init = False

        # Init JSON printer
        self.printer = None
        if hasattr(json, "dumps"):
            self.printer = json.dumps
        elif hasattr(json, "write"):
            self.printer = json.write

class Root(VBoxPage):

    @cherrypy.expose
    def vboxGetUpdates (self):
        if self.init is False:
            return ""

        arr=[]
        vboxVMList=self.ctx['global'].getArray(self.vbox, 'machines')

        arr.append(jsHeader(self.ctx, vboxVMList)) # Append header
        for m in vboxVMList: # Append all machines
            arr.append(jsMachine(self.ctx, m))

        return self.printer(arr, default=convertObjToJSON)

    @cherrypy.expose
    def index(self):

        if self.init is False:
            if sys.platform == 'win32':
                # What we're trying to do here?
                import win32com
                i = pythoncom.CoGetInterfaceAndReleaseStream(self.vbox_stream, pythoncom.IID_IDispatch)
                self.vbox = win32com.client.Dispatch(i)
            self.init = True

        file = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'www/templates/index.html')
        return serve_file(file, content_type='text/html')

g_virtualBoxManager = vboxapi.VirtualBoxManager(None, None)

def perThreadInit(threadIndex):
    g_virtualBoxManager.initPerThread()

def perThreadDeinit(threadIndex):
    g_virtualBoxManager.deinitPerThread()

def main(argv):

    # Why subscribe() doesn't take callback argument, having global vboxMgr is a bit ugly
    cherrypy.engine.subscribe('start_thread', perThreadInit)
    cherrypy.engine.subscribe('stop_thread',  perThreadDeinit)

    print "VirtualBox Version:", g_virtualBoxManager.vbox.version[:3];

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

    # Run web server
    cherrypy.quickstart(Root(ctx), '/', {
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'www/static'},
        '/images': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'www/static/images'}}
        )

if __name__ == '__main__':
    main(sys.argv)
