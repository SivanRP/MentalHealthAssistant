document.getElementById('recordButton').addEventListener('click', function() {
    document.getElementById('voiceStatus').innerText = "Recording... Please speak.";
    
    fetch('/process_voice', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            document.getElementById('response').innerText = data.response;
            document.getElementById('voiceStatus').innerText = ""; // Clear status message
        })
        .catch(error => {
            document.getElementById('response').innerText = "Error processing voice input.";
            document.getElementById('voiceStatus').innerText = ""; // Clear status message
        });
});

document.getElementById('submitText').addEventListener('click', function() {
    const textInput = document.getElementById('textInput').value;

    if (!textInput) {
        alert("Please enter some text.");
        return;
    }

    fetch('/process_text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: textInput })
    })
        .then(response => response.json())
        .then(data => {
            document.getElementById('response').innerText = data.response;
            document.getElementById('textInput').value = ""; // Clear input field
        })
        .catch(error => {
            document.getElementById('response').innerText = "Error processing text input.";
        });
});

function updateDetectedEmotion(emotion) {
    document.getElementById('detected-emotion').textContent = emotion || 'None';
}

function updateUIForEmotion(emotion) {
    const body = document.body;
    const responseBox = document.getElementById('response');

    // Reset classes
    body.classList.remove('happy', 'sad', 'angry', 'surprised', 'neutral');
    responseBox.classList.remove('happy', 'sad', 'angry', 'surprised', 'neutral');

    // Add new class based on emotion
    body.classList.add(emotion);
    responseBox.classList.add(emotion);
}

let lastEmotion = null;

function checkEmotionAndRespond() {
    fetch('/get_current_emotion')
        .then(response => response.json())
        .then(data => {
            updateDetectedEmotion(data.emotion);
            updateUIForEmotion(data.emotion);
            
            // If emotion has changed, get a new response
            if (data.emotion !== lastEmotion && data.emotion !== 'None') {
                lastEmotion = data.emotion;
                getEmotionResponse(data.emotion);
            }
        });
}

function getEmotionResponse(emotion) {
    fetch('/process_emotion', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ emotion: emotion })
    })
        .then(response => response.json())
        .then(data => {
            document.getElementById('emotion-response').innerText = data.response;
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

// Check emotion every 5 seconds
setInterval(checkEmotionAndRespond, 5000);