
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

var vboxSelectorWnd = Class.create(
{
    initialize: function(vboxVMListView, vboxTabWidget, vboxVMToolbar)
    {
       this.mVMToolbar = vboxVMToolbar;
       this.mVMListView = vboxVMListView;
       this.mVMModel = new vboxVMModel(this.mVMListView);
       this.mTabWidget = vboxTabWidget;

       this.mVMToolbar.setParent(this);
       this.mVMListView.setParent(this);
       this.mVMListView.setModel(this.mVMModel);
       this.mTabWidget.setParent(this);
    },

    onResize: function()
    {
    },

    vmRefresh: function(machineId)
    {
        this.refreshVMItem(
            machineId,
            true /* aDetails */,
            true /* aRDP */,
            true /* aDescription */);
    },

    refreshVMList: function()
    {
        var vbox = vbGlobal.virtualBox();
        var numMachines = vbox.getMachineCount();

        this.mVMModel.clear();
        for (var i = 0; i < numMachines; i++)
        {
            var newItem = new vboxVMListItem(vbox.getMachineByIndex(i));
            this.mVMModel.addItem(newItem);
        }

        if (numMachines > 0)
        {
            /* we want the VMs to appear in alphabetic order */
            this.mVMModel.sortByName();
            /* Select first item in list. */
            this.mVMListView.selectItemByRow(0);
            this.invalidate();
        }
        else
        {
            /* Show dialog. */
        }
    },

    invalidate: function()
    {
        /* Refresh widgets. */
        this.mVMToolbar.invalidate();
        this.mVMListView.invalidate();
        this.mTabWidget.invalidate();

        /* Refresh globals. */
        jQuery(".cfg-server-address").text(vbGlobal.config().serverAddress());
    },

    /* Refresh a specific VM item in the list. */
    refreshVMItem: function(machineId, abDetails, aRDP, aDescription)
    {

    },

    curItem: function()
    {
        return this.mVMListView.selectedItem();
    }
});
