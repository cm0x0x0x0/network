import socketserver
import threading

HOST = ''
PORT = 9009
lock = threading.Lock()  # syncronized 동기화 진행하는 스레드 생성


class UserManager:  # 사용자관리 및 채팅 메세지 전송을 담당하는 클래스
    # ① 채팅 서버로 입장한 사용자의 등록
    # ② 채팅을 종료하는 사용자의 퇴장 관리
    # ③ 사용자가 입장하고 퇴장하는 관리
    # ④ 사용자가 입력한 메세지를 채팅 서버에 접속한 모두에게 전송

    def __init__(self):
        self.users = {}  # 사용자의 등록 정보를 담을 사전 {사용자 이름:(소켓,주소,패스워드),...}
        self.unconnectedUsers = {}

    def addUser(self, username, conn, addr, password):  # 사용자 ID를 self.users에 추가하는 함수
        if username in self.users:  # 이미 등록된 사용자라면
            # print(conn)
            # print(addr)
            # print(password)
            # print(self.users[username])
            # print(self.users[username][2])
            if password != self.users[username][2]:
                conn.send('이미 등록된 사용자입니다.\n'.encode())
                return None
            else:

                conn.send('다시 연결하였습니다.'.encode())
                # del self.unconnectedUsers[username]
                # 새로운 사용자를 등록함
                lock.acquire()  # 스레드 동기화를 막기위한 락
                self.users[username] = (conn, addr, password)
                lock.release()  # 업데이트 후 락 해제

                self.sendMessageToAll('[%s]님이 다시 연결하였습니다.' % username)
                # print('+++ 대화 참여자 수 [%d]' % len(self.users))
                # print('+++ 대화 참여자 명단')
                # for username in self.users:
                #     print(username)
                # return username

        else :
            # 새로운 사용자를 등록함
            lock.acquire()  # 스레드 동기화를 막기위한 락
            self.users[username] = (conn, addr, password)
            lock.release()  # 업데이트 후 락 해제

            self.sendMessageToAll('[%s]님이 입장했습니다.' % username)
            # print('+++ 대화 참여자 수 [%d]' % len(self.users))
            # print('+++ 대화 참여자 명단')
            # for username in self.users:
            #     print(username)
            #
            # return username

        print('+++ 대화 참여자 수 [%d]' % len(self.users))
        print('+++ 대화 참여자 명단')
        for username in self.users:
            print(username)
        print('+++++++++++++++++')

        return username



    def removeUser(self, username, hostQuitBySystem):  # 사용자를 제거하는 함수
        if username not in self.users:
            return
        if (hostQuitBySystem == False) :
           # print('hi')
           lock.acquire()
           del self.users[username]
           lock.release()
           self.sendMessageToAll('[%s]님이 퇴장했습니다.' % username)
           print('--- 대화 참여자 수 [%d]' % len(self.users))
        else:
            # lock.acquire()
            # self.unconnectedUsers[username] = (self.users[0], self.users[1], self.users[2])
            # lock.release()

            self.sendMessageToAllExceptSender(username,'[%s]님이 예기치 않은 상황으로 인해 연결이 끊어졌습니다. ' % username)
            print('--- 대화 참여자 수 [%d]' % len(self.users))

    def messageHandler(self, username, msg, hostQuitBySystem):  # 전송한 msg를 처리하는 부분

        if msg[0] != '/':  # 보낸 메세지의 첫문자가 '/'가 아니면
            self.sendMessageToAll('[%s] %s' % (username, msg))
            return

        if msg.strip() == '/quit':  # 보낸 메세지가 'quit'이면
            self.removeUser(username, hostQuitBySystem)
            return -1

    def sendMessageToAll(self, msg):
        for conn, addr, password in self.users.values():
            conn.send(msg.encode())

    def sendMessageToAllExceptSender(self, sender_user, msg):
        for conn, addr, password in self.users.values():
            if((conn, addr, password) == self.users[sender_user]):
                continue
            else:
                conn.send(msg.encode())

    def sendFileToAllStartExceptSender(self, sender_user, filename):
        for conn, addr, password in self.users.values():
            if ((conn, addr, password) == self.users[sender_user]):
                continue
            else:
                conn.send(('/file' + '_' + filename).encode())

    def sendFileToAllEndExceptSender(self, sender_user):
        for conn, addr, password in self.users.values():
            if ((conn, addr, password) == self.users[sender_user]):
                continue
            else:
                conn.send('/fileend'.encode())

    def sendFileToAllExceptSender(self, sender_user, filedata):
        for conn, addr, password in self.users.values():
            if ((conn, addr, password) == self.users[sender_user]):
                continue
            else:
                size = conn.send(filedata)
        return size


class MyTcpHandler(socketserver.BaseRequestHandler):
    userman = UserManager()

    def handle(self):  # 클라이언트가 접속시 클라이언트 주소 출력
        print('[%s] 연결됨' % self.client_address[0])
        data_transferred = 0
        hostQuitBySystem = False
        isQuit = True

        try:
           try:
               username = self.registerUsername()
               msg = self.request.recv(1024)
               while msg:
                   filemsg = msg.decode()
                   if filemsg == '/file':
                       filename = self.request.recv(1024)
                       filename = filename.decode()
                       filedata = self.request.recv(1024)
                       if filedata == '/fileend'.encode():
                           print("파일[%s]: 전송 중 오류발생" % filename)
                       else:
                           with open('download/' + filename, 'wb') as f:
                               try:
                                   while filedata != '/fileend'.encode():
                                       f.write(filedata)
                                       data_transferred += len(filedata)
                                       filedata = self.request.recv(1024)
                               except Exception as e:
                                   print(e)
                           print("파일[%s] 수신완료. 수신량 [%d]" % (filename, data_transferred))
                           data_transferred = 0
                           self.userman.sendFileToAllStartExceptSender(username, filename)
                           with open('download/' + filename, 'rb') as f:
                               try:
                                   filedata = f.read(1024)
                                   while filedata:  # data가 없을 때 까지
                                       data_transferred += self.userman.sendFileToAllExceptSender(username, filedata)
                                       filedata = f.read(1024)
                                   print("파일[%s] broadcasting 완료. 전송량 [%d]" % (filename, data_transferred))
                               except Exception as e:
                                   print(e)
                           self.userman.sendFileToAllEndExceptSender(username)
                   else:
                       print(msg.decode())
                       if self.userman.messageHandler(username, msg.decode(), hostQuitBySystem) == -1:
                           self.request.close()
                           break
                   data_transferred = 0
                   msg = self.request.recv(1024)

           except:
              # print("KeyboardInterrupt")
              hostQuitBySystem = True
              print('[%s]님이 예기치 않은 상황으로 연결 두절되었습니다.' % (username))


        except:
           # print("elseExcept")
           print(hostQuitBySystem)

        print('[%s] 접속종료' % self.client_address[0])
        #self.userman.removeUser(username, hostQuitBySystem)

    def registerUsername(self):
        while True:
            self.request.send('로그인ID:'.encode())
            username = self.request.recv(1024)
            username = username.decode().strip()

            self.request.send('password:'.encode())
            password = self.request.recv(1024)
            password = password.decode().strip()

            if self.userman.addUser(username, self.request, self.client_address, password):
                return username


class ChatingServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


def runServer():
    print('+++ 채팅 서버를 시작합니다.')
    print('+++ 채텅 서버를 끝내려면 Ctrl-C를 누르세요.')

    try:
        server = ChatingServer((HOST, PORT), MyTcpHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print('--- 채팅 서버를 종료합니다.')
        # self.user.removeUser()
        server.shutdown()
        server.server_close()


runServer()