
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

var vboxHardDisk = Class.create(
{
    initialize: function()
    {
        this.mId = ""
        this.mName = "";
        this.mType = -1;
        this.mLogicalSize = 0;
    },

    loadSettingsJSON: function(jsonObject)
    {
        this.mId = jsonObject.id;
        this.mName = jsonObject.name;
        this.mType = jsonObject.type;
        this.mLogicalSize = jsonObject.logicalSize;
    },

    /* Public attributes. */
    getId: function()
    {
        return this.mId;
    },

    getName: function()
    {
        return this.mName;
    },

    getType: function()
    {
        return this.mType;
    },

    getLogicalSize: function()
    {
        return this.mLogicalSize;
    },

    getLogicalSizeGB: function()
    {
        return this.mLogicalSize / 1024;
    }
});
