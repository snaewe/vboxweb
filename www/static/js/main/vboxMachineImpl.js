
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
        this.mBootOrder = "";
        this.mMemorySize = 0;
        this.mVRAMSize = 0;
        this.mAccelerate3DEnabled = false;
        this.mHWVirtExEnabled = false;
        this.mHWVirtExNestedPagingEnabled = false;
        this.mVRDPServer = new vboxMachineVRDPServer();
        this.mSessionState =  -1;
        this.mState =  -1;
        this.mHardDiskAttachments = [];
    },

    loadSettingsJSON: function(jsonObject)
    {
        this.mAccessible = jsonObject.accessible;
        this.mName = jsonObject.name;
        this.mDesc = jsonObject.desc;
        this.mId = jsonObject.id;
        this.mOSType = jsonObject.ostype;
        this.mCPUCount = jsonObject.CPUCount;
        this.mBootOrder = jsonObject.bootOrder;
        this.mMemorySize = jsonObject.memorySize;
        this.mVRAMSize = jsonObject.VRAMSize;
        this.mAccelerate3DEnabled = jsonObject.accelerate3DEnabled ? true : false;
        this.mHWVirtExEnabled = jsonObject.HWVirtExEnabled ? true : false;
        this.mHWVirtExNestedPagingEnabled = jsonObject.HWVirtExNestedPagingEnabled ? true : false;
        this.mVRDPServer.loadSettingsJSON(jsonObject.VRDPServer);
        this.mState = jsonObject.state;
        this.mSessionState = jsonObject.sessState;

        for(i=0; i<jsonObject.hardDiskAttachments.length; i++) 
        {
            attachment = new vboxHardDiskAttachment();
            attachment.loadSettingsJSON(jsonObject.hardDiskAttachments[i]);
            this.mHardDiskAttachments.push(attachment);
        }
    },

    getBootOrder: function(position)
    {
        return this.mBootOrder;
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

    getOSTypeID: function()
    {
        return this.mOSType.id;
    },

    getOSTypeDescription: function()
    {
        return this.mOSType.description;
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
    },

    getHardDiskAttachments: function()
    {
        return this.mHardDiskAttachments;
    }
});
