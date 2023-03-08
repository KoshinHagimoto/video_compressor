import socket
import json
import sys
import os

from tkinter import *
from tkinter import filedialog
from tkinter import ttk

"""
Global Variables
"""
SERVER_PORT = 9001
SERVER_ADDRESS = '127.0.0.1'

"""
Base client class
"""
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
    def __init__(self):
        self.server= (SERVER_ADDRESS, SERVER_PORT)
        super().__init__(timeout=60, buffer=4096)
        super().connect(self.server, socket.AF_INET, socket.SOCK_STREAM,  0)


def button_clicked():
    global method_params
    """
    --- second frame --
    """
    frame2 = ttk.Frame(root, padding=10)
    # button
    if method.get() == 'convert_mp3':
        button_clicked_file()
    elif method.get() == 'convert' or method.get() == 'compress':
        label_frame2 = ttk.LabelFrame(frame2, text='options', padding=(10), style='My.TLabelframe')
        if method.get() == 'convert':
            rb1 = ttk.Radiobutton(label_frame2, text='.avi', value='.avi', variable=method_params)
            rb2 = ttk.Radiobutton(label_frame2, text='.mpeg', value='.mpeg', variable=method_params)
            rb3 = ttk.Radiobutton(label_frame2, text='.mov', value='.mpeg', variable=method_params)
        elif method.get() == 'compress':
            rb1 = ttk.Radiobutton(label_frame2, text='high', value='high', variable=method_params)
            rb2 = ttk.Radiobutton(label_frame2, text='medium', value='medium', variable=method_params)
            rb3 = ttk.Radiobutton(label_frame2, text='low', value='low', variable=method_params)
        # Button
        button2 = ttk.Button(frame2, text='OK', padding=(20,5), command=button_clicked_file)
        frame2.grid()
        label_frame2.grid(row=0, column=0)
        rb1.grid(row=0, column=0)
        rb2.grid(row=0, column=1)
        rb3.grid(row=0, column=2)
        button2.grid(row=1, pady=5)
    else:
        if method.get() == 'change_resolution':
            label_frame2 = ttk.LabelFrame(frame2, text='Resolution')
            entry1 = ttk.Entry(frame2, textvariable=method_params)
            button2 = ttk.Button(frame2, text='OK', command=button_clicked_file)
            frame2.grid()
            label_frame2.grid(row=0, column=0)
            entry1.grid(row=1, column=0)
            button2.grid(row=2, pady=5)
        elif method.get() == 'convert_gif':
            global start
            global end
            label_frame2 = ttk.LabelFrame(frame2, text='Time')
            entry1 = ttk.Entry(frame2, textvariable=start)
            entry2 = ttk.Entry(frame2, textvariable=end)
            button2 = ttk.Button(frame2, text='OK', command=button_clicked_file)
            frame2.grid()
            label_frame2.grid(row=0, column=0)
            entry1.grid(row=1, column=0)
            entry2.grid(row=1, column=1)
            button2.grid(row=2, pady=5)

def button_clicked_file():
    global filepath
    file_name = filedialog.askopenfilename(initialdir='~/')
    if file_name:
        filepath.set(file_name)
        root.destroy()
        second()

def second(requests={}):
    print(f'method: {method.get()}, method_params: {method_params.get()}, filepath: {filepath.get()}')
    requests['method'] = method.get()
    if requests['method'] == 'convert_gif':
        requests['method_params']['start'] = start.get()
        requests['method_params']['end'] = end.get()
    else:
        requests['method_params'] = method_params.get()
    requests['filepath'] = filepath.get()

    try:
        with open("setting.json", "w", encoding="utf-8") as f:
            json.dump(requests, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(e)
        sys.exit()
    cli.send(filepath.get(), "setting.json")

def main():
    """
    --- main frame ---
    """
    # Frame
    frame1 = ttk.Frame(root, padding=10)
    # Style - Theme
    ttk.Style().theme_use('classic')
    # Label Frame
    label_frame = ttk.LabelFrame(frame1, text='Options', padding=(10), style='My.TLabelframe')
    # Radiobutton
    global method
    rb1 = ttk.Radiobutton(label_frame, text='convert', value='convert', variable=method)
    rb2 = ttk.Radiobutton(label_frame, text='convert to audio file', value='convert_mp3', variable=method)
    rb3 = ttk.Radiobutton(label_frame, text='change resolution', value='change_resolution', variable=method)
    rb4 = ttk.Radiobutton(label_frame, text='compress', value='compress', variable=method)
    rb5 = ttk.Radiobutton(label_frame, text='convert to gif', value='convert_gif', variable=method)
    # Button
    button1 = ttk.Button(frame1, text='OK', padding=(20,5), command=button_clicked)
    # Layout
    frame1.grid()
    label_frame.grid(row=0, column=0)
    rb1.grid(row=0, column=0)
    rb2.grid(row=0, column=1)
    rb3.grid(row=0, column=2)
    rb4.grid(row=0, column=3)
    rb5.grid(row=0, column=4)
    button1.grid(row=1, pady=5)

    # start app
    root.mainloop()

if __name__ == '__main__':
    cli = InetClient()
    root = Tk()
    root.title('Video Compressor')
    method = StringVar()
    method_params = StringVar()
    filepath=StringVar()
    start = StringVar()
    end = StringVar()
    main()