import pyaudio
import numpy as np
import tkinter as tk
import threading

# Initialize audio input stream
audio = pyaudio.PyAudio()
stream = audio.open(format=pyaudio.paInt16, channels=2, rate=48000, input=True, frames_per_buffer=2048)

# Initialize audio output stream
output = audio.open(format=pyaudio.paInt16, channels=2, rate=48000, output=True, frames_per_buffer=2048)



class App:
    def __init__(self, master):
        self.master = master
        master.title("Audio Parameters")

        # Noise Reduction Parameters
        self.noise_floor_label = tk.Label(master, text="Noise Floor")
        self.noise_floor_label.pack()
        self.noise_floor_slider = tk.Scale(master, from_=0, to=10000, orient=tk.HORIZONTAL, command=self.update_params)
        self.noise_floor_slider.pack()
        self.noise_floor_slider.set(3000)

        # Signal Threshold
        self.signal_threshold_label = tk.Label(master, text="Signal Threshold")
        self.signal_threshold_label.pack()
        self.signal_threshold_slider = tk.Scale(master, from_=0, to=1200, orient=tk.HORIZONTAL, command=self.update_params)
        self.signal_threshold_slider.pack()
        self.signal_threshold_slider.set(500)

        # Buffer Size Parameter
        self.buffer_size_label = tk.Label(master, text="Buffer Size")
        self.buffer_size_label.pack()
        self.buffer_size_slider = tk.Scale(master, from_=1024, to=8192, orient=tk.HORIZONTAL, command=self.update_params)
        self.buffer_size_slider.pack()
        self.buffer_size_slider.set(2048)

        self.quit_button = tk.Button(master, text="Quit", command=master.quit)
        self.quit_button.pack()

        # Initialize noise mask
        self.noise_mask = np.zeros((2048, 2), dtype=np.int16)

        # Start audio processing thread
        self.is_running = True
        self.audio_thread = threading.Thread(target=self.process_audio)
        self.audio_thread.start()

    def process_audio(self):
        while self.is_running:
            # Read noise reduction and buffer size parameters from GUI
            noise_floor = self.noise_floor_slider.get()
            signal_threshold = self.signal_threshold_slider.get()
            buffer_size = self.buffer_size_slider.get()

            # Process audio stream with updated parameters
            input_data = stream.read(buffer_size)
            input_data_np = np.frombuffer(input_data, dtype=np.int16)
            input_data_np = input_data_np.reshape((buffer_size, 2))

            # Compute noise mask
            abs_data = np.abs(input_data_np)
            self.noise_mask = np.logical_and(abs_data < noise_floor, self.noise_mask).astype(np.int16)

            # Compute signal mask
            signal_mask = abs_data >= signal_threshold

            # Compute output data
            output_data = input_data_np * signal_mask + self.noise_mask * noise_floor

            # Write audio output buffer
            output.write(output_data.tobytes())

    def update_params(self, event):
        # Read noise reduction and buffer size parameters from GUI
        noise_floor = self.noise_floor_slider.get()
        signal_threshold = self.signal_threshold_slider.get()
        buffer_size = self.buffer_size_slider.get()

        # Process audio stream with updated parameters
        input_data = stream.read(buffer_size)
        input_data_np = np.frombuffer(input_data, dtype=np.int16)
        input_data_np = input_data_np.reshape((buffer_size, 2))
        # Compute noise mask
        abs_data = np.abs(input_data_np)
        self.noise_mask = np.logical_and(abs_data < noise_floor, self.noise_mask).astype(np.int16)

        # Compute signal mask
        signal_mask = abs_data >= signal_threshold

        # Compute output data
        output_data = input_data_np * signal_mask + self.noise_mask * noise_floor

        # Write audio output buffer
        output.write(output_data.tobytes())

    def on_quit(self):
        self.is_running = False
        self.audio_thread.join()
        root.quit()

root = tk.Tk()
app = App(root)
root.protocol("WM_DELETE_WINDOW", app.on_quit)
root.mainloop()
