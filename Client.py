from twisted.internet.protocol import Protocol
#from twisted.protocols import basic
from sys import stdout
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

    def connectionMade(self):
        self.transport.write(b"Enter message: ")

    def dataReceived(self, data):
        self.client.send_mesage(data)

    def dataSend(self, data):
        self.transport.write(data)




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
    Need to double check that we validate input.
    '''
    def menu(self):
        menu = input("\nList 0\nCreate 1\nJoin Room 2\n")

        if menu[0] == '0':
            menu = "LIST!"
        elif menu[0] == '1':
            menu = "CREAT" + buffered_payload_len(self.user_name, 8) + self.user_name + input("Enter Room Name: ")
        elif menu[0] == '2':
            menu = "JOIN!" + buffered_payload_len(self.user_name, 8) + self.user_name + input("Enter Room Name: ")

        return menu.encode()

    def catch_list(self, data):
        message_length = int(data[0:8].decode())  # 5 byte header 8 byte message length
        if message_length == 0:
            stdout.write("No chat rooms")
        else:
            message = data[8:].decode()
            stdout.write(message)
        self.converse()

    def catch_join(self, data):
        if data[:5].decode() == "NACK!":
            stdout.write("No, the room does not exist.\n")
            self.converse()
        else:
            room_name = data[5:].decode()
            stdout.write("Welcome " + self.user_name + " to " + room_name + ".\n")  # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            self.room_name = room_name
            #self.init_messaging()
            self.messanger = Messanger(self)
            stdio.StandardIO(self.messanger)

    def send_mesage(self, data):
        self.transport.write(b"MESS!" + buffered_payload_len(self.room_name, 8).encode() + self.room_name.encode() + b"\n" +self.user_name.encode() + b" " + data)

#///////////////////////////////////////////////////////////
    def init_messaging(self):
        mssg = input("Enter Message: ")
        if mssg == "REMOVE ME FROM THE ROOM!!!":
            stdout.write("Girl bye.")
            self.converse()
            return
        mssg = "MESS!" + buffered_payload_len(self.room_name, 8) + self.room_name + self.user_name + ": " + mssg
        self.transport.write(mssg.encode())

    def catch_message(self, data):
        self.messanger.dataSend(data)



#////////////////////////////////////////////////////////////////
    def catch_create(self, data):
        mssg = {"NACK": "No. Try again.\n", "ACK": "We've made your room.\n"}
        stdout.write(mssg[data.decode()])
        self.converse()

    '''
        def catch_message(self, data):  # Assume one room at a time.
            stdout.write(data.decode() + "\n")

            mssg = input("Enter Message: ")
            if mssg == "REMOVE ME FROM THE ROOM!!!":
                stdout.write("Girl bye.")
                self.converse()
                return
            mssg = "MESS!" + buffered_payload_len(self.room_name, 8) + self.room_name + self.user_name + ": " + mssg
            self.transport.write(mssg.encode())
    '''

    def panic(self):
        stdout.write("PANIC!!!!\n")

def end():
    stdout.write("turning off\n")
    reactor.stop()


socket = TCP4ClientEndpoint(reactor, serverIP, serverPort)
proto = connectProtocol(socket, Client())
theConnection = ClientService(socket, proto)

theConnection.startService()

#reactor.callLater(20, end)
reactor.run()  # Begin running Twisted's OS interacting processes.

