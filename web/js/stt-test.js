// STT (Speech-to-Text) Testing Module

// Global variables for STT testing
let sttMediaRecorder = null;
let sttAudioChunks = [];
let sttStream = null;

// STT Testing Functions
async function testSTTUpload() {
    const fileInput = document.getElementById('stt-file');
    const outputArea = document.getElementById('stt-output');
    
    if (!fileInput.files || fileInput.files.length === 0) {
        outputArea.innerHTML += '<div class="console-output error">Please select an audio file first</div>';
        return;
    }
    
    const file = fileInput.files[0];
    outputArea.innerHTML += `<div class="console-output">Testing STT with file: ${file.name} (${(file.size / 1024).toFixed(1)} KB)</div>`;
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const startTime = Date.now();
        const response = await fetch(`${API_URLS.stt}/upload`, {
            method: 'POST',
            body: formData
        });
        
        const endTime = Date.now();
        const responseTime = endTime - startTime;
        
        if (response.ok) {
            const data = await response.json();
            outputArea.innerHTML += `<div class="console-output success">STT Upload Success (${responseTime}ms)<br>Transcription: "${data.text}"<br>Audio path: ${data.audio_path || 'N/A'}</div>`;
        } else {
            const errorData = await response.text();
            let errorMsg;
            try {
                const jsonError = JSON.parse(errorData);
                errorMsg = jsonError.error || errorData;
            } catch (e) {
                errorMsg = errorData;
            }
            outputArea.innerHTML += `<div class="console-output error">STT Upload Failed (${responseTime}ms)<br>Error: ${errorMsg}</div>`;
        }
    } catch (error) {
        outputArea.innerHTML += `<div class="console-output error">STT Upload Error: ${error.message}</div>`;
    }
}

async function testSTTRecord() {
    const outputArea = document.getElementById('stt-output');
    const recordingControls = document.getElementById('stt-recording-controls');
    
    try {
        // Check browser support
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            outputArea.innerHTML += '<div class="console-output error">Browser does not support audio recording</div>';
            return;
        }
        
        // Request microphone access
        sttStream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                sampleRate: 16000,
                channelCount: 1,
                echoCancellation: true,
                noiseSuppression: true
            }
        });
        
        outputArea.innerHTML += '<div class="console-output">Starting STT recording test... Speak now!</div>';
        recordingControls.style.display = 'block';
        
        // Initialize MediaRecorder
        sttMediaRecorder = new MediaRecorder(sttStream, {
            mimeType: 'audio/webm;codecs=opus'
        });
        sttAudioChunks = [];
        
        sttMediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                sttAudioChunks.push(event.data);
            }
        };
        
        sttMediaRecorder.onstop = async () => {
            recordingControls.style.display = 'none';
            outputArea.innerHTML += '<div class="console-output">Recording stopped. Processing audio...</div>';
            
            const audioBlob = new Blob(sttAudioChunks, { type: 'audio/webm' });
            outputArea.innerHTML += `<div class="console-output">Recorded audio size: ${(audioBlob.size / 1024).toFixed(1)} KB</div>`;
            
            await testSTTWithBlob(audioBlob, 'recording.webm');
            
            // Stop all tracks
            sttStream.getTracks().forEach(track => track.stop());
            sttStream = null;
        };
        
        sttMediaRecorder.onerror = (event) => {
            outputArea.innerHTML += `<div class="console-output error">Recording error: ${event.error}</div>`;
            recordingControls.style.display = 'none';
        };
        
        // Start recording
        sttMediaRecorder.start(1000); // Collect data every second
        
        // Auto-stop after 10 seconds
        setTimeout(() => {
            if (sttMediaRecorder && sttMediaRecorder.state === 'recording') {
                stopSTTRecording();
            }
        }, 10000);
        
    } catch (error) {
        outputArea.innerHTML += `<div class="console-output error">STT Recording Error: ${error.message}</div>`;
        recordingControls.style.display = 'none';
        if (sttStream) {
            sttStream.getTracks().forEach(track => track.stop());
            sttStream = null;
        }
    }
}

