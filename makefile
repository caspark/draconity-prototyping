server: a.out
	./a.out

a.out: cpp/server.cpp
	g++ -ggdb -pipe -Og -Wall -pedantic -fsanitize=address -std=c++17 cpp/server.cpp -I cpp/uvw/src -luv `pkg-config --libs --cflags libbson-1.0`

clean:
	rm a.out

# ==== Python tasks ====
pyserver: pypipenv
	cd py && pipenv run python server.py

pyclient: pypipenv
	cd py && while true; do pipenv run python client.py; sleep 1; done

pytest: pypipenv
	cd py && pipenv run python -m unittest -v ring_buffer_test.TestRingBuffer

pypipenv:
	cd py && pipenv sync
