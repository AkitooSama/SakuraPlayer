from customtkinter import *
from downaloder import get_video_info
from pytube import YouTube
from youtube_search import YoutubeSearch
import threading
import requests
from PIL import Image, ImageTk
import eyed3
import re
import time
import io
import colorthief
from pygame import mixer
import random
import pylrc
import syncedlyrics
import ffmpeg

mixer.init()
mixer.music.load(r"D:\CodeBase\Sakura Player\Music\ATARASHII GAKKO! - 恋の遮断機 feat.H ZETTRIO.mp3")
mixer.music.set_volume(0.25)
mixer.music.play(-1)

set_appearance_mode(mode_string="dark")
vol = 25
lyrics_thread = False
downloads = 0
path = r"C:\Users\DigiTronic\Downloads"
history = "No Downloads..."
state = "downloader"
global_image=None
video_tag = None
audio_tag = None
offset = 0
starting_time = None
lyrics_loop = True
last_lyric_displayed = False
original_filepath = None
stop_event = threading.Event()

#Functions
def state_toggler():
    global state
    if state=="downloader":
        video_opt_button.configure(state=DISABLED)
        audio_opt_button.configure(state=DISABLED)
        player.configure(text="Download")
        path_entry.delete(0, END)
        if global_image:global_image.configure(image=None)
        path_entry.insert(0, "Paste the link to stream music")
        download_name.configure(text="------")
        if not wait_label.cget("text") == "Lets stream now!":wait_label.configure(text="Lets stream now!")
        state="player"
    elif state=="player":
        video_opt_button.configure(state=NORMAL)
        audio_opt_button.configure(state=NORMAL)
        player.configure(text="Player")
        path_entry.delete(0, END)
        path_entry.insert(0, "Enter the name or Paste the link")
        download_name.configure(text="------")
        wait_label.place_forget()
        if not wait_label.cget("text") == "Retrieving data...":wait_label.configure(text="Retrieving data...")
        state="downloader"

def choose_folder():
    global path
    folder_path = filedialog.askdirectory(title="Select a folder")
    path = folder_path
    path_label.configure(text=f"Current download path: {folder_path[:13]}\n{folder_path[13:]}")

def open_history():
    os.startfile(r"Downloader\history.txt")

def toggle_mute_music():
    global vol
    if mute_music.cget("fg_color") == ["#1e5631","#07da63"]:
        mixer.music.set_volume(0.0)
        volume_slider.set(0)
        mute_music.configure(fg_color=["#800000","#990000"])
    elif mute_music.cget("fg_color") == ["#800000","#990000"]:
        mixer.music.set_volume(vol)
        volume_slider.set(vol)
        mute_music.configure(fg_color=["#1e5631","#07da63"])

def set_volume(value):
    global vol
    volume = int(value) / 100.0
    mixer.music.set_volume(volume)
    if mute_music.cget("fg_color") == ["#800000","#990000"]:mute_music.configure(fg_color=["#800000","#990000"])
    vol = value
    if vol>0.1:mute_music.configure(fg_color=["#1e5631","#07da63"])
    
def add_offset():
    global offset
    offset+=0.5
    threading.Thread(target=adjust_lrc_timings(), args=()).start()

def minus_offset():
    global offset
    offset-=0.5
    threading.Thread(target=adjust_lrc_timings(), args=()).start()

def add_offsett():
    global offset
    offset+=0.1
    threading.Thread(target=adjust_lrc_timings(), args=()).start()

def minus_offsett():
    global offset
    offset-=0.1
    threading.Thread(target=adjust_lrc_timings(), args=()).start()