function stopSTTRecording() {
    if (sttMediaRecorder && sttMediaRecorder.state === 'recording') {
        sttMediaRecorder.stop();
    }
}

async function testSTTWithBlob(audioBlob, filename = 'test-audio') {
    const outputArea = document.getElementById('stt-output');
    
    try {
        const formData = new FormData();
        formData.append('file', audioBlob, filename);
        
        const startTime = Date.now();
        const response = await fetch(`${API_URLS.stt}/upload`, {
            method: 'POST',
            body: formData
        });
        
        const endTime = Date.now();
        const responseTime = endTime - startTime;
        
        if (response.ok) {
            const data = await response.json();
            const transcription = data.text || 'No transcription returned';
            outputArea.innerHTML += `<div class="console-output success">STT Processing Success (${responseTime}ms)<br>Transcription: "${transcription}"<br>Audio size: ${(audioBlob.size / 1024).toFixed(1)} KB</div>`;
            
            // If we got a meaningful transcription, test it with the coordinator
            if (transcription.trim() && transcription.length > 3) {
                outputArea.innerHTML += '<div class="console-output">Testing transcription with AI coordinator...</div>';
                await testTranscriptionWithCoordinator(transcription);
            }
        } else {
            const errorText = await response.text();
            let errorMsg;
            try {
                const jsonError = JSON.parse(errorText);
                errorMsg = jsonError.error || errorText;
            } catch (e) {
                errorMsg = errorText;
            }
            outputArea.innerHTML += `<div class="console-output error">STT Processing Failed (${responseTime}ms)<br>Status: ${response.status}<br>Error: ${errorMsg}</div>`;
        }
    } catch (error) {
        outputArea.innerHTML += `<div class="console-output error">STT Processing Error: ${error.message}</div>`;
    }
}

async function testTranscriptionWithCoordinator(text) {
    const outputArea = document.getElementById('stt-output');
    
    try {
        const response = await fetch(`${API_URLS.coordinator}/process_text`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text })
        });
        
        if (response.ok) {
            const data = await response.json();
            outputArea.innerHTML += `<div class="console-output success">Coordinator processed transcription successfully<br>AI Response: "${data.ai_response}"<br>IoT Commands: ${data.iot_commands ? data.iot_commands.length : 0}</div>`;
        } else {
            const errorData = await response.json();
            outputArea.innerHTML += `<div class="console-output warning">Coordinator processing failed: ${errorData.error || 'Unknown error'}</div>`;
        }
    } catch (error) {
        outputArea.innerHTML += `<div class="console-output warning">Could not test with coordinator: ${error.message}</div>`;
    }
}

async function testSTTHealth() {
    const outputArea = document.getElementById('stt-output');
    outputArea.innerHTML += '<div class="console-output">Checking STT service health...</div>';
    
    try {
        // Test basic connectivity
        const healthResponse = await fetch(`${API_URLS.stt}/`, {
            headers: { 'Accept': '*/*' }
        });
        const healthText = await healthResponse.text();
        
        let healthData;
        try {
            healthData = JSON.parse(healthText);
        } catch (e) {
            healthData = { message: healthText, status: 'text_response' };
        }
        
        outputArea.innerHTML += `<div class="console-output ${healthResponse.ok ? 'success' : 'error'}">STT Health Check: ${healthResponse.ok ? 'OK' : 'Failed'}<br>Status: ${healthResponse.status}<br>Response: ${JSON.stringify(healthData, null, 2)}</div>`;
        
        if (healthResponse.ok) {
            // Test upload endpoint availability
            outputArea.innerHTML += '<div class="console-output">Testing STT upload endpoint...</div>';
            
            const testFormData = new FormData();
            const dummyBlob = new Blob(['dummy audio data'], { type: 'audio/wav' });
            testFormData.append('file', dummyBlob, 'test.wav');
            
            const uploadResponse = await fetch(`${API_URLS.stt}/upload`, {
                method: 'POST',
                body: testFormData
            });
            
            if (uploadResponse.status === 400 || uploadResponse.status === 422) {
                outputArea.innerHTML += '<div class="console-output success">STT upload endpoint is responding (expected error for dummy data)</div>';
            } else if (uploadResponse.ok) {
                outputArea.innerHTML += '<div class="console-output success">STT upload endpoint is fully functional</div>';
            } else {
                outputArea.innerHTML += `<div class="console-output warning">STT upload endpoint returned: ${uploadResponse.status}</div>`;
            }
        }
        
    } catch (error) {
        outputArea.innerHTML += `<div class="console-output error">STT Health Check Failed: ${error.message}</div>`;
    }
}

