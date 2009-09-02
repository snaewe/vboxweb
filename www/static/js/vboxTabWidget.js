
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
    Disconnecting: 2,
    Connecting: 3,
    Disconnected: 4,
    Connected: 5,
    Redirecting: 6
};

var vboxTabWidget = Class.create(
{
    initialize: function()
    {
        this.mCurTab = "tabs-center-details";
        this.mFlashRDPStatus = RDPState.Unloaded;
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
            jQuery(".tab-sections").show(); /* Show all sections by default. */
            return this.invalidatePage(this.mCurTab);
        }
        else return false;
    },

    onResize: function(eventObject)
    {
        if (this.mFlashRDPStatus > RDPState.Unloaded)
        {
            log("vboxTabWidget::onResize: mFlashRDPStatus = %d", this.mFlashRDPStatus);
            var bRenewConn = false;
            if (this.mFlashRDPStatus >= RDPState.Connected)
                bRenewConn = true;

            if (bRenewConn)
                this.rdpHandleConnect();
            this.rdpResize();
            if (bRenewConn)
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
            log("vboxTabWidget::invalidatePage: Current item is undefined.");
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
                log("vboxTabWidget::invalidatePage: Invalid page name: %s", curId);
                return false;
        }

        return true;
    },

    invalidatePageDetails: function(curItem, pageSelected)
    {
        var mach = curItem.machine();
        var bootOrder = mach.jsonObject.bootOrder; /* A bit hacky, find a better way later! */
        var strBootOrder = vbGlobal.deviceType(bootOrder[0])
        for (i=1; i<bootOrder.length; i++)
        {
            if (bootOrder[i] > 0)
                strBootOrder = strBootOrder + ", " + vbGlobal.deviceType(bootOrder[i]);
        }

        var vrdpServer = new vboxIVRDPServerImpl(mach.getVRDPServer());
        var guestOSType = vbGlobal.virtualBox().getGuestOSTypeById(mach.getOSTypeId());
        var hardDiskAttachments = mach.getHardDiskAttachments();

        jQuery("#tab-details-vm-general-name-val").text(curItem.name());
        jQuery("#tab-details-vm-general-osname-val").text(guestOSType.getDescription());

        jQuery("#tab-details-vm-system-ram-val").text(mach.getMemorySize() + tr(" MB"));
        jQuery("#tab-details-vm-system-cpu-val").text(mach.getCPUCount());
        jQuery("#tab-details-vm-system-bootorder-val").text(strBootOrder);
        jQuery("#tab-details-vm-system-hwvirt-val").text(mach.getHWVirtExEnabled() ? tr("Enabled") : tr("Disabled"));
        jQuery("#tab-details-vm-system-nestedp-val").text(mach.getHWVirtExNestedPagingEnabled() ? tr("Enabled") : tr("Disabled"));

        jQuery("#tab-details-vm-display-videomem-val").text(mach.getVRAMSize() + tr(" MB"));
        jQuery("#tab-details-vm-display-3daccel-val").text(mach.getAccelerate3DEnabled() ? tr("Enabled") : tr("Disabled"));
        if (vrdpServer.getEnabled())
            jQuery("#tab-details-vm-display-rdpport-val").text(tr("Enabled") + ", " + tr("Port ") + vrdpServer.getPort());
        else
            jQuery("#tab-details-vm-display-rdpport-val").text(tr("Disabled") + " (" + tr("Port ") + vrdpServer.getPort() + ")");

        jQuery("li.harddisks-list-item").remove();
        for (i = 0; i < hardDiskAttachments.length; i++)
        {
            attachment = new vboxIHardDiskAttachmentImpl(hardDiskAttachments[i]);
            hardDisk = new vboxIHardDiskImpl(attachment.getHardDisk());
            if (attachment.getController() === "IDE")
            {
                port = (attachment.getPort() === 0) ? tr("Primary") : tr("Secondary");
                device = (attachment.getDevice() === 0) ? tr("Master") : tr("Slave");
            }
            else if (attachment.getController() === "SATA")
            {
                port = tr("Port ") + attachment.getPort();
                device = "";
            }
            else if (attachment.getController() === "SCSI")
            {
                port = tr("Port ") + attachment.getPort();
                device = "";
            }
            else
            {
                port = attachment.getPort();
                device = attachment.getDevice();
            }

            if (device != "")
                device = ' ' + device;
            strHardDisk = hardDisk.getName() + " (" + vbGlobal.hardDiskType(hardDisk.getType()) +
                          ", " + (hardDisk.getLogicalSize() / 1024) + " GB)";
            strListItem = '<div class="tab-details-vm-attribute">' +
                          attachment.getController() + " " + port + device + ":" +
                          '</div><div class="tab-details-vm-value">' + strHardDisk +
                          '</div><div style="clear: both"></div>';
            jQuery("#tab-details-vm-harddisks-list").append('<li class="harddisks-list-item">' + strListItem + "</li>");
        }

        if (hardDiskAttachments.length <= 0)
        {
            jQuery("#tab-details-vm-harddisks-list").
                append('<li class="harddisks-list-item">' + tr("No hard disks attached") + "</li>");
        }
    },

    invalidatePageRDP: function(curItem, pageSelected)
    {
        var rdpServ = curItem.machine().getVRDPServer();
        var rdpStatus = "";

        /* Do some sanity checks. */
        try
        {
            if (vbGlobal.flashPlayerInstalled() == false)
                throw(tr("Please install at least Flash Player 9 first!"));

            if (curItem.state() < 4)
                throw(tr("The remote view is not available because the virtual machine is not running"));

            switch (this.mFlashRDPStatus)
            {
                case RDPState.Unloaded:

                    rdpStatus = tr("Loading Console ...");
                    jQuery("#tab-rdp-sec-conn").hide();

                    // TODO this is not good. We need to enable the VRDP server
                    // but this is an asynchronous thing so we should have a
                    // callback handler and wait for the callback
                    vbGlobal.mVirtualBox.setVRDPState(curItem.machine().getId(), true);

                    /* Request header to see if SWF file is present. */
                    var bError = false;
                    jQuery.ajax({
                            url:"/static/rdpweb.swf",
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
                    if (rdpServ.authType != 0)
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
        var strDesc = curItem.machine().getDescription();
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

    /*
     * RDP Web Control event handlers.
     */

    rdpStatus: function(e)
    {
        //log("vboxTabWidget::rdpStatus: Success = %s, ID = %s, Ref = %s",
        //    e.success, e.id, e.ref);
        return false;
    },

    rdpLoaded: function(flashObj)
    {
        this.mFlashRDPStatus = RDPState.Disconnected;
        this.invalidatePage();
        return false;
    },

    rdpUnloaded: function(flashObj)
    {
        this.mFlashRDPStatus = RDPState.Unloaded;
        this.invalidatePage();
        return false;
    },

    rdpConnected: function(flashObj)
    {
        log("vboxTabWidget::rdpConnected");
        this.mFlashRDPStatus = RDPState.Connected;
        this.invalidatePage();
        return false;
    },

    rdpRedirect: function(flashObj)
    {
        log("vboxTabWidget::rdpRedirect");
        this.mFlashRDPStatus = RDPState.Redirecting;
        this.invalidatePage();
        return false;
    },

    rdpDisconnected: function(flashObj)
    {
        this.mFlashRDPStatus = RDPState.Disconnected;
        this.invalidatePage();
    },

    rdpHandleConnect: function()
    {
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
        if (this.mFlashRDPStatus >= RDPState.Connecting)
        {
            var curItem = this.mParent.curItem();
            var rdpServ = curItem.machine().getVRDPServer();

            log("Establishing RDP connection to IP " + rdpServ.netAddress +
                " on port " + rdpServ.port + " for VM with ID " + curItem.id());

            var flash = RDPWebClient.getFlashById(RDPWebClient.FlashId);
            flash.setProperty("serverAddress", rdpServ.netAddress);

            if (rdpServ.port > 0)
                flash.setProperty("serverPort", rdpServ.port);

            if (rdpServ.authType > 0)
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
        /*
         * we accept calls to this function independent of the state
         * so that we can always disconnect, even when things get wrong
         */
        var flash = RDPWebClient.getFlashById(RDPWebClient.FlashId);
        if (flash)
            flash.disconnect();
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
        /* make sure the RDP connection gets terminated */
        this.rdpDisconnect();
        this.invalidatePage(this.mCurTab);
    }
});
