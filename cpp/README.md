# C++ version of network protocol

## Prereqs

* libuv installed - `apt install automake libtool build-essential` then follow https://github.com/libuv/libuv#build-instructions

## Running

```
# terminal 1
g++ -ggdb -Og -fsanitize=address -std=c++17 -I uvw/src server.cpp -luv && ./a.out

# terminal 2
pipenv run python client.py
```
