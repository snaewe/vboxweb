
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
        jQuery("#tab-details-vm-general-name-val").text(curItem.name());
        jQuery("#tab-details-vm-general-osname-val").text(vbGlobal.vmGuestOSTypeDescription(curItem.machine().getOSType()));

        jQuery("#tab-details-vm-system-ram-val").text(curItem.machine().getMemorySize() + tr(" MB"));
        jQuery("#tab-details-vm-system-cpu-val").text(curItem.machine().getCPUCount());
        jQuery("#tab-details-vm-system-bootorder-val").text(curItem.machine().getBootOrder());
        jQuery("#tab-details-vm-system-hwvirt-val").text(curItem.machine().getHWVirtExEnabled() ? tr("Enabled") : tr("Disabled"));
        jQuery("#tab-details-vm-system-nestedp-val").text(curItem.machine().getHWVirtExNestedPagingEnabled() ? tr("Enabled") : tr("Disabled"));

        jQuery("#tab-details-vm-display-videomem-val").text(curItem.machine().getVRAMSize() + tr(" MB"));
        jQuery("#tab-details-vm-display-3daccel-val").text(curItem.machine().getAccelerate3DEnabled() ? tr("Enabled") : tr("Disabled"));
        jQuery("#tab-details-vm-display-rdpport-val").text(curItem.machine().getVRDPServer().getPort());
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
                case 0: /* Not loaded */

                    rdpStatus = "Loading Console ...";
                    jQuery("#tab-rdp-sec-conn").hide();
                    break;

                case 1: /* Connecting ... */

                    rdpStatus = "Connecting To Console ...";
                    jQuery("#tab-rdp-sec-conn").hide();
                    break;

                case 2: /* Connected */

                    rdpStatus = "Connected.";
                    this.rdpInvalidateConnBtn("Disconnect", false);
                    jQuery("#tab-rdp-sec-conn").show();
                    break;

                case 3: /* Disconnecting ... */

                    rdpStatus = "Disconnecting From Console ...";
                    jQuery("#tab-rdp-sec-conn").hide();
                    break;

                case 4: /* Disconnected */

                    rdpStatus = "Not connected.";
                    this.rdpInvalidateConnBtn("Connect", false);
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

                case 5: /* Redirect */

                    rdpStatus = "Redirecting Connection ...";
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
        if (strDesc == "")
            strDesc = tr("This machine has no description.");
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
        this.mFlashRDPStatus = 4; /* Disconnected. */
        this.invalidatePage();
        return false;
    },

    rdpUnloaded: function(flashObj)
    {
        console.log("vboxTabWidget::rdpUnloaded");
        this.mFlashRDPStatus = 0; /* Not loaded. */
        this.invalidatePage();
        return false;
    },

    rdpConnected: function(flashObj)
    {
        console.log("vboxTabWidget::rdpConnected");
        this.mFlashRDPStatus = 2; /* Connected. */
        this.invalidatePage();
        return false;
    },

    rdpRedirect: function(flashObj)
    {
        console.log("vboxTabWidget::rdpRedirect");
        this.mFlashRDPStatus = 5; /* Redirect. */
        this.invalidatePage();
        return false;
    },

    rdpDisconnected: function(flashObj)
    {
        console.log("vboxTabWidget::rdpDisconnected");
        this.mFlashRDPStatus = 4; /* Redirect. */
        this.invalidatePage();
        return false;
    },

    rdpHandleConnect: function()
    {
        var rc;
        if (this.mFlashRDPStatus == 4) /* Disconnected. */
        {
            this.mFlashRDPStatus = 1;
            this.invalidatePage();
            return this.rdpConnect();
        }
        else if (this.mFlashRDPStatus == 2) /* Connected. */
        {
            this.mFlashRDPStatus = 3;
            this.invalidatePage();
            return this.rdpDisconnect();
        }
        return false;
    },

    rdpConnect: function()
    {
        console.log("vboxTabWidget::rdpConnect");

        if (this.mFlashRDPStatus > 0)
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
        if (this.mFlashRDPStatus == 3)
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
