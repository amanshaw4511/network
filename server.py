import socket
import threading
import subprocess
import os

# import pathlib

BUFFER = 2048


# ansi escape sequence color

class Server(socket.socket):
    def __init__(self, *args, **kwargs):
        self.ip = ""
        self.port = 6789
        self.conn = None
        try:
            print("[+] creating socket")
            socket.socket.__init__(self, *args, **kwargs)
            print("--- socket created successfully")
        except socket.error as e:
            print("[-] Error Creating Socket :", str(e))

    def bindSocket(self):
        try:
            print("[+] binding socket to port : ", self.port)
            self.bind((self.ip, self.port))
            print("--- binding successfull")
            self.listen(5)
        except socket.error as e:
            print("[-] Error Binding :", str(e))

    def acceptClient(self):
        try:
            print("[+] waiting for connection")
            self.conn, addr = self.accept()
            print("--- connection established : ip = ", addr[0], "port :", addr[1])
        except socket.error as e:
            print("[-] Error Accepting Client :", str(e))

    def sendm(self, msg):
        try:
            self.conn.send(str.encode(msg))  # encode msg to binary and send
        except socket.error as e:
            print("[-] Error Sending Message/Command", str(e))

    def recvm(self):
        try:
            msg = self.conn.recv(BUFFER)  # receive msg
            return msg.decode("utf-8")  # convert binary msg to str and return
        except socket.error as e:
            print("[-] Error Receiving Message/Command", str(e))

    def download(self, fileName):
        downloadedSize = 0
        try:
            file = open(fileName, "wb")  # open file for writing data
        except Exception as e:
            print("[+} Error Opening ", fileName, ":", str(e))
            return
        while True:
            try:
                data = self.conn.recv(BUFFER)  # receive data
                downloadedSize += 2
                print("downloading", downloadedSize, "KB")
                if data[-3:] == str.encode("~~~"):  # check if download complete command(check EOF)
                    file.write(data[:-3])  # write data except extra EOF command
                    print("download successfull")
                    file.close()
                    return
                file.write(data)  # write data to file
            except socket.error as e:
                print("[-] Error Downloading File :", str(e))
                return
            except Exception as e:
                print("[-] Error Writing Data :", str(e))
                return

    def upload(self, fileName):
        uploadedSize = 0
        try:
            file = open(fileName, "rb")  # open file for reading data
        except Exception as e:
            print("[-} Error Opening", fileName, ":", str(e))
            return
        while True:
            try:
                data = file.read(BUFFER)  # read data from file
                if not data:  # check if upload complete
                    self.conn.send(str.encode("~~~"))  # send EOF ( upload complete command)
                    print("upload successfull")
                    file.close()
                    break
                self.conn.send(data)  # send data
                uploadedSize += 2
                print("uploading", uploadedSize, "KB")
            except socket.error as e:
                print("[-] Error Uploading File :", str(e))
            except Exception as e:
                print("[-] Error Reading Data :", str(e))
                return


def chatting(server):
    def send(stopConversation):
        while True:
            msg = input().strip()
            # check if conversation if ended
            if stopConversation[0]:
                print("conversation stopped")
                return
            elif msg == "quit":
                server.sendm(msg)
                # server.conn.close()
                stopConversation[0] = True
                return
            else:
                server.sendm(msg)

    def recv(stopConversation):
        while True:
            # check if conversation if ended
            if stopConversation[0]: return
            msg = server.recvm()
            if msg == "quit":
                server.sendm("quit")  # send quit back
                # server.conn.close()
                stopConversation[0] = True
                print("conversation stopped")
                return
            else:
                print("\033[46m" + msg)  # "\033[46m" -> show green background text
                # print("\033[44m")        # "\033[44m" -> show blue background text

    # there are two thread
    # one for sending msg (t_send) and one for receiving msg (t_recv)
    stopConversation = [False]  # flag to stop thread (list to make it mutable so that called by ref.)
    t_send = threading.Thread(target=send, args=(stopConversation,))
    t_recv = threading.Thread(target=recv, args=(stopConversation,))
    t_send.start()
    t_recv.start()
    while not stopConversation[0]:
        pass
    return


def remoteAccess(server, mode):
    def masterMode():
        while True:
            command = input().strip()
            if command == "quit":
                server.sendm(command)
                break
            elif command[:4] == "down":
                server.sendm(command)
                # fileName = pathlib.Path("C:/Users/Aman/Desktop") / command[5:]
                server.download(command[5:])
            elif command[:6] == "upload":
                server.sendm(command)
                server.upload(command[7:])
            else:
                server.sendm(command)
                print(server.recvm())

    def slaveMode():
        while True:
            command = server.recvm()
            print(command)
            if command == "quit":
                break
            elif command[:2] == "cd":
                try:
                    os.chdir(command[3:])
                    curDir = os.getcwd() + ">>"
                    server.sendm(curDir)
                except Exception:
                    server.sendm("error")
            elif command[:4] == "down":
                server.upload(command[5:])
            elif command[:6] == "upload":
                server.download(command[7:])
            else:
                cmd = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                output = cmd.stdout.read() + cmd.stderr.read()
                output = str(output, "utf-8")
                curDir = os.getcwd() + ">>"
                server.sendm(output + curDir)
                print(output)

    if mode == "master":
        masterMode()
    elif mode == "slave":
        slaveMode()


def interface(server):
    while True:
        # print Menu
        print("Select Mode :")
        print("1. Chatting")
        print("2. Remote Access (Master)")
        print("3. Remote Access (Slave)")
        print("0. Exit")
        choice = int(input("choice :"))
        # execute options
        if choice == 1:
            chatting(server)
        elif choice == 2:
            remoteAccess(server, "master")
        elif choice == 3:
            remoteAccess(server, "slave")
        elif choice == 0:
            exit()
        else:
            print("[-] Invalid selection")


if __name__ == "__main__":
    # def main():
    server = Server()
    server.bindSocket()
    server.acceptClient()

    interface(server)
