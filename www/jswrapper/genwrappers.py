#!/usr/bin/env python
#
# Copyright (C) 2009 Sun Microsystems, Inc.

# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:

# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

#
# Generate Javascript wrappers out of VirtualBox.xidl file,
# now just simple wrapper around xsltproc, in the future
# can do smarter pre- and post- processing, along with finding
# appropriate tools.
#

import os, sys
import subprocess

def process(xslt, xml, outdir):
    cmd = "xsltproc"
    file = os.path.join(outdir, "VirtualBox_Main.js")
    retval = subprocess.call([cmd, "-o", file, xslt, xml], 0, None, None, None, None)
    if not retval == 0:
        print "Error while processing XSLT! Return value:", retval
    else:
        print "Generation successful. Output is in:", file


def main(argv):
    basepath = os.path.dirname(os.path.abspath(__file__))
    out = os.path.abspath(os.path.join(basepath, "../static/js/"))
    if not os.path.isdir(out):
        os.mkdir(out)
    process(os.path.join(basepath, "genJsWrappers.xsl"), os.path.join(basepath, "VirtualBox.xidl"), out)

if __name__ == '__main__':
    main(sys.argv)
