#coding=utf-8
import os
import sys
def output(*argv):
    sargv = [str(s) for s in argv]
    sys.__stdout__.write(' '.join(sargv)+"\n")
import cStringIO
import subprocess
import threading
import socket
import struct
import time 
class System(object):
    def __init__(self, stdin = None):
        self.stdin = stdin 
    def pipe_read(self, wt):
        try:
            wt.seek(0, os.SEEK_END)
            l = wt.tell()
        except:
            return ""
        return wt.read(l)
    def __call__(self, cmd):
        if self.stdin is not None:
            p = subprocess.Popen(cmd,shell=True,stdin = subprocess.PIPE, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        else:
            p = subprocess.Popen(cmd,shell=True, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        while True:
            rst = p.poll()
            #output("<rst:", rst,">")
            s = self.pipe_read(p.stdout)+self.pipe_read(p.stderr)
            if len(s)>0:
                print s 
            if rst is None:
                rcv = None 
                if self.stdin is not None and hasattr(self.stdin, "timeout_read"):
                    rcv = self.stdin.timeout_read()
                    output("<recv from timeout_read:",rcv,">")
                else:
                    time.sleep(0.1) 
                if rcv is not None:
                    p.stdin.write(rcv)
                continue 
            break 
        s = p.stdout.read()+p.stderr.read()
        p.stdout.close()
        p.stderr.close()
        print s
        return rst
system = System()
def system_backup(cmd):
    p = subprocess.Popen(cmd,shell=True,stdin = subprocess.PIPE, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    while True:
        rst = p.poll()
        if rst is None:
            time.sleep(1.0)
            continue 
            pass 
        break 
    s = p.stdout.read()+p.stderr.read()
    p.stdout.close()
    p.stderr.close()
    print s
    return rst
os.system=system
"""
server:

python
import remotec as rm
rm.server()


client:

python
import remotec
client = remotec.connect()


"""
max_recv = 65536
class IOBase(object):
    def read(self, size=-1):
        return ""
    def readline(self, size=-1):
        return ""
    def flush(self):
        pass 
    def write(self, s):
        pass 
class ClientOrder(object):
    def command(self, cmd):
        return 'e'+cmd
    def close(self):
        return 'c'
    def is_close(self, cmd):
        return cmd == 'c'
    def is_command(self, cmd):
        return cmd[0] == 'e'
    def get_command(self, cmd):
        return cmd[1:]
    def close_all(self):
        return 'a'

class ServerOrder(object):
    def finish_result(self):
        return 'f'
    def result(self, rst):
        return 'n'+rst
    def exception(self, err):
        return 'e'+str(err)
    def close(self):
        return 'c'
    def is_finish_result(self, cmd):
        return cmd == 'f' 
    def is_close(self, cmd):
        return cmd == 'c'
    def is_exception(self, cmd):
        return cmd[0] == 'e'
    def is_normal(self, cmd):
        return cmd[0] == 'n'
    def get_command(self, cmd):
        return cmd[1:]

client_order = ClientOrder()
server_order = ServerOrder()
class SafeSocket(object):
    def __init__(self, socket):
        self.socket = socket 
        self.buf = ""
    def __getattribute__(self, name):
        if name in ['socket', 'send', 'recv', 'buf','safe_get','timeout_recv']:
            return object.__getattribute__(self, name)
        return getattr(self.socket, name)
    def send(self, s):
        l = len(s) 
        s = struct.pack(">i",l)+s 
        self.socket.send(s)
    def safe_get(self):
        s = self.buf 
        if len(s)<4:
            return None 
        sl = s[:4]
        l, = struct.unpack(">i", sl)
        s = s[4:]
        if len(s)<l:
            return None 
        rst = s[:l]
        s = s[l:]
        self.buf = s 
        return rst
    def recv(self, max_size = -1):
        s = None
        while s is None:
            s = self.safe_get()
            if s is None:
                rcv = self.socket.recv(max_size)
                self.buf += rcv
        return s 
    def timeout_recv(self, max_size = -1, timeout = None):
        if timeout is not None:
            backup_timeout = self.socket.gettimeout()
            self.socket.settimeout(timeout)
        try:
            rst = self.recv(max_size)
            return rst 
        except Exception,err:
            serr = str(err).strip()
            if serr == "timed out":
                return None 
            raise err
        finally:
            if timeout is not None:
                self.socket.settimeout(backup_timeout)
class RemoteInput(IOBase):
    def __init__(self, socket):
        self.socket = socket 
        self.buf = []
    def remain(self):
        s = '\n'.join(self.buf)
        self.buf = []
        return s 
    def timeout_read(self, size = -1, timeout = 0.1):
        size = max(max_recv, size)
        rst = self.socket.timeout_recv(size, timeout)
        if rst is not None:
            rst = client_order.get_command(rst)
        return rst 
        
    def readline(self, size=-1):
        rst = self.read(size)
        rst = rst.split("\n")
        self.buf += rst[1:]
        return rst[0]
    def read(self, size=-1):
        size = max(max_recv, size)
        rst = self.socket.recv(size)
        output("server recv:",rst)
        rst = client_order.get_command(rst)
        return rst 
    def __getattribute__(self, name):
        if name in ['socket', 'buf', 'read', 'readline','remain','timeout_read']:
            return object.__getattribute__(self, name)
        output("__getattribute__ unknown in input:", name)
        return object.__getattribute__(self, name)
    
class RemoteOutput(IOBase):
    def __init__(self, socket):
        self.socket = socket 
        self.softspace = 0
    def write(self, s):
        s = server_order.result(s)
        output("<send to socket:[%s],%d>"% (s, len(s)))
        self.socket.send(s)
    def flush(self):
        output("call to flush")
    def __getattribute__(self, name):
        if name in ['socket', 'softspace', 'write', 'flush']:
            return object.__getattribute__(self, name)
        output("__getattribute__ unknown in output:", name)
        return object.__getattribute__(self, name)

class Client(object):
    @staticmethod
    def connect(ip, port, timeout = 1.5):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(timeout)
        try:
            client.connect((ip,port))
            return client
        except Exception,err:
            return None
    def connected(self):
        return self.socket != None
    def __init__(self, ip, port, timeout =1.5):
        self.ip = ip
        self.port = port
        socket = self.connect(ip, port, timeout)
        if socket is not None:
            socket = SafeSocket(socket)
        self.socket =socket
    def close(self, timeout = None):
        command = client_order.close()
        try:
            self.socket.settimeout(timeout)
            while True:
                #self.socket.setblocking(1)
                self.socket.send(command)
                rst = self.socket.recv(max_recv)
                if server_order.is_close(rst):
                    break
        except Exception, err:
            print "error in run command:", err
            try:
                import traceback
                traceback.print_exc()
            except:
                print("Can't use module traceback to show details") 
            return None
        finally:
            self.socket.close()
    def recv(self):
        try:
            rst = self.socket.recv(max_recv)
            return rst 
        except Exception,err:
            serr = str(err).strip()
            if serr == "timed out":
                #output("<time out>")
                return None 
            raise err
    def update(self, command, timeout = None):
        command = client_order.command(command)
        try:
            self.socket.settimeout(timeout)
            #output("<command send:",command,">")
            self.socket.send(command)
            _timeout = self.socket.gettimeout()
            self.socket.settimeout(0.3)
            while True:
                rst = self.recv()
                if rst is None:
                    return None  
                cmd = server_order.get_command(rst)
                if server_order.is_exception(rst):
                    print "command Error:", cmd
                    break 
                elif server_order.is_close(rst):
                    print "Server Closed"
                    self.socket.close()
                elif server_order.is_finish_result(rst):
                    break 
                else:
                    sys.stdout.write(cmd)
            self.socket.settimeout(_timeout)
            return ""
        except Exception, err:
            self.socket.close()
            print "update: error in run command:", err
            try:
                import traceback
                traceback.print_exc()
            except:
                print("Can't use module traceback to show details") 
            return ""
pass
#from multiprocessing import Process
class RemoteCommand(object):
    lock = threading.Lock()
    @staticmethod
    def new_remote(socket, address):
        rc = RemoteCommand(socket, address)
        #p = Process(target=prun,args=(rc,))
        thd = threading.Thread(target = rc.run)
        thd.start()
        return thd
    def __init__(self, socket, address):
        socket = SafeSocket(socket)
        self.socket = socket
        self.address = address
        self.input = RemoteInput(socket)
        self.output = RemoteOutput(socket)
    def run(self):
        try:
            while True:
                recv = self.socket.recv(max_recv)
                if client_order.is_close(recv):
                    self.socket.send(server_order.close())
                    output("close socket")
                    break
                cmd = client_order.get_command(recv)
                try:
                    #with RemoteCommand.lock:
                    #redirect_output = cStringIO.StringIO()
                    out_mark = sys.stdout == sys.__stdout__
                    err_mark = sys.stderr == sys.__stderr__
                    in_mark = sys.stdin == sys.__stdin__
                    self.output.send_mark = False
                    if out_mark:
                        sys.stdout = self.output
                    if err_mark:
                        sys.stderr = self.output
                    if in_mark:
                        sys.stdin = self.input 
                        global system
                        system.stdin = self.input 
                    output("cmd:", cmd)
                    exec(cmd)
                    rst = server_order.finish_result()
                    self.socket.send(rst)
                    output("send finish_result:", rst)
                except Exception,err:
                    rst = server_order.exception(err)
                    self.socket.send(rst)
                finally:
                    out_mark = sys.stdout == self.output
                    err_mark = sys.stderr == self.output
                    in_mark = sys.stdin == self.input 
                    if out_mark:
                        sys.stdout = sys.__stdout__
                    if err_mark:
                        sys.stderr = sys.__stderr__
                    if in_mark:
                        sys.stdin = sys.__stdin__
        except Exception, err:
            try:
                import traceback
                traceback.print_exc()
            except:
                print("Can't use module traceback to show details") 
            pass
        finally:
            self.socket.close()
class Server(object):
    def __init__(self, ip, port, max_connect = 5):
        self.ip = ip
        self.port = port
        self.max_connect = max_connect
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((ip,port))
        server.listen(max_connect)
        self.socket = server
    def run(self):
        while True:
            client, address = self.socket.accept()
            RemoteCommand.new_remote(client, address)

def server(ip = '127.0.0.1', port = 3456, max_connect = 10):
    sv = Server(ip, port, max_connect)
    sv.run()
    return

def connect(ip = '127.0.0.1', port = 3456, timeout = 1.5):
    client = Client(ip, port, timeout)
    return client
def mark_continue(s):
    tmp_s = s.split("#")[0].strip()
    return len(tmp_s) >0 and tmp_s[-1] == ":"
def client_run(client, start_mark = '<', end_mark = '>', input_mark = ">>>", middle_mark = "..."):
    try:
        input_mark_show = True
        while True:
            if input_mark_show:
                sys.stdout.write(input_mark)
            s = raw_input()+"\n"
            if mark_continue(s):
                while True:
                    sys.stdout.write(middle_mark)
                    ts = raw_input()+"\n"
                    s += ts
                    if len(ts) == 1:
                        break 
                    elif len(ts.strip())>0 and ts.strip()[0] == ts[0] and not mark_continue(ts):
                        break 
            while s.count('"""')%2!=0:
                sys.stdout.write(middle_mark)
                ts = raw_input()+"\n"
                s += ts
                
            if s[:len(start_mark)] == start_mark:
                s = ""
                while True:
                    sys.stdout.write(middle_mark)
                    ts = raw_input()+"\n"
                    if ts[:len(end_mark)] == end_mark :
                        break
                    if len(ts) == 0 or ts[-1]!="\n":
                        ts+="\n"
                    s += ts
            ts = s.rstrip()
            #print "command:", s 
            if ts == "close()":
                client.close()
                break
            else:
                input_mark_show = client.update(s) is not None
                #sys.stdout.write(client.update(s))
    except Exception,err:
        print "Get Error:", err
        try:
            import traceback
            traceback.print_exc()
        except:
            print("Can't use module traceback to show details") 


def cmd():
    kind = 'server'
    ip = '127.0.0.1'
    port = 3456
    max_connect = 10
    timeout = 1.5
    la = len(sys.argv)
    if la > 1:
        kind = sys.argv[1]
        if la > 2:
            ip = sys.argv[2]
            if la >3:
                port = int(sys.argv[3])
    if kind == 'server':
        if la > 4:
            max_connect  = int(sys.argv[4])
        server(ip, port, max_connect)
    elif kind == 'client':
        if la > 4:
            timeout  = float(sys.argv[4])
        client = connect(ip, port, timeout)
        if not client.connected():
            print "failed to connect server", ip, port
            return
        client_run(client)
    else:
        print "error kind", kind,", it should be server or client"
if __name__ == '__main__':
    cmd()