async function testSTTWithSample() {
    const outputArea = document.getElementById('stt-output');
    outputArea.innerHTML += '<div class="console-output">Testing STT with generated sample audio...</div>';
    
    try {
        // Generate a simple audio tone for testing
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const duration = 2; // seconds
        const sampleRate = 16000; // Whisper prefers 16kHz
        const numSamples = duration * sampleRate;
        
        const audioBuffer = audioContext.createBuffer(1, numSamples, sampleRate);
        const channelData = audioBuffer.getChannelData(0);
        
        // Generate a more complex waveform (multiple tones)
        for (let i = 0; i < numSamples; i++) {
            const t = i / sampleRate;
            // Combine multiple frequencies to create a more realistic audio signal
            channelData[i] = (
                Math.sin(2 * Math.PI * 440 * t) * 0.3 +  // A4
                Math.sin(2 * Math.PI * 554 * t) * 0.2 +  // C#5
                Math.sin(2 * Math.PI * 659 * t) * 0.1    // E5
            );
        }
        
        // Convert to WAV blob
        const wavBlob = audioBufferToWav(audioBuffer);
        outputArea.innerHTML += `<div class="console-output">Generated sample audio: ${(wavBlob.size / 1024).toFixed(1)} KB, ${duration}s duration</div>`;
        
        // Test with generated audio
        await testSTTWithBlob(wavBlob, 'sample-tone.wav');
        
    } catch (error) {
        outputArea.innerHTML += `<div class="console-output error">Sample audio generation failed: ${error.message}</div>`;
    }
}