def select_and_play_music():
    global global_image
    try:
        file_path = filedialog.askopenfilename(title="Select a music file", filetypes=[("Music files", "*.mp3")])
        mixer.music.stop()

        if file_path:
            song_name = os.path.splitext(os.path.basename(file_path))[0]
            try:
                audiofile = eyed3.load(file_path)
                if audiofile.tag and audiofile.tag.images:
                    # Get the first image (Assuming there's only one image)
                    image_data = audiofile.tag.images[0].image_data
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
                    hex_color = rgb_to_hex(dominant_color)

                    thumbnail_frame.place_forget()

                    thumbnail_frame2 = CTkFrame(master=downloader_frame, width=125, height=125, corner_radius=0, fg_color=hex_color, border_color=["#4e4e50","#8f9095"], border_width=4)
                    thumbnail_frame2.place(anchor="center", relx=0.181, rely=0.47)
                    
                    thumbnail_image = ImageTk.PhotoImage(resized_image)

                    thumbnail_label = CTkLabel(master=thumbnail_frame2, image=thumbnail_image, text="")

                    thumbnail_label.place(anchor="center", relx=0.496779, rely=0.5)
                    global_image = thumbnail_label
                else:
                    if global_image:global_image.configure(image=None)

                current_music.configure(text=song_name[:10])
                music_button.configure(text="||", border_color=["#4a9058","#25b04c"], fg_color=["#3dfb74","#71bc68"], hover_color="#2fff82")
                
                download_name.configure(text=song_name[:33])

                mixer.music.load(file_path)
                mixer.music.play(-1)

            except:pass
            wait_label.configure(text="Playing from local...🎵", text_color="#f4ede5")
            wait_label.place(anchor="center", relx=0.5, rely=0.25)
            
    except:pass

def load_lyrics_lrc(name):
    num = random.randint(123232, 99999999)
    filepath = f"{num}.lrc"
    matter = syncedlyrics.search(name)

    if matter is not None:
        with open(filepath, 'w', encoding='utf-8') as fil:
            fil.write(matter)

        with open(filepath, 'r', encoding='utf-8') as lrc_file:
            lrc_data = lrc_file.read()
            lrc = pylrc.parse(lrc_data)
            return lrc, filepath

    filepath = r"D:\Discord Bot version-1\lyricsnotfound.lrc"
    with open(filepath, 'r', encoding='utf-8') as lrc_file:
        lrc_data = lrc_file.read()
        lrc = pylrc.parse(lrc_data)
        return lrc, filepath

def adjust_timing(time):
    global offset

    return max(0, time + offset)

def adjust_lrc_timings():
    global original_filepath, lyrics_thread

    adjusted_lyrics = []
    with open(original_filepath, 'r') as file:
        for line in file:
            parts = line.split(']')
            if len(parts) > 1:
                try:
                    time_code = float(parts[0][1:])
                    adjusted_time = adjust_timing(time_code)
                    adjusted_line = f"[{adjusted_time:.2f}]{parts[1]}"
                    adjusted_lyrics.append(adjusted_line)
                except ValueError:
                    adjusted_lyrics.append(line)
            else:
                adjusted_lyrics.append(line)

    with open(original_filepath, 'w') as file:
        file.writelines(adjusted_lyrics)
    stop_event.set()
    print("Done")

def lyrics_control(lyrics, filepath):
    global starting_time, last_lyric_displayed
    if starting_time is None:
        starting_time = time.time()

    last_lyric_displayed = False 
    while lyrics_loop and not last_lyric_displayed: 
        for lyric_line, lyric_line2 in zip(lyrics, lyrics[1:]):
            if lyrics_thread:
                print("breaking")
                break
            current_time = time.time() - starting_time
            if adjust_timing(lyric_line.time) < current_time:
                continue

            seconds = adjust_timing(lyric_line.time) - current_time
            line = lyric_line.text
            timer = threading.Timer(max(0,seconds), lambda: None)
            timer.start()
            timer.join()  

            if stop_event.is_set():
                print("break")
                stop_event.clear()
                break
            lyricss = f" {line} 🎤\n-{lyric_line2.text}"
            lyrics_text.configure(text=lyricss)


        if adjust_timing(lyrics[-1].time) < current_time:
            last_lyric_displayed = True

        

    lyrics_text.configure(text="")
    if filepath != r"D:\Discord Bot version-1\lyricsnotfound.lrc":
        os.remove(filepath)

