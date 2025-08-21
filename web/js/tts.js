// Text-to-speech module

// Synthesize speech
async function synthesizeSpeech() {
    const text = document.getElementById('tts-text').value.trim();
    const voice = document.getElementById('tts-voice').value;
    const outputArea = document.getElementById('tts-output');
    
    if (!text) {
        outputArea.innerHTML = '<div class="console-output error">Please enter text to synthesize</div>';
        return;
    }
    
    outputArea.innerHTML = '<div class="console-output">Synthesizing speech...</div>';
    
    try {
        const response = await fetch(`${API_URLS.tts}/synthesize`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text,
                voice,
                format: 'mp3'
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Create complete audio URL
            const audioServer = API_URLS.tts;
            const audioFilename = data.audio_path.split('/').pop();
            const audioUrl = `${audioServer}/audio/${audioFilename}`;
            
            outputArea.innerHTML = `
                <div class="console-output success">
                    Speech synthesis successful!<br>
                    Voice: ${data.voice}<br>
                    Format: ${data.format}<br>
                    <audio controls src="${audioUrl}" style="width:100%; margin-top:10px;"></audio>
                </div>`;
        } else {
            outputArea.innerHTML = `<div class="console-output error">Speech synthesis failed: ${data.error || 'Unknown error'}</div>`;
        }
    } catch (error) {
        outputArea.innerHTML = `<div class="console-output error">Request error: ${error.message}</div>`;
    }
}

// Get available voices
async function getAvailableVoices() {
    const outputArea = document.getElementById('tts-output');
    outputArea.innerHTML = '<div class="console-output">Getting available voices list...</div>';
    
    try {
        const response = await fetch(`${API_URLS.tts}/voices`);
        const data = await response.json();
        
        if (response.ok && data.voices) {
            let output = '<div class="console-output"><strong>Available voices:</strong><br>';
            
            // Filter English voices
            const englishVoices = data.voices.filter(voice => voice.Name.startsWith('en-'));
            
            if (englishVoices.length > 0) {
                englishVoices.forEach((voice, index) => {
                    output += `${index + 1}. <span class="success">${voice.Name}</span> - ${voice.Gender || 'Unknown gender'}<br>`;
                });
            } else {
                output += 'No English voices found<br>';
                
                // Show first 10 voices
                data.voices.slice(0, 10).forEach((voice, index) => {
                    output += `${index + 1}. ${voice.Name} - ${voice.Gender || 'Unknown gender'}<br>`;
                });
            }
            
            output += '</div>';
            outputArea.innerHTML = output;
        } else {
            outputArea.innerHTML = `<div class="console-output error">Failed to get voice list: ${data.error || 'Unknown error'}</div>`;
        }
    } catch (error) {
        outputArea.innerHTML = `<div class="console-output error">Request error: ${error.message}</div>`;
    }
}