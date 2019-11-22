from twisted.internet.protocol import Protocol
import sys
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol
from twisted.application.internet import ClientService
from twisted.internet import stdio


serverIP = "10.0.0.58" # Stevens ip address #"10.200.185.199"  # school ip address  #"192.168.0.19" # Bob's ip  #"10.0.0.58" #Home ip address
serverPort = 8007


def buffered_payload_len(payload, offset):
    buffer = offset - len(str(len(payload)))
    return "0"*buffer + str(len(payload))


class Messanger(Protocol):
    def __init__(self, client):
        self.client = client

    def prompt(self):
        self.transport.write(b"You: ")

    def connectionMade(self):
        self.transport.write(b"Begin Messaging\n")
        self.prompt()

    def dataReceived(self, data):
        self.client.send_mesage(data)
        self.prompt()

    def dataSend(self, data):
        self.transport.write(data)
        self.prompt()

    def connectionLost(self):
        self.transport.write(b" ")
        return


class Client(Protocol):
    def __init__(self):
        self.phase = "GREET"
        self.user_name = None

    def connectionMade(self):
        data = b"HELLO"
        self.transport.write(data)

    def dataReceived(self, data):
        if self.phase == "GREET":
            self.handle_GREET(data)

        elif self.phase == "CONVO":
            self.handle_CONVO(data)

    def handle_GREET(self, data):
        switcher = {
            'WHAT!': self.get_credentials,
            'NACK!': self.get_credentials,  # time out mechanism
            'ACK!!': self.phase_transition,
        }

        switcher.get(data[:5].decode(), self.panic)()

    def handle_CONVO(self, data):
        switcher = {
            'LIST!': self.catch_list,
            'CREAT': self.catch_create,
            'JOIN!': self.catch_join,
            'MESS!': self.catch_message,
            'LEAVE': self.catch_leave,
        }

        switcher.get(data[:5].decode(), self.panic)(data[5:])

    def get_credentials(self):
        self.user_name = input("Type user name: ")  # APPLICATION
        data = "MAKE!" + self.user_name
        self.transport.write(data.encode())

    def converse(self):
        self.transport.write(self.menu())

    def list(self, data):
        self.transport.write(data.encode())

    def phase_transition(self):
        self.phase = "CONVO"
        self.converse()

    '''
    Displays options to user, gets their selection, and translates it to the appropriate application layer
    protocol. Validates user input. 
    '''
    def menu(self):
        options = ["list\n", "create\n", "join\n"]
        menu = "\nTo select an action type the command to the left of the colon.\n" \
               + "List available rooms : " + options[0] \
               + "Create a room        : " + options[1] \
               + "Join a room          : " + options[2] \
               + "Your selection: "

        sys.stdout.write(menu)
        user_selection = sys.stdin.readline()

        while user_selection not in options:
            sys.stdout.write("\nThat selection is unviable. Try again.\nYour selection: ")
            user_selection = sys.stdin.readline()

        if user_selection == options[0]:
            user_selection = "LIST!"

        elif user_selection == options[1]:
            user_selection = "CREAT" + buffered_payload_len(self.user_name, 8) + self.user_name + input("Enter Room Name: ")

        elif user_selection == options[2]:
            user_selection = "JOIN!" + buffered_payload_len(self.user_name, 8) + self.user_name + input("Enter Room Name: ")

        return user_selection.encode()

    def catch_list(self, data):
        message_length = int(data[0:8].decode())  # 5 byte header 8 byte message length
        if message_length == 0:
            sys.stdout.write("No chat rooms")
        else:
            message = data[8:].decode()
            sys.stdout.write(message)
        self.converse()

    def catch_join(self, data):
        if data[:5].decode() == "NACK!":
            sys.stdout.write("No, the room does not exist.\n")
            self.converse()
        else:
            room_name = data[5:].decode()
            sys.stdout.write("Welcome " + self.user_name + " to " + room_name + ".\n")
            self.room_name = room_name
            self.messanger = Messanger(self)
            stdio.StandardIO(self.messanger)

    def send_mesage(self, data):
        if data.decode() != "IM LEAVING THE ROOM\n":
            self.transport.write(b"MESS!" + buffered_payload_len(self.room_name, 8).encode()
                                          + self.room_name.encode()
                                          + b"\n"
                                          + self.user_name.encode()
                                          + b": "
                                          + data)
        else:
            self.messanger.connectionLost()
            self.messanger = None
            sys.stdin = sys.__stdin__
            sys.stdout = sys.__stdout__
            self.transport.write(b"LEAVE" + self.room_name.encode())

    def catch_leave(self, data):  # Data == None. Will change if implement ACK!!/NACK
        self.converse()

    def catch_message(self, data):
        self.messanger.dataSend(data)

    def catch_create(self, data):
        mssg = {"NACK": "No. Try again.\n", "ACK": "We've made your room.\n"}
        sys.stdout.write(mssg[data.decode()])
        self.converse()

    def panic(self):
        sys.stdout.write("PANIC!!!!\n")

def end():
    sys.stdout.write("turning off\n")
    reactor.stop()


socket = TCP4ClientEndpoint(reactor, serverIP, serverPort)
proto = connectProtocol(socket, Client())
theConnection = ClientService(socket, proto)

theConnection.startService()

#reactor.callLater(20, end)
reactor.run()  # Begin running Twisted's OS interacting processes.

