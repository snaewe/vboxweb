
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

RDPState =
{
    Unloaded: 0,
    NotFound: 1,
    Connecting: 2,
    Connected: 3,
    Disconnecting: 4,
    Disconnected: 5,
    Redirecting: 6
};

var vboxTabWidget = Class.create(
{
    initialize: function()
    {
        this.mCurTab = "tabs-center-details";
        this.mFlashRDPStatus = 0;
    },

    setParent: function(parent)
    {
        this.mParent = parent;
    },

    onTabChange: function(event, ui)
    {
        if (ui.panel.id == undefined)
            return false;

        if (this.canChangeTab())
        {
            this.mCurTab = ui.panel.id;
            console.log("vboxTabWidget::onTabChange: curTab = %s", this.mCurTab);

            jQuery(".tab-sections").show(); /* Show all sections by default. */
            return this.invalidatePage(this.mCurTab);
        }
        else return false;
    },

    onResize: function(eventObject)
    {
        console.log("vboxTabWidget::onResize");
        if (this.mFlashRDPStatus > 0)
        {
            this.rdpDisconnect();
            this.rdpResize();
            this.rdpConnect();
        }
    },

    canChangeTab: function()
    {
        /** @todo check for open RDP connection and warn user. */
        return true;
    },

    invalidate: function()
    {
        console.log("vboxTabWidget::invalidate: curTab = %s", this.mCurTab);
        this.selectionChanged();
    },

    invalidatePage: function(id)
    {
        var curItem = this.mParent.curItem();
        var curId = id;
        if (curId == undefined)
            curId = this.mCurTab;

        if (curItem == undefined)
        {
            console.log("vboxTabWidget::invalidatePage: Current item is undefined.");
            return false;
        }

        switch (curId)
        {
            case 'tabs-center-details':
                this.invalidatePageDetails(curItem, true);
                break;

            case 'tabs-center-rdp':
                this.invalidatePageRDP(curItem, true);
                break;

            case 'tabs-center-desc':
                this.invalidatePageDesc(curItem, true);
                break;

            default:
                console.log("vboxTabWidget::invalidatePage: Invalid page name: %s", curId);
                return false;
        }

        return true;
    },

    invalidatePageDetails: function(curItem, pageSelected)
    {
        var bootOrder = curItem.machine().getBootOrder()
        var strBootOrder = vbGlobal.deviceType(bootOrder[0])
        for(i=1; i<bootOrder.length; i++) {
            if(bootOrder[i] > 0){
                strBootOrder = strBootOrder + ", " + vbGlobal.deviceType(bootOrder[i]);
            }
        }

        jQuery("#tab-details-vm-general-name-val").text(curItem.name());
        jQuery("#tab-details-vm-general-osname-val").text(curItem.machine().getOSTypeDescription());

        jQuery("#tab-details-vm-system-ram-val").text(curItem.machine().getMemorySize() + tr(" MB"));
        jQuery("#tab-details-vm-system-cpu-val").text(curItem.machine().getCPUCount());
        jQuery("#tab-details-vm-system-bootorder-val").text(strBootOrder);
        jQuery("#tab-details-vm-system-hwvirt-val").text(curItem.machine().getHWVirtExEnabled() ? tr("Enabled") : tr("Disabled"));
        jQuery("#tab-details-vm-system-nestedp-val").text(curItem.machine().getHWVirtExNestedPagingEnabled() ? tr("Enabled") : tr("Disabled"));

        jQuery("#tab-details-vm-display-videomem-val").text(curItem.machine().getVRAMSize() + tr(" MB"));
        jQuery("#tab-details-vm-display-3daccel-val").text(curItem.machine().getAccelerate3DEnabled() ? tr("Enabled") : tr("Disabled"));
        jQuery("#tab-details-vm-display-rdpport-val").text(curItem.machine().getVRDPServer().getPort());

        jQuery("li.harddisks-list-item").remove();
        var hardDiskAttachments = curItem.machine().getHardDiskAttachments();
        for (i = 0; i < hardDiskAttachments.length; i++)
        {
            attachment = hardDiskAttachments[i];
            hardDisk = attachment.getHardDisk();
            if (attachment.getController() === 'IDE')
            {
                port = (attachment.getPort() === 0) ? tr('Primary') : tr('Secondary');
                device = (attachment.getDevice() === 0) ? tr('Master') : tr('Slave');
            }
            else if (attachment.getController() === 'SATA')
            {
                port = 'Port ' + attachment.getPort();
                device = '';
            }
            else if (attachment.getController() === 'SCSI')
            {
                port = 'Port ' + attachment.getPort();
                device = '';
            }
            else
            {
                port = attachment.getPort();
                device = attachment.getDevice();
            }
            
            if (device != "")
                device = ' ' + device;
            strHardDisk = hardDisk.getName() + ' (' + vbGlobal.hardDiskType(hardDisk.getType()) +
                          ', ' + hardDisk.getLogicalSizeGB() + ' GB)';
            strListItem = '<div class="tab-details-vm-attribute">' +
                          attachment.getController() + ' ' + port + ' ' + device + ':' +
                          '</div><div class="tab-details-vm-value">' + strHardDisk +
                          '</div><div style="clear: both"></div>';
            jQuery("#tab-details-vm-harddisks-list").append("<li class='harddisks-list-item'>" + strListItem + "</li>");
        }

        if (hardDiskAttachments.length <= 0)
        {
            jQuery("#tab-details-vm-harddisks-list").
                append("<li class='harddisks-list-item'>" + tr("No hard disks attached") + "</li>");
        }
    },

    invalidatePageRDP: function(curItem, pageSelected)
    {
        console.log("vboxTabWidget::invalidatePageRDP: Machine status = %d", curItem.state());
        var rdpServ = curItem.machine().getVRDPServer();
        var rdpStatus = "";

        /* Do some sanity checks. */
        try
        {
            if (vbGlobal.flashPlayerInstalled() == false)
                throw(tr("Please install at least Flash Player 9 first!"));

            if (curItem.state() < 4)
                throw(tr("No remote view available because virtual machine is not running."));

            if (!rdpServ.getEnabled())
                throw(tr("Virtual machine is running but RDP server not enabled."));

            switch (this.mFlashRDPStatus)
            {
                case RDPState.Unloaded:

                    rdpStatus = tr("Loading Console ...");
                    jQuery("#tab-rdp-sec-conn").hide();

                    /* Request header to see if SWF file is present. */
                    var bError = false;
                    jQuery.ajax({
                            url:"/static/RDPClientUI.swf",
                            type: "HEAD",
                            async: true,
                            global: false,
                            cache: false,
                            timeout: 5000,
                            error: jQuery.context(this).callback('rdpNotFound')
                    });

                    break;

                case RDPState.NotFound:

                    rdpStatus = tr("Remote viewer file not found!");
                    jQuery("#tab-rdp-sec-conn").hide();
                    break;

                case RDPState.Connecting:

                    rdpStatus = tr("Connecting To Console ...");
                    jQuery("#tab-rdp-sec-conn").hide();
                    break;

                case RDPState.Connected:

                    rdpStatus = tr("Connected.");
                    this.rdpInvalidateConnBtn("Disconnect", false);
                    jQuery("#tab-rdp-sec-conn").show();
                    break;

                case RDPState.Disconnecting:

                    rdpStatus = tr("Disconnecting From Console ...");
                    jQuery("#tab-rdp-sec-conn").hide();
                    break;

                case RDPState.Disconnected:

                    rdpStatus = tr("Not connected.");
                    this.rdpInvalidateConnBtn(tr("Connect"), false);
                    jQuery("#tab-rdp-sec-conn").show();
                    if (rdpServ.getAuthType() != 0)
                    {
                        jQuery("#tab-rdp-auth-user").show();
                        jQuery("#tab-rdp-auth-pwd").show();
                    }
                    else
                    {
                        jQuery("#tab-rdp-auth-user").hide();
                        jQuery("#tab-rdp-auth-pwd").hide();
                    }
                    break;

                case RDPState.Redirecting:

                    rdpStatus = tr("Redirecting Connection ...");
                    break;

                default:

                    throw(tr("Unknown Flash RDP status!"));
                    break;
            }

            jQuery("#tab-rdp-desc-val").text(rdpStatus);
        }
        catch (e)
        {
            jQuery("#tab-rdp-sec-conn").hide();
            jQuery("#tab-rdp-desc-val").text(tr(e));
        }
    },

    invalidatePageDesc: function(curItem, pageSelected)
    {
        var strDesc = curItem.machine().getDesc();
        if (strDesc == null || strDesc == "")
            strDesc = tr("No description available.");
        jQuery("#tab-desc-desc-val").text(strDesc);
    },

    rdpInvalidateConnBtn: function(text, disabled)
    {
        if (text != "")
            jQuery("#tab-rdp-auth-btnconn").attr("value", text);
        jQuery("#tab-rdp-auth-btnconn").attr("disabled", disabled);
    },

    rdpStatus: function(e)
    {
        console.log("vboxTabWidget::rdpStatus: Success = %s, ID = %s, Ref = %s",
            e.success, e.id, e.ref);
        return false;
    },

    rdpLoaded: function(flashObj)
    {
        console.log("vboxTabWidget::rdpLoaded");
        this.mFlashRDPStatus = RDPState.Disconnected;
        this.invalidatePage();
        return false;
    },

    rdpUnloaded: function(flashObj)
    {
        console.log("vboxTabWidget::rdpUnloaded");
        this.mFlashRDPStatus = RDPState.Unloaded;
        this.invalidatePage();
        return false;
    },

    rdpConnected: function(flashObj)
    {
        console.log("vboxTabWidget::rdpConnected");
        this.mFlashRDPStatus = RDPState.Connected;
        this.invalidatePage();
        return false;
    },

    rdpRedirect: function(flashObj)
    {
        console.log("vboxTabWidget::rdpRedirect");
        this.mFlashRDPStatus = RDPState.Redirecting;
        this.invalidatePage();
        return false;
    },

    rdpDisconnected: function(flashObj)
    {
        console.log("vboxTabWidget::rdpDisconnected");
        this.mFlashRDPStatus = RDPState.Disconnected;
        this.invalidatePage();
        return false;
    },

    rdpHandleConnect: function()
    {
        var rc;
        if (this.mFlashRDPStatus == RDPState.Disconnected)
        {
            this.mFlashRDPStatus = RDPState.Connecting;
            this.invalidatePage();
            return this.rdpConnect();
        }
        else if (this.mFlashRDPStatus == RDPState.Connected)
        {
            this.mFlashRDPStatus = RDPState.Disconnecting;
            this.invalidatePage();
            return this.rdpDisconnect();
        }
        return false;
    },

    rdpNotFound: function(request, textStatus, errorThrown)
    {
        this.mFlashRDPStatus = RDPState.NotFound;
        this.invalidatePage();
    },

    rdpConnect: function()
    {
        console.log("vboxTabWidget::rdpConnect");

        if (this.mFlashRDPStatus >= RDPState.Connecting)
        {
            var curItem = this.mParent.curItem();
            var rdpServ = curItem.machine().getVRDPServer();
            var flash = RDPWebClient.getFlashById(RDPWebClient.FlashId);
            flash.setProperty("serverAddress", rdpServ.getNetAddress());

            console.log("vboxTabWidget::rdpConnect: Connecting to %s:%d (auth type=%d)",
                rdpServ.getNetAddress(), rdpServ.getPort(), rdpServ.getAuthType());

            if (rdpServ.getPort() > 0)
                flash.setProperty("serverPort", rdpServ.getPort());

            if (rdpServ.getAuthType() > 0)
            {
                var strUser = jQuery("#tab-rdp-auth-user-val").val();
                var strPwd = jQuery("#tab-rdp-auth-pwd-val").val();
                if (strUser != "")
                {
                    flash.setProperty("logonUsername", strUser);
                    flash.setProperty("logonPassword", strPwd);
                }
            }

            /* Set initial size. */
            this.rdpResize();
            flash.connect();
        }

        return false;
    },

    rdpDisconnect: function()
    {
        console.log("vboxTabWidget::rdpDisconnect");
        if (this.mFlashRDPStatus == RDPState.Disconnecting)
        {
            var flash = RDPWebClient.getFlashById(RDPWebClient.FlashId);
            flash.disconnect();
        }

        return false;
    },

    rdpResize: function()
    {
        var flash = RDPWebClient.getFlashById(RDPWebClient.FlashId);
        var r = jQuery("#FlashRDP");
        if (flash && r)
        {
            flash.setProperty("displayWidth", r.width());
            flash.setProperty("displayHeight", r.height());
        }
    },

    selectionChanged: function()
    {
        console.log("vboxTabWidget::selectionChanged: curTab = %s", this.mCurTab);
        this.invalidatePage(this.mCurTab);
    }
});
