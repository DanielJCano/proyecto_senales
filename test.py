from scipy import signal
import numpy as np
import soundfile as sf
from pathlib import Path


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

    for n in range(input_signal.shape[0]):
        # The allpass coefficient is computed for each sample
        # to show its adaptability
        a1 = a1_coefficient(break_frequency[n], sampling_rate)

        # The allpass difference equation
        # Check the article on the allpass filter for an 
        # in-depth explanation
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
    filter_output = filter_output * 0.5  # Changed here

    # Apply the given amplitude
    filter_output = filter_output * amplitude  # Changed here

    return filter_output


def white_noise_filtering_example(input_filename, output_filename):
    # Read the input file
    sampling_rate, input_signal = wavfile.read(input_filename)

    # Make the cutoff frequency decay with time ("real-time control")
    cutoff_frequency = np.geomspace(20000, 20, input_signal.shape[0])

    # Actual filtering
    filter_output = allpass_based_filter(input_signal, \
        cutoff_frequency, sampling_rate, highpass=False, amplitude=0.1)

    # Write the result to the output file
    wavfile.write(output_filename, sampling_rate, filter_output.astype(np.int16))  # Cast to int16 here



def main():
    input_filename = 'Frase_Ruido.wav'
    output_filename = 'output.wav'
    white_noise_filtering_example(input_filename, output_filename)


if __name__ == '__main__':
    main()