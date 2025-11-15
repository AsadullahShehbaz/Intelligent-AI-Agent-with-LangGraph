"""
Voice Input System for Streamlit
"""
import speech_recognition as sr
from io import BytesIO
import tempfile
import os


class VoiceInput:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        # Adjust for ambient noise
        self.recognizer.energy_threshold = 4000
        self.recognizer.dynamic_energy_threshold = True
    
    def transcribe_audio_file(self, audio_file) -> dict:
        """
        Transcribe uploaded audio file to text
        
        Args:
            audio_file: Audio file from st.file_uploader or st.audio_input
        
        Returns:
            dict with 'success', 'text', and optional 'error'
        """
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(audio_file.getvalue())
                tmp_path = tmp_file.name
            
            # Load audio file
            with sr.AudioFile(tmp_path) as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio_data = self.recognizer.record(source)
            
            # Transcribe using Google Speech Recognition (free)
            text = self.recognizer.recognize_google(audio_data)
            
            # Clean up temp file
            os.unlink(tmp_path)
            
            return {
                "success": True,
                "text": text
            }
            
        except sr.UnknownValueError:
            return {
                "success": False,
                "error": "Could not understand audio. Please speak clearly."
            }
        except sr.RequestError as e:
            return {
                "success": False,
                "error": f"Speech recognition service error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error processing audio: {str(e)}"
            }
    
    def transcribe_microphone(self, duration: int = 5) -> dict:
        """
        Record from microphone and transcribe (for local development)
        
        Args:
            duration: Recording duration in seconds
        
        Returns:
            dict with 'success', 'text', and optional 'error'
        """
        try:
            with sr.Microphone() as source:
                print(f"🎤 Listening for {duration} seconds...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                audio_data = self.recognizer.listen(source, timeout=duration)
            
            # Transcribe
            text = self.recognizer.recognize_google(audio_data)
            
            return {
                "success": True,
                "text": text
            }
            
        except sr.WaitTimeoutError:
            return {
                "success": False,
                "error": "No speech detected. Please try again."
            }
        except sr.UnknownValueError:
            return {
                "success": False,
                "error": "Could not understand audio."
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Initialize voice input (choose one)
voice_input = VoiceInput()  # Free option using Google Speech Recognition