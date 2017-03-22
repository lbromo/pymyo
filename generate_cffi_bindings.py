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
import cffi

MYOHW = 'myo-bluetooth/myohw.h'

ffi = cffi.FFI()

cdef = ""

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
