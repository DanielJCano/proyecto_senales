import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import pyaudio
import time
import threading
import queue




# ==================> PARAMETERS <==================

BABY_POWDER = '#F7F9F7'
VISTA_BLUE = '#8093F1'
CORAL_PINK = '#FE938C'

# ==================> Create a tkinter window <==================

root = tk.Tk()
root.title("Filtro Pasa Bandas y Filtro Notch")
root.geometry("800x500")
# add background color
root.configure(bg=BABY_POWDER)


# Set some parameters
fs = 44100  # Sampling rate
chunk_size = 5112  # Number of audio frames processed per chunk
channels = 2  # Mono audio
format = pyaudio.paFloat32  # 32-bit float audio data
# cutoff_frequency = 500  # Cutoff frequency in Hz
# notch_center_frequency = 6000 # Center frequency of the notch filter in Hz
# notch_quality_factor = 17  # Quality factor of the notch filter

lock = threading.Lock()
# Variables to hold the filter settings
cutoff_frequency = tk.DoubleVar(root, value=120)
notch_center_frequency = tk.DoubleVar(root, value=6000)
notch_quality_factor = tk.DoubleVar(root, value=17)
amplitude = tk.DoubleVar(root, value=0.4)
notch_filter_radio = tk.BooleanVar(root, value=True)





# ==================> FUNCTIONS <==================

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


def allpass_based_filter(input_signal, cutoff_frequency, sampling_rate, highpass=False, amplitude=1):
    # Perform allpass filtering
    allpass_output = allpass_filter(input_signal, cutoff_frequency, sampling_rate)

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


def notch_filter(input_signal, center_frequency, quality_factor, sampling_rate):
    try:
        w0 = 2 * np.pi * center_frequency / sampling_rate
        alpha = np.sin(w0) / (2 * quality_factor)
        
        b0 = 1
        b1 = -2 * np.cos(w0)
        b2 = 1
        a0 = 1 + alpha
        a1 = -2 * np.cos(w0)
        a2 = 1 - alpha
        
        # Apply the notch filter difference equation
        output_signal = np.zeros_like(input_signal)
        for n in range(input_signal.shape[0]):
            if n >= 2:
                output_signal[n] = (
                    (b0 * input_signal[n] + b1 * input_signal[n - 1] + b2 * input_signal[n - 2])
                    - (a1 * output_signal[n - 1] + a2 * output_signal[n - 2])
                ) / a0
            elif n == 1:
                output_signal[n] = (
                    (b0 * input_signal[n] + b1 * input_signal[n - 1])
                    - (a1 * output_signal[n - 1])
                ) / a0
            else:
                output_signal[n] = (b0 * input_signal[n]) / a0
    except:
        pass
        
    return output_signal

# Create a queue to pass the data between threads
audio_queue = queue.Queue()
output_queue = queue.Queue()

# Function to process audio data
def audio_processing_thread():
    while True:
        # Get the next chunk of data from the queue
        data = audio_queue.get()

        # If the data is None, this is a signal to exit
        if data is None:
            break

        # Ensure the input data is the right shape and type
        input_data = np.frombuffer(data, dtype=np.float32)

        # Lock the access to shared variables for thread safety
        with lock:
            cutoff_freq = cutoff_frequency.get()
            notch_center_freq = notch_center_frequency.get()
            notch_quality = notch_quality_factor.get()
            amp = amplitude.get()

        # Apply the notch filter

        # filtered_data = notch_filter(input_data, notch_center_freq, notch_quality, fs)

        filtered_data = input_data

        # Apply the allpass-based filter
        output_data = allpass_based_filter(
            filtered_data, cutoff_freq, fs, highpass=False, amplitude=amp)
        
        # Put the output data in the output queue
        output_queue.put(output_data.tobytes())

        # Indicate that the task is done
        audio_queue.task_done()

# Create a stream and audio_thread as global variables
stream = None
audio_thread = None

# Callback function to process audio chunks
def callback(in_data, frame_count, time_info, status):
    # Put the incoming data in the queue
    audio_queue.put(in_data)

    # Convert in_data to a NumPy array for the buffer
    input_data = np.frombuffer(in_data, dtype=np.float32)

    # Update the input buffer for plotting
    input_buffer[:] = input_data[:chunk_size]

    # Get the processed data from the audio processing thread
    output_data = output_queue.get()

    # Update the plot with the output buffer
    subplot.clear()
    subplot.plot(np.frombuffer(output_data, dtype=np.float32))
    subplot.set_ylim([-0.5, 0.5])
    canvas.draw()

    # Return the output data and a flag indicating the stream should continue
    return (output_data, pyaudio.paContinue,)

# Initialize PyAudio
p = pyaudio.PyAudio() 

# Initialize the input buffer for plotting
input_buffer = np.zeros(chunk_size)

# Function to start the stream
def start_stream():
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
    # Create and start the audio processing thread
    audio_thread = threading.Thread(target=audio_processing_thread)
    audio_thread.start()

# Function to stop the stream
def stop_stream():
    # stop the tkinter loop
    root.quit()
    # Stop the audio stream and terminate PyAudio
    # stream.stop_stream()
    stream.close()
    p.terminate()
    # At the end of your program, you'll need to stop the thread
    # Put None in the queue to signal the thread to exit
    audio_queue.put(None)

    # Wait for the thread to finish
    audio_thread.join()
    exit()


# Create a slider to change the notch center frequency
notch_freq_slider = tk.Scale(root, from_=1000, to=20000, variable=notch_center_frequency, label='Notch Center Frequency', orient='horizontal', length=150, bg=VISTA_BLUE)
notch_freq_slider.place(x=450, y=100)

# Create a slider to change the notch quality factor
quality_factor_slider = tk.Scale(root, from_=1, to=30, variable=notch_quality_factor, label='Notch Quality Factor', orient='horizontal', length=150, bg=VISTA_BLUE)
quality_factor_slider.place(x=450, y=20)


# Create a slider to change the amplitude
amplitude_slider = tk.Scale(root, from_=0.1, to=1, resolution=0.1, variable=amplitude, label='Amplitude', orient='horizontal', length=150, bg=VISTA_BLUE)
amplitude_slider.place(x=250, y=100)


# Create a slider to change the cutoff frequency
cutoff_slider = tk.Scale(root, from_=10, to=1200, variable=cutoff_frequency, label='Cutoff Frequency', orient='horizontal', resolution=10, length=150, bg=VISTA_BLUE)
cutoff_slider.place(x=250, y=20)


# Create a button to start the stream
start_button = tk.Button(root, text='Start', command=start_stream, bg=VISTA_BLUE)
start_button.place(x=350, y=230)

# Create a button to stop the stream
stop_button = tk.Button(root, text='Stop', command=stop_stream, bg=CORAL_PINK)
stop_button.place(x=450, y=230)

# add raido buttons that changes if it uses the notch filter or not
notch_filter_button = tk.Checkbutton(root, text='Notch Filter', variable=notch_filter_radio, bg=BABY_POWDER)
notch_filter_button.place(x=50, y=20)


# Create a Figure and a subplot for the plot
fig = Figure(figsize=(8, 2), dpi=100, facecolor=BABY_POWDER)
subplot = fig.add_subplot(1, 1, 1)

# Create a canvas for the Figure
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().place(x=0, y=280)
canvas.draw()


if __name__ == '__main__':
    # Start the tkinter event loop
    root.mainloop()



