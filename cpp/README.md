# C++ version of network protocol

## Prereqs

* libuv installed - `apt install automake libtool build-essential` then follow https://github.com/libuv/libuv#build-instructions

## Running

```
g++ -ggdb -fsanitize=address -std=c++17 -I uvw/src demo.cpp -luv && ./a.out
```
