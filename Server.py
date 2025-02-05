from twisted.internet.protocol import Protocol
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor
from twisted.internet.protocol import Factory
import sys


def buffered_payload_len(payload, offset):
    buffer = offset - len(str(len(payload)))
    return "0"*buffer + str(len(payload))


server_port = 8007


# This is the protocol that translates the applications messages
class Chat(Protocol):
    def __init__(self, client_list, chatroom_list):
        self.client_list = client_list
        self.chatroom_list = chatroom_list
        self.user_name = None
        self.phase = "GREET"

    def connectionLost(self, reason):
        if self.user_name in self.client_list:
            del self.client_list[self.user_name]

        tar_room_name = None
        for room_name, room in self.chatroom_list.items():
            if self in room:
                tar_room_name = room_name
                break

        if tar_room_name:
            self.chatroom_list[tar_room_name].remove(self)

    def dataReceived(self, data):
        if self.phase == "GREET":
            self.handle_GREET(data)

        elif self.phase == "CONVO":
            self.handle_CONVO(data)

    def handle_GREET(self, data):
        switcher = {
            "HELLO": self.hello,
            "MAKE!": self.make,
        }

        switcher.get(data[:5].decode(), self.panic)(data[5:])

    def handle_CONVO(self, data):
        switcher = {
            "LIST!": self.list,
            "CREAT": self.create,
            "JOIN!": self.join,
            "MESS!": self.message,
            "LEAVE": self.leave,
            "TERM!": self.terminate,
        }

        switcher.get(data[:5].decode(), self.panic)(data[5:])

    def leave(self, data):
        self.chatroom_list[data.decode()].remove(self.client_list[self.user_name])
        self.transport.write(b"LEAVE")

    def terminate(self, data):  # data is intentionally None.
        self.transport.write(b"TERM!ACK!!")

    def message(self, data):
        name_len = int(data[:8].decode())
        room_name = data[8:8+name_len].decode()
        message = data[8+name_len:]

        for aChat in self.chatroom_list[room_name]:
            if aChat.user_name != self.user_name:
                aChat.transport.write(b"MESS!" + message)

    def join(self, data):
        name_len = int(data[:8].decode())
        user_name = data[8:8+name_len].decode()
        room_name = data[8+name_len:].decode()

        if room_name not in self.chatroom_list:  # Guard against duplicate chat room names.
            self.transport.write(b"JOIN!NACK!")
            return

        a = "JOIN!ACK!!" + room_name

        self.chatroom_list[room_name].append(self.client_list[user_name])
        self.transport.write(a.encode())

    def create(self, data):
        name_len = int(data[:8].decode())
        user_name = data[8:8+name_len].decode()
        room_name = data[8+name_len:].decode()

        if room_name in self.chatroom_list:
            self.transport.write(b"CREATNACK")
            return

        self.chatroom_list[room_name] = list()
        self.transport.write(b"CREATACK")

    def list(self, data):
        if self.chatroom_list:
            payload = '\n'.join(list(self.chatroom_list.keys()))+'\n'
        else:
            payload = ''

        payload = "LIST!" + buffered_payload_len(payload, 8) + payload
        self.transport.write(payload.encode())

    def hello(self, data):  # data == HELLO
        data = b'WHAT!'
        self.transport.write(data)

    def make(self, name):
        # If add password, parse byte lengths of username and password
        name = name.decode()
        if name in self.client_list:
            self.transport.write(b'NACK!')
        else:
            self.user_name = name
            self.client_list[self.user_name] = self
            self.phase = "CONVO"
            self.transport.write(b'ACK!!')

    def panic(self):
        sys.stdout = sys.__stdout__
        sys.stdout.write("PANIC!!!!")
        reactor.stop()


class ChatFactory(Factory):
    def __init__(self):
        self.client_list = {}  # maps user names to Chat instances
        self.chatroom_list = {}

    def buildProtocol(self, addr):
        return Chat(self.client_list, self.chatroom_list)


endpoint = TCP4ServerEndpoint(reactor, server_port)  # A TCP socket
endpoint.listen(ChatFactory())
reactor.run()




