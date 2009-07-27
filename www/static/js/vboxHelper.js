
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

function tr(a_String)
{
    /* Dummy. Nothing translated so far. */
    return a_String;
}

/* Fallback console for non-debugging environments. */
if (window.console == undefined /* add more check here when using "console.*" functions */)
{
        var names = ["log", "debug", "info", "warn", "error", "assert", "dir", "dirxml",
        "group", "groupEnd", "time", "timeEnd", "count", "trace", "profile", "profileEnd"];

        console = {};
        window.console = {};
        for (var i = 0; i < names.length; ++i)
        {
            console[names[i]] = function() {}
            window.console[names[i]] = function() {}
        }
}

/* Extend jQuery with context function to handle callbacks correctly.
   Example: error: jQuery.context(this).callback('rdpNotFound') */
jQuery.extend(
{
    context: function (context)
    {
        var co =
        {
            callback: function (method)
            {
                if (typeof method == 'string')
                    method = context[method];
                var cb = function () { method.apply(context, arguments); }
                return cb;
            }
        };
        return co;
    }
});