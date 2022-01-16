import socketserver
import time

cache = {}

class MyTCPHandler(socketserver.StreamRequestHandler):

    def handle(self):
        while True:
            if not self.rfile.peek():
                break
            data = self.rfile.readline().strip()
            print("{} wrote: {}".format(self.client_address[0], data))
            data_split = data.split()

            command = data_split[0].lower()
            if command == b"set":
                key, flags, exptime, length = data_split[1:5]
                no_reply = len(data_split) == 6

                value = self.rfile.read(int(length)+2)
                if exptime == b"0":
                    max_time = 0
                else:
                    max_time = time.time()+int(exptime)
                cache[key] = (int(flags), max_time, value[:-2])
                if not no_reply:
                    self.wfile.write(b"STORED\r\n")
            elif command == b"get":
                key = data_split[1]
                output = b""
                
                if cache.get(key):
                    flags, max_time, value = cache[key]
                    if max_time > 0 and time.time() > max_time:
                        del cache[key]
                    else:
                        output += b"VALUE %s %d %d\r\n%s\r\n" % (key, flags, len(value), value)

                self.wfile.write(output + b"END\r\n")



if __name__ == "__main__":
    HOST, PORT = "127.0.0.1", 9999
    with socketserver.TCPServer((HOST, PORT), MyTCPHandler) as server:
        server.serve_forever()