"""Audio Feature Extraction Module

This module implements audio feature extraction for the VidID system.
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
import torch
import torch.nn as nn
import librosa
from pathlib import Path

from .base import FeatureVector, AudioFeatureExtractor, FeatureExtractorFactory

logger = logging.getLogger(__name__)


class MFCCExtractor(AudioFeatureExtractor):
    """Feature extractor using Mel-frequency cepstral coefficients (MFCCs)."""
    
    def __init__(
        self, 
        n_mfcc: int = 20,
        feature_dim: int = 256,
        device: str = 'cpu'
    ):
        """Initialize the MFCC feature extractor.
        
        Args:
            n_mfcc: Number of MFCCs to extract
            feature_dim: Dimension of the output feature vector
            device: Device to run computations on
        """
        super().__init__(device=device)
        self.n_mfcc = n_mfcc
        self.feature_dim = feature_dim
    
    def initialize(self) -> None:
        """Initialize the MFCC extractor."""
        # No model initialization needed for MFCC extraction
        pass
    
    def extract_segment(self, audio_segment: np.ndarray, sample_rate: int) -> np.ndarray:
        """Extract MFCC features from an audio segment.
        
        Args:
            audio_segment: Audio segment as a numpy array
            sample_rate: Audio sample rate in Hz
            
        Returns:
            MFCC feature vector
        """
        # Convert to mono if stereo
        if audio_segment.ndim > 1:
            audio_segment = np.mean(audio_segment, axis=1)
        
        # Extract MFCCs
        mfccs = librosa.feature.mfcc(
            y=audio_segment,
            sr=sample_rate,
            n_mfcc=self.n_mfcc
        )
        
        # Compute statistics over time
        means = np.mean(mfccs, axis=1)
        stds = np.std(mfccs, axis=1)
        skews = np.zeros_like(means)  # Placeholder for skewness
        
        # Compute skewness if there are enough frames
        if mfccs.shape[1] > 2:
            for i in range(self.n_mfcc):
                skews[i] = librosa.feature.delta(mfccs[i:i+1], width=3).mean()
        
        # Combine statistics
        features = np.concatenate([means, stds, skews])
        
        # Ensure fixed dimensionality
        if len(features) > self.feature_dim:
            features = features[:self.feature_dim]
        elif len(features) < self.feature_dim:
            features = np.pad(features, (0, self.feature_dim - len(features)))
        
        return features
    
    def extract(self, input_data: Dict[str, Any]) -> FeatureVector:
        """Extract MFCC features from the input data.
        
        Args:
            input_data: Dictionary with 'audio' and 'sample_rate' keys
            
        Returns:
            Extracted feature vector
        """
        if not isinstance(input_data, dict) or 'audio' not in input_data or 'sample_rate' not in input_data:
            raise ValueError("Input must be a dictionary with 'audio' and 'sample_rate' keys")
        
        audio = input_data['audio']
        sample_rate = input_data['sample_rate']
        
        features = self.extract_segment(audio, sample_rate)
        
        return FeatureVector(features, {
            'type': 'mfcc',
            'sample_rate': sample_rate,
            'n_mfcc': self.n_mfcc
        })


class AudioFingerprint(AudioFeatureExtractor):
    """Audio fingerprinting extractor similar to Shazam's approach."""
    
    def __init__(
        self, 
        feature_dim: int = 512,
        n_fft: int = 2048,
        hop_length: int = 512,
        device: str = 'cpu'
    ):
        """Initialize the audio fingerprinting extractor.
        
        Args:
            feature_dim: Dimension of the output feature vector
            n_fft: FFT window size
            hop_length: Number of samples between frames
            device: Device to run computations on
        """
        super().__init__(device=device)
        self.feature_dim = feature_dim
        self.n_fft = n_fft
        self.hop_length = hop_length
    
    def initialize(self) -> None:
        """Initialize the audio fingerprinting extractor."""
        # No model initialization needed
        pass
    
    def compute_constellation_map(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Compute a constellation map of peaks in the spectrogram.
        
        Args:
            audio: Audio data as numpy array
            sample_rate: Audio sample rate in Hz
            
        Returns:
            Array of peak points (time, frequency, amplitude)
        """
        # Convert to mono if stereo
        if audio.ndim > 1:
            audio = np.mean(audio, axis=1)
        
        # Compute spectrogram
        D = librosa.stft(audio, n_fft=self.n_fft, hop_length=self.hop_length)
        magnitude = np.abs(D)
        
        # Apply logarithmic scaling
        log_spec = librosa.amplitude_to_db(magnitude, ref=np.max)
        
        # Find local peaks
        peaks = []
        for i in range(1, log_spec.shape[1] - 1):
            for j in range(1, log_spec.shape[0] - 1):
                if log_spec[j, i] > log_spec[j-1:j+2, i-1:i+2].mean() + 3.0:  # Peak threshold
                    time = librosa.frames_to_time(i, sr=sample_rate, hop_length=self.hop_length)
                    freq = librosa.fft_frequencies(sr=sample_rate, n_fft=self.n_fft)[j]
                    amplitude = log_spec[j, i]
                    peaks.append((time, freq, amplitude))
        
        # Sort by amplitude (strongest peaks first)
        peaks.sort(key=lambda x: x[2], reverse=True)
        
        # Take top N peaks
        num_peaks = min(len(peaks), 200)
        return np.array(peaks[:num_peaks]) if num_peaks > 0 else np.empty((0, 3))
    
    def extract_segment(self, audio_segment: np.ndarray, sample_rate: int) -> np.ndarray:
        """Extract audio fingerprint features from an audio segment.
        
        Args:
            audio_segment: Audio segment as a numpy array
            sample_rate: Audio sample rate in Hz
            
        Returns:
            Audio fingerprint feature vector
        """
        # Compute constellation map
        constellation = self.compute_constellation_map(audio_segment, sample_rate)
        
        if constellation.size == 0:
            # No peaks found, return zero vector
            return np.zeros(self.feature_dim)
        
        # Extract fingerprint features from constellation map
        # For simplicity, use a histogram of frequency bins
        freq_bins = np.linspace(0, sample_rate/2, self.feature_dim // 2)
        freq_hist, _ = np.histogram(constellation[:, 1], bins=freq_bins)
        
        # Also add time-based features
        time_bins = np.linspace(0, audio_segment.shape[0] / sample_rate, self.feature_dim // 2)
        time_hist, _ = np.histogram(constellation[:, 0], bins=time_bins)
        
        # Combine features
        features = np.concatenate([freq_hist, time_hist])
        
        # Normalize
        if np.sum(features) > 0:
            features = features / np.sum(features)
        
        return features
    
    def extract(self, input_data: Dict[str, Any]) -> FeatureVector:
        """Extract audio fingerprint from the input data.
        
        Args:
            input_data: Dictionary with 'audio' and 'sample_rate' keys
            
        Returns:
            Extracted feature vector
        """
        if not isinstance(input_data, dict) or 'audio' not in input_data or 'sample_rate' not in input_data:
            raise ValueError("Input must be a dictionary with 'audio' and 'sample_rate' keys")
        
        audio = input_data['audio']
        sample_rate = input_data['sample_rate']
        
        features = self.extract_segment(audio, sample_rate)
        
        # Create metadata for the feature vector
        constellation = self.compute_constellation_map(audio, sample_rate)
        peak_count = len(constellation)
        
        return FeatureVector(features, {
            'type': 'audio_fingerprint',
            'sample_rate': sample_rate,
            'duration': audio.shape[0] / sample_rate,
            'peak_count': peak_count
        })


class WaveformStatisticsExtractor(AudioFeatureExtractor):
    """Extractor for basic waveform statistics."""
    
    def __init__(
        self, 
        feature_dim: int = 64,
        device: str = 'cpu'
    ):
        """Initialize the waveform statistics extractor.
        
        Args:
            feature_dim: Dimension of the output feature vector
            device: Device to run computations on
        """
        super().__init__(device=device)
        self.feature_dim = feature_dim
    
    def initialize(self) -> None:
        """Initialize the waveform statistics extractor."""
        # No model initialization needed
        pass
    
    def extract_segment(self, audio_segment: np.ndarray, sample_rate: int) -> np.ndarray:
        """Extract waveform statistics from an audio segment.
        
        Args:
            audio_segment: Audio segment as a numpy array
            sample_rate: Audio sample rate in Hz
            
        Returns:
            Waveform statistics feature vector
        """
        # Convert to mono if stereo
        if audio_segment.ndim > 1:
            audio_segment = np.mean(audio_segment, axis=1)
        
        # Basic time-domain features
        mean = np.mean(audio_segment)
        std = np.std(audio_segment)
        rms = np.sqrt(np.mean(audio_segment**2))
        zcr = np.mean(librosa.feature.zero_crossing_rate(audio_segment))
        
        # Energy metrics
        energy = np.sum(audio_segment**2) / len(audio_segment)
        
        # Split into frames and compute statistics per frame
        frame_length = int(sample_rate * 0.025)  # 25ms frames
        hop_length = int(sample_rate * 0.010)   # 10ms hop
        
        frames = librosa.util.frame(audio_segment, frame_length=frame_length, hop_length=hop_length)
        frame_means = np.mean(frames, axis=0)
        frame_stds = np.std(frames, axis=0)
        frame_energies = np.sum(frames**2, axis=0) / frame_length
        
        # Compute spectral features
        spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=audio_segment, sr=sample_rate))
        spectral_bandwidth = np.mean(librosa.feature.spectral_bandwidth(y=audio_segment, sr=sample_rate))
        spectral_rolloff = np.mean(librosa.feature.spectral_rolloff(y=audio_segment, sr=sample_rate))
        
        # Base features
        base_features = np.array([mean, std, rms, zcr, energy, 
                              spectral_centroid, spectral_bandwidth, spectral_rolloff])
        
        # Statistics of frame features
        frame_features = np.concatenate([
            np.percentile(frame_means, [25, 50, 75]),
            np.percentile(frame_stds, [25, 50, 75]),
            np.percentile(frame_energies, [25, 50, 75]),
        ])
        
        # Combine all features
        combined = np.concatenate([base_features, frame_features])
        
        # Ensure fixed dimensionality
        if len(combined) > self.feature_dim:
            combined = combined[:self.feature_dim]
        elif len(combined) < self.feature_dim:
            combined = np.pad(combined, (0, self.feature_dim - len(combined)))
        
        return combined
    
    def extract(self, input_data: Dict[str, Any]) -> FeatureVector:
        """Extract waveform statistics from the input data.
        
        Args:
            input_data: Dictionary with 'audio' and 'sample_rate' keys
            
        Returns:
            Extracted feature vector
        """
        if not isinstance(input_data, dict) or 'audio' not in input_data or 'sample_rate' not in input_data:
            raise ValueError("Input must be a dictionary with 'audio' and 'sample_rate' keys")
        
        audio = input_data['audio']
        sample_rate = input_data['sample_rate']
        
        features = self.extract_segment(audio, sample_rate)
        
        return FeatureVector(features, {
            'type': 'waveform_stats',
            'sample_rate': sample_rate,
            'duration': audio.shape[0] / sample_rate
        })


# Register audio feature extractors
FeatureExtractorFactory.register('mfcc', MFCCExtractor)
FeatureExtractorFactory.register('audio_fingerprint', AudioFingerprint)
FeatureExtractorFactory.register('waveform_stats', WaveformStatisticsExtractor)
