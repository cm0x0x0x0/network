import socket
from threading import Thread
from os.path import exists
import sys

HOST = 'localhost'
PORT = 9009

def rcvMsg(sock):
   File_ON = False
   File_Name_ON = False
   data_transferred = 0
   while True:
      try:
         data = sock.recv(1024)
         if not data:
            break
         elif data.decode() == '/file':
            File_ON = True

         elif data.decode() == '/fileend':
            File_ON = False
            File_Name_ON = False
            print("파일[%s] 수신완료. 수신량 [%d]" % (filename, data_transferred))
            data_transferred = 0


         elif File_ON == True and File_Name_ON == False: # 아직 filename 안 받았을 때,
            filename = data.decode()
            File_Name_ON = True

         elif File_ON == True and File_Name_ON == True: # filename받고 filedata만 받을 때,
            with open('download/' + filename, 'wb') as f:
               try:
                  filedata = data
                  f.write(filedata)
                  data_transferred += len(filedata)
               except Exception as e:
                  print(e)
         else:
            print(data.decode())

      except:
         pass

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
                  while filedata: # data가 없을 때 까지
                     data_transferred += sock.send(filedata)
                     filedata = f.read(1024)
               except Exception as e:
                  print(e)
            print("/fileend 입력 시 전송완료 %s, 전송량 %d" %(filename, data_transferred))
         else:
            sock.send(msg.encode())
            
runChat()