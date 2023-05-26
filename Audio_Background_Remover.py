import noisereduce as nr
import soundfile as sf
from IPython.display import Audio, display
import pyaudio
import numpy as np
import tkinter as tk
import threading
import pyaudio
import wave
import numpy as np
from scipy.io.wavfile import read, write
import time

# Record audio
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "file.wav"

audio = pyaudio.PyAudio()
# Initialize audio output stream
output = audio.open(format=pyaudio.paInt16, channels=2,
                    rate=48000, output=True, frames_per_buffer=2048)
try:
    while True:  # This will make it run indefinitely
        # start Recording
        stream = audio.open(format=FORMAT, channels=CHANNELS,
                            rate=RATE, input=True,
                            frames_per_buffer=CHUNK)
        print("recording...")
        frames = []

        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK)
            frames.append(data)
        print("finished recording")

        # stop Recording
        # stream.stop_stream()
        # stream.close()

        waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
        waveFile.setnchannels(CHANNELS)
        waveFile.setsampwidth(audio.get_sample_size(FORMAT))
        waveFile.setframerate(RATE)
        waveFile.writeframes(b''.join(frames))
        waveFile.close()

        # Read the audio file
        sample_rate, data = read(WAVE_OUTPUT_FILENAME)


        # Perform operation on audio data (e.g., attenuation)
        data = nr.reduce_noise(y=data, sr=sample_rate)


        # Write back to the file
        write(WAVE_OUTPUT_FILENAME, sample_rate, data.astype(np.int16))

        # Play the modified audio
        # stream = audio.open(format=FORMAT, channels=CHANNELS,
        #                     rate=RATE, output=True)

        # # read data
        # wf = wave.open(WAVE_OUTPUT_FILENAME, 'rb')

        # # play stream
        # data = wf.readframes(CHUNK)

        # Write audio output stream
        output.write(data)

        while len(data) > 0:
            stream.write(data)
            data = wf.readframes(CHUNK)

        # stream.stop_stream()
        # stream.close()

        # wait for the same duration as the recording time before starting a new loop
        # time.sleep(RECORD_SECONDS)
finally:
    audio.terminate()  # make sure to terminate the PyAudio instance when you stop the program

# # Load audio file
# data, rate = sf.read(
#     '/content/drive/MyDrive/Señales_Digitales/Practica 3/Audios Daniel/Frase_Ruido.wav')
# display(Audio(data, rate=rate))

# # Save the result
# # sf.write('reduced_noise.wav', reduced_noise, rate)
# display(Audio(data, rate=rate))
