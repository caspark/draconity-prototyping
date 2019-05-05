# C++ version of network protocol

## Prereqs

* libuv installed - `apt install automake libtool build-essential` then follow https://github.com/libuv/libuv#build-instructions
* libbson installed (tested w/ 1.9.2) - `apt install libbson-1.1-0 libbson-dev` on 18.04

## Running

Server:

```
make
```

Client:

```
make client
```

## Reference

http://mongoc.org/libbson/1.9.2/parsing.html
https://skypjack.github.io/uvw/index.html
http://docs.libuv.org/en/v1.x/
