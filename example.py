#-*- coding: utf_8 -*-
import matplotlib
import cPickle
import numpy as np
import os
import sys
import librosa
from scipy.misc import imsave
import auralise

''' 2015-09-28 Keunwoo Choi
- [0] load cnn weights that is learned from keras (http://keras.io) - but you don't need to install it.
- [1] load a song file (STFT).
---[1-0] log_amplitude(abs(STFT))
-- [1-1] feed-forward the spectrogram,
--- [1-1-0]using NOT theano, just scipy and numpy on CPU. Thus it's slow.
-- [1-2] then 'deconve' using switch matrix for every convolutional layer.
-- [1-3] 'separate' or 'auralise' the deconved spectrogram using phase information of original signal.
- [2]listen up!
'''

if __name__ == "__main__":
	'''
	This is main body of program I used for the paper at ismir. 
	You need a keras model weights file with music files at the appropriate folder... In other words, it won't be executed at your computer.
	Just see the part after 
		print '--- deconve! ---'
	, where the deconvolution functions are used.

	'''
	# load learned weights
	W, layer_names = auralise.load_weights()
	num_conv_layer = len(W)

	# load files
	print '--- prepare files ---'
	filenames_src = ['bach.wav', 'dream.wav', 'toy.wav']
	path_SRC = 'src_songs/'
	path_src = 'src_songs/'
	print '--- Please modify above to run on your file ---'
	filenames_SRC = []
	
	N_FFT = 512
	SAMPLE_RATE = 11025

	# get STFT of the files.
	for filename in filenames_src:
		song_id = filename.split('.')[0]
		if os.path.exists(path_SRC + song_id + '.npy'):
			pass
		else:
			src = librosa.load(os.path.join(path_src, filename), sr=SAMPLE_RATE, mono=True, duration=4.)[0]
			SRC = librosa.stft(src, n_fft=N_FFT, hop_length=N_FFT/2)
			if SRC.shape[1] > 173:
				SRC = SRC[:, :173]
			elif SRC.shape[1] < 173:
				temp = np.zeros((257, 173))
				temp[:, :SRC.shape[1]] = SRC
				SRC = temp
			np.save(path_SRC + song_id + '.npy', SRC)
		filenames_SRC.append(song_id + '.npy')

	# deconve
	depths = [5,4,3,2,1]
	for filename in filenames_SRC:
		song_id = filename.split('.')[0]
		SRC = np.load(path_SRC + filename)
		filename_out = '%s_a_original.wav' % (song_id)	
		if not os.path.exists(path_SRC + song_id):
			os.makedirs(path_src + song_id)	
		if not os.path.exists(path_SRC + song_id + '_img'):
			os.makedirs(path_src + song_id + '_img')
		librosa.output.write_wav(path_src+ song_id + '/' + filename_out, librosa.istft(SRC, hop_length=N_FFT/2), sr=SAMPLE_RATE, norm=True)

		for depth in depths:
	
			print '--- deconve! ---'
			deconvedMASKS = auralise.get_deconve_mask(W[:depth], layer_names, SRC, depth) # size can be smaller than SRC due to downsampling

			print 'result; %d masks with size of %d, %d' % deconvedMASKS.shape
			for deconved_feature_ind, deconvedMASK_here in enumerate(deconvedMASKS):
				MASK = np.zeros(SRC.shape)
				MASK[0:deconvedMASK_here.shape[0], 0:deconvedMASK_here.shape[1]] = deconvedMASK_here
				deconvedSRC = np.multiply(SRC, MASK)

				filename_out = '%s_deconved_from_depth_%d_feature_%d.wav' % (song_id, depth, deconved_feature_ind)
				librosa.output.write_wav(path_src+ song_id + '/' + filename_out, librosa.istft(deconvedSRC, hop_length=N_FFT/2), SAMPLE_RATE, norm=True)
				filename_img_out = 'spectrogram_%s_from_depth_%d_feature_%d.png' % (song_id, depth, deconved_feature_ind)
				imsave(path_src+song_id + '_img' + '/' + filename_img_out , np.flipud(np.multiply(np.abs(SRC), MASK)))

				filename_img_out = 'filter_for_%s_from_depth_%d_feature_%d.png' % (song_id, depth, deconved_feature_ind)
				imsave(path_src+song_id + '_img' + '/' + filename_img_out , np.flipud(MASK))
				
