import os
import io
import threading
from PIL import Image, ImageTk
from tkinter import filedialog
from customtkinter import *
from editing_tools import JSONEditor
from base_frames import PrimaryFrame
from mixer import SakuraMixer
import random
import colorthief
import time
import eyed3

SETTINGS_FILE_PATH = 'settings.json'
last_color = '#f5c1d9'
settings_file = JSONEditor(json_file_path=SETTINGS_FILE_PATH)
settings_contents = settings_file.get_json_data()

class Player:
    def __init__(self, primary_frame: PrimaryFrame) -> None:
        self.primary_frame = primary_frame
        self._current_stream_name = settings_contents['last_stream_name']
        self._stream_time = '->00:00<-'
        self._stream_volume = 50
        self._processing_status_label = CTkLabel(master=self.primary_frame, text="", width=0, height=0, font=("Fira Code", 12, "italic"), text_color="#8b0000")
        self._processing_status_label.place(anchor="center", relx=0.5, rely=0.25)
        self._audio = io.BytesIO
        self.sliding = False
        self.mixer = SakuraMixer()
        self.playing = False
        self.mixer.set_loop(True)
        self.paused = False
        self._setup_ui()
        self._bind_keys()

    def _setup_ui(self):
        self._stream_name = CTkLabel(master=self.primary_frame.title_frame, text=self._current_stream_name, width=0, height=0, text_color=["#ffe0e8","#fcd2e5"], font=("Fira Code", 13, "bold"), corner_radius=0)
        self._stream_name.place(anchor="center", relx=0.5, rely=0.32)

        self._search_term = CTkEntry(
            master=self.primary_frame,
            placeholder_text='Enter the name or Paste the link',
            width=400,
            height=35,
            fg_color='#000000',
            placeholder_text_color='#7689d6',
            font=('Fira Code', 15, 'italic'),
            border_color=['#4e4e50', '#8f9095'],
            corner_radius=0,
            border_width=4
        )
        self._search_term.place(anchor='center', relx=0.43, rely=0.17)
        self._search_term.bind(sequence='<Return>', command=self.on_enter)

        paste_button = CTkButton(
            master=self.primary_frame,
            command=self.auto_paste,
            text='Paste',
            font=('Fira Code', 15),
            width=70,
            height=35,
            corner_radius=0,
            border_width=4,
            border_color=['#4a9058', '#25b04c'],
            fg_color=['#3dfb74', '#2fff6d'],
            hover_color='#006400'
        )
        paste_button.place(anchor='center', relx=0.8521, rely=0.17)

        self._stream_time_label = CTkLabel(master=self.primary_frame.secondary_frame, text=self._stream_time, width=0, height=0, text_color=["#ffe0e8","#fcd2e5"], font=("Fira Code",13,"bold"), corner_radius=0)
        self._stream_time_label.place(anchor="center", relx=0.132, rely=0.3)

        self._position_slider = CTkSlider(master=self.primary_frame.secondary_frame, from_=0, to=100, command=self.set_position, orientation="horizontal", width=170, button_color=["#382120","#54384b"], button_hover_color=["#7c5969","#19100a"], border_color="#986d5a", border_width=2)
        self._position_slider.set(0)
        self._position_slider.place(anchor="center", relx=0.5, rely=0.3)
        self._position_slider.bind("<ButtonPress-1>", self.slider_drag_start)
        self._position_slider.bind("<ButtonRelease-1>", self.slider_drag_end)

        self._mute_stream_button = CTkButton(master=self.primary_frame.secondary_frame,command=self.toggle_mute_button, text="", corner_radius=100, width=20, height=7, border_width=0, fg_color=["#1e5631","#07da63"])
        self._mute_stream_button.place(anchor="center", relx=0.81, rely=0.3)

        self._control_stream_button = CTkButton(master=self.primary_frame.secondary_frame,command=self.pause_unpause, text="|>", font=("Fira Code",15), width=10, height=10, corner_radius=50, border_color=["#000000","#a9a9a9"], fg_color=["#de0826","#f01e2c"], hover_color="#ff2c2c")
        self._control_stream_button.place(anchor="center", relx=0.92, rely=0.3)

        self._local_stream_button = CTkButton(master=self.primary_frame.secondary_frame,command=self.select_and_play_stream, text="Local", font=("Fira Code",15), width=20, height=25, corner_radius=0, border_width=4, border_color=["#deaf84","#2f1b12"], fg_color=["#714423","#43392f"], hover_color="#977045")
        self._local_stream_button.place(anchor="center", relx=0.13, rely=0.66)

        self._filter_button = CTkButton(master=self.primary_frame.secondary_frame,command=self.filter_thread, text="Filters", font=("Fira Code",15), width=20, height=25, corner_radius=0, border_width=4, border_color=["#deaf84","#2f1b12"], fg_color=["#714423","#43392f"], hover_color="#977045")
        self._filter_button.place(anchor="center", relx=0.3478, rely=0.66)

        self._playlist_button = CTkButton(master=self.primary_frame.secondary_frame,command=self.reset_filter, text="Playlists", font=("Fira Code",15), width=20, height=25, corner_radius=0, border_width=4, border_color=["#deaf84","#2f1b12"], fg_color=["#714423","#43392f"], hover_color="#977045")
        self._playlist_button.place(anchor="center", relx=0.62, rely=0.66)

        self._volume_slider = CTkSlider(master=self.primary_frame.secondary_frame, from_=0, to=100, command=self.set_volume, orientation="horizontal", width=67, height=10, button_color=["#382120","#54384b"], button_hover_color=["#7c5969","#19100a"], border_color="#986d5a", border_width=2)
        self._volume_slider.set(50)
        self._volume_slider.place(anchor="center", relx=0.88, rely=0.66)

    def _bind_keys(self):
        self.primary_frame.bind("<space>", self.pause_unpause)
        self.primary_frame.bind("m", self.toggle_mute_button)
        self.primary_frame.bind("l", self.select_and_play_stream)

    @property
    def current_stream_name(self):
        return self._current_stream_name

    @current_stream_name.setter
    def current_stream_name(self, value):
        self._current_stream_name = value
        self._stream_name.configure(text=value)

    @property
    def stream_time(self):
        return self._stream_time

    @stream_time.setter
    def stream_time(self, value):
        self._stream_time = value
        self._stream_time_label.configure(text=value)

    @property
    def stream_volume(self):
        return self._stream_volume

    @stream_volume.setter
    def stream_volume(self, value):
        self._stream_volume = value
        self._position_slider.set(value)

    def auto_paste(self):
        clipboard_text = self.primary_frame.clipboard_get()
        self._search_term.delete(0, END)
        self._search_term.insert(0, clipboard_text)
        if clipboard_text.startswith("https://www.youtube.com/watch") or clipboard_text.startswith("https://youtu.be/"):
            pass

    def on_enter(self, event):
        clipboard_text = self.primary_frame.clipboard_get()
        print(clipboard_text)

    def set_position(self, value):
        self._position_slider.set(value)
        max_slider_value = self._position_slider.cget('to')
        self.mixer.set_position(value, max_slider_value)
        self._stream_time_label.configure(text=f'->{self.mixer.format_time()}<-')

    def filter_thread(self):
        threading.Thread(target=self.apply_filter).start()

    def apply_filter(self):
        if self.mixer.filter_type == 'low_pass':
            self.mixer.set_filter('high_pass')
        else:
            self.mixer.set_filter('low_pass')

    def _position_changer(self):
        while True:
            if self.mixer.break_loop:
                self._stream_time_label.configure(text='->00:00<-')
                self._position_slider.set(0)
                self.playing = False
                break
            if self.sliding:
                time.sleep(0.1)
                continue
            if not self.paused:
                self._stream_time_label.configure(text=f'->{self.mixer.format_time()}<-')
                self._position_slider.set(self.mixer.position)
            if self.paused:
                time.sleep(0.1)
                continue
            time.sleep(0.01)

    def reset_filter(self):
        self.mixer.set_filter('normal')

    def check_color(self, gradient_colors):
        global last_color
        gradient_colors = ['#f5c1d9', '#f0bed8', '#ebbcd6', '#e6b9d5',
                           '#e1b7d3', '#dcb4d2', '#d7b1d0', '#d2afce',
                           '#ccaccd', '#c7a9cb', '#c2a7c9', '#bda4c8',
                           '#b8a1c6', '#b39fc4', '#ae9cc2', '#a99ac1',
                           '#a497bf', '#9f94bd', '#9a92bb', '#958fba',
                           '#908cb8', '#8b8ab6', '#8687b4', '#8185b3',
                           '#7b82b1', '#7680af', '#717dad', '#6c7aaa',
                           '#6778a8', '#6275a6', '#5d73a5', '#5870a3',
                           '#536ea1', '#4e6b9f', '#49699e', '#44669c',
                           '#3f639a', '#3a6198', '#355f97', '#305c95',
                           '#2b5a93', '#265791', '#22548f', '#1d518e',
                           '#184f8c', '#134c8a', '#0e4a88', '#094786', '#044583']
        color = random.choice(gradient_colors)
        if color == last_color:
            while True:
                new_color = random.choice(gradient_colors)
                if new_color != last_color:
                    return new_color
        else: return color

    def color_border(self):
        global last_color
        while True:
            if not self.playing:
                self.primary_frame.configure(border_color=['#f5c1d9', '#edb1cb'])
                break
            else:
                if not self.paused:
                    color = self.check_color(last_color)
                    self.primary_frame.configure(border_color=color)
                    last_color = color
                    time.sleep(0.5)

    def pause_unpause(self):
        state = self._control_stream_button.cget("text")
        if state == "||":
            self.mixer.pause_audio()
            self.paused = True
            self._control_stream_button.configure(text="|>", border_color=["#000000","#a9a9a9"], fg_color=["#de0826","#f01e2c"], hover_color="#ff2c2c")
        elif state == "|>":
            self.mixer.resume_audio()
            self.paused = False
            self._control_stream_button.configure(text="||", border_color=["#4a9058","#25b04c"], fg_color=["#3dfb74","#71bc68"], hover_color="#2fff82")

    def toggle_mute_button(self):
        color = self._mute_stream_button.cget("fg_color")
        if color == ["#1e5631","#07da63"]:
            self.mixer.set_volume(0)
            self._volume_slider.set(0)
            self._mute_stream_button.configure(fg_color=["#800000","#990000"])
        elif color == ["#800000","#990000"]:
            self.mixer.set_volume(self._stream_volume)
            self._volume_slider.set(self._stream_volume)
            self._mute_stream_button.configure(fg_color=["#1e5631","#07da63"])

    def set_volume(self, value):
        self.mixer.set_volume(value)
        self._stream_volume = value
        if self._stream_volume > 0:self._mute_stream_button.configure(fg_color=["#1e5631","#07da63"])
        else:self._mute_stream_button.configure(fg_color=["#de0826","#f01e2c"])
        

    def rgb_to_hex(cls, rgb: str) -> str:
        return "#{:02x}{:02x}{:02x}".format(*rgb)

    def select_and_play_stream(self):
        thread = threading.Thread(target=self._select_and_play_stream_thread)
        thread.daemon = True
        thread.start()

    def change_position_stream(self):
        thread = threading.Thread(target=self._position_changer)
        thread.daemon = True
        thread.start()

    def _select_and_play_stream_thread(self):
        file_path = filedialog.askopenfilename(
            title="Select a music file",
            filetypes=[
                ("All Supported Audio", "*.mp3 *.wav *.ogg *.flac *.aac *.m4a *.wma *.aiff *.mid *.midi"),
                ("MP3 files", "*.mp3"),
                ("WAV files", "*.wav"),
                ("OGG files", "*.ogg"),
                ("FLAC files", "*.flac"),
                ("AAC files", "*.aac"),
                ("M4A files", "*.m4a"),
                ("WMA files", "*.wma"),
                ("AIFF files", "*.aiff"),
                ("MIDI files", "*.mid *.midi"),
                ("All files", "*.*")
            ]
        )

        self._processing_status_label.configure(text="")
        self.mixer.stop()

        if file_path:
            song_name = os.path.splitext(os.path.basename(file_path))[0]
            with open(file_path, 'rb') as file:
                audio_bytes = io.BytesIO(file.read())
                self._audio = audio_bytes

            self.mixer.load_audio(audio_bytes)
            self._position_slider.configure(to=self.mixer.audio_length)
            self._position_slider.set(0)
            self.place_local_thumbnail(file_path=file_path)

            self._control_stream_button.configure(text="||", border_color=["#4a9058","#25b04c"], fg_color=["#3dfb74","#71bc68"], hover_color="#2fff82")
            self.mixer.play_audio('ok')
            self.change_position_stream()
            self.playing = True
            threading.Thread(target=self.color_border).start()
            self.current_stream_name = song_name[:33]
            self._processing_status_label.configure(text="Playing from local...🎵", text_color="#f4ede5")

    def slider_drag_start(self, event):
        self.mixer.sliding = True
        self.sliding = True

    def slider_drag_end(self, event):
        self.mixer.sliding = False
        self.sliding= False

    def place_local_thumbnail(self, file_path):
        audiofile = eyed3.load(file_path)
        try:
            if audiofile.tag and audiofile.tag.images:
                image_data = audiofile.tag.images[0].image_data
                self.place_thumbnail(image_data=image_data)
            else:pass
        except:pass

    def place_thumbnail(self, image_data):
        original_image = Image.open(io.BytesIO(image_data))

        # Calculate cropping coordinates for a 1:1 aspect ratio centered crop
        min_dim = min(original_image.width, original_image.height)
        left = (original_image.width - min_dim) // 2
        top = (original_image.height - min_dim) // 2
        right = left + min_dim
        bottom = top + min_dim

        # Crop and resize the image to 120x120
        cropped_image = original_image.crop((left, top, right, bottom))
        resized_image = cropped_image.resize((143, 143), Image.Resampling.LANCZOS)
        
        color_thief = colorthief.ColorThief(io.BytesIO(image_data))
        dominant_color = color_thief.get_color(quality=1)
        stream_thumbnail_hex_color = self.rgb_to_hex(dominant_color)

        self.primary_frame.thumbnail_frame.configure(fg_color=stream_thumbnail_hex_color)
        
        stream_thumbnail_image = ImageTk.PhotoImage(resized_image)

        thumbnail_image_label = CTkLabel(master=self.primary_frame.thumbnail_frame, image=stream_thumbnail_image, text="")
        thumbnail_image_label.place(anchor="center", relx=0.496779, rely=0.5)

if __name__ == "__main__":
    pass
