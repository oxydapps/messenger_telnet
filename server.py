from twisted.internet import reactor
from twisted.internet.protocol import ServerFactory, connectionDone

from twisted.protocols.basic import LineOnlyReceiver


class ServerProtocol(LineOnlyReceiver):
    factory: 'Server'
    history = []

    def __init__(self, users):
        self.users = users
        self.name = None
        self.state = "LOGIN"

    def connectionMade(self):
        self.sendLine("Please log in chat, write below 'login:' and write your login".encode())

    def connectionLost(self, reason=connectionDone):
        if self.name in self.users:
            del self.users[self.name]

    def handle_LOGIN(self, name):
        if name.startswith('login:'):
            name = name.replace('login:', '')
            if name in self.users:
                self.sendLine(f"Логин {name} уже занят, попробуйте другой".encode())
                self.transport.loseConnection()
                return
            self.name = name
            self.users[name] = self
            self.sendLine('Welcome!'.encode())
            self.send_history()
            self.state = "CHAT"
        else:
            self.sendLine('Invalid login'.encode())

    def handle_CHAT(self, message):

        if len(self.history) < 10:
            self.history.append(message)
        else:
            self.history.pop(0)
            self.history.append(message)

        message = f"message from {self.name}: {message}"

        for name, protocol in self.users.items():
            if protocol is not self:
                protocol.sendLine(message.encode())

    def lineReceived(self, line: bytes):
        content = line.decode()
        if self.state == "LOGIN":
            self.handle_LOGIN(content)
        else:
            self.handle_CHAT(content)

    def send_history(self):
        for line in self.history:
            self.sendLine(line.encode())


class Server(ServerFactory):
    protocol = ServerProtocol

    def __init__(self):
        self.users = {}

    def buildProtocol(self, addr):
        return ServerProtocol(self.users)

    def startFactory(self):
        print('server started')

    def doStop(self):
        print('server closed')


reactor.listenTCP(1234, Server())
reactor.run()
