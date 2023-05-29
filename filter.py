import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import pyaudio
import time


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


def allpass_based_filter(input_signal, cutoff_frequency, sampling_rate, highpass=False, amplitude=0.8):
    # Perform allpass filtering
    allpass_output = allpass_filter(input_signal, cutoff_frequency, sampling_rate)

    # If we want a highpass, we need to invert 
    # the allpass output in phase
    if highpass:
        allpass_output *= -1

    # Sum the allpass output with the direct path
    filter_output = input_signal + allpass_output

    # Scale the amplitude to prevent clipping
    filter_output *= .4

    # Apply the given amplitude
    filter_output *= amplitude

    return filter_output

# Set some parameters
fs = 44100  # Sampling rate
chunk_size = 4056  # Number of audio frames processed per chunk
channels = 2  # Mono audio
format = pyaudio.paFloat32  # 32-bit float audio data
cutoff_frequency = 120  # Cutoff frequency in Hz

# Initialize PyAudio
p = pyaudio.PyAudio()

# Initialize the input buffer for plotting
input_buffer = np.zeros(chunk_size)

# Create a tkinter window
root = tk.Tk()
root.title("Audio Output Visualization")

# Create a Figure and a subplot for the plot
fig = Figure(figsize=(8, 4), dpi=100)
subplot = fig.add_subplot(1, 1, 1)
#subplot.set_xlim([0, chunk_size])
#subplot.set_ylim([-1, 1])

# Create a canvas for the Figure
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
canvas.draw()

# Callback function to process audio chunks
def callback(in_data, frame_count, time_info, status):
    # Ensure the input data is the right shape and type
    input_data = np.frombuffer(in_data, dtype=np.float32)

    # Apply the filter
    output_data = allpass_based_filter(
        input_data, cutoff_frequency, fs, highpass=False, amplitude=0.29
    )

    # Update the input buffer for plotting
    input_buffer[:] = input_data[:chunk_size]

    # Update the plot with the input buffer
    subplot.clear()
    subplot.plot(input_buffer)
    #subplot.set_xlim([0, chunk_size])
    subplot.set_ylim([-0.2, 0.2])
    canvas.draw()

    # Return the output data and a flag indicating the stream should continue
    return output_data.tobytes(), pyaudio.paContinue

# Create a stream and start it
stream = p.open(
    format=format,
    channels=channels,
    rate=fs,
    input=True,
    output=True,
    frames_per_buffer=chunk_size,
    stream_callback=callback
)

stream.start_stream()

# Start the tkinter event loop
root.mainloop()

# Stop the audio stream and terminate PyAudio
stream.stop_stream()
stream.close()
p.terminate()
