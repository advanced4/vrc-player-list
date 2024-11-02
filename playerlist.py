import ctypes
import threading
import time
import datetime
import os
import glob
import sys

from tkinter import Tk, Text, font, ttk, END, DISABLED, NORMAL
import pytz
from prettytable import PrettyTable
from tzlocal import get_localzone

# made by lightbulb 💡

### SETTINGS ###
update_frequency_ms = 1000
check_new_log_interval = 30  # seconds
dynamic_sizing = True  # Set to False for fixed window size
################

player_list = []
join_msg = "[Behaviour] Initialized PlayerAPI"
left_msg = "[Behaviour] Unregistering "
new_world_msg = "[Behaviour] Finished entering world"
local_tz = get_localzone()
current_file = None

class LogWatcher(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True  # Allow thread to be killed when main program exits
        self.start()

    def raise_exception(self):
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(self.ident),
                          ctypes.py_object(SystemExit))
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(self.ident, 0)
            print('Exception raise failure')

    def watch(self, logfile):
        global player_list
        global current_file
        last_file_check_time = time.time()
        while True:
            line = logfile.readline()
            if not line:
                time.sleep(0.1)
            else:
                parseme = line.strip()
                if not parseme:
                    continue

                if new_world_msg in parseme:
                    player_list = []

                if join_msg in parseme:
                    # Someone joined
                    try:
                        playername = parseme.split(join_msg)[1].split("\"")[1]
                        print("Player Joined: " + playername)
                        if not is_user_in_list(playername):
                            player_list.append({"name": playername, "joined": int(time.time())})
                    except IndexError as e:
                        print(f"Error parsing join message: {e}")
                    print(player_list)

                if left_msg in parseme:
                    # Someone left
                    try:
                        playername = parseme.split(left_msg)[1]
                        print("Player Left: " + playername)
                        if is_user_in_list(playername):
                            player_list = [i for i in player_list if i['name'] != playername]
                    except IndexError as e:
                        print(f"Error parsing left message: {e}")
                    print(player_list)

            # Check every 'check_new_log_interval' seconds if a new log file is available
            if time.time() - last_file_check_time > check_new_log_interval:
                last_file_check_time = time.time()
                tmp_latest_file = get_latest_file()
                if tmp_latest_file != current_file:
                    current_file = tmp_latest_file
                    print(f"Switching to new log file: {current_file}")
                    logfile.close()
                    logfile = open(current_file, "r", encoding="utf-8")
                    continue

    def run(self):
        global current_file
        while True:
            try:
                latest_file = get_latest_file()
                if latest_file is None:
                    print("No log file found. Waiting for log file to be created...")
                    time.sleep(1)
                    continue

                current_file = latest_file
                print(f"Using log file: {current_file}")
                with open(latest_file, "r", encoding="utf-8") as logfile:
                    self.watch(logfile)
            except Exception as e:
                print(f"LogWatcher error: {e}")
                time.sleep(1)  # Wait before retrying

def get_latest_file():
    appdata = os.path.dirname(os.getenv('APPDATA'))
    logpath = os.path.join(appdata, "LocalLow", "VRChat", "vrchat")
    logfiles = glob.glob(os.path.join(logpath, "output_log_*.txt"))
    if not logfiles:
        return None
    return max(logfiles, key=os.path.getctime)

def get_timestamp(timestamp_s):
    x = datetime.datetime.utcfromtimestamp(timestamp_s)
    local_now = x.replace(tzinfo=pytz.utc).astimezone(local_tz).strftime("%H:%M:%S")  # utc -> local
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
    if len(player_list) == 0:
        # Clear the text boxes if no players
        txtbox.config(state=NORMAL)
        txtbox.delete("1.0", END)
        txtbox.config(state=DISABLED)
        txtboxr.config(state=NORMAL)
        txtboxr.delete("1.0", END)
        txtboxr.config(state=DISABLED)
        return

    how_many_on_left_side = int(len(player_list) / 2) + (len(player_list) % 2 > 0)

    # Allow changing text
    txtbox.config(state=NORMAL)
    txtbox.delete("1.0", END)
    txtboxr.config(state=NORMAL)
    txtboxr.delete("1.0", END)

    # Updated PrettyTable instantiation
    table = PrettyTable()
    table.header = True
    table.border = False
    table.align = "l"
    table.padding_width = 2
    table.field_names = ["Users -" + str(len(player_list)), "Joined", "Time With U"]

    tabler = PrettyTable()
    tabler.header = True
    tabler.border = False
    tabler.align = "l"
    tabler.padding_width = 2
    tabler.field_names = ["Users -" + str(len(player_list)), "Joined", "Time With U"]

    for idx, player in enumerate(player_list):
        row = [player["name"], get_timestamp(player["joined"]), get_time_with_you(player["joined"])]
        if idx < how_many_on_left_side:
            table.add_row(row)
        else:
            tabler.add_row(row)

    txtbox.insert(END, table.get_string())
    txtbox.config(state=DISABLED)
    txtboxr.insert(END, tabler.get_string())
    txtboxr.config(state=DISABLED)
    root.update()

def die():
    logwatcher.raise_exception()
    root.destroy()
    sys.exit()

def setup_window():
    # Set window properties based on dynamic_sizing setting
    if dynamic_sizing:
        root.resizable(True, True)
        root.geometry("500x600")  # Initial size; can be resized
    else:
        root.resizable(False, False)
        root.geometry("500x600")  # Fixed size

if __name__ == "__main__":
    logwatcher = LogWatcher()

    root = Tk()
    root.title("PlayerList 💡")
    setup_window()

    # Set window icon
    try:
        root.iconbitmap('icon.ico')
    except Exception as e:
        print(f"Could not set icon: {e}")

    # Configure grid
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=1)

    # Left text box
    txtbox = Text(root, wrap="none")
    txtbox.grid(row=0, column=0, sticky='nsew' if dynamic_sizing else 'nsw')
    txtbox.config(state=DISABLED)  # make it readonly
    txtbox.configure(font=font.Font(family="Consolas", size=10), background="black", foreground="white")

    # Right text box
    txtboxr = Text(root, wrap="none")
    txtboxr.grid(row=0, column=1, sticky='nsew' if dynamic_sizing else 'nse')
    txtboxr.config(state=DISABLED)  # make it readonly
    txtboxr.configure(font=font.Font(family="Consolas", size=10), background="black", foreground="white")

    # Quit button
    ttk.Button(root, text="Quit", command=die).grid(column=0, row=1, pady=10, sticky='w')

    root.protocol("WM_DELETE_WINDOW", die)
    root.after(update_frequency_ms, update_playerlist)
    root.mainloop()
