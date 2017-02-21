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
