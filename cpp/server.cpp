#include <uvw.hpp>
#include <memory>
#include <iostream>
#include <unistd.h>
#include <mutex>

#define NETWORK_DEBUG true

void dump_vector(std::vector<char> buffer) {
    for (auto const& c : buffer) {
        std::cout << std::hex << (int) c;
    }
    std::cout << std::endl;
}

class UvClient {
    public:
        UvClient() {
            std::cout << "bytes needed initially " << msg_len << std::endl;
        }

        void onEnd(const uvw::EndEvent &, uvw::TCPHandle &client) {
            client.close();
        }
        void onData(const uvw::DataEvent &event, uvw::TCPHandle &client) {
            if (NETWORK_DEBUG) std::cout << "client on data " << event.length << std::endl;
            lock.lock();
            auto data = &event.data[0];
            buffer.insert(buffer.end(), data, data + event.length);
            if (NETWORK_DEBUG) dump_vector(buffer);

            if (msg_tid == 0) {
                // tid 0 == broadcast, which we should never receive
                // so that means we're expecting a new message, which starts with transaction id
                if (buffer.size() >= sizeof(uint32_t)) {
                    msg_tid = htonl(*reinterpret_cast<uint32_t *>(&buffer[0]));
                    if (NETWORK_DEBUG) std::cout << "read tid " << msg_tid << std::endl;
                    buffer.erase(buffer.begin(), buffer.begin() + sizeof(uint32_t));
                }
            }
            if (msg_len == 0) {
                if (buffer.size() >= sizeof(uint32_t)) {
                    msg_len = htonl(*reinterpret_cast<uint32_t *>(&buffer[0]));
                    if (NETWORK_DEBUG) std::cout << "read len " << msg_len << std::endl;
                    buffer.erase(buffer.begin(), buffer.begin() + sizeof(uint32_t));
                }
            }
            if (msg_tid > 0 && msg_len > 0 && buffer.size() >= msg_len) {
                std::cout << "message - tid=" << msg_tid << ", len=" << msg_len << std::endl;
            }
            lock.unlock();
        }

    private:
        std::vector<char> buffer;
        std::mutex lock;

        uint32_t msg_tid = 0;
        uint32_t msg_len = 0;
};

class UvServer {
    public:
        UvServer();
        ~UvServer();
        void listen(const char *host, int port);
        void run();

        void publish(const uint8_t *msg, size_t length);
    private:
        std::list<std::shared_ptr<UvClient>> clients;
        std::shared_ptr<uvw::Loop> loop;
        std::mutex lock;
};

UvServer::UvServer() {
    loop = uvw::Loop::create();
}

UvServer::~UvServer() {
    loop->stop();
    // TODO: figure out if we actually need to call this close
    loop->close();
}

void UvServer::listen(const char *host, int port) {
    std::shared_ptr<uvw::TCPHandle> tcp = loop->resource<uvw::TCPHandle>();

    tcp->on<uvw::ListenEvent>([this](const uvw::ListenEvent &, uvw::TCPHandle &srv) {
        std::shared_ptr<uvw::TCPHandle> tcpClient = srv.loop().resource<uvw::TCPHandle>();
        auto peer = tcpClient->peer();
        std::cout << "accepted " << tcpClient << " " << peer.ip << ":" << peer.port << std::endl;

        auto client = std::make_shared<UvClient>();
        tcpClient->on<uvw::CloseEvent>([this, client](const uvw::CloseEvent &, uvw::TCPHandle &tcpClient) {
            auto peer = tcpClient.peer();
            std::cout << "close " << &tcpClient << " " << peer.ip << ":" << peer.port << std::endl;
            lock.lock();
            clients.remove(client);
            lock.unlock();
        });
        tcpClient->on<uvw::EndEvent>([client](const uvw::EndEvent &event, uvw::TCPHandle &tcpClient) {
            client->onEnd(event, tcpClient);
        });
        tcpClient->on<uvw::DataEvent>([client](const uvw::DataEvent &event, uvw::TCPHandle &tcpClient) {
            client->onData(event, tcpClient);
        });

        lock.lock();
        clients.push_back(client);
        lock.unlock();

        srv.accept(*tcpClient);
        tcpClient->read();
    });

    tcp->bind(host, port);
    tcp->listen();
}

void UvServer::run() {
    loop->run();
}

int main() {
    auto port = 8000;
    auto addr = "127.0.0.1";
    std::cout << "Server starting on " << addr << ":" << port << "..." << std::endl;
    UvServer server;
    server.listen(addr, port);
    server.run();
}
