import os
from pathlib import Path
from customtkinter import CTk, CTkFrame, CTkButton, CTkLabel, filedialog
from PIL import Image, ImageTk
import threading
import random
from typing import List, Dict
from editing_tools import JSONEditor
from base_frames import PrimaryFrame
from player import Player
from colors import Color
from sentences import sentences
from mixer import SakuraMixer

# Paths to JSON files
paths: List[str] = ['config.json', 'settings.json', 'backup_settings.json']
for path in paths:
    try:
        os.remove(path=path)
    except:
        pass

def get_downloads_folder() -> Path:
    if os.name == 'posix':
        return Path.home() / 'Downloads'
    elif os.name == 'nt':
        return Path.home() / 'Downloads'

# Constants
CONFIG_FILE_PATH: str = 'config.json'
SETTINGS_FILE_PATH: str = 'settings.json'
BACKUP_SETTINGS_FILE_PATH: str = 'backup_settings.json'

# Ensure necessary files exist
if not os.path.exists(CONFIG_FILE_PATH):
    JSONEditor.build_json_file(
        file_path=CONFIG_FILE_PATH,
        content={'window_size': '1000x600',
                 'application_title': '𝙎𝙖𝙠𝙪𝙧𝙖 𝙋𝙡𝙖𝙮𝙚𝙧 🌸',
                 'icon_path': 'icon.ico'}
    )

if not os.path.exists(SETTINGS_FILE_PATH):
    if not os.path.exists(BACKUP_SETTINGS_FILE_PATH):
        content: Dict[str, any] = {'downloads': 0,
                                   'downloads_folder_path': str(get_downloads_folder()),
                                   'last_stream_name': '------',
                                   'status':'player'}
        JSONEditor.build_json_file(
            file_path=SETTINGS_FILE_PATH,
            content=content
        )
        JSONEditor.build_json_file(
            file_path=BACKUP_SETTINGS_FILE_PATH,
            content=content
        )
    else:
        JSONEditor.duplicate_json_file(
            from_file_path=BACKUP_SETTINGS_FILE_PATH,
            to_file_path=SETTINGS_FILE_PATH
        )

# Loading contents
config_file: JSONEditor = JSONEditor(json_file_path=CONFIG_FILE_PATH)
config_contents: Dict[str, any] = config_file.get_json_data()

settings_file: JSONEditor = JSONEditor(json_file_path=SETTINGS_FILE_PATH)
settings_contents: Dict[str, any] = settings_file.get_json_data()

# Config data
WINDOW_SIZE: str = config_contents['window_size']
APPLICATION_TITLE: str = config_contents['application_title']
ICON_PATH: str = config_contents['icon_path']

# Settings data
DOWNLOADS_FOLDER_PATH: str = settings_contents['downloads_folder_path']

