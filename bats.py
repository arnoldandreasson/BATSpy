import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

import numpy as np
import matplotlib.pyplot as plt

from dataloader import load_data
from powerspectrum import spectrogram, decibel

from IPython import embed


class Batspy:

    def __init__(self, file_path, f_resolution=1000., overlap_frac=0.9, dynamic_range=50, pcTape_rec=False):
        self.file_path = file_path
        self.file_name = file_path.split('/')[-1]
        self.freq_resolution = f_resolution  # in Hz
        self.overlap_frac = overlap_frac  # Overlap fraction of the NFFT windows
        self.dynamic_range = dynamic_range  # in dB
        self.pcTape_rec = pcTape_rec  # Was this file recorded by PC-Tape?

        # Flow control booleans
        self.data_loaded = False
        self.spectogram_computed = False

    def load_data(self):
        dat, sr, u = load_data(self.file_path)
        self.recording_trace = dat.squeeze()

        if self.pcTape_rec:  # This fixes PC-Tape's bug that writes 1/10 of the samplingrate in the header of the .wav file
            self.sampling_rate = sr * 10.
        else:
            self.sampling_rate = sr

        self.data_loaded = True
        pass

    def compute_spectogram(self, plottable=False):
        if not self.data_loaded:
            self.load_data()
        temp_spec, self.f, self.t = spectrogram(self.recording_trace, self.sampling_rate,
                                                fresolution=self.freq_resolution, overlap_frac=self.overlap_frac)

        # set dynamic range
        dec_spec = decibel(temp_spec)
        ampl_max = np.nanmax(dec_spec)  # define maximum; use nanmax, because decibel function may contain NaN values
        dec_spec -= ampl_max + 1e-20  # subtract maximum so that the maximum value is set to lim x--> -0
        dec_spec[dec_spec < -self.dynamic_range] = -self.dynamic_range

        self.spec_mat = dec_spec

        self.spectogram_computed = True

        if plottable:
            self.plot_spectogram()
        pass

    def plot_spectogram(self):
        if not self.spectogram_computed:
            self.compute_spectogram()

        inch_factor = 2.54
        fig, ax = plt.subplots(figsize=(56. / inch_factor, 30. / inch_factor))
        im = ax.imshow(self.spec_mat, cmap='jet', extent=[self.t[0], self.t[-1], self.f[0], self.f[-1]], aspect='auto',
                       origin='lower', alpha=0.7)
        # ToDo: Impossible to update the colorbar ticks for them to be multiples of 10!!!
        cb_ticks = np.arange(0, self.dynamic_range + 10, 10)

        cb = fig.colorbar(im)

        cb.set_label('dB')
        ax.set_ylabel('Frequency [Hz]')
        ax.set_xlabel('Time [sec]')
        pass

    def detect_calls(self, det_range=(110000., 150000.), th_above_dynamic_range=5., freq_ch_th=15):

        # Set detection threshold relative to the dynamic range
        det_th = -(self.dynamic_range - th_above_dynamic_range)

        # Get the indices of the frequency channels where we want to detect calls
        # ToDo: This needs to be a Matrix that analyses all channels in not just one time lapse, but rather a time window of considerabe length
        ind = np.where(np.logical_and(self.f > det_range[0], self.f < det_range[1]))[0]

        # Sum detection events across all frequency channels and set a second order filter
        suma = np.sum(self.spec_mat[ind] >= det_th, axis=0)
        over_th_ind = np.where(suma > freq_ch_th)[0]

        # ToDo: Join multiple detection events of each call

        # plot call-detection events
        self.plot_spectogram()
        ax = plt.gca()
        ax.plot(self.t[over_th_ind], np.ones(len(over_th_ind))*det_range[1] + 10000, 'o', ms=20, color='darkred', alpha=.8,
                mec='k', mew=3)
        pass


if __name__ == '__main__':

    # Get the data
    recording1 = '../../data/pc-tape_recordings/' \
                'macaregua__february_2018/natalus_outside_cave/natalusTumidirostris0024.wav'
    recording2 = '../../data/pc-tape_recordings/' \
                'macaregua__february_2018/natalus_outside_cave/natalusTumidirostris0045.wav'

    bat1 = Batspy(recording1, pcTape_rec=True)
    bat1.compute_spectogram()
    bat1.detect_calls()

    # bat2 = Batspy(recording1, pcTape_rec=True)
    # bat2.compute_spectogram()
    # bat2.detect_calls()


    plt.show()
    quit()