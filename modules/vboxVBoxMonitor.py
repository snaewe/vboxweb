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

import sys

# Implementation of IVirtualBoxCallback, simply re-routes to page object (parent)
class VBoxMonitor:
    def __init__(self, parent):
        print "VBoxMonitor callback registered. Parent =",parent
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

        return bRet, ""

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
