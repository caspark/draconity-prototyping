# C++ version of network protocol

## Prereqs

* libuv installed - `apt install automake libtool build-essential` then follow https://github.com/libuv/libuv#build-instructions
* libbson installed (tested w/ 1.9.2) - `apt install libbson-1.1-0 libbson-dev` on 18.04

## Running

Server:

```
# sh derivatives
g++ -ggdb -Og -fsanitize=address -std=c++17 -luv -I uvw/src $(pkg-config --libs --cflags libbson-1.0) server.cpp  && ./a.out
# fish
g++ -ggdb -Og -fsanitize=address -std=c++17 -luv -I uvw/src (pkg-config --libs --cflags libbson-1.0 | string split " ") server.cpp  && ./a.out
```

Client:

```
cd ../network-protocol/ && pipenv run python client.py
```
