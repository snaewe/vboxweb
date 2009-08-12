
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

var vboxVMToolbar = Class.create(
{
    initialize: function()
    {
        /* bind the static new VM toolbar button */
        jQuery("#toolbar-button-new").bind("click", this.buttonClicked);
    },

    setParent: function(parent)
    {
        this.mParent = parent;
    },

    invalidate: function()
    {
        this.selectionChanged();
    },

    buttonClicked: function(event)
    {
        var state = vmSelWnd.curItem().state();
        var id = vmSelWnd.curItem().id();

        /* where does it come from? */
        switch (event.target.id)
        {
            case "toolbar-button-new":
                vbGlobal.mVirtualBox.addMessage("New VM not implemented yet!");
                break;

            case "toolbar-button-settings":
                vbGlobal.mVirtualBox.addMessage("Change VM settings not implemented!");
                break;

            case "toolbar-button-start-pause":
                if (state == VMState.Running)
                    vbGlobal.mVirtualBox.pauseVM(id);
                else if (state == VMState.Paused)
                    vbGlobal.mVirtualBox.resumeVM(id);
                else
                    vbGlobal.mVirtualBox.startVM(id);
                break;

            case "toolbar-button-stop-discard":
                if (state == VMState.Running ||
                    state == VMState.Paused)
                {
                    vbGlobal.mVirtualBox.addMessage("Stop VM: here will be a dialog in da future!");
                }
                else if (state == VMState.Saved)
                {
                    vbGlobal.mVirtualBox.addMessage("Discard VM not implemented!");
                }
                break;

            default:
                console.log("vboxVMToolbar::buttonClicked: unknown source ID: " + event.target.id);
        }
    },

    selectionChanged: function()
    {
        var curItem = this.mParent.curItem();

        if (curItem == undefined)
        {
            console.log("vboxVMToolbar::invalidatePage: Current item is undefined.");
            return;
        }

        var state = curItem.state();

        /* settings can only be changed for powered off and aborted VMs */
        if (state == VMState.PoweredOff ||
            state == VMState.Aborted)
            jQuery("#toolbar-button-vm-settings-span").html('<img id="toolbar-button-settings" src="/images/vbox/vm_settings_32px.png" alt="VM settings"/>');
        else
            jQuery("#toolbar-button-vm-settings-span").html('<img src="/images/vbox/vm_settings_disabled_32px.png" alt=""/>');

        /* powered off / aborted, paused and saved VMs can be started */
        if (state == VMState.PoweredOff ||
            state == VMState.Aborted ||
            state == VMState.Saved ||
            state == VMState.Paused)
            jQuery("#toolbar-button-vm-start-span").html('<img id="toolbar-button-start-pause" src="/images/vbox/vm_start_32px.png" alt="Start VM"/">');
        else if (state == VMState.Running)
            jQuery("#toolbar-button-vm-start-span").html('<img id="toolbar-button-start-pause" src="/images/vbox/vm_pause_32px.png" alt="Pause VM"/>');
        else
            jQuery("#toolbar-button-vm-start-span").html('<img src="/images/vbox/vm_start_disabled_32px.png" alt=""/>');

        /* saved VMs can be discarded */
        if (state == VMState.Saved)
            jQuery("#toolbar-button-vm-stop-span").html('<img id="toolbar-button-stop-discard" src="/images/vbox/vm_discard_32px.png" alt="Discard saved state"/>');
        else if (state == VMState.Running ||
                 state == VMState.Paused)
            jQuery("#toolbar-button-vm-stop-span").html('<img id="toolbar-button-stop-discard" src="/images/vbox/vm_poweroff_32px.png" alt="Power off VM"/>');
        else
            jQuery("#toolbar-button-vm-stop-span").html('<img src="/images/vbox/vm_poweroff_disabled_32px.png" alt=""/>');

        jQuery("#toolbar-button-settings").bind("click", this.buttonClicked);
        jQuery("#toolbar-button-start-pause").bind("click", this.buttonClicked);
        jQuery("#toolbar-button-stop-discard").bind("click", this.buttonClicked);
    }
});
