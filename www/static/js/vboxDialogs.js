
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

var vboxDialogs = Class.create(
{
    showPowerOffDialog: function()
    {
        /* already loaded? Then show */
        if (jQuery("#poweroff-dialog").length)
        {
            jQuery('#poweroff-dialog').dialog('open');
            return;
        }
        /* load the dialog */
        jQuery.get("dialog?dialogid=poweroff-dialog", function(data) {
            /* append the loaded HTML to the body section */
            jQuery("body").append(data);

            jQuery(function() {
                jQuery("#poweroff-dialog").dialog({
                    bgiframe: true,
                    resizable: false,
                    height: 200,
                    modal: true,
                    autoOpen: false,
                    overlay: {
                        backgroundColor: '#000',
                        opacity: 0.5
                    },
                    buttons: {
                        Ok: function() {
                            var poweroffMethod = jQuery("input[@name='poweroff-dialog-selection']:checked").val();
                            if (poweroffMethod == "savestate")
                                vbGlobal.mVirtualBox.savestateVM(vmSelWnd.curItem().id());
                            else if (poweroffMethod == "acpipoweroff")
                                vbGlobal.mVirtualBox.acpipoweroffVM(vmSelWnd.curItem().id());
                            else
                                vbGlobal.mVirtualBox.poweroffVM(vmSelWnd.curItem().id());
                            jQuery(this).dialog('close');
                        },
                        Cancel: function() {
                            jQuery(this).dialog('close');
                        }
                    }
                });
            });
            jQuery('#poweroff-dialog').dialog('open');
        });
    },

    showNewVMWizard: function()
    {
        /* already loaded? Then show */
        if (jQuery("#newvm-dialog").length)
        {
            selectOSType("WindowsXP");
            jQuery("#newvm-form").formwizard("reset");
            jQuery('#newvm-dialog').dialog('open');
            return;
        }
        /* load the dialog */
        jQuery.get("dialog?dialogid=newvm-dialog", function(data) {
            /* append the loaded HTML to the body section */
            jQuery("body").append(data);

            jQuery(function(){
                jQuery("#newvmdialog-ostype").buildMenu(
                {
                    menuWidth:200,
                    openOnRight:false,
                    menuSelector: ".menuContainer",
                    containment:"wrapper",
                    iconPath:"/images/vbox/",
                    hasImages:true,
                    fadeInTime:100,
                    fadeOutTime:300,
                    adjustLeft:2,
                    minZindex:"auto",
                    adjustTop:10,
                    opacity:.95,
                    shadow:true,
                    closeOnMouseOut:true,
                    closeAfter:1000
                });
            });
            jQuery(function(){
                jQuery("#newvm-form").formwizard({
                    //form wizard settings
                    historyEnabled : true,
                    formPluginEnabled: true,
                    validationEnabled : true},
                {
                   //validation settings
                },
                {
                   // form plugin settings
                }
                );
            });
            jQuery(function() {
                jQuery("#newvm-dialog").dialog({
                    bgiframe: true,
                    resizable: false,
                    height: 360,
                    width: 550,
                    modal: true,
                    autoOpen: false,
                    overlay: {
                        backgroundColor: '#000',
                        opacity: 0.5
                    }
                });
            });

            /*
             * Create the OS type menu. We're doing this here and not at dialog
             * loading time for several reasons. First of all, the OS type list
             * might not have been loaded from the server yet and also this is a
             * potentially time consuming task. Later, we should load the whole
             * dialog not at startup time but when called for the first time.
             */
            selectOSType = function(osTypeId)
            {
                var guestOSType = vbGlobal.mVirtualBox.getGuestOSTypeById(osTypeId);
                jQuery("#ostype-selected").html(
                    "<img alt=\"\" width=\"20px\" align=\"top\" style=\"padding-right: 20px;\" src=\"" +
                    vbGlobal.vmGuestOSTypeIcon(osTypeId, false) + "\"/>" +
                    "<span id=\"ostype-selected-id\">" +
                    guestOSType.getDescription() +
                    "</span>"
                );
                /* set the recommended RAM size */
                /* it's kind of dirty to do all this slider business here, think of a better solution! */
                jQuery("#newvm-recommendedram").text(guestOSType.getRecommendedRAM());
                jQuery("#newvm-ramsize").val(guestOSType.getRecommendedRAM());
                /** TODO: get max ram from server */
                jQuery("#newvm-maxram").text("4096");
                jQuery("#newvm-ramslider").slider({
                    max: 4096,
                    step: 4,
                    value: guestOSType.getRecommendedRAM(),
                    slide: function(event, ui) {
                        jQuery("#newvm-ramsize").val(ui.value);
                    }
                });
                jQuery("#newvm-ramslider").slider('option', 'value', guestOSType.getRecommendedRAM());
                jQuery("#newvm-ramsize").keyup(function() {
                    jQuery("#newvm-ramslider").slider('option', 'value', jQuery(this).val());
                });
            }

            var osTypes = vbGlobal.mVirtualBox.mArrGuestOSTypes;
            for (var i = 0; i < osTypes.length; i++)
            {
                /* check if the menu for the family exists */
                var submenu = jQuery("#ostype-submenu-" + osTypes[i].getFamilyId());
                if (submenu.length == 0)
                {
                    /* create link to the submenu */
                    jQuery("#osfamilies-span").append(
                        "<a class=\"{menu: 'ostype-submenu-" + osTypes[i].getFamilyId() + "', " +
                        "img: 'vm_start_32px.png'}\">" + osTypes[i].getFamilyId() + "</a>"
                    );
                    /* create the submenu */
                    jQuery("#ostype_submenues").append(
                        "<div id=\"ostype-submenu-" + osTypes[i].getFamilyId() + "\" class=\"menu\">" +
                        "<span id=\"osfamily-" + osTypes[i].getFamilyId() + "-span\"></span>" +
                        "</div>"
                    );
                }
                /* now add the OS entry to the right submenu, check if present to multiple calls to this method */
                if (jQuery("#ostype-entry-" + osTypes[i].getId()).length == 0)
                    jQuery("#osfamily-" + osTypes[i].getFamilyId() + "-span").append(
                        "<a id=\"ostype-entry-" + osTypes[i].getId() + "\" class=\"{action: 'selectOSType(\\'" + osTypes[i].getId() + "\\')', img: '" +
                        vbGlobal.vmGuestOSTypeIcon(osTypes[i].getId(), true) +
                        "'}\">" + osTypes[i].getDescription() + "</a>"
                    );
            }
            /* start with Windows XP as the default */
            selectOSType("WindowsXP");
            jQuery("#newvm-form").formwizard("reset");
            jQuery("#newvm-dialog").dialog("open");
        });
    }

});
