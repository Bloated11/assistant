let recognition;
let synthesis = window.speechSynthesis;
let isListening = false;
let isSpeaking = false;

function initVoice() {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';
        
        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript.toLowerCase();
            console.log('Voice command:', transcript);
            handleVoiceCommand(transcript);
        };
        
        recognition.onerror = function(event) {
            console.error('Speech recognition error:', event.error);
            stopVoiceRecognition();
        };
        
        recognition.onend = function() {
            if (isListening) {
                recognition.start();
            }
        };
    } else {
        // console.warn('Speech recognition not supported');
    }
}

function startVoiceRecognition() {
    if (recognition && !isListening) {
        isListening = true;
        recognition.start();
        console.log('Voice recognition started');
    }
}

function stopVoiceRecognition() {
    if (recognition && isListening) {
        isListening = false;
        recognition.stop();
        console.log('Voice recognition stopped');
        
        const voiceBtn = document.getElementById('voiceButton');
        if (voiceBtn) {
            voiceBtn.classList.remove('active');
        }
    }
}

function speakText(text) {
    if (synthesis) {
        synthesis.cancel();
        
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        utterance.volume = 1.0;
        
        utterance.onstart = function() {
            isSpeaking = true;
            startLipSync();
        };
        
        utterance.onend = function() {
            isSpeaking = false;
            stopLipSync();
        };
        
        synthesis.speak(utterance);
    }
}

function startLipSync() {
    const avatar = document.getElementById('avatarCore');
    if (avatar) {
        avatar.style.animation = 'avatarPulse 0.2s ease-in-out infinite';
        updateAvatarPulse(0.8);
    }
}

function stopLipSync() {
    const avatar = document.getElementById('avatarCore');
    if (avatar) {
        avatar.style.animation = 'avatarPulse 3s ease-in-out infinite';
        updateAvatarPulse(0);
    }
}

function handleVoiceCommand(command) {
    if (command.includes('dashboard') || command.includes('home')) {
        speakText('Opening dashboard');
        setTimeout(() => window.location.href = '/', 500);
    }
    else if (command.includes('ai') || command.includes('assistant')) {
        speakText('Opening AI assistant');
        setTimeout(() => window.location.href = '/ai', 500);
    }
    else if (command.includes('task')) {
        speakText('Opening tasks');
        setTimeout(() => window.location.href = '/tasks', 500);
    }
    else if (command.includes('project')) {
        speakText('Opening projects');
        setTimeout(() => window.location.href = '/projects', 500);
    }
    else if (command.includes('note')) {
        speakText('Opening notes');
        setTimeout(() => window.location.href = '/notes', 500);
    }
    else if (command.includes('goal')) {
        speakText('Opening goals');
        setTimeout(() => window.location.href = '/goals', 500);
    }
    else if (command.includes('habit')) {
        speakText('Opening habits');
        setTimeout(() => window.location.href = '/habits', 500);
    }
    else if (command.includes('health')) {
        speakText('Opening health tracker');
        setTimeout(() => window.location.href = '/health', 500);
    }
    else if (command.includes('finance') || command.includes('money')) {
        speakText('Opening finance manager');
        setTimeout(() => window.location.href = '/finance', 500);
    }
    else if (command.includes('meal') || command.includes('food')) {
        speakText('Opening meal planner');
        setTimeout(() => window.location.href = '/meals', 500);
    }
    else if (command.includes('read')) {
        speakText('Opening reading list');
        setTimeout(() => window.location.href = '/reading', 500);
    }
    else if (command.includes('learn')) {
        speakText('Opening learning tracker');
        setTimeout(() => window.location.href = '/learning', 500);
    }
    else if (command.includes('time')) {
        speakText('Opening time tracker');
        setTimeout(() => window.location.href = '/time', 500);
    }
    else if (command.includes('journal')) {
        speakText('Opening journal');
        setTimeout(() => window.location.href = '/journal', 500);
    }
    else if (command.includes('contact')) {
        speakText('Opening contacts');
        setTimeout(() => window.location.href = '/contacts', 500);
    }
    else if (command.includes('travel')) {
        speakText('Opening travel planner');
        setTimeout(() => window.location.href = '/travel', 500);
    }
    else if (command.includes('remind')) {
        speakText('Opening reminders');
        setTimeout(() => window.location.href = '/reminders', 500);
    }
    else if (command.includes('idea')) {
        speakText('Opening idea vault');
        setTimeout(() => window.location.href = '/ideas', 500);
    }
    else if (command.includes('inventory')) {
        speakText('Opening inventory');
        setTimeout(() => window.location.href = '/inventory', 500);
    }
    else if (command.includes('quote')) {
        speakText('Opening quotes');
        setTimeout(() => window.location.href = '/quotes', 500);
    }
    else if (command.includes('event')) {
        speakText('Opening events');
        setTimeout(() => window.location.href = '/events', 500);
    }
    else if (command.includes('archive')) {
        speakText('Opening archive');
        setTimeout(() => window.location.href = '/archive', 500);
    }
    else if (command.includes('show data') || command.includes('data mode')) {
        speakText('Data visualization activated');
        setHologramMode('data');
    }
    else if (command.includes('show network') || command.includes('network mode')) {
        speakText('Network visualization activated');
        setHologramMode('network');
    }
    else if (command.includes('idle') || command.includes('reset')) {
        speakText('Returning to idle mode');
        setHologramMode('idle');
    }
    else if (command.includes('help') || command.includes('what can you do')) {
        speakText('I can help you navigate to different modules, display data visualizations, and respond to voice commands. Try saying open dashboard, show data, or show network.');
    }
    else if (command.includes('hello') || command.includes('hi')) {
        speakText('Hello. How may I assist you?');
        updateAvatarPulse(0.5);
        setTimeout(() => updateAvatarPulse(0), 1000);
    }
    else {
        speakText('Command not recognized. Say help to hear available commands.');
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initVoice);
} else {
    initVoice();
}
