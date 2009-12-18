
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
        /* bind the static toolbar buttons */
        jQuery("#toolbar-button-new").bind("click", this.buttonClicked);
        jQuery("#toolbar-button-new").qtip({ content: 'Create new virtual machine' });

        jQuery("#toolbar-button-logout").bind("click", this.buttonClicked);
        jQuery("#toolbar-button-logout").qtip({
            content: 'Logout and return to the login page',
            position: {
                corner: {
                    target: 'bottomLeft',
                    tooltip: 'topRight'
                }
            }
        });
    },

    setParent: function(parent)
    {
        this.mParent = parent;
    },

    invalidate: function()
    {
        jQuery("#toolbar-username-span").text(vbGlobal.mVirtualBox.getUserName());
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
                vboxDialogs.showNewVMWizard();
                break;

            case "toolbar-button-settings":
                log("Change VM settings not implemented!");
                break;

            case "toolbar-button-start-pause":
                if (state == MachineState.Running)
                    vbGlobal.mVirtualBox.pauseVM(id);
                else if (state == MachineState.Paused)
                    vbGlobal.mVirtualBox.resumeVM(id);
                else
                    vbGlobal.mVirtualBox.startVM(id);
                break;

            case "toolbar-button-stop-discard":
                if (state == MachineState.Running ||
                    state == MachineState.Paused)
                {
                    vboxDialogs.showPowerOffDialog();
                }
                else if (state == MachineState.Saved)
                {
                    log("Discard VM not implemented!");
                }
                break;

            case "toolbar-button-logout":
                vbGlobal.virtualBox().logout();
                break;

            default:
                log("vboxVMToolbar::buttonClicked: unknown source ID: " + event.target.id);
        }
    },

    selectionChanged: function()
    {
        var curItem = this.mParent.curItem();

        if (curItem == undefined)
        {
            log("vboxVMToolbar::invalidatePage: Current item is undefined.");
            return;
        }

        var state = curItem.state();

        /* settings can only be changed for powered off and aborted VMs */
        if (state == MachineState.PoweredOff ||
            state == MachineState.Aborted)
        {
            jQuery("#toolbar-button-vm-settings-span").html('<img id="toolbar-button-settings" src="/images/vbox/vm_settings_32px.png" alt=""/>');
            jQuery("#toolbar-button-settings").qtip({ content: 'Change settings of selected virtual machine' });
        }
        else
            jQuery("#toolbar-button-vm-settings-span").html('<img src="/images/vbox/vm_settings_disabled_32px.png" alt=""/>');

        /* powered off / aborted, paused and saved VMs can be started */
        if (state == MachineState.PoweredOff ||
            state == MachineState.Aborted ||
            state == MachineState.Saved ||
            state == MachineState.Paused)
        {
            jQuery("#toolbar-button-vm-start-span").html('<img id="toolbar-button-start-pause" src="/images/vbox/vm_start_32px.png" alt=""/">');
            jQuery("#toolbar-button-start-pause").qtip({ content: 'Start currently selected virtual machine' });
        }
        else if (state == MachineState.Running)
        {
            jQuery("#toolbar-button-vm-start-span").html('<img id="toolbar-button-start-pause" src="/images/vbox/vm_pause_32px.png" alt=""/>');
            jQuery("#toolbar-button-start-pause").qtip({ content: 'Pause the currently selected virtual machine' });
        }
        else
            jQuery("#toolbar-button-vm-start-span").html('<img src="/images/vbox/vm_start_disabled_32px.png" alt=""/>');

        /* saved VMs can be discarded */
        if (state == MachineState.Saved)
        {
            jQuery("#toolbar-button-vm-stop-span").html('<img id="toolbar-button-stop-discard" src="/images/vbox/vm_discard_32px.png" alt=""/>');
            jQuery("#toolbar-button-stop-discard").qtip({ content: 'Discard the saved state of the currently selected virtual machine' });
        }
        else if (state == MachineState.Running ||
                 state == MachineState.Paused)
        {
            jQuery("#toolbar-button-vm-stop-span").html('<img id="toolbar-button-stop-discard" src="/images/vbox/vm_poweroff_32px.png" alt=""/>');
            jQuery("#toolbar-button-stop-discard").qtip({ content: 'Power down the currently selected virtual machine' });
        }
        else
            jQuery("#toolbar-button-vm-stop-span").html('<img src="/images/vbox/vm_poweroff_disabled_32px.png" alt=""/>');

        jQuery("#toolbar-button-settings").bind("click", this.buttonClicked);
        jQuery("#toolbar-button-start-pause").bind("click", this.buttonClicked);
        jQuery("#toolbar-button-stop-discard").bind("click", this.buttonClicked);
    }
});
