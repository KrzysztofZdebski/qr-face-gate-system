document.addEventListener('DOMContentLoaded', function() {
    const faceImageInput = document.getElementById('face_image');
    const preview = document.getElementById('preview');

    if (faceImageInput) {
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
    }

    const form = document.getElementById('addUserForm');
    if (!form) return;

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        const formData = new FormData();
        formData.append('name', document.getElementById('name').value);
        const fileInput = document.getElementById('face_image');
        if (fileInput && fileInput.files[0]) {
            formData.append('face_image', fileInput.files[0]);
        }

        const errorDiv = document.getElementById('error');
        const successDiv = document.getElementById('success');
        const qrResult = document.getElementById('qrResult');

        if (errorDiv) errorDiv.classList.remove('show');
        if (successDiv) successDiv.classList.remove('show');
        if (qrResult) qrResult.classList.remove('show');

        try {
            const response = await fetch('/add_user', {
                method: 'POST',
                body: formData
            });

            const data = await response.json().catch(() => null);

            if (response.ok && data) {
                document.getElementById('userName').textContent = data.name;
                document.getElementById('userId').textContent = data.user_id;
                document.getElementById('qrImage').src = data.qr_code;
                qrResult.classList.add('show');
                form.reset();
                if (preview) preview.innerHTML = '';
            } else {
                const msg = (data && data.error) ? data.error : 'An error occurred';
                if (errorDiv) { errorDiv.textContent = msg; errorDiv.classList.add('show'); }
            }
        } catch (error) {
            if (errorDiv) { errorDiv.textContent = 'Network error: ' + error.message; errorDiv.classList.add('show'); }
        }
    });
    // Expose print function for the button in the template
    window.printQRCode = function() {
        const qrImage = document.getElementById('qrImage');
        const userName = document.getElementById('userName').textContent;
        const userId = document.getElementById('userId').textContent;

        if (!qrImage || !qrImage.src) return alert('No QR code available to print');

        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <html>
            <head>
                <title>QR Code - ${userName}</title>
                <style>
                    body { font-family: Arial, sans-serif; text-align: center; padding: 20px; }
                    .qr-container { margin: 20px auto; }
                    .qr-container img { max-width: 300px; }
                    .info { margin-top: 20px; }
                </style>
            </head>
            <body>
                <h1>QR Code for Access</h1>
                <div class="qr-container">
                    <img src="${qrImage.src}" alt="QR Code">
                </div>
                <div class="info">
                    <p><strong>Name:</strong> ${userName}</p>
                    <p><strong>User ID:</strong> ${userId}</p>
                </div>
            </body>
            </html>
        `);
        printWindow.document.close();
        printWindow.print();
    };
});