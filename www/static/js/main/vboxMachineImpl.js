
/* Copyright (C) 2009 Sun Microsystems, Inc.

 * Permission is hereby granted, free of charge, to any person
 * obtaining a copy of this software and associated documentation
 * files (the "Software"), to deal in the Software without
 * restriction, including without limitation the rights to use,
 * copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the
 * Software is furnished to do so, subject to the following
 * conditions:

 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.

 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
 * OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
 * HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
 * WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
 * OTHER DEALINGS IN THE SOFTWARE.
 */

var vboxMachineVRDPServer = Class.create(
{
    initialize: function()
    {
        this.mEnabled = false;
        this.mPort = 0;
        this.mAddress = "";
        this.mAuthType = "";
    },

    loadSettingsJSON: function(jsonObject, arrIndex)
    {
        this.mEnabled = jsonObject.enabled == "1" ? true : false;
        this.mPort = jsonObject.port;
        this.mAddress = jsonObject.netAddress;
        this.mAuthType = jsonObject.authType;
    },

    getEnabled: function()
    {
        return this.mEnabled;
    },

    getPort: function()
    {
        if ((this.mPort == "") || (this.mPort == "0"))
            return "3389";
        return this.mPort;
    },

    getNetAddress: function()
    {
        if (this.mAddress == "")
            return tr("127.0.0.1");
        return this.mAddress;
    },

    getAuthType: function()
    {
        if (this.mAuthType == "")
            return "0";
        return this.mAuthType;
    }
});

var vboxMachineImpl = Class.create(
{
    initialize: function()
    {
        this.mAccessible = false;
        this.mName = "";
        this.mDesc = "";
        this.mId = "";
        this.mOSType = "";
        this.mCPUCount = 0;
        this.mMemorySize = 0;
        this.mVRAMSize = 0;
        this.mAccelerate3DEnabled = false;
        this.mHWVirtExEnabled = false;
        this.mHWVirtExNestedPagingEnabled = false;
        this.mVRDPServer = new vboxMachineVRDPServer();
        this.mSessionState =  -1;
        this.mState =  -1;
    },

    loadSettingsJSON: function(jsonObject)
    {
        this.mAccessible = jsonObject.accessible;
        this.mName = jsonObject.name;
        this.mDesc = jsonObject.desc;
        this.mId = jsonObject.id;
        this.mOSType = jsonObject.ostype;
        this.mCPUCount = jsonObject.CPUCount;
        this.mMemorySize = jsonObject.memorySize;
        this.mVRAMSize = jsonObject.VRAMSize;
        this.mAccelerate3DEnabled = jsonObject.accelerate3DEnabled ? true : false;
        this.mHWVirtExEnabled = jsonObject.HWVirtExEnabled ? true : false;
        this.mHWVirtExNestedPagingEnabled = jsonObject.HWVirtExNestedPagingEnabled ? true : false;
        this.mVRDPServer.loadSettingsJSON(jsonObject.VRDPServer);
        this.mState = jsonObject.state;
        this.mSessionState = jsonObject.sessState;
    },

    getBootOrder: function(position)
    {
        return "";
    },

    /* Public attributes. */
    getAccessible: function()
    {
        return this.mAccessible;
    },

    getName: function()
    {
        return this.mName;
    },

    getDesc: function()
    {
        return this.mDesc;
    },

    getId: function()
    {
        return this.mId;
    },

    getOSType: function()
    {
        return this.mOSType;
    },

    getCPUCount: function()
    {
        return this.mCPUCount;
    },

    getMemorySize: function()
    {
        return this.mMemorySize;
    },

    getVRAMSize: function()
    {
        return this.mVRAMSize;
    },

    getAccelerate3DEnabled: function()
    {
        return this.mAccelerate3DEnabled;
    },

    getHWVirtExEnabled: function()
    {
        return this.mHWVirtExEnabled;
    },

    getHWVirtExNestedPagingEnabled: function()
    {
        return this.mHWVirtExNestedPagingEnabled;
    },

    getVRDPServer: function()
    {
        return this.mVRDPServer;
    },

    getState: function()
    {
        return this.mState;
    },

    getSessionState: function()
    {
        return this.mSessionState;
    }
});