def control_music():
    state = music_button.cget("text")
    if state == "||":
        mixer.music.pause()
        music_button.configure(text="|>", border_color=["#000000","#a9a9a9"], fg_color=["#de0826","#f01e2c"], hover_color="#ff2c2c")
    elif state == "|>":
        mixer.music.unpause()
        music_button.configure(text="||", border_color=["#4a9058","#25b04c"], fg_color=["#3dfb74","#71bc68"], hover_color="#2fff82")

def rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(*rgb)

def get_audio_data(yt):
    audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
    stream_url = audio_stream.url
    audio, info = (
        ffmpeg
        .input(stream_url)
        .output("pipe:", format='wav', acodec='pcm_s16le')
        .run(capture_stdout=True, capture_stderr=True)
    )
    return audio, info

def sort_audio_streams(bitrates):
    numeric_bitrates = [int(b.replace('kbps', '')) for b in bitrates]
    sorted_bitrates = sorted(numeric_bitrates, reverse=True)
    formatted_bitrates = [f"{b}-kbps" for b in sorted_bitrates]
    formatted_bitrates.insert(0, "best")
    formatted_bitrates.insert(0, "None")
    formatted_bitrates.insert(-1,"wav-raw")
    return formatted_bitrates

def sort_video_streams(bitrates):
    bitrates = bitrates[2:]
    bitrates.insert(0,"highest")
    bitrates.insert(0,"None")
    return bitrates

def get_player_info(video_url: str, song_name):
    global global_image, lyrics_thread, original_filepath
    try:
        yt = YouTube(video_url)
        title = yt.title
        thumbnail_url = yt.thumbnail_url
        audio_byte, info = get_audio_data(yt)
        response = requests.get(thumbnail_url)
        lyrics, filepath = load_lyrics_lrc(song_name)
        if response.status_code == 200:
            original_image = Image.open(io.BytesIO(response.content))

            # Calculate cropping coordinates for a 1:1 aspect ratio centered crop
            min_dim = min(original_image.width, original_image.height)
            left = (original_image.width - min_dim) // 2
            top = (original_image.height - min_dim) // 2
            right = left + min_dim
            bottom = top + min_dim

            # Crop and resize the image to 120x120
            cropped_image = original_image.crop((left, top, right, bottom))
            resized_image = cropped_image.resize((143, 143), Image.Resampling.LANCZOS)
            
            color_thief = colorthief.ColorThief(io.BytesIO(response.content))
            dominant_color = color_thief.get_color(quality=1)
            hex_color = rgb_to_hex(dominant_color)

            thumbnail_frame.place_forget()

            thumbnail_frame2 = CTkFrame(master=downloader_frame, width=125, height=125, corner_radius=0, fg_color=hex_color, border_color=["#4e4e50","#8f9095"], border_width=4)
            thumbnail_frame2.place(anchor="center", relx=0.181, rely=0.47)
            
            thumbnail_image = ImageTk.PhotoImage(resized_image)

            thumbnail_label = CTkLabel(master=thumbnail_frame2, image=thumbnail_image, text="")

            thumbnail_label.place(anchor="center", relx=0.496779, rely=0.5)
            global_image = thumbnail_label

            if len(title) > 33:
                download_name.configure(text=f"{title[:33]}...")
            else:download_name.configure(text=title)
            state = music_button.cget("text")

            if state == "|>":music_button.configure(text="||", border_color=["#4a9058","#25b04c"], fg_color=["#3dfb74","#71bc68"], hover_color="#2fff82")
            # sample_rate_match = re.search(r'(\d+) Hz', str(info))
            # sample_rate = int(sample_rate_match.group(1))
            if not lyrics_thread:
                lyrics_thread=True
                lyrics_text.configure(text = "")
                lyrics_thread=False
                
            print(title)
            mixer.music.stop()
            mixer.music.load(io.BytesIO(audio_byte))
            current_music.configure(text=title[:10])
            wait_label.configure(text="Playing...🎵", text_color="#f4ede5")
            path_entry.delete(0, END)
            path_entry.insert(0, video_url)
            threading.Thread(target=lyrics_control, args=(lyrics,filepath)).start()
            original_filepath = filepath
            mixer.music.play()

    except:wait_label.configure(text="Couldn't find the media", text_color="#8b0000")