// Helper function to convert AudioBuffer to WAV
function audioBufferToWav(buffer) {
    const length = buffer.length;
    const arrayBuffer = new ArrayBuffer(44 + length * 2);
    const view = new DataView(arrayBuffer);
    const channels = buffer.numberOfChannels;
    const sampleRate = buffer.sampleRate;
    
    // WAV header
    const writeString = (offset, string) => {
        for (let i = 0; i < string.length; i++) {
            view.setUint8(offset + i, string.charCodeAt(i));
        }
    };
    
    writeString(0, 'RIFF');
    view.setUint32(4, 36 + length * 2, true);
    writeString(8, 'WAVE');
    writeString(12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, channels, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    writeString(36, 'data');
    view.setUint32(40, length * 2, true);
    
    // Convert float samples to 16-bit PCM
    const channelData = buffer.getChannelData(0);
    let offset = 44;
    for (let i = 0; i < length; i++) {
        const sample = Math.max(-1, Math.min(1, channelData[i]));
        view.setInt16(offset, sample * 0x7FFF, true);
        offset += 2;
    }
    
    return new Blob([arrayBuffer], { type: 'audio/wav' });
}

// STT Performance test
async function performSTTPerformanceTest() {
    const outputArea = document.getElementById('stt-output');
    outputArea.innerHTML += '<div class="console-output">Starting STT performance test...</div>';
    
    const testSizes = [1, 2, 5]; // seconds
    const results = [];
    
    for (const duration of testSizes) {
        try {
            outputArea.innerHTML += `<div class="console-output">Testing ${duration}s audio...</div>`;
            
            // Generate audio of specified duration
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const sampleRate = 16000;
            const numSamples = duration * sampleRate;
            
            const audioBuffer = audioContext.createBuffer(1, numSamples, sampleRate);
            const channelData = audioBuffer.getChannelData(0);
            
            // Generate test audio
            for (let i = 0; i < numSamples; i++) {
                const t = i / sampleRate;
                channelData[i] = Math.sin(2 * Math.PI * 440 * t) * 0.3;
            }
            
            const wavBlob = audioBufferToWav(audioBuffer);
            
            // Test STT processing time
            const startTime = Date.now();
            const formData = new FormData();
            formData.append('file', wavBlob, `test-${duration}s.wav`);
            
            const response = await fetch(`${API_URLS.stt}/upload`, {
                method: 'POST',
                body: formData
            });
            
            const endTime = Date.now();
            const processingTime = endTime - startTime;
            
            results.push({
                duration: duration,
                fileSize: (wavBlob.size / 1024).toFixed(1),
                processingTime: processingTime,
                success: response.ok
            });
            
            if (response.ok) {
                const data = await response.json();
                outputArea.innerHTML += `<div class="console-output success">${duration}s test: ${processingTime}ms processing time</div>`;
            } else {
                outputArea.innerHTML += `<div class="console-output error">${duration}s test failed: ${response.status}</div>`;
            }
            
            // Small delay between tests
            await new Promise(resolve => setTimeout(resolve, 1000));
            
        } catch (error) {
            outputArea.innerHTML += `<div class="console-output error">${duration}s test error: ${error.message}</div>`;
            results.push({
                duration: duration,
                error: error.message
            });
        }
    }
    
    // Display summary
    outputArea.innerHTML += '<div class="console-output"><strong>STT Performance Test Summary:</strong><br>';
    results.forEach(result => {
        if (result.error) {
            outputArea.innerHTML += `${result.duration}s: ERROR - ${result.error}<br>`;
        } else {
            const efficiency = result.success ? (result.duration * 1000 / result.processingTime).toFixed(2) : 'N/A';
            outputArea.innerHTML += `${result.duration}s audio (${result.fileSize}KB): ${result.processingTime}ms processing (${efficiency}x realtime)<br>`;
        }
    });
    outputArea.innerHTML += '</div>';
}

// STT debugging utilities
function debugSTTService() {
    const outputArea = document.getElementById('stt-output');
    outputArea.innerHTML += '<div class="console-output">Starting STT service debug...</div>';
    
    // Test multiple endpoints
    const endpoints = [
        { path: '/', method: 'GET', description: 'Health check' },
        { path: '/transcribe', method: 'POST', description: 'Transcribe endpoint' },
        { path: '/upload', method: 'POST', description: 'Upload endpoint' }
    ];
    
    endpoints.forEach(async (endpoint, index) => {
        setTimeout(async () => {
            try {
                outputArea.innerHTML += `<div class="console-output">Testing ${endpoint.description} (${endpoint.method} ${endpoint.path})...</div>`;
                
                let fetchOptions = { method: endpoint.method };
                
                if (endpoint.method === 'POST') {
                    // Create minimal test payload
                    const formData = new FormData();
                    const testBlob = new Blob(['test'], { type: 'audio/wav' });
                    formData.append('file', testBlob, 'test.wav');
                    fetchOptions.body = formData;
                }
                
                const response = await fetch(`${API_URLS.stt}${endpoint.path}`, fetchOptions);
                const responseText = await response.text();
                
                outputArea.innerHTML += `<div class="console-output">
                    ${endpoint.description}: Status ${response.status}<br>
                    Headers: ${JSON.stringify(Object.fromEntries(response.headers.entries()), null, 2)}<br>
                    Response: ${responseText.substring(0, 50000)}${responseText.length > 50000 ? '...' : ''}
                </div>`;
                
            } catch (error) {
                outputArea.innerHTML += `<div class="console-output error">${endpoint.description} failed: ${error.message}</div>`;
            }
        }, index * 1000);
    });
}

// Export functions for console use
if (typeof window !== 'undefined') {
    window.testSTTUpload = testSTTUpload;
    window.testSTTRecord = testSTTRecord;
    window.stopSTTRecording = stopSTTRecording;
    window.testSTTHealth = testSTTHealth;
    window.testSTTWithSample = testSTTWithSample;
    window.performSTTPerformanceTest = performSTTPerformanceTest;
    window.debugSTTService = debugSTTService;
    window.testSTTWithBlob = testSTTWithBlob;
}