class Application(CTk):
    def __init__(self) -> None:
        super().__init__(fg_color=Color.BLACK.value)

        # Application setup
        self.geometry(geometry_string=WINDOW_SIZE)
        self.title(string=APPLICATION_TITLE)
        self.iconbitmap(bitmap=ICON_PATH)
        self.mixer = SakuraMixer()

        # Main frame information
        self.downloads_number: int = settings_contents['downloads']
        self.status: str = settings_contents['status']

        self.main_frame = CTkFrame(
            master=self,
            width=350,
            height=500,
            fg_color=['#fca08c', '#fe9383'],
            border_color=['#b97f64', '#be7559'],
            border_width=4,
            corner_radius=0
        )
        self.main_frame.place(anchor='center', relx=0.22, rely=0.53)

        path_button = CTkButton(
            master=self.main_frame,
            command=self.choose_folder,
            text='Path',
            font=('Summer Pixel 22', 15, 'bold'),
            corner_radius=0,
            width=85,
            height=32,
            border_width=4,
            text_color='#000000',
            fg_color=['#f4ede5', '#c8c7d7'],
            border_color=['#000000', '#808080']
        )
        path_button.place(anchor='center', relx=0.2, rely=0.55)

        history_button = CTkButton(
            master=self.main_frame,
            command=self.open_history_button,
            text='History',
            font=('Summer Pixel 22', 15, 'bold'),
            corner_radius=0,
            width=85,
            height=32,
            border_width=4,
            text_color='#000000',
            fg_color=['#f4ede5', '#88978a'],
            border_color=['#000000', '#808080']
        )
        history_button.place(anchor='center', relx=0.5, rely=0.55)

        switch_button = CTkButton(
            master=self.main_frame,
            text='Switch',
            font=('Summer Pixel 22', 15, 'bold'),
            corner_radius=0,
            width=85,
            height=32,
            border_width=4,
            text_color='#000000',
            fg_color=['#f4ede5', '#d1e8ee'],
            border_color=['#000000', '#808080']
        )
        switch_button.place(anchor='center', relx=0.8, rely=0.55)

        dot_label = CTkLabel(
            master=self.main_frame,
            text=',-,-,-,-,-,-,-,-,-,-,-,-,-,-,-,-,-,-,-,',
            text_color='#000000',
            width=0,
            height=0,
            anchor='s',
            font=('Summer Pixel 22', 15)
        )
        dot_label.place(anchor='center', relx=0.5, rely=0.605)

        black_screen = CTkLabel(
            master=self.main_frame,
            text='',
            fg_color=Color.BLACK.value,
            width=280,
            height=150,
            anchor='s',
            font=('Summer Pixel 22', 20)
        )
        black_screen.place(anchor='center', relx=0.5, rely=0.78)

        self.black_display = CTkLabel(
            master=black_screen,
            text='No History...',
            text_color=['#000000', '#808080'],
            width=0,
            height=0,
            font=('Summer Pixel 22', 15)
        )
        self.black_display.place(anchor='center', relx=0.5, rely=0.5)

        self.path_label = CTkLabel(
            master=self.main_frame,
            text=f'Current download path: {DOWNLOADS_FOLDER_PATH[:13]}\n{DOWNLOADS_FOLDER_PATH[13:]}',
            text_color='#000000',
            width=0,
            height=0,
            anchor='s',
            font=('Summer Pixel 22', 15)
        )
        self.path_label.place(anchor='center', relx=0.5, rely=0.963)

        main_image = Image.open(r'image.jpg')
        resized_image = main_image.resize((370, 200), Image.Resampling.LANCZOS)

        main_image_background = CTkLabel(
            master=self.main_frame,
            text='',
            fg_color='#000000',
            width=320,
            height=230,
            anchor='s',
            font=('Summer Pixel 22', 20)
        )
        main_image_background.place(anchor='center', relx=0.5, rely=0.27)

        main_image_label = CTkLabel(
            master=main_image_background,
            image=ImageTk.PhotoImage(resized_image),
            text=''
        )
        main_image_label.place(anchor='center', relx=0.5, rely=0.5)

        self.main_text = CTkButton(
            master=self.main_frame,
            command=self.change_text,
            text=random.choice(sentences),
            font=('Summer Pixel 22', 15),
            corner_radius=3,
            width=72,
            height=32,
            border_width=1,
            text_color='#ffd3da',
            fg_color='#000000',
            border_color='#000000',
            hover_color='#000000'
        )
        self.main_text.place(anchor='center', relx=0.5, rely=0.47)

        primary_frame = PrimaryFrame(application_frame=self)
        primary_frame.place(anchor='center', relx=0.69, rely=0.55)

        if self.status == 'player':
            Player(primary_frame=primary_frame)
        elif self.status == 'downloader':
            pass

    def play_button(self, filename: str) -> None:
        self.mixer.load_audio(audio_path=filename, wav=True)
        self.mixer.play_audio(audio_data='ok')

    def change_text(self):
        threading.Thread(target=self.play_button, args=('change_text.wav',)).start()
        self.main_text.configure(text=random.choice(sentences))
 
    def choose_folder(self):
        folder_path = filedialog.askdirectory(title='Select a folder')
        if folder_path:
            global DOWNLOADS_FOLDER_PATH
            DOWNLOADS_FOLDER_PATH = folder_path
            JSONEditor(json_file_path=SETTINGS_FILE_PATH).edit_json_file(content={'downloads_folder_path': DOWNLOADS_FOLDER_PATH})
            JSONEditor.duplicate_json_file(from_file_path=SETTINGS_FILE_PATH, to_file_path=BACKUP_SETTINGS_FILE_PATH)
            self.path_label.configure(text=f'Current download path: {folder_path[:13]}\n{folder_path[13:]}')

    def open_history_button(cls) -> None:
        os.startfile('history.txt')

def main():
    app = Application()
    app.mainloop()

if __name__ == '__main__':
    main()