def get_video_info(video_url: str):
    global global_image
    try:
        yt = YouTube(video_url)
        title = yt.title
        thumbnail_url = yt.thumbnail_url
        video_streams = yt.streams.filter(type='video', progressive=False)
        audio_streams = yt.streams.filter(type="audio")
        audio_streams = [stream.abr for stream in audio_streams]
        print(audio_streams)
        print(video_streams)
        video_info_list = [f"({stream.mime_type.split('/')[-1]})-{stream.resolution}" for stream in video_streams]
        video_list = sort_video_streams(bitrates=video_info_list)
        audio_list = sort_audio_streams(bitrates=audio_streams)
    
        response = requests.get(thumbnail_url)
        if response.status_code == 200:
            original_image = Image.open(io.BytesIO(response.content))

            # Calculate cropping coordinates for a 1:1 aspect ratio centered crop
            min_dim = min(original_image.width, original_image.height)
            left = (original_image.width - min_dim) // 2
            top = (original_image.height - min_dim) // 2
            right = left + min_dim
            bottom = top + min_dim

            # Crop and resize the image to 120x120
            cropped_image = original_image.crop((left, top, right, bottom))
            resized_image = cropped_image.resize((143, 143), Image.Resampling.LANCZOS)

            color_thief = colorthief.ColorThief(io.BytesIO(response.content))
            dominant_color = color_thief.get_color(quality=1)
            hex_color = rgb_to_hex(dominant_color)

            thumbnail_frame.place_forget()

            thumbnail_frame2 = CTkFrame(master=downloader_frame, width=125, height=125, corner_radius=0, fg_color=hex_color, border_color=["#4e4e50","#8f9095"], border_width=4)
            thumbnail_frame2.place(anchor="center", relx=0.181, rely=0.47)

            thumbnail_image = ImageTk.PhotoImage(resized_image)

            thumbnail_label = CTkLabel(master=thumbnail_frame2, image=thumbnail_image, text="")

            thumbnail_label.place(anchor="center", relx=0.496779, rely=0.5)
            global_image = thumbnail_label

            video_opt_button.configure(values=video_list)
            audio_opt_button.configure(values=audio_list)

            if len(title) > 33:
                download_name.configure(text=f"{title[:33]}...")
            else:download_name.configure(text=title)

            wait_label.configure(text="Please choose video or audio stream.", text_color="#a2d9a1")
            path_entry.delete(0, END)
            path_entry.insert(0, video_url)

    except:wait_label.configure(text="Couldn't find the media", text_color="#8b0000")

def get_yt_link(link):
    results = YoutubeSearch(link).to_dict()
    video_id = results[0]['id']
    link = f"https://www.youtube.com/watch?v={video_id}"
    return link

def auto_paste():
    try:
        clipboard_text = options_frame.clipboard_get()
        path_entry.delete(0, END)
        path_entry.insert(0, clipboard_text)
        if clipboard_text.startswith("http"):
            clipboard_text = get_yt_link(link=clipboard_text)

        wait_label.configure(text="Retrieving data..")
        wait_label.place(anchor="center", relx=0.5, rely=0.25)

        if state=="downloader":threading.Thread(target=get_video_info, args=(clipboard_text,)).start()
        elif state=="player":threading.Thread(target=get_player_info, args=(clipboard_text,)).start()
    except:wait_label.configure(text="Couldn't find the media", text_color="#8b0000")

def on_enter(event):
    try:
        clipboard_text: str = path_entry.get()
        song_name = clipboard_text

        wait_label.place(anchor="center", relx=0.5, rely=0.25)
        wait_label.configure(text="Retrieving data..")

        if not clipboard_text.startswith("http"):
            clipboard_text = get_yt_link(link=clipboard_text)

        if state=="downloader":threading.Thread(target=get_video_info, args=(clipboard_text,)).start()
        elif state=="player":threading.Thread(target=get_player_info, args=(clipboard_text,song_name)).start()
    except:wait_label.configure(text="Couldn't find the media", text_color="#8b0000")

