
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
