import socket

import webserver

##########
# CONFIG #
##########
IP = socket.gethostbyname(socket.gethostname())
PORT = 8888

# There ain't much to do here, is there?
if __name__ == "__main__":
    app = webserver.main(PORT, IP)
    print("")
