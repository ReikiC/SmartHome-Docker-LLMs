// IoT device control module

// Update action dropdown
function updateActionDropdown() {
    const deviceType = document.getElementById('device-type').value;
    const actionSelect = document.getElementById('device-action');
    
    // Clear existing options
    actionSelect.innerHTML = '';
    
    // Add options based on device type
    const options = DEVICE_ACTIONS[deviceType] || [];
    
    // Add options to dropdown
    options.forEach(opt => {
        const option = document.createElement('option');
        option.value = opt.value;
        option.textContent = opt.text;
        actionSelect.appendChild(option);
    });
}

// Send IoT control command
async function sendIoTCommand() {
    const device = document.getElementById('device-type').value;
    const action = document.getElementById('device-action').value;
    const location = document.getElementById('device-location').value;
    const outputArea = document.getElementById('iot-output');
    
    outputArea.innerHTML = `<div class="console-output">Sending command: ${device} (${location}) - ${action}...</div>`;
    
    try {
        const response = await fetch(`${API_URLS.iot}/control`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                commands: [
                    { device, action, location }
                ]
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            outputArea.innerHTML = `<div class="console-output">Command sent successfully!<br>Result: ${JSON.stringify(data, null, 2)}</div>`;
        } else {
            outputArea.innerHTML = `<div class="console-output error">Command sending failed: ${data.error || 'Unknown error'}</div>`;
        }
    } catch (error) {
        outputArea.innerHTML = `<div class="console-output error">Request error: ${error.message}</div>`;
    }
}

// Get all device status
async function getAllDevices() {
    const outputArea = document.getElementById('iot-output');
    outputArea.innerHTML = '<div class="console-output">Getting device status...</div>';
    
    try {
        const response = await fetch(`${API_URLS.iot}/devices`);
        const data = await response.json();
        
        if (response.ok) {
            outputArea.innerHTML = `<div class="console-output">Device status:<br><pre>${JSON.stringify(data, null, 2)}</pre></div>`;
        } else {
            outputArea.innerHTML = `<div class="console-output error">Failed to get device status: ${data.error || 'Unknown error'}</div>`;
        }
    } catch (error) {
        outputArea.innerHTML = `<div class="console-output error">Request error: ${error.message}</div>`;
    }
}