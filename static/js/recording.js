/**
 * Audio Recording Module
 * Handles microphone recording and audio upload
 */

// Recording state
let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let isProcessing = false;

// DOM elements
const recordButton = document.getElementById('recordButton');
const buttonText = document.getElementById('buttonText');
const statusText = document.getElementById('statusText');
const reportSection = document.getElementById('reportSection');

// ========== RECORDING FUNCTIONS ==========
async function toggleRecording() {
    if (isProcessing) return;

    if (!isRecording) {
        await startRecording();
    } else {
        await stopRecording();
    }
}

async function startRecording() {
    try {
        // Request microphone access
        const stream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                channelCount: 1,
                sampleRate: 16000
            } 
        });
        
        // Create MediaRecorder - browser records audio locally
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
        
        // Collect audio data chunks
        mediaRecorder.addEventListener("dataavailable", event => {
            audioChunks.push(event.data);
        });
        
        // Start recording in browser
        mediaRecorder.start();
        isRecording = true;
        
        recordButton.className = 'record-button recording';
        buttonText.textContent = 'Stop Recording';
        statusText.textContent = '🔴 Recording in progress... Click to stop';
        reportSection.style.display = 'none';

        console.log('🎙️  Recording started in browser');

    } catch (error) {
        showError('Microphone access denied: ' + error.message);
        console.error('Microphone error:', error);
    }
}

async function stopRecording() {
    return new Promise((resolve) => {
        mediaRecorder.addEventListener("stop", async () => {
            // Stop all audio tracks
            mediaRecorder.stream.getTracks().forEach(track => track.stop());
            
            // Convert collected chunks to audio blob
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            
            console.log('🎵 Audio recorded:', audioBlob.size, 'bytes');
            
            // Upload to server for processing
            await uploadAudio(audioBlob);
            resolve();
        });
        
        mediaRecorder.stop();
    });
}

async function uploadAudio(audioBlob) {
    try {
        isRecording = false;
        isProcessing = true;
        recordButton.className = 'record-button processing';
        buttonText.innerHTML = '<div class="loader"></div>';
        statusText.textContent = '⏳ Uploading and processing...';

        // Create form data with audio file
        const formData = new FormData();
        formData.append('audio_file', audioBlob, 'recording.wav');
        formData.append('session_id', SESSION_ID);

        console.log('📤 Uploading audio to server...');

        // Upload to server
        const response = await fetch('/api/upload-audio', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to process recording');
        }

        const data = await response.json();
        console.log('✅ Processing completed');
        displayReport(data);

        // Reset button
        recordButton.className = 'record-button idle';
        buttonText.textContent = 'Start Recording';
        statusText.textContent = '✅ Report generated successfully!';

    } catch (error) {
        showError('Failed to process recording: ' + error.message);
        recordButton.className = 'record-button idle';
        buttonText.textContent = 'Start Recording';
        statusText.textContent = 'Click the button to begin';
        console.error('Processing error:', error);
    } finally {
        isProcessing = false;
    }
}

function showError(message) {
    const errorHtml = `<div class="error-message">${message}</div>`;
    if (reportSection) {
        reportSection.innerHTML = errorHtml;
        reportSection.style.display = 'block';
    }
}

