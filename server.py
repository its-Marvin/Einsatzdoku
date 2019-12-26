import sys
from shutil import copyfile
import getpass

import manage as django
from socket import *
from multiprocessing import Process
import atexit


def announceserver():
    print('Starte Autodiscover Service')
    sock = socket(AF_INET, SOCK_DGRAM)
    server_address = ('', 8001)
    sock.bind(server_address)
    response = 'Einsatzdoku autodiscover service'

    while True:
        data, address = sock.recvfrom(4096)
        data = str(data.decode('UTF-8'))
        if data == 'Einsatzdoku autodiscover client':
            sent = sock.sendto(response.encode(), address)


# @atexit.register
def backup():
    user = getpass.getuser()
    src = "./db.sqlite"
    dst = "C:/Users/" + user + "/OneDrive/db.sqlite"
    copyfile(src, dst)


def main():
    sys.argv[0] = "manage.py"
    # p2 = Process(target=announceserver)
    # p2.start()
    django.main()


if __name__ == '__main__':
    main()
