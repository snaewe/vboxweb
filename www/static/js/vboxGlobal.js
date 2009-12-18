
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

MachineState =
{
    PoweredOff: 1,
    Saved: 2,
    Teleported: 3,
    Aborted: 4,
    Running: 5,
    Paused: 6,
    Stuck: 7,
    Teleporting: 8,
    LiveSnapshotting: 9,
    Starting: 10,
    Stopping: 11,
    Saving: 12,
    Restoring: 13,
    TeleportingPausedVM: 14,
    TeleportingIn: 15,
    RestoringSnapshot: 16,
    DeletingSnapshot: 17,
    SettingUp: 18,
    FirstOnline: 5,
    LastOnline: 13,
	FirstTransient: 8,
	LastTransient: 18
};

var vboxGlobal = Class.create(
{
    initialize: function()
    {
        this.mVirtualBox = new vboxVirtualBox();
        this.mConfig = new vboxConfig();
        this.mFlashPlayerVer = swfobject.getFlashPlayerVersion();
    },

    setSelectorWnd: function(selWnd)
    {
        this.mWndSelector = selWnd;
    },

    virtualBox: function()
    {
        return this.mVirtualBox;
    },

    config: function()
    {
        return this.mConfig;
    },

    selectorWnd: function()
    {
        return this.mWndSelector;
    },

    flashPlayerVer: function ()
    {
        return this.mFlashPlayerVer;
    },

    flashPlayerInstalled: function ()
    {
        return (swfobject.hasFlashPlayerVersion("9.0.0")) ? true : false;
    },

    deviceType: function(device)
    {
        var strDevice = tr("Unknown");

        switch (device)
        {
            case 0: strDevice = tr("None"); break;
            case 1: strDevice = tr("Floppy"); break;
            case 2: strDevice = tr("CD/DVD-ROM"); break;
            case 3: strDevice = tr("Hard Disk"); break;
            case 4: strDevice = tr("Network"); break;
            case 5: strDevice = tr("USB"); break;
            case 6: strDevice = tr("Shared Folder"); break;

            default:
                break;
        }

        return strDevice;
    },

    machineStateIcon: function (state)
    {
        var strBasePath = "/images/vbox/";
        var strIcon = "state_powered_off_16px.png";
        var strNoIcon = "state_running_16px.png";

        switch (state)
        {
            case MachineState.PoweredOff: strIcon = "state_powered_off_16px.png"; break;
            case MachineState.Saved: strIcon = "state_saved_16px.png"; break;
            case MachineState.Teleported: strIcon = strNoIcon; break;
            case MachineState.Aborted:  strIcon = "state_aborted_16px.png"; break;
            case MachineState.Running: strIcon = "state_running_16px.png"; break;
            case MachineState.Paused: strIcon = "state_paused_16px.png"; break;
            case MachineState.Stuck: strIcon = "state_stuck_16px.png"; break;
            case MachineState.Teleporting: strIcon = strNoIcon; break;
            case MachineState.LiveSnapshotting: strIcon = strNoIcon; break;
            case MachineState.Starting: strIcon = strNoIcon; break;
            case MachineState.Stopping: strIcon = strNoIcon; break;
            case MachineState.Saving: strIcon = "state_discarding_16px.png"; break;
            case MachineState.Restoring: strIcon = "settings_16px.png"; break;
            case MachineState.TeleportingPausedVM: strIcon = strNoIcon; break;
            case MachineState.TeleportingIn: strIcon = strNoIcon; break;
            case MachineState.RestoringSnapshot: strIcon = strNoIcon; break;
            case MachineState.DeletingSnapshot: "discarding_16px.png"; break;
            case MachineState.SettingUp: strIcon = strNoIcon; break;
            default:
                break;
        }

        return strBasePath + strIcon;
    },

    machineStateDescription: function(state)
    {
        /** @todo use an array instead of this huge switch statement */
        var strState = tr("Unknown");
        switch(state)
        {
            case MachineState.PoweredOff:
                strState = tr("Powered Off");
                break;
            case MachineState.Saved:
                strState = tr("Saved");
                break;
            case MachineState.Teleported:
                strState = tr("Teleported");
                break;
            case MachineState.Aborted:
                strState = tr("Aborted");
                break;
            case MachineState.Running:
                strState = tr("Running");
                break;
            case MachineState.Paused:
                strState = tr("Paused");
                break;
            case MachineState.Stuck:
                strState = tr("Stuck");
                break;
            case MachineState.Teleporting:
                strState = tr("Teleporting");
                break;
            case MachineState.LiveSnapshotting:
                strState = tr("LiveSnapshotting");
                break;
            case MachineState.Starting:
                strState = tr("Starting");
                break;
            case MachineState.Stopping:
                strState = tr("Stopping");
                break;
            case MachineState.Saving:
                strState = tr("Saving");
                break;
            case MachineState.Restoring:
                strState = tr("Restoring");
                break;
            case MachineState.TeleportingPausedVM:
                strState = tr("Teleporting Paused");
                break;
            case MachineState.TeleportingIn:
                strState = tr("Teleporting In");
                break;
            case MachineState.RestoringSnapshot:
                strState = tr("Restoring Snapshot");
                break;
            case MachineState.DeletingSnapshot:
                strState = tr("Deleting Snapshot");
                break;
            case MachineState.SettingUp:
                strState = tr("Setting Up");
                break;
            default:
                break;
        }
        return strState;
    },

    vmSessionStateDescription: function(sessionState)
    {
        var strState = tr("Unknown");
        switch(sessionState)
        {
            case 1:
                strState = tr("Closed");
                break;

            case 2:
                strState = tr("Open");
                break;

            case 3:
                strState = tr("Spawning");
                break;

            case 4:
                strState = tr("Closing");
                break;

            default:
                break;
        }
        return strState;
    },

    vmGuestOSTypeIcon: function (osTypeId, fRelative)
    {
        var strBasePath = "/images/vbox/";
        var strIcon = "os_linux_other.png";
        switch (osTypeId)
        {
            case "Other":           strIcon = "os_other.png"; break;
            case "DOS":             strIcon = "os_dos.png"; break;
            case "Netware":         strIcon = "os_netware.png"; break;
            case "L4":              strIcon = "os_l4.png"; break;
            case "Windows31":       strIcon = "os_win31.png"; break;
            case "Windows95":       strIcon = "os_win95.png"; break;
            case "Windows98":       strIcon = "os_win98.png"; break;
            case "WindowsMe":       strIcon = "os_winme.png"; break;
            case "WindowsNT4":      strIcon = "os_winnt4.png"; break;
            case "Windows2000":     strIcon = "os_win2k.png"; break;
            case "WindowsXP":       strIcon = "os_winxp.png"; break;
            case "WindowsXP_64":    strIcon = "os_winxp_64.png"; break;
            case "Windows2003":     strIcon = "os_win2k3.png"; break;
            case "Windows2003_64":  strIcon = "os_win2k3_64.png"; break;
            case "WindowsVista":    strIcon = "os_winvista.png"; break;
            case "WindowsVista_64": strIcon = "os_winvista_64.png"; break;
            case "Windows2008":     strIcon = "os_win2k8.png"; break;
            case "Windows2008_64":  strIcon = "os_win2k8_64.png"; break;
            case "Windows7":        strIcon = "os_win7.png"; break;
            case "Windows7_64":     strIcon = "os_win7_64.png"; break;
            case "WindowsNT":       strIcon = "os_win_other.png"; break;
            case "OS2Warp3":        strIcon = "os_os2warp3.png"; break;
            case "OS2Warp4":        strIcon = "os_os2warp4.png"; break;
            case "OS2Warp45":       strIcon = "os_os2warp45.png"; break;
            case "OS2eCS":          strIcon = "os_os2ecs.png"; break;
            case "OS2":             strIcon = "os_os2_other.png"; break;
            case "Linux22":         strIcon = "os_linux22.png"; break;
            case "Linux24":         strIcon = "os_linux24.png"; break;
            case "Linux24_64":      strIcon = "os_linux24_64.png"; break;
            case "Linux26":         strIcon = "os_linux26.png"; break;
            case "Linux26_64":      strIcon = "os_linux26_64.png"; break;
            case "ArchLinux":       strIcon = "os_archlinux.png"; break;
            case "ArchLinux_64":    strIcon = "os_archlinux_64.png"; break;
            case "Debian":          strIcon = "os_debian.png"; break;
            case "Debian_64":       strIcon = "os_debian_64.png"; break;
            case "OpenSUSE":        strIcon = "os_opensuse.png"; break;
            case "OpenSUSE_64":     strIcon = "os_opensuse_64.png"; break;
            case "Fedora":          strIcon = "os_fedora.png"; break;
            case "Fedora_64":       strIcon = "os_fedora_64.png"; break;
            case "Gentoo":          strIcon = "os_gentoo.png"; break;
            case "Gentoo_64":       strIcon = "os_gentoo_64.png"; break;
            case "Mandriva":        strIcon = "os_mandriva.png"; break;
            case "Mandriva_64":     strIcon = "os_mandriva_64.png"; break;
            case "RedHat":          strIcon = "os_redhat.png"; break;
            case "RedHat_64":       strIcon = "os_redhat_64.png"; break;
            case "Turbolinux":      strIcon = "os_turbolinux.png"; break;
            case "Ubuntu":          strIcon = "os_ubuntu.png"; break;
            case "Ubuntu_64":       strIcon = "os_ubuntu_64.png"; break;
            case "Xandros":         strIcon = "os_xandros.png"; break;
            case "Xandros_64":      strIcon = "os_xandros_64.png"; break;
            case "Linux":           strIcon = "os_linux_other.png"; break;
            case "FreeBSD":         strIcon = "os_freebsd.png"; break;
            case "FreeBSD_64":      strIcon = "os_freebsd_64.png"; break;
            case "OpenBSD":         strIcon = "os_openbsd.png"; break;
            case "OpenBSD_64":      strIcon = "os_openbsd_64.png"; break;
            case "NetBSD":          strIcon = "os_netbsd.png"; break;
            case "NetBSD_64":       strIcon = "os_netbsd_64.png"; break;
            case "Solaris":         strIcon = "os_solaris.png"; break;
            case "Solaris_64":      strIcon = "os_solaris_64.png"; break;
            case "OpenSolaris":     strIcon = "os_opensolaris.png"; break;
            case "OpenSolaris_64":  strIcon = "os_opensolaris_64.png"; break;
            case "QNX":             strIcon = "os_qnx.png"; break;

            default:
                break;
        }
        if (fRelative == true)
            return strIcon;
        else
            return strBasePath + strIcon;
    },

    hardDiskType: function (type)
    {
        var strType = ("Unkown Hard Disk Type");
        switch (type)
        {
            case 0: strType = tr("Normal"); break;
            case 1: strType = tr("Immutable"); break;
            case 2: strType = tr("Writethrough"); break;

            default: break;
        }
        return strType;
    },

    storageBusName: function (storageBus)
    {
        var strName = tr("Unkown Bus Name");
        switch (controllerType)
        {
            case 1: strName = tr("IDE"); break;
            case 2: strName = tr("SATA"); break;
            case 3: strName = tr("SCSI"); break;
            case 4: strName = tr("Floppy"); break;

            default: break;
        }
        return strName;
    },

    storageBusPortName: function (storageBus, deviceSlot, portNum)
    {
        var strName = tr("Invalid Bus Port Name");
        switch (storageBus)
        {
            case 1: /* IDE */
                switch (deviceSlot)
                {
                    case 0: strName = tr("Primary"); break;
                    case 1: strName = tr("Secondary"); break;
                }
                strName += " ";
                switch (portNum)
                {
                    case 0: strName += tr("Master"); break;
                    case 1: strName += tr("Slave"); break;
                }
                break;

            case 2: /* SATA */
                strName = "Port " + portNum;
                break;
            case 3: /* SCSI */
                strName = "ID " + portNum;
                break;
            case 4: /* Floppy */
                strName = "Floppy Device "  + portNum;
                break;

            default: break;
        }
        return strName;
    },

    storageControllerName: function (controllerType)
    {
        var strName = tr("Unkown Storage Controller");
        switch (controllerType)
        {
            case 1: strName = tr("LsiLogic"); break;
            case 2: strName = tr("BusLogic"); break;
            case 3: strName = tr("IntelAhci"); break;
            case 4: strName = tr("PIIX3"); break;
            case 5: strName = tr("PIIX4"); break;
            case 6: strName = tr("ICH6"); break;
            case 7: strName = tr("I82078"); break;

            default: break;
        }
        return strName;
    }
});
