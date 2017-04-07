#!/usr/bin/env python3
#################################################################################
# generate_cffi_bindings.py
# Generate python bindings using CFFI for the myohw
#
#-------------------------------------------------------------------------------
# "THE BEER-WARE LICENSE" (Revision 42):
#
# <lbromo@protonmail.ch> wrote this file. As long as you retain this notice
# you can do whatever you want with this stuff. If we meet some day, and you
# think this stuff is worth it, you can buy me a beer in return.
#
# - Lasse Bromose
#-------------------------------------------------------------------------------
################################################################################
import os, io, zipfile
from urllib import request

import cffi

HYOHW_URL = 'https://github.com/lbromo/myo-bluetooth/archive/master.zip'
MYOHW = 'myo-bluetooth-master/myohw.h'

ffi = cffi.FFI()

cdef = ""

if not os.path.exists(MYOHW):
    request.urlretrieve(HYOHW_URL, 'tmp.zip')
    with zipfile.ZipFile('tmp.zip') as z:
        print(z)
        z.extractall()

with open(MYOHW) as f:
    for l in f.readlines():
        if ('#' in l  and "#define" not in l or
            'MYOHW_STATIC_ASSERT_SIZED' in l):
            continue
        cdef = cdef + l.replace('MYOHW_PACKED', '')


ffi.cdef(cdef)
ffi.set_source('myohw', cdef)

if __name__ == '__main__':
    ffi.compile(verbose=True)
