
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

var vboxVMListItem = Class.create(
{
    initialize: function(vboxMachine)
    {
        this.mMachine = vboxMachine;
        this.mConnected = false;
        this.recache();
    },

    recache: function()
    {
        this.mAccessible = this.mMachine.getAccessible();
        if (this.mAccessible == true)
        {
            this.mName = this.mMachine.getName();
            this.mId = this.mMachine.getId();
            this.mState = this.mMachine.getState();
            this.mSessionState = this.mMachine.getSessionState();
            this.mOSTypeId = this.mMachine.getOSTypeId();
        }
        else
        {
            /** @todo */
        }
    },

    machine: function()
    {
        return this.mMachine;
    },

    name: function()
    {
        return this.mName;
    },

    osIcon: function()
    {
        return vbGlobal.vmGuestOSTypeIcon(this.mOSTypeId);
    },

    id: function()
    {
        return this.mId;
    },

    sessionStateName: function()
    {
    },

    sessionStateIcon: function()
    {
    },

    snapshotName: function()
    {
    },

    snapshotCount: function()
    {
    },

    toolTipText: function()
    {
    },

    accessible: function()
    {
        return this.mAccessible;
    },

    state: function()
    {
        return this.mState;
    },

    sessionState: function()
    {
        return this.mSessionState;
    },

    canSwitchTo: function()
    {
        return true;
    },

    switchTo: function()
    {
    },

    connected: function()
    {
        return this.mConnected;
    }
});

var vboxVMModel = Class.create(
{
    initialize: function(vboxVMListView)
    {
        this.mVMListView = vboxVMListView;
        this.mArrItems = new Array();
    },

    addItem: function(vboxVMListItem)
    {
        this.mArrItems[this.mArrItems.length] = vboxVMListItem;
    },

    clear: function()
    {
        this.mArrItems.clear();
    },

    getCount: function()
    {
        return this.mArrItems.length;
    },

    itemById: function(machineId)
    {
    },

    itemByRow: function(row)
    {
        return this.mArrItems[row];
    },

    indexById: function(machineId)
    {
    },

    rowById: function(machineId)
    {
    },

    sortByName: function()
    {
        this.mArrItems.sort(
            function(entry1, entry2)
            {
                return entry1.mName > entry2.mName ? 1 :
                    entry1.mName < entry2.mName ? -1 : 0;
            }
            );
    }
});

var vboxVMListView = Class.create(
{
    initialize: function()
    {
        this.mCurItem = undefined;
    },

    setModel: function(vboxVMModel)
    {
        this.mVMModel = vboxVMModel;
    },

    selectItemByRow: function(row)
    {
        this.mCurItem = this.mVMModel.itemByRow(row);
        return this.mCurItem;
    },

    setParent: function(parent)
    {
    },

    onResize: function()
    {
    },

    invalidate: function()
    {
        var numItems = this.mVMModel.getCount();
        var newItems = "";

        /* empty table */
        jQuery("#vmList").html("");
        for (var i = 0; i < numItems; i++)
        {
            /** @todo Needs cleanup! Maybe put this into a template? */
            var curItem = this.mVMModel.itemByRow(i);
            var newItemData = '';
            var newItem =
                '<tr class="vmlist-entry-row"><td>' +
                    '<table class="vmlist-entry-table" width="100%">'+
                        '<tr>'+
                            '<td>'+
                                '<img alt="" class="vmlist-entry-osicon" src="' + curItem.osIcon() + '"/>' +
                            '</td>'+
                            '<td width="100%" nowrap="nowrap" class="vmlist-entry-vmname">'+
                                '<b>' + curItem.name() + '</b><br/>' +
                                '<img alt="" class="vmlist-entry-stateicon" src="' + vbGlobal.vmStateIcon(curItem.state()) + '"/>&nbsp;' +
                                vbGlobal.vmStateDescription(curItem.state()) +
                            '</td>'+
                        '</tr>'+
                    '</table>'+
                '</td></tr>';
            jQuery("#vmList").append(newItem);
        }

        /* Select first item */
        /* @todo Save old selected item, create list (see above) and select the old
                 VM again (if still present). Otherwise set first entry. */
        jQuery("#vmList .vmlist-entry-row:first").toggleClass('ui-selected');

        /* (Re-)connect all handlers */
        jQuery('#vmList .vmlist-entry-row').
            mouseover(function()
            {
                jQuery(this).toggleClass('ui-state-hover');
            }).
            mouseout(function()
            {
                jQuery(this).toggleClass('ui-state-hover');
            }).
            click(function(event, ui)
            {
                jQuery(this).
                    toggleClass('ui-selected').
                    siblings().removeClass('ui-selected');

                vmListView.selectionChanged(event);
                vmTabView.selectionChanged();
                vmToolbar.selectionChanged();
            });
    },

    selectionChanged: function(event)
    {
        var curIndex = jQuery("#vmList .vmlist-entry-row").index(event.currentTarget);
        this.mCurItem = this.mVMModel.itemByRow(curIndex);
    },

    selectedItem: function()
    {
        return this.mCurItem;
    }
});
