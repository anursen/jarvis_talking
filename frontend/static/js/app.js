let mediaRecorder;
let audioChunks = [];
let sessionId = null;
let isRecording = false;
let stream = null;

const talkButton = document.getElementById('talkButton');
const autoplayToggle = document.getElementById('autoplayToggle');
const status = document.getElementById('status');
const chatHistory = document.getElementById('chatHistory');

// Generate a unique browser ID if not exists
function generateBrowserId() {
    const timestamp = new Date().getTime();
    const random = Math.random().toString(36).substring(2);
    return `browser_${timestamp}_${random}`;
}

// Get or create browser session ID
function getBrowserSessionId() {
    let browserId = localStorage.getItem('jarvis_browser_id');
    if (!browserId) {
        browserId = generateBrowserId();
        localStorage.setItem('jarvis_browser_id', browserId);
    }
    return browserId;
}

// Initialize sessionId with browser-specific ID
sessionId = getBrowserSessionId();

// Function to start recording
async function startRecording() {
    try {
        if (!stream) {
            stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        }
        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };
        audioChunks = [];
        mediaRecorder.start();
        isRecording = true;
        talkButton.classList.add('recording');
        status.textContent = 'Recording...';
    } catch (err) {
        console.error('Error:', err);
        status.textContent = 'Error accessing microphone';
    }
}

// Function to stop recording
function stopRecording() {
    if (isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        talkButton.classList.remove('recording');
        status.textContent = 'Processing...';
        // Handle the recorded audio
        mediaRecorder.onstop = sendAudioToServer;
    }
}

// Add message to chat history
function addMessage(text, isUser = false) {
    const div = document.createElement('div');
    div.className = `message ${isUser ? 'user-message' : 'jarvis-message'}`;
    div.innerHTML = `<strong>${isUser ? 'You' : 'Jarvis'}:</strong> ${text}`;
    chatHistory.appendChild(div);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

// Send audio to server
async function sendAudioToServer() {
    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
    const formData = new FormData();
    formData.append('file', audioBlob);
    formData.append('session_id', sessionId);  // Always send the browser-specific session ID
    
    try {
        const response = await fetch('/chat/', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        addMessage(data.transcription, true);
        addMessage(data.response, false);
        
        const audioPlayer = document.getElementById('audioPlayer');
        audioPlayer.src = data.audio;
        
        if (autoplayToggle.checked) {
            const playPromise = audioPlayer.play();
            if (playPromise !== undefined) {
                playPromise.catch(error => {
                    console.warn("Auto-play was prevented:", error);
                    status.textContent = 'Click to hear Jarvis response';
                    audioPlayer.style.display = 'block';
                });
            }
        }
        
        status.textContent = '';
    } catch (err) {
        console.error('Error:', err);
        status.textContent = 'Error communicating with server';
    }
}

// Event Listeners
talkButton.addEventListener('mousedown', startRecording);
talkButton.addEventListener('mouseup', stopRecording);
talkButton.addEventListener('mouseleave', stopRecording);

// Touch support for mobile devices
talkButton.addEventListener('touchstart', (e) => {
    e.preventDefault();
    startRecording();
});
talkButton.addEventListener('touchend', (e) => {
    e.preventDefault();
    stopRecording();
});
