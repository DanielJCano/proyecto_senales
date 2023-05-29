from scipy import signal
import numpy as np
import soundfile as sf
from pathlib import Path
import pyaudio
import time
import wave


import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import tkinter as tk

# Other imports and function definitions go here

# Set up the Tkinter window
root = tk.Tk()


output_figure = Figure(figsize=(5, 5), dpi=100)
output_plot = output_figure.add_subplot(111)


output_canvas = FigureCanvasTkAgg(output_figure, root)
output_canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)



def generate_white_noise(duration_in_seconds, sampling_rate):
    duration_in_samples = int(duration_in_seconds * sampling_rate)
    return np.random.default_rng().uniform(-1, 1, duration_in_samples)


def a1_coefficient(break_frequency, sampling_rate):
    tan = np.tan(np.pi * break_frequency / sampling_rate)
    return (tan - 1) / (tan + 1)


def allpass_filter(input_signal, break_frequency, sampling_rate):
    # Initialize the output array
    allpass_output = np.zeros_like(input_signal)

    # Initialize the inner 1-sample buffer
    dn_1 = 0

    # The allpass coefficient is computed once outside the loop
    a1 = a1_coefficient(break_frequency, sampling_rate)

    for n in range(input_signal.shape[0]):
        # The allpass difference equation
        allpass_output[n] = a1 * input_signal[n] + dn_1

        # Store a value in the inner buffer for the 
        # next iteration
        dn_1 = input_signal[n] - a1 * allpass_output[n]
    return allpass_output


def allpass_based_filter(input_signal, cutoff_frequency, \
    sampling_rate, highpass=False, amplitude=1.0):
    # Perform allpass filtering
    allpass_output = allpass_filter(input_signal, \
        cutoff_frequency, sampling_rate)

    # If we want a highpass, we need to invert 
    # the allpass output in phase
    if highpass:
        allpass_output *= -1

    # Sum the allpass output with the direct path
    filter_output = input_signal + allpass_output

    # Scale the amplitude to prevent clipping
    filter_output *= 0.5

    # Apply the given amplitude
    filter_output *= amplitude

    return filter_output



# Set some parameters
fs = 44100  # Sampling rate
chunk_size = 1024    # Number of audio frames processed per chunk
channels = 1  # Mono audio
format = pyaudio.paFloat32  # 32-bit float audio data
# format = pyaudio.paInt16
cutoff_frequency = 4500  # Cutoff frequency in Hz
WAVE_OUTPUT_FILENAME_BEFORE = "before_processing.wav"
WAVE_OUTPUT_FILENAME_AFTER = "after_processing.wav"

# Initialize PyAudio
p = pyaudio.PyAudio()


# Open wave files for writing
waveFile_before = wave.open(WAVE_OUTPUT_FILENAME_BEFORE, 'wb')
waveFile_before.setnchannels(channels)
waveFile_before.setsampwidth(p.get_sample_size(format))
waveFile_before.setframerate(fs)

waveFile_after = wave.open(WAVE_OUTPUT_FILENAME_AFTER, 'wb')
waveFile_after.setnchannels(channels)
waveFile_after.setsampwidth(p.get_sample_size(format))
waveFile_after.setframerate(fs)



# Callback function to process audio chunks
def callback(in_data, frame_count, time_info, status):
    # Ensure the input data is the right shape and type
    input_data = np.frombuffer(in_data, dtype=np.float32)


    # Write the original audio data to the wave file
    waveFile_before.writeframes(input_data.tobytes())

    # Apply the filter
    output_data = allpass_based_filter(
        input_data, cutoff_frequency, fs, highpass=False, amplitude=1.0
    )

    # Write the processed audio data to the wave file
    waveFile_after.writeframes(output_data.tobytes())
  

    output_plot.clear()

    # Plot the new data
    output_plot.plot(output_data)

    # Redraw the plots
    output_canvas.draw()

    # Return the output data and a flag indicating the stream should continue
    return output_data.tobytes(), pyaudio.paContinue


# Create a stream and start it
stream = p.open(format=format,
                channels=channels,
                rate=fs,
                input=True,
                output=True,
                frames_per_buffer=chunk_size,
                stream_callback=callback)

stream.start_stream()

# Keep the stream running until it's manually stopped
try:
    while stream.is_active():
        root.mainloop()  # Short delay to reduce CPU usage
except KeyboardInterrupt:
    # If the user presses Ctrl+C, stop the stream
    stream.stop_stream()
    stream.close()
    p.terminate()