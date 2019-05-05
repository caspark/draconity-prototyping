Draconity Prototyping
=====================

Prototyping a new network protocol for [Draconity](https://github.com/talonvoice/draconity) to add support for Windows, in C++ and Python.

The Python implementation is mainly intended to ease development of the C++ version.

## Prereqs

C++ server:

* libuv installed - `apt install automake libtool build-essential` then follow https://github.com/libuv/libuv#build-instructions
* libbson installed (tested w/ 1.9.2) - `apt install libbson-1.1-0 libbson-dev` on 18.04

Python server & client:

* Python 3.6
* pipenv

## Running & Developing

Compile and run the C++ Server:

```
make
```

Run the Python client (will restart on error for easier server dev):

```
make pyclient
```

Run the Python server (useful to confirm client is implemented correctly):

```
make pyserver
```

Run Python tests (because I went overboard and implemented a ringbuffer that was initially very buggy):

```
make pytest
```

## Reference

* http://mongoc.org/libbson/1.9.2/parsing.html
* https://skypjack.github.io/uvw/index.html
* http://docs.libuv.org/en/v1.x/


## Scratchpad

protocol format
https://talonvoice.slack.com/archives/CGX00GNDP/p1553145568076300

on windows binaries
https://github.com/lunixbochs/lib43

rough work areas
1. adding a new transport layer that roughly mirrors xpc but works over tcp so it'll work on windows too
2. per platform build system. check out https://github.com/lunixbochs/lib43 . get it running on linux first is probably easier, just to verify there's no mac bits
3. introducing a cross platform way to load the symbols we need

