#!/usr/bin/env python
#
# Copyright (C) 2010 Oracle Corporation

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

# Implementation of IConsoleCallback
class VBoxGuestMonitor:
    def __init__(self, mach):
        self.mach = mach

    def onMousePointerShapeChange(self, visible, alpha, xHot, yHot, width, height, shape):
        print "%s: onMousePointerShapeChange: visible=%d" %(self.mach.name, visible)

    def onMouseCapabilityChange(self, supportsAbsolute, needsHostCursor):
        print "%s: onMouseCapabilityChange: needsHostCursor=%d" %(self.mach.name, needsHostCursor)

    def onKeyboardLedsChange(self, numLock, capsLock, scrollLock):
        print "%s: onKeyboardLedsChange capsLock=%d"  %(self.mach.name, capsLock)

    def onStateChange(self, state):
        print "%s: onStateChange state=%d" %(self.mach.name, state)

    def onAdditionsStateChange(self):
        print "%s: onAdditionsStateChange" %(self.mach.name)

    def onDVDDriveChange(self):
        print "%s: onDVDDriveChange" %(self.mach.name)

    def onFloppyDriveChange(self):
        print "%s: onFloppyDriveChange" %(self.mach.name)

    def onNetworkAdapterChange(self, adapter):
        print "%s: onNetworkAdapterChange" %(self.mach.name)

    def onSerialPortChange(self, port):
        print "%s: onSerialPortChange" %(self.mach.name)

    def onParallelPortChange(self, port):
        print "%s: onParallelPortChange" %(self.mach.name)

    def onStorageControllerChange(self):
        print "%s: onStorageControllerChange" %(self.mach.name)

    def onVRDPServerChange(self):
        print "%s: onVRDPServerChange" %(self.mach.name)

    def onUSBControllerChange(self):
        print "%s: onUSBControllerChange" %(self.mach.name)

    def onUSBDeviceStateChange(self, device, attached, error):
        print "%s: onUSBDeviceStateChange" %(self.mach.name)

    def onSharedFolderChange(self, scope):
        print "%s: onSharedFolderChange" %(self.mach.name)

    def onRuntimeError(self, fatal, id, message):
        print "%s: onRuntimeError fatal=%d message=%s" %(self.mach.name, fatal, message)

    def onCanShowWindow(self):
        print "%s: onCanShowWindow" %(self.mach.name)
        return True

    def onShowWindow(self, winId):
        print "%s: onShowWindow: %d" %(self.mach.name, winId)
