import socket

import webserver

##########
# CONFIG #
##########
IP = socket.gethostbyname(socket.gethostname())
PORT = 8888

if __name__ == "__main__":
    app = webserver.main(PORT, IP)
    print("")
