import socket
import json
import sys
import os


SERVER_PORT = 9001

class BaseClient:
    def __init__(self, timeout:int=10, buffer:int=4096):
        self.__socket = None
        self.__address = None
        self.__timeout = timeout
        self.__buffer = buffer

    def connect(self, address, family:int, typ:int, proto:int):
        self.__address = address
        self.__socket = socket.socket(family, typ, proto)
        self.__socket.settimeout(self.__timeout)
        print('connecting to {}'.format(address))
        try:
            self.__socket.connect(self.__address)
        except socket.error as err:
            print(err)
            sys.exit(1)
    
    def send(self, filepath:str, json_file:json) -> None:
        try:
            with open(filepath, 'rb') as f:
                filesize = self.getFilesize(filepath)
                filename = os.path.basename(f.name)
                filename_bits = filename.encode('utf-8')

                with open(json_file) as f2:
                    json_dict = json.load(f2)
                    json_bits = json.dumps(json_dict).encode()

                header = self.protocol_header(len(filename_bits), len(json_bits), filesize)

                self.__socket.send(header)
                self.__socket.send(filename_bits)
                self.__socket.send(json_bits)

                data = f.read(4096)
                while data:
                    self.__socket.send(data)
                    data = f.read(4096)
                
            p_header = self.__socket.recv(8)
            p_filename_length = int.from_bytes(p_header[:1], "big")
            p_data_length = int.from_bytes(p_header[1:8], "big")
            stream_rate = 4096

            print('Received header from server. Byte length: Title length {}, Data length {}'.format(p_filename_length, p_data_length))

            p_filename = self.__socket.recv(p_filename_length).decode('utf-8')
            print('Filename: {}'.format(p_filename))
            if p_data_length == 0:
                raise Exception('No data to read from client.')
        
            with open(p_filename, 'wb+') as f:
                while p_data_length > 0:
                    data = self.__socket.recv(p_data_length if p_data_length <= stream_rate else stream_rate)
                    f.write(data)
                    p_data_length -= len(data)
            print('Completed !!!')
        except TypeError as err:
            print(err)
            sys.exit()
        try:
            self.__socket.shutdown(socket.SHUT_RDWR)
            self.__socket.close()
        except:
            pass

    def getFilesize(self, filepath):
        with open(filepath, 'rb') as f:
            f.seek(0, os.SEEK_END)
            filesize = f.tell()
        return filesize
    
    def protocol_header(self, filename_length, json_length, data_length):
        return filename_length.to_bytes(1, "big") + json_length.to_bytes(2, "big") + data_length.to_bytes(5, "big")

class InetClient(BaseClient):
    def __init__(self, server_address):
        self.server= (server_address, SERVER_PORT)
        super().__init__(timeout=60, buffer=4096)
        super().connect(self.server, socket.AF_INET, socket.SOCK_STREAM,  0)

def main():
    server_address = input("Type in the server's address to connect to: ")
    cli = InetClient(server_address)
    requests = {}
    requests['filepath'] = input('Type in a mp4 file to upload: ')
    print('Please enter a method.\n')
    print('Choises: convert, convert to audio file, change resolution, compress, convert to gif')
    method = input('>>>')
    while True:
        if method == 'convert':
            requests['method'] = 'convert'
            requests['method_params'] = input('Please enter extension: ')
            break
        elif method == 'convert to audio file':
            requests['method'] = 'convert_mp3'
            break
        elif method == 'change resolution':
            requests['method'] = 'change_resolution'
            requests['method_params'] = input('Please enter resolution(1280:720...): ')
            break
        elif method == 'compress':
            requests = 'compress'
            print('Please select compression level (high, medium or low)\n')
            requests['method_params'] = input('>>>')
            break
        elif method == 'convert to gif':
            requests['method'] = 'convert_gif'
            requests['method_params']['start'] = input('Please enter start time: ')
            requests['method_params']['end'] = input('Please enter end time: ')
            break
        else:
            print('Please re-enter a method ')
            method = input('>>> ')
    filepath = requests['filepath']
    try:
        with open("setting.json", "w", encoding="utf-8") as f:
            json.dump(requests, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(e)
        sys.exit()
    cli.send(filepath, "setting.json")

if __name__ == '__main__':
    main()