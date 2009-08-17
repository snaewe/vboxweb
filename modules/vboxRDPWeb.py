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

import os
import sys
import zipfile

if sys.version_info < (3, 0):
    import urllib
    url_open = urllib.urlopen
else:
    import urllib.request
    import urllib.error
    url_open = urllib2.urlopen

def getRemoteVersion(url = None, proxies = None):
    fVersion = -1
    try:
        fhFileVer = url_open(url + "LATEST.TXT", None, proxies)
        strLine = fhFileVer.readline().rstrip("\n")
        fVersion = float(strLine)

    except Exception, e:
        print e

    finally:
        if fhFileVer <> None:
            fhFileVer.close()

    return fVersion

def downloadCallback(blocks, blockSize, size):
    percentage = (blockSize * blocks * 100) / size
    if percentage > 100:
        percentage = 100
    print "Status: %d%%" % (percentage)

def download(url = None, dest = None, proxies = None):
    try:
        bDownloaded = False
        urllib.urlretrieve(url, dest, downloadCallback)
        bDownloaded = True

    except Exception, e:
        print e

    finally:

        return bDownloaded

def extract(file, dest):
    # Extract from ZIP
    fhFileLocal = zipfile.ZipFile(file, "r")

    if fhFileLocal.testzip() <> None:
        raise IOError("File is corrupted!")
    if fhFileLocal is None:
        raise IOError("Could not decompress file!")

    for i, name in enumerate(fhFileLocal.namelist()):
        print "Extracting %s" % name
        if not name.endswith('/'):
            outfile = open(os.path.join(dest, name), 'wb')
            outfile.write(fhFileLocal.read(name))
            outfile.flush()
            outfile.close()

    fhFileLocal.close()

def checkForUpdate(url = None, dest = None, proxies = None, forceUpdate = False):
    try:
        bUpdated = False
        if url is None or dest is None:
            raise ValueError("No download URL given!")
        if dest is None:
            raise ValueError("No destination URL given!")

        # Get latest version information
        print "Looking up latest version of Sun RDP Web Control (from %s) ..." %(url)
        fVersion = getRemoteVersion(url, proxies)
        print "Latest version is: ",fVersion

        # @todo Implement check of remotely retrieved fVersion to a local
        #       version to only get update if required (newer)
        bRDPInstalled = os.path.isfile(dest + "rdpweb.swf")
        if bRDPInstalled and (forceUpdate is False):
            return

        # Download the ZIP
        print "Downloading Sun RDP Web Control ..."
        rdpFile = "rdpweb_" + str(fVersion) + ".zip"
        download(url + rdpFile, dest + rdpFile)
        print "Download complete. Extracting ..."
        extract(dest + rdpFile, dest)

        # Clean up
        print "Cleaning up ..."
        os.remove(dest + rdpFile)
        os.rename(dest + "rdpweb_" + str(fVersion) + ".swf", dest + "rdpweb.swf")

        print "Installation successful."
        bUpdated = True

    except Exception, e:
        print e

    finally:
        return bUpdated