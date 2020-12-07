import socket
from threading import Thread
from os.path import exists
import sys

HOST = 'localhost'
PORT = 9009


def rcvMsg(sock):
    while True:
        try:
            data = sock.recv(1024)
            print(data.decode())
            if not data:
                break
            elif '/file_' in data.decode():
                #print('############ /file ##############')
                temp_str = data.decode()
                filename = temp_str.split('_')[1]
                getFileFromServer(sock, filename)
            # else:
            #     print('############ else ##############')
            #     print(data.decode())

        except:
            pass
def getFileFromServer(sock, filename):
    data_transferred = 0
    filedata = sock.recv(1024)
    if not filedata:
        print('if not data!!!')
        return

    with open('download/' + filename, 'ab') as f:
        try:
            while True:
                f.write(filedata)
                data_transferred += len(filedata)
                filedata = sock.recv(1024)
                if '/fileend'.encode() in filedata:
                    #filedata = str(filedata).split('/fileend')[0][2:].encode()
                    #filedata = filedata.split()[0]
                    filedata = filedata.split(b'/fileend')[0]
                    f.write(filedata)
                    data_transferred += len(filedata)
                    break
        except Exception as e:
            print(e)

        print("파일[%s] 수신완료. 수신량 [%d]" % (filename, data_transferred))

def runChat():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((HOST, PORT))
        t = Thread(target=rcvMsg, args=(sock,))
        t.daemon = True
        t.start()

        while True:
            msg = input('')
            if msg == '/quit':
                sock.send(msg.encode())
                break
            elif msg == '/file':
                sock.send('/file'.encode())
                filename = input('전송할 파일 이름을 입력하세요: ')
                sock.send(filename.encode())
                if not exists(filename):
                    print("There is no such file");
                    sys.exit();
                print("파일 %s 전송 시작" % filename)
                data_transferred = 0
                with open(filename, 'rb') as f:
                    try:
                        filedata = f.read(1024)
                        while filedata:  # data가 없을 때 까지
                            data_transferred += sock.send(filedata)
                            filedata = f.read(1024)
                    except Exception as e:
                        print(e)
                print("/fileend 입력 시 전송완료 %s, 전송량 %d" % (filename, data_transferred))
            else:
                sock.send(msg.encode())


runChat()