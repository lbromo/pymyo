#!/usr/bin/env python

from distutils.core import setup, Extension

import generate_cffi_bindings

setup(name='pymyo',
      version='1.0',
      description='Myo Band handler',
      author='Lasse Bromose',
      author_email='lbromo@protonmail.ch',
      url='https://github.com/lbromo/pymyo',
      classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "License :: Beer-Ware License",
      ],
      py_modules=['pymyo', 'myohw', 'generate_cffi_bindings'],
      install_requires=["cffi>=1.0.0"],
      setup_requires=["cffi>=1.0.0"],
      ext_modules=[
          generate_cffi_bindings.ffibuilder.distutils_extension(),
      ]
)
