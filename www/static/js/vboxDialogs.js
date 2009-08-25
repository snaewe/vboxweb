
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
    /*
     * This performs the initial setup work for the dialogs, like
     * loading the HTML file and inserting it into the DOM, configuring
     * the DIVs, etc. Called when the HTML loads.
     */
    initDialogs: function()
    {
        /* load the dialogs HTML file with a completion function */
        jQuery.get("/html/dialogs.html", function(data) {
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
        });
    },

    showNewVMWizard: function()
    {
        /** @todo go to the first page of the wizard (how?) */
        jQuery("#newvm-dialog").dialog("open");
    }

});
