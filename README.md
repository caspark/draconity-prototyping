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


Removing case sensitivity on Windows since Visual Studio does not support that - https://stackoverflow.com/a/51593302
https://developercommunity.visualstudio.com/content/problem/287514/clexe-cant-find-files-in-casesensitive-folders.html

```
(Get-ChildItem -Recurse -Directory).FullName | ForEach-Object {fsutil.exe file setCaseSensitiveInfo $_ disable}
```

Building libbson on Windows:

```
Download and extract https://github.com/mongodb/libbson/releases/download/1.9.2/libbson-1.9.2.tar.gz

In a command prompt, run:

cd libbson-1.9.2

cmake -G "Visual Studio 15 2017" "-DCMAKE_INSTALL_PREFIX=C:\tools\libbson" "-DCMAKE_BUILD_TYPE=Release" "-DENABLE_TESTS:BOOL=OFF"

"C:\Program Files (x86)\Microsoft Visual Studio\2017\Community\VC\Auxiliary\Build\vcvars32.bat"

msbuild.exe /p:Configuration=Release ALL_BUILD.vcxproj
msbuild.exe /p:Configuration=Release INSTALL.vcxproj

then follow libbson instructions at http://mongoc.org/libmongoc/1.9.2/visual-studio-guide.html
```

Getting libuv working in visual studio:
https://ericeastwood.com/blog/24/using-libuv-with-windows-and-visual-studio-getting-started
and
https://stackoverflow.com/a/19845109/775982
