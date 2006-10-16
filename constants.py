# Copyright (c) 2005-2006 XenSource, Inc. All use and distribution of this 
# copyrighted material is governed by and subject to terms and conditions 
# as licensed by XenSource, Inc. All other rights reserved.
# Xen, XenSource and XenEnterprise are either registered trademarks or 
# trademarks of XenSource Inc. in the United States and/or other countries.

###
# XEN CLEAN INSTALLER
# Functions to perform the XE installation
#
# written by Andrew Peace & Mark Nijmeijer

import version

# exit status
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_USER_CANCEL = 2

# install types:
INSTALL_TYPE_FRESH = 1
INSTALL_TYPE_REINSTALL = 2

# disk sizes
min_primary_disk_size = 16

# filesystems and partitions (sizes in MB):
root_size = 4096
rootfs_type = 'ext3'
rootfs_label = '/-main'
default_sr_firstpartition = 3
swap_location = '/var/swap/swap.001'
swap_size = 512

MIN_PASSWD_LEN=6

# file locations - installer filesystem
EULA_PATH = "/opt/xensource/installer/EULA"
timezone_data_file = '/opt/xensource/installer/timezones'
kbd_data_file = '/opt/xensource/installer/keymaps'

# host filesystem - always absolute paths from root of install
# and never start with a '/', so they can be used safely with
# os.path.join.
ANSWERS_FILE = "upgrade_answers"
INVENTORY_FILE = "etc/xensource-inventory"

# files that should be writeable in the dom0 FS
writeable_files = [ '/etc/sysconfig/keyboard',
                    '/etc/yp.conf',
                    '/etc/ntp.conf',
                    '/etc/resolv.conf',
                    '/etc/dhclient-exit-hooks',
                    '/etc/hosts',
                    '/etc/hostname',
                    '/etc/syslog.conf',
                    '/etc/issue',
                    '/etc/adjtime',
                    '/etc/passwd',
                    '/etc/.pwd.lock',
                    '/etc/lvm/.cache',
                    '/etc/vendorkernel-inventory',
                    '/usr/sbin/system-info.sh']

# directories to be created in the dom0 FS
asserted_dirs = [ '/etc',
                  '/etc/sysconfig',
                  '/etc/sysconfig/network-scripts',
                  '/etc/lvm',
                  '/etc/lvm/archive',
                  '/etc/lvm/backup',
                  '/usr/sbin' ]

# directories that should be writeable in the dom0 FS
writeable_dirs = [ '/etc/ntp',
                   '/etc/lvm/archive',
                   '/etc/lvm/backup',
                   '/etc/ssh',
                   '/root' ]
