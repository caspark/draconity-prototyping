serve: server
	./server

server: cpp/server.cpp
	g++ -ggdb -pipe -Og -Wall -pedantic -fsanitize=address -std=c++17 -o server cpp/server.cpp -I cpp/uvw/src -luv `pkg-config --libs --cflags libbson-1.0`

client:
	cd network-protocol && while true; do pipenv run python client.py; sleep 1; done

clean:
	rm server
