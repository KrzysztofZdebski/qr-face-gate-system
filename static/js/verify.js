const faceImageInput = document.getElementById('face_image');
const preview = document.getElementById('preview');
let html5QrCode = null;
let faceStream = null;

// QR Code Scanner
const scanQRBtn = document.getElementById('scanQRBtn');
const stopScanBtn = document.getElementById('stopScanBtn');
const qrScanner = document.getElementById('qrScanner');
const qrCodeInput = document.getElementById('qr_code_data');

scanQRBtn.addEventListener('click', function() {
    if (html5QrCode) {
        // Already scanning, stop it
        stopQRScanning();
    } else {
        startQRScanning();
    }
});

stopScanBtn.addEventListener('click', function() {
    stopQRScanning();
});

function startQRScanning() {
    html5QrCode = new Html5Qrcode("qr-reader");
    qrScanner.style.display = 'block';
    scanQRBtn.style.display = 'none';
    stopScanBtn.style.display = 'inline-block';
    
    html5QrCode.start(
        { facingMode: "environment" },
        {
            fps: 10,
            qrbox: { width: 250, height: 250 }
        },
        (decodedText, decodedResult) => {
            // QR code scanned successfully
            qrCodeInput.value = decodedText;
            stopQRScanning();
        },
        (errorMessage) => {
            // Ignore errors, keep scanning
        }
    ).catch((err) => {
        console.error("Unable to start scanning", err);
        alert("Unable to access camera. Please check permissions.");
        stopQRScanning();
    });
}

function stopQRScanning() {
    if (html5QrCode) {
        html5QrCode.stop().then(() => {
            html5QrCode.clear();
            html5QrCode = null;
            qrScanner.style.display = 'none';
            scanQRBtn.style.display = 'inline-block';
            stopScanBtn.style.display = 'none';
        }).catch((err) => {
            console.error("Error stopping scanner", err);
        });
    }
}

// Face Camera Capture
const captureFaceBtn = document.getElementById('captureFaceBtn');
const cameraPreview = document.getElementById('cameraPreview');
const faceVideo = document.getElementById('faceVideo');
const faceCanvas = document.getElementById('faceCanvas');
const captureBtn = document.getElementById('captureBtn');
const stopCameraBtn = document.getElementById('stopCameraBtn');

captureFaceBtn.addEventListener('click', function() {
    startFaceCamera();
});

stopCameraBtn.addEventListener('click', function() {
    stopFaceCamera();
});

captureBtn.addEventListener('click', function() {
    captureFacePhoto();
});

function startFaceCamera() {
    navigator.mediaDevices.getUserMedia({ 
        video: { 
            facingMode: "user",
            width: { ideal: 640 },
            height: { ideal: 480 }
        } 
    })
    .then(function(stream) {
        faceStream = stream;
        faceVideo.srcObject = stream;
        cameraPreview.style.display = 'block';
        captureFaceBtn.style.display = 'none';
    })
    .catch(function(err) {
        console.error("Error accessing camera", err);
        alert("Unable to access camera. Please check permissions.");
    });
}

function stopFaceCamera() {
    if (faceStream) {
        faceStream.getTracks().forEach(track => track.stop());
        faceStream = null;
        faceVideo.srcObject = null;
        cameraPreview.style.display = 'none';
        captureFaceBtn.style.display = 'inline-block';
    }
}

function captureFacePhoto() {
    const context = faceCanvas.getContext('2d');
    faceCanvas.width = faceVideo.videoWidth;
    faceCanvas.height = faceVideo.videoHeight;
    context.drawImage(faceVideo, 0, 0);
    console.log("kamera")
    faceCanvas.toBlob(function(blob) {
        const file = new File([blob], "captured-face.jpg", { type: "image/jpeg" });
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        faceImageInput.files = dataTransfer.files;
        
        // Trigger preview
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.innerHTML = '<h4>Preview:</h4><img src="' + e.target.result + '" alt="Preview">';
        };
        reader.readAsDataURL(file);
        
        stopFaceCamera();
    }, "image/jpeg", 0.95);
}

faceImageInput.addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.innerHTML = '<h4>Preview:</h4><img src="' + e.target.result + '" alt="Preview">';
        };
        reader.readAsDataURL(file);
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    stopQRScanning();
    stopFaceCamera();
});

document.getElementById('verifyForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = new FormData();
    formData.append('qr_code_data', document.getElementById('qr_code_data').value);
    formData.append('face_image', faceImageInput.files[0]);
    
    const errorDiv = document.getElementById('error');
    const resultDiv = document.getElementById('result');
    const resultTitle = document.getElementById('resultTitle');
    const resultMessage = document.getElementById('resultMessage');
    
    errorDiv.classList.remove('show');
    resultDiv.classList.remove('show', 'success', 'error');
    
    try {
        const response = await fetch('/verify', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            if (data.match) {
                resultDiv.classList.add('show', 'success');
                resultTitle.textContent = '✅ Access Granted!';
                resultMessage.innerHTML = `
                    <strong>User:</strong> ${data.user_name}<br>
                    <strong>User ID:</strong> ${data.user_id}<br>
                    <strong>Face Distance:</strong> ${data.face_distance.toFixed(4)}<br>
                    <strong>Match Threshold:</strong> ${data.threshold}
                `;
            } else {
                resultDiv.classList.add('show', 'error');
                resultTitle.textContent = '❌ Access Denied!';
                resultMessage.innerHTML = `
                    <strong>Face does not match the QR code owner.</strong><br>
                    <strong>Expected User:</strong> ${data.user_name}<br>
                    <strong>Face Distance:</strong> ${data.face_distance.toFixed(4)}<br>
                    <strong>Threshold:</strong> ${data.threshold} (lower is better match)
                `;
            }
        } else {
            errorDiv.textContent = data.error || 'An error occurred';
            errorDiv.classList.add('show');
        }
    } catch (error) {
        errorDiv.textContent = 'Network error: ' + error.message;
        errorDiv.classList.add('show');
    }
});