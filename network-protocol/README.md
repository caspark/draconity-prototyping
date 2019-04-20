Draconity Prototyping
=====================

Prototyping a new network protocol for [Draconity](https://github.com/talonvoice/draconity) to add support for Windows.

## Developing

### Prerequisites

* Python 3.6
* pipenv

### Linux

```
pipenv sync

# terminal 1
pipenv run python server.py

# terminal 2
pipenv run python client.py
```

## Tests

```
pipenv run python -m unittest -v ring_buffer_test.TestRingBuffer
```

## Scratchpad

protocol format
https://talonvoice.slack.com/archives/CGX00GNDP/p1553145568076300

on windows binaries
https://github.com/lunixbochs/lib43

rough work areas
1. adding a new transport layer that roughly mirrors xpc but works over tcp so it'll work on windows too
2. per platform build system. check out https://github.com/lunixbochs/lib43 . get it running on linux first is probably easier, just to verify there's no mac bits
3. introducing a cross platform way to load the symbols we need

