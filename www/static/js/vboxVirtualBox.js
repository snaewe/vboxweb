
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

/* This class is needed for having a correct scope when getting back from the Ajax callback. See checkForUpdates() below. */
Abstract.XMLHttpCatch = Class.create();
Abstract.XMLHttpCatch.prototype =
{
    initialize: function()
    {
    },

    updateProcess: function(response, scope)
    {
        scope.updateProcess(response);
    },

    updateFailed: function(response, scope)
    {
        scope.updateFailed(response);
    }
};

var vboxVirtualBox = Class.create(
{
    initialize: function()
    {
        this.mArrMachines = new Array();
        this.XMLHttpCatch = new Abstract.XMLHttpCatch();

        this.checkForUpdates();

        var scope = this; /* Save scope. */
        /*this.perExec = new PeriodicalExecuter(
                scope.checkForUpdates.bind(scope), 10
            ); /* Search for updates every minute. */
    },

    refresh: function()
    {
        this.checkForUpdates();
    },

    receiveData: function(page)
    {
        var XMLHttpCatch = this.XMLHttpCatch; /* Get a local name for our catch object. */
        var scope = this; /* Save scope. */
        new Ajax.Request(page,
            {
                method:'get',
                requestHeaders: {Accept: 'application/json'},
                onSuccess: function(resp) {
                    XMLHttpCatch.updateProcess(resp, scope);
                },
                onFailed: function(resp) {
                    XMLHttpCatch.onFailed(resp, scope);
                }
            });
    },

    checkForUpdates: function()
    {
        console.log("vboxVirtualBox::checkForUpdates: Called.");
        this.receiveData("/vboxGetUpdates");
    },

    updateProcess: function(response)
    {
        try
        {
            var res = response.responseText.evalJSON(true);

            /* Index 0 is *always* the header! */
            if ((res[0].magic != "jsVBxWb") || (res[0].ver != "1"))
                throw "Invalid header!";

            var n = res[0].numMach;
            switch (res[0].__class__)
            {
                case "jsHeader":

                    if (n > 0)
                    {
                        var newMach;
                        console.log("vboxVirtualBox::updateProcess: Updates for %d machines ...", n);
                        this.clearMachines(); /** @todo don't clear all machines later! */
                        for (var i=0; i<n; i++)
                        {
                            newMach = new vboxMachineImpl();
                            newMach.loadSettingsJSON(res[i+1]);
                            this.addMachine(newMach);
                        }

                        var sel = vbGlobal.selectorWnd();
                        sel.refreshVMList();
                    }
                    else console.log("vboxVirtualBox::updateProcess: No updates.");
                    break;

                default:

                    throw "Wrong class!"
                    break;
            }
        }
        catch (e)
        {
            console.log("vboxVirtualBox::updateProcess: %s", e);
            this.dispatchException(e);
        }
        finally
        {
            return;
        }
    },

    updateFailed: function(response)
    {
        try
        {
            var res = response.responseText.evalJSON(true);
            console.log("vboxVirtualBox::updateFailed: Update failed! Data = %s", res);
        }
        catch (e)
        {
            console.log("vboxVirtualBox::updateFailed: %s", e);
            this.dispatchException(e);
            return false;
        }
        
        return true;
    },

    addMachine: function(vboxMachineImpl)
    {
        /** @todo Search for machine first before adding. */
        console.log("vboxVirtualBox::addMachine: Name = %s", vboxMachineImpl.getName());
        this.mArrMachines[this.mArrMachines.length] = vboxMachineImpl;
    },

    clearMachines: function()
    {
        this.mArrMachines.clear();
    },

    getMachineCount: function()
    {
        return this.mArrMachines.length;
    },

    getMachines: function()
    {
        return this.mArrMachines;
    },

    getMachineByIndex: function(index)
    {
        if (   (this.mArrMachines < 0)
            || (this.mArrMachines >= this.mArrMachines.length))
            return None;
        return this.mArrMachines[index];
    },

    getMachineById: function(id)
    {
        /** @todo Slow lookup, improve this! */
        var l = this.mArrMachines.length;
        for (var i=0; i<l; i++)
        {
            if (this.mArrMachines[i].getId() == id)
                return this.mArrMachines[i];
        }

        return null;
    }
});