import wave
import pyaudio
from pydub import AudioSegment
import io
import pydub
import time
import threading
from queue import Queue

class SakuraMixer:
    def __init__(self):
        self.audio = None
        self.playing = False
        self.paused = False
        self.position = 0
        self.volume = 0.5
        self.filter_type = 'normal'
        self.audio_thread = None
        self.player_thread = None
        self.queue = Queue()
        self.loop = False
        self.audio_length = 0.1
        self.break_loop = False
        self.sliding = False

    def load_audio(self, audio_path, wav=None):
        if not wav:
            if isinstance(audio_path, str):
                with open(audio_path, 'rb') as f:
                    audio_bytes = f.read()
            elif isinstance(audio_path, io.BytesIO):
                audio_bytes = audio_path.getvalue()
            else:
                raise ValueError("Invalid audio source type. Must be either file path or BytesIO object.")

            audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes))
            wav_bytes = audio_segment.export(format="wav").read()
            self.audio = wav_bytes
            self.audio_length = len(audio_segment) / 1000
        elif wav:
            with open(audio_path, 'rb') as f:
                audio_bytes = f.read()
                self.audio = audio_bytes

    def stop(self):
        self.playing = False
        self.paused = False
        self.position = 0

    def set_position(self, position, max_slider_value):
        position_seconds = (position / max_slider_value) * self.audio_length
        if not self.playing:
            self.position = position_seconds
        else:
            self.position = position_seconds

    def set_volume(self, volume):
        if 0 <= volume <= 100:
            self.volume = volume / 100.0  # Convert volume from 0-100 to 0.0-1.0

    def set_filter(self, filter_type):
        if filter_type in ['normal', 'low_pass', 'high_pass']:
            self.filter_type = filter_type

    def apply_filters(self, data, sw, fr, ch):
        # Apply volume adjustment
        data = self.apply_volume(data, self.volume)

        # Apply filters based on the selected filter type
        if self.filter_type == 'low_pass':
            data = self.apply_low_pass_filter(data, sw, fr, ch)
        elif self.filter_type == 'high_pass':
            data = self.apply_high_pass_filter(data, sw, fr, ch)

        return data

    def get_audio_length(self):
        return self.audio_length

    def play_audio(self, audio_data=None):
        if not self.playing and audio_data is not None:
            self.playing = True
            if not audio_data=='ok':
                self.load_audio(audio_data)
            self.audio_thread = threading.Thread(target=self._play_audio_thread)
            self.audio_thread.daemon = True
            self.audio_thread.start()

    def pause_audio(self):
        self.paused = True

    def resume_audio(self):
        self.paused = False

    def set_loop(self, loop):
        self.loop = loop

    def get_current_position(self):
        return self.position

    def get_current_volume(self):
        return self.volume * 100

    def _play_audio_thread(self):
        chunk = 1024
        wf = wave.open(io.BytesIO(self.audio), 'rb')
        p = pyaudio.PyAudio()
        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True)
        data = wf.readframes(chunk)
        sample_width = wf.getsampwidth()
        frame_rate = wf.getframerate()
        channels = wf.getnchannels()
        self.playing = True
        while self.playing:
            if self.paused:
                time.sleep(0.1)
                continue
                
            # Check if position has changed and seek to the new position
            if self.sliding:
                frame_position = int(self.position * frame_rate)
                wf.setpos(frame_position)
                self.sliding = False

            data = wf.readframes(chunk)
            if not data:  # If no more data, end playback
                break

            data = self.apply_filters(data, sample_width, frame_rate, channels)
            stream.write(data)

            # Update position
            self.position += chunk / frame_rate

            # Check if end of audio
            if self.position >= len(self.audio) / 1000:break

        self.break_loop = True
        stream.stop_stream()
        stream.close()
        p.terminate()
        self.playing = False

        if self.loop:self.play_audio(audio_data='ok')

    def enqueue_audio(self, audio_data):
        self.queue.put(audio_data)

    def format_time(self, seconds=None):
        if not seconds:seconds = self.position
        minutes, seconds = divmod(seconds, 60)
        return f"{int(minutes):02}:{int(seconds):02}"

    def play_from_queue(self):
        if not self.playing and not self.queue.empty():
            audio_data = self.queue.get()
            self.play_audio(audio_data)

    def apply_volume(self, data, volume):
        data_array = bytearray(data)

        # Apply volume adjustment
        for i in range(0, len(data_array), 2):
            sample = int.from_bytes(data_array[i:i + 2], byteorder='little', signed=True)
            adjusted_sample = int(sample * volume)
            adjusted_sample = max(min(adjusted_sample, 32767), -32768)  # Clamp adjusted sample value
            data_array[i:i + 2] = adjusted_sample.to_bytes(2, byteorder='little', signed=True)
        return bytes(data_array)


    def apply_low_pass_filter(self, data, sw, fr, ch):
        audio = pydub.AudioSegment.from_raw(io.BytesIO(data), sample_width=sw, frame_rate=fr, channels=ch)

        # Apply a low-pass filter to boost lower frequencies
        audio_low_pass = audio.low_pass_filter(1000)

        # Convert back to raw audio data
        raw_audio_data = audio_low_pass.raw_data

        return raw_audio_data


    def apply_high_pass_filter(self, data, sw, fr, ch):
        audio = pydub.AudioSegment.from_raw(io.BytesIO(data), sample_width=sw, frame_rate=fr, channels=ch)

        # Apply a high-pass filter to boost higher frequencies
        audio_high_pass = audio.high_pass_filter(100)

        # Convert back to raw audio data
        raw_audio_data = audio_high_pass.raw_data

        return raw_audio_data

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from threading import Thread
import time

class PlayerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Music Player")
        self.mixer = SakuraMixer()

        self.position_slider = ttk.Scale(root, from_=0, to=100, orient="horizontal", command=self.on_slider_move)
        self.position_slider.pack(fill="x", padx=10, pady=5)

        self.play_button = ttk.Button(root, text="Play", command=self.play_music)
        self.play_button.pack(pady=5)

        self.load_button = ttk.Button(root, text="Load Music", command=self.load_music)
        self.load_button.pack(pady=5)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def play_music(self):
        Thread(target=self.mixer.play_audio).start()

    def load_music(self):
        file_path = filedialog.askopenfilename(title="Select a music file")
        if file_path:
            self.mixer.load_audio(file_path)

    def on_slider_move(self, position):
        position_in_seconds = float(position) * self.mixer.audio_length / 100
        self.mixer.set_position(position_in_seconds)

    def update_slider_position(self):
        while True:
            if not self.mixer.playing or self.mixer.paused:
                time.sleep(0.1)
                continue
            position_percentage = self.mixer.position / self.mixer.audio_length * 100
            self.position_slider.set(position_percentage)
            time.sleep(1)

    def start(self):
        Thread(target=self.update_slider_position).start()
        self.root.mainloop()

    def on_close(self):
        self.mixer.stop()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = PlayerApp(root)
    app.start()
