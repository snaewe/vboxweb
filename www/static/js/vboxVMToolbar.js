
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
    },

    setParent: function(parent)
    {
        this.mParent = parent;
    },

    invalidate: function()
    {
        this.selectionChanged();
    },

    selectionChanged: function()
    {
        var curItem = this.mParent.curItem();

        if (curItem == undefined)
        {
            console.log("vboxVMToolbar::invalidatePage: Current item is undefined.");
            return false;
        }

        /* settings can only be changed for powered off and aborted VMs */
        if (curItem.state() == VMState.PoweredOff ||
            curItem.state() == VMState.Aborted)
            jQuery("#toolbar-button-vm-settings").html('<img src="/images/vbox/vm_settings_32px.png"/>');
        else
            jQuery("#toolbar-button-vm-settings").html('<img src="/images/vbox/vm_settings_disabled_32px.png"/>');

        /* powered off / aborted and saved VMs can be started */
        /** @todo when saved, start means "show" in the Qt GUI, we can go to the RDP console */
        if (curItem.state() == VMState.PoweredOff ||
            curItem.state() == VMState.Aborted ||
            curItem.state() == VMState.Saved)
            jQuery("#toolbar-button-vm-start").html('<img src="/images/vbox/vm_start_32px.png"/>');
        else
            jQuery("#toolbar-button-vm-start").html('<img src="/images/vbox/vm_start_disabled_32px.png"/>');

        /* saved VMs can be discarded */
        if (curItem.state() == VMState.Saved)
            jQuery("#toolbar-button-vm-discard").html('<img src="/images/vbox/vm_discard_32px.png"/>');
        else
            jQuery("#toolbar-button-vm-discard").html('<img src="/images/vbox/vm_discard_disabled_32px.png"/>');
    }
});
