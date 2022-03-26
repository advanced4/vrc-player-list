import ctypes
from tkinter import *
from tkinter import ttk, font
from tkinter import scrolledtext
import glob
import os
import time
import datetime
import threading

import pytz
from prettytable import prettytable
from tzlocal import get_localzone

# made by lightbulb 💡

# TODO - tbh probably never going to get to these
# persistent player join log
# better taskbar icon/window icon
# dynamic window sizing

### SETTINGS ###
update_frequency_ms = 1000
################
# you shouldn't have to touch any of these
logpath = "%AppData%\\..\\LocalLow\\VRChat\\vrchat\\"
#"%AppData%\..\LocalLow\VRChat\vrchat\"
#player_list = []
player_list = [{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob1", "joined":1648253578},{"name":"bob5", "joined":1648253578},{"name":"bob4", "joined":1648253578},{"name":"bob3", "joined":1648253578},{"name":"bob2", "joined":1648253578}]
# this is probably more reliable than "OnPlayerJoined"
join_msg = "[Behaviour] Initialized PlayerAPI"
left_msg = "[Behaviour] OnPlayerLeft "
newworld = "[Behaviour] Finished entering world"
logfile, loggenerator = None, None
local_tz = get_localzone()
root = Tk()
current_file = None
################


class LogWatcher(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.start()

    def raise_exception(self):
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(self.ident,
              ctypes.py_object(SystemExit))
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(self.ident, 0)
            print('Exception raise failure')

    def watch(self, generator):
        global player_list
        global current_file
        last_file_check_time = time.time()
        for line in generator:
            # every minute check and make sure we're on the latest file
            if time.time() - last_file_check_time > 60:
                tmp_latest_file = get_latest_file()
                if tmp_latest_file != current_file:
                    current_file = tmp_latest_file
                    break

            # vrchat y u have so many newlines hmm
            if not (line == "" or line == "\n"):
                parseme = line.strip()

                if newworld in parseme:
                    player_list = []

                if join_msg in parseme:
                    # Someone joined
                    playername = parseme.split(join_msg)[1].split("\"")[1]
                    print("Player Joined: " + playername)
                    if not is_user_in_list(playername):
                        player_list.append({"name": playername, "joined": int(time.time())})
                    print(player_list)

                if left_msg in parseme:
                    # Someone left
                    playername = parseme.split(left_msg)[1]
                    print("Player Left: " + playername)
                    if is_user_in_list(playername):
                        player_list = [i for i in player_list if not (i['name'] == playername)]
                    print(player_list)

    def run(self):
        global current_file
        while True:
            latest_file = get_latest_file()
            current_file = latest_file
            logfile = open(latest_file, "r", encoding="utf-8")
            self.watch(follow(logfile))


def get_latest_file():
    appdata = os.path.dirname(os.getenv('APPDATA'))
    logpath = os.path.join(appdata, "LocalLow", "VRChat", "vrchat")
    logfiles = glob.glob(logpath + os.sep + "output_log_*.txt")
    return max(logfiles, key=os.path.getctime)


def follow(thefile):
    # seek the end of the file
    thefile.seek(0, os.SEEK_END)

    # start infinite loop
    while True:
        # read last line of file
        line = thefile.readline()
        # sleep if file hasn't been updated
        if not line:
            time.sleep(0.1)
            continue
        yield line


def get_timestamp(timestamp_s):
    x = datetime.datetime.utcfromtimestamp(timestamp_s)
    local_now = x.replace(tzinfo=pytz.utc).astimezone(local_tz).strftime("%H:%M:%S") # utc -> local
    return local_now


def get_time_with_you(timestamp_s):
    diff_seconds = int(time.time()) - timestamp_s
    m, s = divmod(diff_seconds, 60)
    h, m = divmod(m, 60)
    return f'{h:d}:{m:02d}:{s:02d}'


def is_user_in_list(username):
    for user in player_list:
        if username == user["name"]:
            return True
    return False


def update_playerlist():
    root.after(update_frequency_ms, update_playerlist)
    how_many_on_left_side = int(len(player_list) / 2) + (len(player_list) % 2 > 0)
    how_many_on_right_side = len(player_list) - how_many_on_left_side

    # allow changing text
    txtbox.config(state=NORMAL)
    txtbox.delete("1.0", END)
    txtboxr.config(state=NORMAL)
    txtboxr.delete("1.0", END)

    table = prettytable.PrettyTable(header=True, vrules=prettytable.FRAME, border=False, align="l", padding_width=2)
    # ya idk alignment is weird, im sure not all of this is needed but it works
    table.align = "l"
    table.field_names = ["Users-"+str(len(player_list)), "Joined", "TimeWithU"]
    table.align["Users-"+str(len(player_list))] = "l"
    table.align["Joined"] = "l"
    table.align["TimeWithU"] = "l"

    tabler = prettytable.PrettyTable(header=True, vrules=prettytable.FRAME, border=False, align="l", padding_width=2)
    # ya idk alignment is weird, im sure not all of this is needed but it works
    tabler.align = "l"
    tabler.field_names = ["Users-"+str(len(player_list)), "Joined", "TimeWithU"]
    tabler.align["Users-"+str(len(player_list))] = "l"
    tabler.align["Joined"] = "l"
    tabler.align["TimeWithU"] = "l"

    counter = 0
    for player in player_list:
        if counter < how_many_on_left_side:
            table.add_row([player["name"], get_timestamp(player["joined"]), get_time_with_you(player["joined"])])
            counter += 1
        else:
            tabler.add_row([player["name"], get_timestamp(player["joined"]), get_time_with_you(player["joined"])])

    txtbox.insert(END, table)
    txtbox.config(state=DISABLED)
    txtboxr.insert(END, tabler)
    txtboxr.config(state=DISABLED)
    root.update()


def die(lw):
    lw.raise_exception()
    root.destroy()
    sys.exit()


if __name__ == "__main__":
    logwatcher = LogWatcher()

    root.geometry("500x600")
    root.attributes('-alpha', 0.9)
    root.title("PlayerList 💡")
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=1)

    root.grid()
    # txtbox = scrolledtext.ScrolledText(root, wrap="none")
    txtbox = Text(root, wrap="none")
    txtbox.grid(row=0, column=0, sticky='NSW')
    txtbox.grid_columnconfigure(0, weight=1)
    txtbox.config(state=DISABLED)  # make it readonly
    txtbox.configure(font=font.Font(family="Consolas", size=8), background="black", foreground="white") # only use monospace fonts

    txtboxr = scrolledtext.ScrolledText(root, wrap="none")
    txtboxr.grid(row=0, column=1, sticky='NSE')
    txtboxr.grid_columnconfigure(1, weight=1)
    txtboxr.config(state=DISABLED)  # make it readonly
    txtboxr.configure(font=font.Font(family="Consolas", size=8), background="black", foreground="white") # only use monospace fonts

    ttk.Button(root, text="Quit", command=lambda: die(logwatcher)).grid(column=0, row=1, pady=10)

    # root.tk.call('wm', 'iconphoto', root._w, PhotoImage(data=ico))

    root.protocol("WM_DELETE_WINDOW", lambda: die(logwatcher))
    root.after(update_frequency_ms, update_playerlist)
    update_playerlist()
    root.mainloop()
