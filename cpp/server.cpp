#include <uvw.hpp>
#include <memory>
#include <iostream>
#include <unistd.h>
#include <mutex>

class UvClient {
    public:
        UvClient() {}

        void onClose(const uvw::CloseEvent &, uvw::TCPHandle &client) {}
        void onEnd(const uvw::EndEvent &, uvw::TCPHandle &client) {
            client.close();
        }
        void onData(const uvw::DataEvent &event, uvw::TCPHandle &client) {
            std::cout << "on data " << event.length << std::endl;
            lock.lock();
            auto data = &event.data[0];
            buffer.insert(buffer.end(), data, data + event.length);
            if (need_bytes == 0) {
                if (buffer.size() >= sizeof(uint32_t)) {
                    need_bytes = htonl(*reinterpret_cast<uint32_t *>(&buffer[0]));
                    std::cout << "need " << need_bytes << std::endl;
                    buffer.erase(buffer.begin(), buffer.begin() + sizeof(uint32_t));
                }
            }
            if (need_bytes > 0 && buffer.size() >= need_bytes) {
                std::cout << "buffer has enough bytes for next message" << std::endl;
            }
            lock.unlock();
        }

    private:
        std::vector<char> buffer;
        std::mutex lock;
        uint32_t need_bytes = 0;
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
        std::cout << "close " << tcpClient << " " << peer.ip << ":" << peer.port << std::endl;

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
    UvServer server;
    server.listen("127.0.0.1", 4242);
    server.run();
}
