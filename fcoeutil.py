# Copyright (c) 2015 Citrix Systems, Inc. All use and distribution of this
# copyrighted material is governed by and subject to terms and conditions
# as licensed by Citrix Systems, Inc. All other rights reserved.
# Xen, XenSource and XenEnterprise are either registered trademarks or
# trademarks of Citrix Systems, Inc. in the United States and/or other 
# countries.

###
#
# FCoE util
#
###

import re, sys
import os.path
import constants
import util
import netutil
from util import dev_null
import xelogging
from disktools import *
import time

def start_fcoe(interfaces):
    ''' startFCoE takes dictonary of {interface: dcb config}
        dcb config could be either 'on' or 'off'

        and returns a dictonary {interface:result}
        result could be either OK or error returned from fipvlan
    '''

    '''
    modprobe sg (scsi generic)
    modprobe bnx2fc if required.
    '''

    result = {}

    util.runCmd2(['/sbin/modprobe', 'sg'])
    util.runCmd2(['/sbin/modprobe', 'fcoe'])

    for interface, dcb in interfaces.iteritems():
        if netutil.getDriver(interface) == 'bnx2x':
            # This will do modprobe multiple times
            util.runCmd2(['/sbin/modprobe', 'bnx2fc'])
        if dcb == 'off':
            util.runCmd2(['/sbin/lldptool', '-i', interface, '-L',
                          'adminStatus=disabled'])
        else:
            util.runCmd2(['/sbin/dcbtool', 'sc', interface, 'dcb', 'on'])
            util.runCmd2(['/sbin/dcbtool', 'sc', interface, 'app:fcoe',
                          'e:1'])
            util.runCmd2(['/sbin/dcbtool', 'sc', interface, 'pfc',
                          'e:1', 'a:1', 'w:1'])


    util.runCmd2(['/sbin/lldpad', '-d'])

    for interface in interfaces:
        xelogging.log("Starting fipvlan on %s"% interface)

        rc, out, err = util.runCmd2(['/usr/sbin/fipvlan',
                                     '-s', '-c', interface], True, True)
        if rc != 0:
            result[interface] = err
        else:
            result[interface] = "OK"

    xelogging.log(result)

    # wait for atleast on block device to appear
    for interface, status in result.iteritems():
        if status == 'OK':
            wait_for_fcoe_disks(interface)

    util.runCmd2(util.udevsettleCmd())

    return result

def get_dcb_capable_ifaces(check_lun):
    ''' Return all dcb capable interfaces.
        if checkLun is True, then this routine
        will check if there are any LUNs associated
        with an interface and will exclued them
        from the dictonary that is returned.
    '''

    dcb_nics = {}
    nics = netutil.scanConfiguration()

    def get_dcb_capablity(interface):
        ''' checks if a NIC is dcb capable.
            If netdev for an interface has dcbnl_ops defined
            then this interface is deemed dcb capable.
            dcbtool gc ethX dcb will return Status = Successful if netdev 
            has dcbnl_ops defined.
        '''

        output = None
        rc, output, err = util.runCmd2(['dcbtool', 'gc', interface, 'dcb'],
                                        True, True)
        if rc != 0:
            return False
        if output is not None:
            outlist = output.split('\n')
            outstr = outlist[3]
            outdata = outstr.split(':')
            if "Successful" in outdata[1]:
                return True
            else:
                return False

    for nic, conf in nics.iteritems():
        if get_dcb_capablity(nic):
            if check_lun and len(get_luns_on_intf(nic)) > 0:
                continue
            if netutil.getDriver(nic) == 'bnx2x':
                # These nics are capable of doing dcb in hardware
                dcb_nics[nic] = False
            else:
                dcb_nics[nic] = True

    return dcb_nics

def wait_for_fcoe_disks(interface):
    ''' This routine will wait for atleast one device to appear in fcoeadm.
        Retries 10 times if the disk doesn't appear.
    '''

    retry = 10
    while retry > 0:
        if len(get_luns_on_intf(interface)) > 0:
            return 1
        time.sleep(1)
        retry -= 1

def get_interface_from_device(device):
    ''' this routing will return the ethernet interface assoicated
        with this block device.
        it should return the parent interface and
        not the slave vlan interface.
    '''
    fcoedisks = get_fcoe_luns()

    for eth, rports in fcoedisks.items():
        for rport, val in rports.items():
            for lun in val['luns'].values():
                if os.path.basename(lun['device']) == device:
                    return eth

    return None

def get_fcoe_vlans(interface):
    ''' This routine return fcoe vlans associated with an interface.
        returns the vlans as a list.
    '''

    vlans = []
    rc, out, err = util.runCmd2(['fcoeadm', '-f'], True, True)
    if rc != 0:
        return vlans

    for l in out.split('\n'):
        line = l.strip()

        if len(line) == 0 or ':' not in line:
            continue

        k, v = line.split(':', 1)
        key = k.strip()
        value = v.strip()

        if key == 'Interface':
            i, v = value.split('.', 1)
            iface = i.strip()

            if iface == interface:
                vlans.append(value)
    return vlans

lun_re = re.compile(r'(\d+)\s+(\S+)\s+(\S+ \S+)\s+(\d+)\s+(.+)')

def get_fcoe_luns():
    ''' returns a dictionary of fcoe luns
    '''

    d = {}
    rc, out, err = util.runCmd2(['fcoeadm', '-t'], True, True)
    if rc != 0:
        return d

    state = 'header'

    for l in out.split('\n'):
        line = l.lstrip()
        if len(line) == 0 or line.startswith('--') or line.startswith('PCI') or line.startswith('No'):
            continue

        if state == 'header':
            if ':' not in line:
                # LUN banner
                rport = header['OS Device Name']
                if iface not in d:
                    d[iface] = {}
                d[iface][rport] = header
                state = 'luns'
                continue

            k, v = line.split(':', 1)
            key = k.strip()
            value = v.strip()

            if key == 'Interface':
                iface = value
                header = {}
            else:
                header[key] = value
        else:
            # LUNs
            m = lun_re.match(line)
            if m:
                if 'luns' not in d[iface][rport]:
                    d[iface][rport]['luns'] = {}
                d[iface][rport]['luns'][m.group(1)] = {'device': m.group(2), 'capacity': m.group(3),
                                                       'bsize': m.group(4), 'description': m.group(5)}
            else:
                # New header, starts with Interface:
                state = 'header'
                _, v = line.split(':', 1)
                iface = v.strip()
                header = {}

    return d



def get_luns_on_intf(interface):
    ''' this routine get all the luns/block devices
        available through interface and returns them
        as a list.
    '''

    fcoedisks = get_fcoe_luns()
    vlans = get_fcoe_vlans(interface)

    lluns = []

    for vlan in vlans:
        if vlan in fcoedisks:
            for rport, val in fcoedisks[vlan].iteritems():
                for lun in val['luns'].values():
                    lluns.append(lun['device'])

    return lluns