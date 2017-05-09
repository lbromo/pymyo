# PyMyo

Get measurements from the Myo band direcly over bluetooth (dongle less).

It is build around [blupy](https://github.com/IanHarvey/bluepy), and [CFFI](https://bitbucket.org/cffi/cffi)

EMG have been tested on Linux, and provides data with 2 measurements per pod with 100Hz (200Hz sampling) as described in [this blog post](http://developerblog.myo.com/myocraft-emg-in-the-bluetooth-protocol/).

IMU data is also getting through, but havn't check the sampling frequency.

# Test it

To test it, simply clone it, generate the `CFFI`bindings, and run `pymyo` (there is a minimalistic demo available there) 

1. get it: `git clone --recursive git@github.com:lbromo/PyMyo.git`
2. `cd PyMyo`
3. generate cffi bindings: `python generate_cffi_bindings.py`
4. use it: `python pymyo.py`

# Install it

To install it system wide, invoke `sudo python setup.py install` (not possible with pip, as the installation is a bit hacky)

