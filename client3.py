# Python program to translate
# speech to text and text to speech
import hashlib
import hmac
import socket
import ssl
import threading as th

import speech_recognition as sr

from enter_screen1 import Ui_startWindow, show_win
from log_in_screen1 import Ui_LogInWindow, show_window
from ready_screen import Ui_readyWindow, show_ready_window
from sign_in_screen import Ui_signUpWindow, show_sign_window
from game_screen1 import Ui_gameWindow, show_game

context = ssl.create_default_context()
# Set the context to not verify the server's SSL/TLS certificate
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE


class Client:

    def __init__(self, server_socket):
        self.socket = server_socket
        self.screen_state = -1
        self.first_name = ""
        self.last_name = ""
        self.username = ""
        self.password = ""
        self.client_ready = False
        self.client_singed = False


def calc_digest(key, message):
    key = bytes(key, 'utf-8')
    message = bytes(message, 'utf-8')
    dig = hmac.new(key, message, hashlib.sha256)
    return dig.hexdigest()


def create_msg(data_to_send):
    data_len = len(data_to_send)
    data_len_len = len(str(data_len))
    data_len = str(data_len)
    for i in range(4 - data_len_len):
        data_len = "0" + data_len
    hmac_data = calc_digest("banana", data_to_send)
    return hmac_data + data_len + data_to_send


def handle_msg(client_socket):
    hmac_received = client_socket.recv(64).decode()
    data_len_received = client_socket.recv(4).decode()
    data_received = client_socket.recv(int(data_len_received)).decode()
    if calc_digest("banana", data_received) != hmac_received:
        return "!"
    return data_received


def voice_to_text():
    global MyText
    r = sr.Recognizer()
    try:
        # use the microphone as source for input.
        with sr.Microphone() as source2:

            # wait for a second to let the recognizer
            # adjust the energy threshold based on
            # the surrounding noise level
            r.adjust_for_ambient_noise(source2, duration=0.2)

            # listens for the user's input
            audio2 = r.listen(source2)
            # Using google to recognize audio
            MyText = r.recognize_google(audio2)

    except sr.RequestError as e:
        print("Could not request results; {0}".format(e))

    except sr.UnknownValueError:
        print("unknown error occurred")


categories_milon = {
    "country": 0,
    "capital": 1,
    "boy": 2,
    "movie": 3,
    "animal": 4,
    "fruit/vegetable": 5,
    "household item": 6,
}
ans = " "
closeFunc = False
MyText = ""
counterOfText = 0
buf = 1024
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('127.0.0.1', 8820))
s = context.wrap_socket(s, server_hostname='127.0.0.1')
socket_running = True
client1 = Client(s)
start_window = Ui_startWindow(client1)
ready_window = Ui_readyWindow(client1)
game_window = Ui_gameWindow(client1)
round_num = 0
try:
    e = th.Thread(target=show_win, args=(start_window,))
    e.start()
except:
    pass

while client1.screen_state == -1:
    pass
if client1.screen_state == 0:
    sign_in_window = Ui_signUpWindow(client1)
    try:
        c = th.Thread(target=show_sign_window, args=(sign_in_window,))
        c.start()
    except:
        pass
    while client1.username == "":
        pass
    s.send(("username:" + client1.username).encode())
    current_username = client1.username
    data = s.recv(1024).decode()
    print(data)
    while "taken" in data:
        sign_in_window.username_taken.show()
        while client1.username == current_username:
            pass
        s.send(("username:" + client1.username).encode())
        data = s.recv(1024).decode()
    userInfo = client1.username + " " + client1.first_name + " " + client1.last_name + " " + client1.password
    client1.client_singed = True
    s.send(userInfo.encode())
    data = s.recv(1024).decode()
    print(data)
elif client1.screen_state == 1:
    log_in_window = Ui_LogInWindow(client1)
    try:
        d = th.Thread(target=show_window, args=(log_in_window,))
        d.start()
    except:
        pass
    while client1.username == "":
        pass
    s.send(("usernameold:" + client1.username).encode())
    old_username = client1.username
    data = s.recv(1024).decode()

    while "found." in data:
        log_in_window.label_2.show()
        while client1.username == old_username:
            pass
        s.send(("username:" + client1.username).encode())
        old_username = client1.username
        data = s.recv(1024).decode()
    s.send(("password:" + client1.password).encode())
    old_password = client1.password
    data = s.recv(1024).decode()
    while "wrong:" in data:
        log_in_window.label_2.show()
        while client1.password == old_password:
            pass
        s.send(("password:" + client1.password).encode())
        data = s.recv(1024).decode()
        print(data)
    client1.client_singed = True
while socket_running:
    client1.client_ready = False
    round_num = 0
    client1.screen_state = 2
    try:
        w = th.Thread(target=show_ready_window, args=(ready_window,))
        w.start()
    except:
        pass
    while client1.client_ready is False:
        pass
    try:
        c = th.Thread(target=ready_window.loading_animation)
        c.start()
    except:
        pass
    s.send("ready: indeed".encode())
    data = s.recv(1024).decode()
    print(data)

    print(data)
    client1.screen_state = 3
    try:
        t1 = th.Thread(target=show_game, args=(game_window,))
        t1.start()
    except:
        pass
    while round_num < 3:
        round_num += 1
        try:
            t1 = th.Thread(target=game_window.start_round)
            t1.start()
        except:
            pass
        while "The letter" not in data:
            data = s.recv(1024).decode()
        letter = data.split(":")[1]
        game_window.set_letter(round_num, letter)
        ans = " "
        while "finished:" not in ans:
            print(ans)
            MyText = " "
            voice_to_text()
            s.send(MyText.encode())
            ans = s.recv(buf).decode()
            if "you " in ans:
                ans_list = ans.split(":")
                cat_list = ans.split("?")
                for i in range(int(len(ans_list) / 2)):
                    # table in row round num, coloum category dictionary = ans list 1+2i
                    game_window.insert_value(categories_milon[cat_list[1 + 2 * i]], round_num, ans_list[1 + 2 * i])
                    pass

        print(ans)
        s.send("game done:".encode())
