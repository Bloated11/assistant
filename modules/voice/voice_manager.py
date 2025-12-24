import logging
import threading

logger = logging.getLogger(__name__)

class VoiceManager:
    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.language = config.get('language', 'en-US')
        self.speech_rate = config.get('speech_rate', 150)
        self.volume = config.get('volume', 0.8)
        self.wake_word = config.get('wake_word', 'phenom')
        
        self.tts_engine = None
        self.recognizer = None
        self.microphone = None
        
        if self.enabled:
            self._initialize()
        
        logger.info(f"VoiceManager initialized (enabled={self.enabled})")
    
    def _initialize(self):
        try:
            import pyttsx3
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', self.speech_rate)
            self.tts_engine.setProperty('volume', self.volume)
            logger.info("Text-to-speech engine initialized")
        except Exception as e:
            logger.error(f"Failed to initialize TTS: {e}")
            self.enabled = False
            return
        
        try:
            import speech_recognition as sr
            self.recognizer = sr.Recognizer()
            
            device_index = self.config.get('microphone_index', None)
            if device_index is not None:
                self.microphone = sr.Microphone(device_index=device_index)
                logger.info(f"Using microphone device {device_index}")
            else:
                self.microphone = sr.Microphone()
                logger.info("Using default microphone")
            
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.8
            
            with self.microphone as source:
                logger.info("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                logger.info(f"Energy threshold set to: {self.recognizer.energy_threshold}")
            
            logger.info("Speech recognition initialized")
        except Exception as e:
            logger.error(f"Failed to initialize speech recognition: {e}")
            self.enabled = False
    
    def speak(self, text: str):
        if not self.enabled or not self.tts_engine:
            logger.warning(f"TTS disabled, would say: {text}")
            return
        
        try:
            logger.info(f"Speaking: {text}")
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            logger.error(f"TTS error: {e}")
    
    def listen(self, timeout: int = 5, show_feedback: bool = False) -> str:
        if not self.enabled or not self.recognizer or not self.microphone:
            logger.error("Speech recognition not available")
            return ""
        
        try:
            import speech_recognition as sr
            
            if show_feedback:
                print("🎤 Listening...")
            logger.info("Listening...")
            
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
            
            if show_feedback:
                print("🔄 Processing speech...")
            logger.info("Processing speech...")
            
            text = self.recognizer.recognize_google(audio, language=self.language)
            logger.info(f"Recognized: {text}")
            
            if show_feedback:
                print(f"✅ Heard: {text}")
            
            return text
        
        except sr.WaitTimeoutError:
            logger.debug("Listening timeout - no speech detected")
            if show_feedback:
                print("⏱️  Timeout - no speech detected")
            return ""
        except sr.UnknownValueError:
            logger.warning("Could not understand audio - speech unclear or too quiet")
            if show_feedback:
                print("❌ Could not understand - please speak louder and clearer")
            return ""
        except sr.RequestError as e:
            logger.error(f"Speech recognition API error: {e}")
            if show_feedback:
                print(f"❌ API error: {e}")
            return ""
        except Exception as e:
            logger.error(f"Unexpected error during listening: {e}")
            if show_feedback:
                print(f"❌ Error: {e}")
            return ""
    
    def listen_for_wake_word(self, timeout: int = 5, show_feedback: bool = False) -> bool:
        text = self.listen(timeout, show_feedback=show_feedback)
        if text and self.wake_word.lower() in text.lower():
            logger.info(f"Wake word '{self.wake_word}' detected")
            return True
        return False
    
    def list_microphones(self):
        try:
            import speech_recognition as sr
            print("\nAvailable microphones:")
            for index, name in enumerate(sr.Microphone.list_microphone_names()):
                print(f"  {index}: {name}")
            print()
        except Exception as e:
            logger.error(f"Error listing microphones: {e}")
    
    def continuous_listen(self, callback, stop_event=None):
        if not self.enabled:
            logger.error("Voice not enabled")
            return
        
        logger.info("Starting continuous listening mode...")
        
        while not (stop_event and stop_event.is_set()):
            try:
                text = self.listen(timeout=10)
                if text:
                    callback(text)
            except Exception as e:
                logger.error(f"Error in continuous listening: {e}")
                break
    
    def is_available(self) -> bool:
        return self.enabled and self.tts_engine is not None and self.recognizer is not None
