import socket
import os
import json
import subprocess

from pathlib import Path

dpath = 'temp'
SERVER_ADDRESS = '0.0.0.0'
SERVER_PORT = 9001

class MethodError(Exception):
    pass

class BaseServer:
    def __init__(self):
        self.__socket = None
        self.close()
    
    def __del__(self):
        self.close()
    
    def close(self) -> None:
        try:
            self.__socket.shutdown(socket.SHUT_RDWR)
            self.__socket.close()
        except:
            pass
    
    def create_socket(self, address, family:int, typ:int, proto:int):
        self.__socket = socket.socket(family, typ, proto)
        self.__socket.settimeout(60)
        self.__socket.bind(address)
        self.__socket.listen(1)
        print("Server started :", address)
        return self.__socket.accept()


class UnixServer(BaseServer):
    def __init__(self, buffer:int=4096):
        self.__buffer = buffer
        self.address = (SERVER_ADDRESS, SERVER_PORT)
        
    def accept(self, connection, client_address):
        while True:
            try:
                print('connection from', client_address)
                print('IP address: {}, port: {}'.format(client_address[0], client_address[1]))
                header = connection.recv(8)

                filename_length = int.from_bytes(header[:1], "big")
                json_length = int.from_bytes(header[1:3], "big")
                data_length = int.from_bytes(header[3:8], "big")
                stream_rate = 4096

                print('Received header from client. Byte length: Title length {}, JSON length {}, Data length {}'.format(filename_length, json_length, data_length))

                filename = connection.recv(filename_length).decode('utf-8')

                print('Filename: {}'.format(filename))
  
                if json_length != 0:
                    json_paket =  connection.recv(json_length)
                    json_dict = json.loads(json_paket.decode('utf-8'))
                    print(json_dict)
    
                if data_length == 0:
                    raise Exception('No data to read from client.')
        
                filepath = os.path.join(dpath, filename)
                with open(filepath, 'wb+') as f:
                    while data_length > 0:
                        data = connection.recv(data_length if data_length <= stream_rate else stream_rate)
                        f.write(data)
                        data_length -= len(data)
                print('Finished downloading the file from client.')
                print('Process method: {}'.format(json_dict['method']))
                try:
                    output_path = self.process(filepath, json_dict)
                except MethodError as err:
                    print(err)
                    break

                with open(output_path, 'rb') as f:
                    f.seek(0, os.SEEK_END)
                    output_filesize = f.tell()
                    f.seek(0, 0)
                    output_filename = os.path.basename(f.name)
                    output_filename_bits = output_filename.encode('utf-8')
                    output_header = self.protocol_header(len(output_filename_bits), output_filesize)

                    connection.send(output_header)
                    connection.send(output_filename_bits)

                    data = f.read(4096)
                    while data:
                        connection.send(data)
                        data = f.read(4096)
                    
                print('Finish !!!')
                break
            except ConnectionResetError:
                break
            except BrokenPipeError:
                break
        self.close()
        print("Finish")
    
    def process(self, filepath:str, json_dict:dict) -> str:
        method = json_dict['method']
        if method == 'convert':
            extension = json_dict['method_params']
            command = f'ffmpeg -i {filepath} {dpath}/output{extension}'
            subprocess.call(command, shell=True)
            return dpath + '/output' + extension
        elif method == 'convert_mp3':
            command = f'ffmpeg -i {filepath} -vn {dpath}/output.mp3'
            subprocess.call(command, shell=True)
            return dpath + '/output.mp3'
        elif method == 'change_resolution':
            resolution = json_dict['method_params']
            command = f'ffmpeg -i {filepath} -filter:v scale={resolution} -c:a copy {dpath}/output.mp4'
            subprocess.call(command, shell=True)
            return dpath + '/output.mp4'
        elif method == 'compress':
            level = json_dict['method_params']
            if level == 'high':
                command = f'ffmpeg -i {filepath} -vcodec libx265 {dpath}/output.mp4'
            elif level == 'low':
                command == f'ffmpeg -i {filepath} {dpath}/output.mp4'
            else:
                command = f'ffmpeg -i {filepath} -b:v 1200k {dpath}/output.mp4'
            subprocess.call(command, shell=True)
            return dpath + '/output.mp4'
        elif method == 'convert_gif':
            start = json_dict['method_params']['start']
            end = json_dict['method_params']['end']
            command = f'ffmepg -ss {start} -i {filepath} -to {end} -r 10 -vf scale=300:-1 {dpath}/output.gif'
            subprocess.call(command, shel=True)
            return dpath + '/output.gif'
        else:
            print("This method cannot be processed.")
            raise MethodError(method)
    
    def protocol_header(self, filename_length, data_length):
        return filename_length.to_bytes(1, "big") + data_length.to_bytes(7, "big")



def main():
    if not os.path.exists(dpath):
        os.makedirs(dpath)
    print('Starting up on {} port {}'.format(SERVER_ADDRESS, SERVER_PORT))
    server = UnixServer()
    connection, client_address = server.create_socket(server.address, socket.AF_INET, socket.SOCK_STREAM, 0)
    server.accept(connection, client_address)


if __name__ == '__main__':
    main()