#Images
#https://youtu.be/AP55-ysy6xo?si=o3z-Ut_jmQ1MrYfX
#CONSTANTS
WINDOW_SIZE = "1000x600"

#Init
app = CTk(fg_color=["#000000", "#000000"])
app.geometry(WINDOW_SIZE)
app.title("𝙆𝙞𝙧𝙗𝙮 𝘿𝙤𝙬𝙣𝙡𝙤𝙖𝙙𝙚𝙧 🌸")
app.iconbitmap(bitmap="icon.ico")

#Widgets
downloader_frame = CTkFrame(master=app, width=550, height=350, fg_color="#000000", border_color=["#f5c1d9", "#edb1cb"], border_width=4, corner_radius=0)
downloader_frame.place(anchor="center", relx=0.69, rely=0.55)

path_frame = CTkFrame(master=app, width=350, height=500, fg_color=["#fca08c","#fe9383"], border_color=["#b97f64", "#be7559"], border_width=4, corner_radius=0)
path_frame.place(anchor="center", relx=0.22, rely=0.53)

thumbnail_frame = CTkFrame(master=downloader_frame, width=125, height=125, corner_radius=0, fg_color=["#8a031e","#ed003a"], border_color=["#4e4e50","#8f9095"], border_width=4)
thumbnail_frame.place(anchor="center", relx=0.181, rely=0.47)

title_frame = CTkFrame(master=downloader_frame, width=344.31, height=40, fg_color="#000000", border_width=4, corner_radius=0, border_color=["#4e4e50","#8f9095"])
title_frame.place(anchor="center", relx=0.601, rely=0.35)

options_frame = CTkFrame(master=downloader_frame,fg_color="#000000", width=344.31, height=104, border_width=4, corner_radius=0, border_color=["#4e4e50","#8f9095"])
options_frame.place(anchor="center", relx=0.601, rely=0.5)

#Texts
download_name = CTkLabel(master=title_frame, text="------", width=0, height=0, text_color=["#ffe0e8","#fcd2e5"],  font=("Fira Code",13,"bold"), corner_radius=0)
download_name.place(anchor="center", relx=0.5, rely=0.32)

#Texts
lyrics_text = CTkLabel(master=app, text="", width=0, height=0, text_color=["#ffe0e8","#880808"],  font=("Fira Code",13,"bold"), corner_radius=0)
lyrics_text.place(anchor="center", relx=0.69, rely=0.93)

percentage_value = CTkLabel(master=downloader_frame, text="100%", width=0, height=0, text_color=["#cb8c92","#fcd2e5"],  font=("Fira Code",13,"bold"), corner_radius=0)
percentage_value.place(anchor="center", relx=0.88, rely=0.8)

#Toggles
parallel_toggle = CTkSwitch(master=options_frame, text="p-ll", width=0, height=0, switch_width=50, font=("Fira Code",10,"bold"), progress_color="#000000", button_color=["#c5c3b0","#efe3b1"], button_hover_color="#474436", border_color="#ad7855", border_width=4, fg_color="#fefdf9", corner_radius=10)
parallel_toggle.place(anchor="center", relx=0.85, rely=0.5)

#Entries
path_entry = CTkEntry(master=downloader_frame, placeholder_text="Enter the name or Paste the link", width=400, height=35, fg_color="#000000", placeholder_text_color="#7689d6", font=("Fira Code", 15, "italic"), border_color=["#4e4e50","#8f9095"], corner_radius=0, border_width=4)
path_entry.place(anchor="center", relx=0.43, rely=0.17)
path_entry.bind("<Return>",on_enter)

#Buttons
paste_button = CTkButton(master=downloader_frame,command=auto_paste, text="Paste", font=("Fira Code",15), width=70, height=35, corner_radius=0, border_width=4, border_color=["#4a9058","#25b04c"], fg_color=["#3dfb74","#2fff6d"], hover_color="#2fff82")
paste_button.place(anchor="center", relx=0.8521, rely=0.17)

