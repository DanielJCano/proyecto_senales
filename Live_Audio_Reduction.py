import pyaudio
import numpy as np
import noisereduce as nr
# Audio parameters
CHANNELS = 2
#RATE = 44100
#RATE = 48000
RATE = 48000
FORMAT = pyaudio.paInt16
#BUFFER_SIZE = 2048
BUFFER_SIZE = 2800

# Noise reduction parameters
NOISE_FLOOR = 3000  # adjust this to reduce or increase the amount of noise reduction
SIGNAL_THRESHOLD = 500  # adjust this to reduce or increase the amount of signal threshold

# Initialize audio input stream
audio = pyaudio.PyAudio()
stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=BUFFER_SIZE)

# Initialize audio output stream
output = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=BUFFER_SIZE)

# Initialize noise mask
noise_mask = np.zeros((BUFFER_SIZE, CHANNELS), dtype=np.int16)

while True:
    # Read audio input buffer
    input_data = stream.read(BUFFER_SIZE)
    input_data_np = np.frombuffer(input_data, dtype=np.int16)
    input_data_np = input_data_np.reshape((BUFFER_SIZE, CHANNELS))
    # Compute noise mask

    abs_data = np.abs(input_data_np)
    noise_mask = np.logical_and(abs_data < NOISE_FLOOR, noise_mask).astype(np.int16)



    # Compute signal mask
    signal_mask = abs_data >= SIGNAL_THRESHOLD
    # Compute output data
    output_data = input_data_np * signal_mask + noise_mask * NOISE_FLOOR

    # apply noise reduction to the chunk of audio data
    reduced_noise = nr.reduce_noise(y=output_data, sr=RATE)
    # Write audio output buffer
    # output.write(output_data.tobytes())
    output.write(reduced_noise.tobytes())
