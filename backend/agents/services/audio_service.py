import logging
import os
import tempfile
from typing import Any

import numpy as np
import speech_recognition as sr
from pydub import AudioSegment

logger = logging.getLogger(__name__)

class AudioService:
    """
    Service for processing audio content including speech recognition and analysis
    """
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.supported_formats = ['wav', 'mp3', 'ogg', 'm4a', 'flac']
        self.languages = {
            'en-US': 'English (US)',
            'en-GB': 'English (UK)',
            'es-ES': 'Spanish',
            'fr-FR': 'French',
            'de-DE': 'German',
            'it-IT': 'Italian',
            'ja-JP': 'Japanese',
            'ko-KR': 'Korean',
            'zh-CN': 'Chinese (Mandarin)'
        }
    
    def process_audio(self, audio_path: str, language: str = 'en-US') -> dict[str, Any]:
        """
        Comprehensive audio processing including speech recognition and analysis
        
        Args:
            audio_path: Path to the audio file
            language: Language code for speech recognition
            
        Returns:
            Audio processing results
        """
        try:
            if not os.path.exists(audio_path):
                return {'error': 'Audio file not found'}
            
            # Load audio file
            audio_info = self._get_audio_info(audio_path)
            
            # Convert to wav if necessary for speech recognition
            wav_path = self._convert_to_wav(audio_path)
            
            analysis = {
                'audio_info': audio_info,
                'speech_recognition': self._recognize_speech(wav_path, language),
                'audio_features': self._analyze_audio_features(wav_path),
                'voice_analysis': self._analyze_voice_characteristics(wav_path)
            }
            
            # Cleanup temporary file if created
            if wav_path != audio_path and os.path.exists(wav_path):
                os.remove(wav_path)
            
            return analysis
            
        except Exception as e:  # noqa: BLE001
            logger.error(f"Audio processing error: {e!s}")
            return {'error': str(e)}
    
    def _get_audio_info(self, audio_path: str) -> dict[str, Any]:
        """Get basic audio file information"""
        try:
            audio = AudioSegment.from_file(audio_path)
            
            return {
                'duration_seconds': len(audio) / 1000.0,
                'duration_minutes': len(audio) / 60000.0,
                'sample_rate': audio.frame_rate,
                'channels': audio.channels,
                'sample_width': audio.sample_width,
                'frame_count': audio.frame_count(),
                'file_size_mb': os.path.getsize(audio_path) / (1024 * 1024)
            }
            
        except Exception as e:  # noqa: BLE001
            logger.error(f"Audio info error: {e!s}")
            return {'error': str(e)}
    
    def _convert_to_wav(self, audio_path: str) -> str:
        """Convert audio file to WAV format for speech recognition"""
        try:
            file_extension = os.path.splitext(audio_path)[1].lower()
            
            if file_extension == '.wav':
                return audio_path
            
            # Load audio and convert to wav
            audio = AudioSegment.from_file(audio_path)
            
            # Create temporary wav file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                wav_path = tmp_file.name
            
            # Export as wav
            audio.export(wav_path, format='wav')
            
            return wav_path
            
        except Exception as e:  # noqa: BLE001
            logger.error(f"Audio conversion error: {e!s}")
            return audio_path
    
    def _recognize_speech(self, wav_path: str, language: str = 'en-US') -> dict[str, Any]:
        """Recognize speech from audio file"""
        try:
            with sr.AudioFile(wav_path) as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # Listen to the audio
                audio_data = self.recognizer.listen(source)
            
            # Try multiple recognition methods
            recognition_results = {}
            
            # Google Speech Recognition (free tier)
            try:
                google_result = self.recognizer.recognize_google(audio_data, language=language)
                recognition_results['google'] = {
                    'text': google_result,
                    'confidence': 0.8  # Google doesn't provide confidence scores for free tier
                }
            except sr.UnknownValueError:
                recognition_results['google'] = {'error': 'Could not understand audio'}
            except sr.RequestError as e:
                recognition_results['google'] = {'error': f'Request error: {e!s}'}
            
            # Sphinx (offline recognition)
            try:
                sphinx_result = self.recognizer.recognize_sphinx(audio_data)
                recognition_results['sphinx'] = {
                    'text': sphinx_result,
                    'confidence': 0.6  # Sphinx generally lower confidence
                }
            except sr.UnknownValueError:
                recognition_results['sphinx'] = {'error': 'Could not understand audio'}
            except sr.RequestError as e:
                recognition_results['sphinx'] = {'error': f'Sphinx error: {e!s}'}
            
            # Determine best result
            best_result = self._select_best_recognition(recognition_results)
            
            return {
                'all_results': recognition_results,
                'best_result': best_result,
                'language': language,
                'word_count': len(best_result.split()) if best_result else 0
            }
            
        except Exception as e:  # noqa: BLE001
            logger.error(f"Speech recognition error: {e!s}")
            return {'error': str(e)}
    
    def _select_best_recognition(self, results: dict[str, dict]) -> str:
        """Select the best recognition result from multiple methods"""
        # Priority order for recognition methods
        priority_methods = ['google', 'sphinx']
        
        for method in priority_methods:
            if method in results and 'text' in results[method]:
                return results[method]['text']
        
        return ""
    
    def _analyze_audio_features(self, wav_path: str) -> dict[str, Any]:
        """Analyze audio features like volume, silence, etc."""
        try:
            audio = AudioSegment.from_wav(wav_path)
            
            # Convert to numpy array for analysis
            samples = np.array(audio.get_array_of_samples())
            if audio.channels == 2:
                samples = samples.reshape((-1, 2))
                samples = samples.mean(axis=1)  # Convert to mono
            
            # Normalize
            samples = samples.astype(np.float32) / np.iinfo(samples.dtype).max
            
            # Audio features
            features = {
                'rms_volume': float(np.sqrt(np.mean(samples**2))),
                'peak_volume': float(np.max(np.abs(samples))),
                'zero_crossing_rate': self._calculate_zero_crossing_rate(samples),
                'silence_ratio': self._calculate_silence_ratio(samples),
                'dynamic_range': float(np.max(samples) - np.min(samples)),
                'energy': float(np.sum(samples**2))
            }
            
            # Classify audio characteristics
            features['volume_level'] = self._classify_volume_level(features['rms_volume'])
            features['audio_quality'] = self._assess_audio_quality(features)
            
            return features
            
        except Exception as e:  # noqa: BLE001
            logger.error(f"Audio features error: {e!s}")
            return {'error': str(e)}
    
    def _calculate_zero_crossing_rate(self, samples: np.ndarray) -> float:
        """Calculate zero crossing rate"""
        zero_crossings = np.sum(np.diff(np.signbit(samples)))
        return float(zero_crossings / len(samples))
    
    def _calculate_silence_ratio(self, samples: np.ndarray, threshold: float = 0.01) -> float:
        """Calculate ratio of silence in audio"""
        silence_samples = np.sum(np.abs(samples) < threshold)
        return float(silence_samples / len(samples))
    
    def _classify_volume_level(self, rms_volume: float) -> str:
        """Classify volume level"""
        if rms_volume > 0.3:
            return 'loud'
        elif rms_volume > 0.1:
            return 'normal'
        elif rms_volume > 0.02:
            return 'quiet'
        else:
            return 'very_quiet'
    
    def _assess_audio_quality(self, features: dict[str, float]) -> str:
        """Assess overall audio quality"""
        quality_score = 0
        
        # Good dynamic range
        if features['dynamic_range'] > 0.5:
            quality_score += 2
        elif features['dynamic_range'] > 0.2:
            quality_score += 1
        
        # Not too much silence
        if features['silence_ratio'] < 0.3:
            quality_score += 2
        elif features['silence_ratio'] < 0.6:
            quality_score += 1
        
        # Reasonable volume
        if 0.05 < features['rms_volume'] < 0.8:
            quality_score += 2
        elif 0.02 < features['rms_volume'] < 0.9:
            quality_score += 1
        
        # Low zero crossing rate (indicates clear speech)
        if features['zero_crossing_rate'] < 0.1:
            quality_score += 1
        
        if quality_score >= 5:
            return 'high'
        elif quality_score >= 3:
            return 'medium'
        else:
            return 'low'
    
    def _analyze_voice_characteristics(self, wav_path: str) -> dict[str, Any]:
        """Analyze voice characteristics (basic implementation)"""
        try:
            audio = AudioSegment.from_wav(wav_path)
            samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
            
            if audio.channels == 2:
                samples = samples.reshape((-1, 2))
                samples = samples.mean(axis=1)
            
            # Basic voice analysis
            characteristics = {
                'speaking_rate': self._estimate_speaking_rate(samples, audio.frame_rate),
                'pitch_variation': self._estimate_pitch_variation(samples),
                'pause_frequency': self._analyze_pauses(samples, audio.frame_rate),
                'speech_clarity': self._estimate_speech_clarity(samples)
            }
            
            return characteristics
            
        except Exception as e:  # noqa: BLE001
            logger.error(f"Voice analysis error: {e!s}")
            return {'error': str(e)}
    
    def _estimate_speaking_rate(self, samples: np.ndarray, sample_rate: int) -> dict[str, Any]:
        """Estimate speaking rate (words per minute)"""
        # Simplified estimation based on energy peaks
        duration_seconds = len(samples) / sample_rate
        
        # Basic peak detection for speech segments
        energy = np.convolve(samples**2, np.ones(int(sample_rate * 0.1)), mode='same')
        peaks = len([i for i in range(1, len(energy)-1) 
                    if energy[i] > energy[i-1] and energy[i] > energy[i+1] 
                    and energy[i] > np.mean(energy) * 0.5])
        
        estimated_wpm = (peaks * 60) / duration_seconds if duration_seconds > 0 else 0
        
        return {
            'words_per_minute': estimated_wpm,
            'classification': 'fast' if estimated_wpm > 150 else 'normal' if estimated_wpm > 100 else 'slow'
        }
    
    def _estimate_pitch_variation(self, samples: np.ndarray) -> dict[str, Any]:
        """Estimate pitch variation in speech"""
        # Basic pitch variation estimation using autocorrelation
        # This is a simplified implementation
        autocorr = np.correlate(samples, samples, mode='full')
        autocorr = autocorr[autocorr.size // 2:]
        
        pitch_variation = float(np.std(autocorr[:min(len(autocorr), 1000)]))
        
        return {
            'variation_score': pitch_variation,
            'classification': 'monotone' if pitch_variation < 0.1 else 'expressive'
        }
    
    def _analyze_pauses(self, samples: np.ndarray, sample_rate: int) -> dict[str, Any]:
        """Analyze speech pauses"""
        # Detect silence periods
        silence_threshold = np.max(np.abs(samples)) * 0.05
        is_silence = np.abs(samples) < silence_threshold
        
        # Find silence segments
        silence_segments = []
        in_silence = False
        silence_start = 0
        
        for i, silent in enumerate(is_silence):
            if silent and not in_silence:
                in_silence = True
                silence_start = i
            elif not silent and in_silence:
                in_silence = False
                silence_duration = (i - silence_start) / sample_rate
                if silence_duration > 0.1:  # Only count pauses > 100ms
                    silence_segments.append(silence_duration)
        
        if silence_segments:
            return {
                'total_pauses': len(silence_segments),
                'average_pause_duration': float(np.mean(silence_segments)),
                'longest_pause': float(np.max(silence_segments)),
                'pause_frequency': len(silence_segments) / (len(samples) / sample_rate / 60)  # pauses per minute
            }
        else:
            return {
                'total_pauses': 0,
                'average_pause_duration': 0.0,
                'longest_pause': 0.0,
                'pause_frequency': 0.0
            }
    
    def _estimate_speech_clarity(self, samples: np.ndarray) -> dict[str, Any]:
        """Estimate speech clarity based on audio characteristics"""
        # Signal-to-noise ratio estimation
        signal_power = np.mean(samples**2)
        noise_estimate = np.min(samples**2[samples**2 > 0]) if np.any(samples**2 > 0) else signal_power
        
        snr = 10 * np.log10(signal_power / noise_estimate) if noise_estimate > 0 else 0
        
        clarity_score = min(100, max(0, (snr + 20) * 2))  # Normalize to 0-100
        
        return {
            'snr_db': float(snr),
            'clarity_score': float(clarity_score),
            'classification': 'clear' if clarity_score > 70 else 'moderate' if clarity_score > 40 else 'unclear'
        }
    
    def generate_audio_summary(self, analysis: dict[str, Any]) -> str:
        """
        Generate natural language summary of audio analysis
        
        Args:
            analysis: Audio analysis results
            
        Returns:
            Natural language summary
        """
        summary_parts = []
        
        # Basic info
        if 'audio_info' in analysis:
            info = analysis['audio_info']
            duration = info.get('duration_seconds', 0)
            summary_parts.append(
                f"This is a {duration:.1f}-second audio file with {info.get('channels', 1)} channel(s)."
            )
        
        # Speech recognition
        if 'speech_recognition' in analysis and analysis['speech_recognition'].get('best_result'):
            text = analysis['speech_recognition']['best_result']
            word_count = analysis['speech_recognition'].get('word_count', 0)
            summary_parts.append(
                f"The audio contains speech with approximately {word_count} words."
            )
            if len(text) < 200:
                summary_parts.append(f"The transcript reads: '{text}'")
        
        # Audio quality
        if 'audio_features' in analysis:
            features = analysis['audio_features']
            quality = features.get('audio_quality', 'unknown')
            volume = features.get('volume_level', 'normal')
            summary_parts.append(f"The audio quality is {quality} with {volume} volume levels.")
        
        # Voice characteristics
        if 'voice_analysis' in analysis:
            voice = analysis['voice_analysis']
            if 'speaking_rate' in voice:
                rate = voice['speaking_rate'].get('classification', 'normal')
                summary_parts.append(f"The speaking rate appears to be {rate}.")
        
        return ' '.join(summary_parts) if summary_parts else "Unable to generate audio summary."
    
    def extract_keywords(self, transcript: str) -> list[str]:
        """Extract keywords from transcript (basic implementation)"""
        if not transcript:
            return []
        
        # Simple keyword extraction
        words = transcript.lower().split()
        
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        keywords = [word.strip('.,!?;:') for word in words if word not in stop_words and len(word) > 3]
        
        # Count frequency and return most common
        from collections import Counter
        word_counts = Counter(keywords)
        
        return [word for word, count in word_counts.most_common(10)]