download_button = CTkButton(master=downloader_frame,state=DISABLED, text="Download", font=("Fira Code",15), width=70, height=30, corner_radius=0, border_width=4, border_color=["#c898b7","#ff92cb"], fg_color=["#c898b7","#ff92cb"], hover_color="#eb82b6")
download_button.place(anchor="center", relx=0.5, rely=0.91)

music_button = CTkButton(master=app,command=control_music, text="||", font=("Fira Code",15), width=20, height=25, corner_radius=0, border_width=4, border_color=["#4a9058","#25b04c"], fg_color=["#3dfb74","#71bc68"], hover_color="#2fff82")
music_button.place(anchor="center", relx=0.96, rely=0.06)

add_button = CTkButton(master=app,command=minus_offset, text="-", font=("Fira Code",15), width=25, height=25, corner_radius=0, border_width=4, border_color=["#4a9058","#25b04c"], fg_color=["#3dfb74","#71bc68"], hover_color="#2fff82")
add_button.place(anchor="center", relx=0.96, rely=0.2)

minus_button = CTkButton(master=app,command=add_offset, text="+", font=("Fira Code",15), width=25, height=25, corner_radius=0, border_width=4, border_color=["#4a9058","#25b04c"], fg_color=["#3dfb74","#71bc68"], hover_color="#2fff82")
minus_button.place(anchor="center", relx=0.9, rely=0.2)

current_music = CTkButton(master=app,command=select_and_play_music, text="Dreamy Nights", font=("Fira Code",15), width=20, height=25, corner_radius=0, border_width=4, border_color=["#deaf84","#2f1b12"], fg_color=["#714423","#43392f"], hover_color="#977045")
current_music.place(anchor="center", relx=0.87, rely=0.06)

add_button = CTkButton(master=app,command=minus_offsett, text="-", font=("Fira Code",15), width=25, height=25, corner_radius=0, border_width=4, border_color=["#4a9058","#25b04c"], fg_color=["#3dfb74","#71bc68"], hover_color="#2fff82")
add_button.place(anchor="center", relx=0.7, rely=0.2)

minus_button = CTkButton(master=app,command=add_offsett, text="+", font=("Fira Code",15), width=25, height=25, corner_radius=0, border_width=4, border_color=["#4a9058","#25b04c"], fg_color=["#3dfb74","#71bc68"], hover_color="#2fff82")
minus_button.place(anchor="center", relx=0.8, rely=0.2)

current_music = CTkButton(master=app,command=select_and_play_music, text="Dreamy Nights", font=("Fira Code",15), width=20, height=25, corner_radius=0, border_width=4, border_color=["#deaf84","#2f1b12"], fg_color=["#714423","#43392f"], hover_color="#977045")
current_music.place(anchor="center", relx=0.87, rely=0.06)

mute_music = CTkButton(master=app,command=toggle_mute_music, text="", corner_radius=100, width=20, height=7, border_width=0, fg_color=["#1e5631","#07da63"])
mute_music.place(anchor="center", relx=0.96, rely=0.115)

current_path = CTkButton(master=path_frame,command=choose_folder, text="Path", font=("Summer Pixel 22",15,"bold"), corner_radius=0, width=85, height=32, border_width=4, text_color="#000000", fg_color=["#f4ede5","#c8c7d7"], border_color=["#000000","#808080"])
current_path.place(anchor="center", relx=0.2, rely=0.55)

history = CTkButton(master=path_frame,command=open_history, text="History", font=("Summer Pixel 22",15,"bold"), corner_radius=0, width=85, height=32, border_width=4, text_color="#000000", fg_color=["#f4ede5","#88978a"], border_color=["#000000","#808080"])
history.place(anchor="center", relx=0.5, rely=0.55)

player = CTkButton(master=path_frame,command=state_toggler, text="Player", font=("Summer Pixel 22",15,"bold"), corner_radius=0, width=85, height=32, border_width=4, text_color="#000000", fg_color=["#f4ede5","#d1e8ee"], border_color=["#000000","#808080"])
player.place(anchor="center", relx=0.8, rely=0.55)

