
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
        this.userName = "";
        this.mArrMachines = new Array();
        this.mArrGuestOSTypes = new Array();
        this.XMLHttpCatch = new Abstract.XMLHttpCatch();

        this.checkForUpdates();

        var scope = this; /* Save scope. */
        this.perExec = new PeriodicalExecuter(
                scope.checkForUpdates.bind(scope), 10
            ); /* Search for updates periodically. */
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
        this.receiveData("/vboxGetUpdates");
    },

    updateGuestOSTypes: function(res)
    {
        var iNumOSTypes = res.numGuestOSTypes;
        this.mArrGuestOSTypes.clear();
        for (var i = 0; i < iNumOSTypes; i++)
        {
            var guestOS = res.arrGuestOSTypes[i];
            this.mArrGuestOSTypes[this.mArrGuestOSTypes.length] = new vboxIGuestOSTypeImpl(guestOS);
        }
    },

    updateProcess: function(response)
    {
        // don't try to parse empty responses
        if (response.responseText == "")
            return;
        try
        {
            var res = response.responseText.evalJSON(true);

            /* Index 0 is *always* the header! */
            if ((res[0].magic != "jsVBxWb") || (res[0].ver != "1"))
                throw "Invalid header!";

            this.userName = res[0].username;

            /* Did we get a status messsage to display? */
            if (res[0].statusMessage)
                vbGlobal.mVirtualBox.addMessage(res[0].statusMessage);

            /* @todo Get rid of the res[INDEX] handling! This is very error
             * prone and leads to confusion as more data will be added. */

            var numUpdates = res[0].numMach;
            var updateType = res[0].updateType;
            switch (res[0].__class__)
            {
                case "jsHeader":

                    /* On full update type (0) wipe existing machines. */
                    if (updateType == 0)
                    {
                        this.clearMachines();
                        this.updateGuestOSTypes(res[1]);
                    }

                    /* Full or diff update. */
                    if (numUpdates > 0)
                    {
                        var newMach;
                        console.log("vboxVirtualBox::updateProcess: Updates for %d machine(s) ...", numUpdates);

                        /* Add new or update existing machines. */
                        for (var i = 0; i < numUpdates; i++)
                        {
                            arrJSON = (updateType == 0) ? res[i + 2] : res[i + 1];
                            newMach = new vboxIMachineImpl(arrJSON);

                            curMach = this.getMachineById(newMach.getId());
                            if (curMach == undefined)
                            {
                                this.addMachine(newMach);
                            }
                            else
                            {
                                console.log("vboxVirtualBox::updateProcess: Updating machine: %s", curMach.getName());
                                curMach.loadSettingsJSON(arrJSON);

                            }
                        }

                        var sel = vbGlobal.selectorWnd();
                        sel.refreshVMList();
                    }
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

    addMessage: function(message)
    {
        /* this is ugly business but I couldn't find a better method */
        date = new Date();
        month = date.getMonth() + 1;
        if (month < 10) month = '0' + month;
        day = date.getDate();
        if (day < 10) day = '0' + day;
        hours = date.getHours();
        if (hours < 10) hours = '0' + hours;
        minutes = date.getMinutes();
        if (minutes < 10) minutes = '0' + minutes;
        seconds = date.getSeconds();
        if (seconds < 10) seconds = '0' + seconds;
        dateStr = date.getFullYear() + '-' + month + '-' + day + ' ' +
            hours + ':' + minutes + ':' + seconds;

        jQuery("#vmMessageTable").prepend('<tr><td class="message" style="width: 120px;" nowrap="nowrap">' +
            dateStr + '</td><td class="message">' + message + '</td></tr>');
    },

    getUserName: function()
    {
        return this.userName;
    },

    logout: function()
    {
        this.receiveData("/logout");
        /* local the main page, that will show the logon dialog */
        /* note: this might not be clean in case the site does not live on / */
        window.location = "/";
    },

    addMachine: function(vboxMachineImpl)
    {
        /** @todo Search for machine first before adding. */
        //console.log("vboxVirtualBox::addMachine: Name = %s", vboxMachineImpl.getName());
        this.mArrMachines[this.mArrMachines.length] = vboxMachineImpl;
    },

    removeMachine: function(id)
    {

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
            return undefined;
        return this.mArrMachines[index];
    },

    getMachineById: function(id)
    {
        /** @todo Slow lookup, improve this! */
        var l = this.mArrMachines.length;
        for (var i = 0; i < l; i++)
        {
            if (this.mArrMachines[i].getId() == id)
                return this.mArrMachines[i];
        }

        return undefined;
    },

    getGuestOSTypeById: function(id)
    {
        /** @todo Slow lookup, improve this! */
        var l = this.mArrGuestOSTypes.length;
        for (var i = 0; i < l; i++)
        {
            if (this.mArrGuestOSTypes[i].getId() == id)
                return this.mArrGuestOSTypes[i];
        }

        return undefined;
    },

    startVM: function(id)
    {
        this.receiveData("/vboxVMAction?operation=startvm&uuid=" + id)
    },

    pauseVM: function(id)
    {
        this.receiveData("/vboxVMAction?operation=pausevm&uuid=" + id);
    },

    resumeVM: function(id)
    {
        this.receiveData("/vboxVMAction?operation=resumevm&uuid=" + id);
    },

    discardVM: function(id)
    {
        this.receiveData("/vboxVMAction?operation=discardvm&uuid=" + id);
    },

    poweroffVM: function(id)
    {
        this.receiveData("/vboxVMAction?operation=poweroffvm&uuid=" + id);
    },

    savestateVM: function(id)
    {
        this.receiveData("/vboxVMAction?operation=savestatevm&uuid=" + id);
    },

    acpipoweroffVM: function(id)
    {
        this.receiveData("/vboxVMAction?operation=acpipoweroffvm&uuid=" + id);
    }
});
