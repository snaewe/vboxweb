
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

/* JS helpers for the Flash RDP client. */
var RDPWebClient = {
    init: function (FlashId)
    {
        RDPWebClient.FlashId = FlashId;

        var flash = RDPWebClient.getFlashById(RDPWebClient.FlashId);
            
        if (window.addEventListener)
        {
            /* Mozilla */
            window.addEventListener("contextmenu", function(event) { return RDPWebClient.MozillaContextMenu(event); }, true);
            window.addEventListener("mousedown", function(event) { return RDPWebClient.MozillaMouse(event, true); }, true);
            window.addEventListener("mouseup", function(event) { return RDPWebClient.MozillaMouse(event, false); }, true);
            flash.addEventListener("mouseout", function(event) { return RDPWebClient.MouseOut(); }, true);
        }
        else
        {
            if (flash)
            {
                document.oncontextmenu = function() { return RDPWebClient.IEContextMenu(); }
                flash.parentNode.onmousedown = function() { return RDPWebClient.IEMouse(true); }
                flash.parentNode.onmouseup = function() { return RDPWebClient.IEMouse(false); }
                flash.onmouseout=function() {return RDPWebClient.MouseOut(); }
            }
        }
    },
    MouseOut: function()
    {
        RDPWebClient.callMouseOut();
        return true;
    },
    IECancelEvent: function()
    {
        window.event.returnValue = false;
        window.event.cancelBubble = true;
        return false;
    },
    IEContextMenu: function()
    {
        if (window.event && window.event.srcElement.id == RDPWebClient.FlashId)
        {
            return RDPWebClient.IECancelEvent();
        }
    },
    IEMouse: function(fMouseDown)
    {
        if (window.event && window.event.srcElement.id == RDPWebClient.FlashId)
        {
            if (window.event.button == 2)
            {
                if (fMouseDown == true)
                {
                    RDPWebClient.getFlashById(RDPWebClient.FlashId).parentNode.setCapture();
                    RDPWebClient.callRightMouseDown();
                }
                else
                {
                    RDPWebClient.callRightMouseUp();
                    RDPWebClient.getFlashById(RDPWebClient.FlashId).parentNode.releaseCapture();
                }
                return RDPWebClient.IECancelEvent();
            }
        }
    },
    MozillaCancelEvent: function(event)
    {
        if (event)
        {
            if (event.preventBubble) event.preventBubble();
            if (event.preventCapture) event.preventCapture();
            if (event.preventDefault) event.preventDefault();
            if (event.stopPropagation) event.stopPropagation();
        }
    },
    MozillaContextMenu: function(event)
    {
        if (event.target.id == RDPWebClient.FlashId)
        {
            RDPWebClient.MozillaCancelEvent(event);
        }
    },
    MozillaMouse: function(event, fMouseDown)
    {
        if (event.target.id == RDPWebClient.FlashId)
        {
            if (event.button == 2)
            {
                if (fMouseDown)
                {
                    RDPWebClient.callRightMouseDown();
                }
                else
                {
                    RDPWebClient.callRightMouseUp();
                }
                RDPWebClient.MozillaCancelEvent(event);
            }
        }
    },
    callRightMouseDown: function()
    {
        var flash = RDPWebClient.getFlashById(RDPWebClient.FlashId);
        if (flash && flash.rightMouseDown)
        {
            try
            {
                flash.rightMouseDown();
            }
            catch (e) {}; /* Hack for IE, which calls the Flash method but then throws the exception. */
        }
    },
    callRightMouseUp: function()
    {
        var flash = RDPWebClient.getFlashById(RDPWebClient.FlashId);
        if (flash && flash.rightMouseUp)
        {
            try
            {
               flash.rightMouseUp();
            }
            catch (e) {}; /* Hack for IE, which calls the Flash method but then throws the exception. */
        }
    },
    callMouseOut: function()
    {
        var flash = RDPWebClient.getFlashById(RDPWebClient.FlashId);
        if (flash && flash.mouseOut)
        {
            try
            {
               flash.mouseOut();
            }
            catch (e) {}; /* Hack for IE, which calls the Flash method but then throws the exception. */
        }
    },
    getFlashById: function(flashId)
    {
        if (document.embeds && document.embeds[flashId])
            return document.embeds[flashId];

        return document.getElementById(flashId);
    },
    resizeContainer: function(containerId, width, height, reason)
    {
        var e = document.getElementById(containerId);
        if (e)
        {
            e.style.width=width + "pt";
            e.style.height=height +  "pt";
        }
    }
}