#Combo Boxes
video_opt_button = CTkComboBox(master=options_frame, corner_radius=0, width=110, values=["None"], font=("Fira Code",10,"bold"), fg_color="#84a7fd", border_width=4, border_color=["#4e4e50","#8f9095"], text_color="#f1feff", dropdown_font=("Fira Code",10,"italic"), dropdown_text_color="#000000", dropdown_fg_color="#84a7fd", dropdown_hover_color="#fd8584")
video_opt_button.place(anchor="center", relx=0.21, rely=0.5)

audio_opt_button = CTkComboBox(master=options_frame, corner_radius=0, width=110, values=["None"], font=("Fira Code",10,"bold"), fg_color="#c3bddf", border_width=4, border_color=["#4e4e50","#8f9095"], text_color="#f1feff", dropdown_font=("Fira Code",10,"italic"), dropdown_text_color="#000000", dropdown_fg_color="#c3bddf", dropdown_hover_color="#fd8584")
audio_opt_button.place(anchor="center", relx=0.55, rely=0.5)

#Progress Bars
progress_bar = CTkProgressBar(master=downloader_frame, width=420, height=30, corner_radius=0, border_width=4, fg_color="#000000", border_color=["#7f7f7d","#fefefe"], progress_color=["#bbb8cf", "#c3bde1"])
progress_bar.place(anchor="center", relx=0.455, rely=0.8)

#Labels
static_img = Image.open(r"image.jpg")
resized_image = static_img.resize((370, 200), Image.Resampling.LANCZOS)

static_image = CTkLabel(master=path_frame, text="Hey! How's your day going? ^o^", fg_color="#000000", width=320, height=230, anchor="s", font=("Summer Pixel 22",20))
static_image.place(anchor="center", relx=0.5, rely=0.27)

thumbnail_label = CTkLabel(master=static_image, image=ImageTk.PhotoImage(resized_image), text="")
thumbnail_label.place(anchor="center", relx=0.5, rely=0.5)

title_path = CTkLabel(master=static_image, text=f"Kirby Downloads: {downloads}", width=0, height=0, font=("Summer Pixel 22",20), text_color=["#aa336a", "#f4bfd4"], corner_radius=0)
title_path.place(anchor="center", relx=0.5, rely=0.087)

wait_label = CTkLabel(master=downloader_frame, text="Retrieving data...", width=0, height=0, font=("Fira Code",12,"italic"), text_color="#8b0000")

black_screen = CTkLabel(master=path_frame, text="", fg_color="#000000", width=280, height=150, anchor="s", font=("Summer Pixel 22",20))
black_screen.place(anchor="center", relx=0.5, rely=0.78)

path_label = CTkLabel(master=path_frame, text=f"Current download path: {path[:13]}\n{path[13:]}", text_color="#000000", width=0, height=0, anchor="s", font=("Summer Pixel 22",15))
path_label.place(anchor="center", relx=0.5, rely=0.963)

dot_label = CTkLabel(master=path_frame, text=",-,-,-,-,-,-,-,-,-,-,-,-,-,-,-,-,-,-,-,", text_color="#000000", width=0, height=0, anchor="s", font=("Summer Pixel 22",15))
dot_label.place(anchor="center", relx=0.5, rely=0.605)

history_label = CTkLabel(master=black_screen, text=f"No Downloads...", text_color=["#000000","#808080"], width=0, height=0, font=("Summer Pixel 22",15))
history_label.place(anchor="center", relx=0.5, rely=0.5) #35

#Sliders
volume_slider = CTkSlider(master=app, from_=0, to=100, command=set_volume, orientation="horizontal", width=120, button_color=["#382120","#54384b"], button_hover_color=["#7c5969","#19100a"], border_color="#986d5a", border_width=2)
volume_slider.set(25)
volume_slider.place(anchor="center", relx=0.87, rely=0.115)

app.mainloop()