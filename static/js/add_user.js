const faceImageInput = document.getElementById('face_image');
const preview = document.getElementById('preview');

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

document.getElementById('addUserForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = new FormData();
    formData.append('name', document.getElementById('name').value);
    formData.append('face_image', faceImageInput.files[0]);
    
    const errorDiv = document.getElementById('error');
    const successDiv = document.getElementById('success');
    const qrResult = document.getElementById('qrResult');
    
    errorDiv.classList.remove('show');
    successDiv.classList.remove('show');
    qrResult.classList.remove('show');
    
    try {
        const response = await fetch('/add_user', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            document.getElementById('userName').textContent = data.name;
            document.getElementById('userId').textContent = data.user_id;
            document.getElementById('qrImage').src = data.qr_code;
            qrResult.classList.add('show');
            document.getElementById('addUserForm').reset();
            preview.innerHTML = '';
        } else {
            errorDiv.textContent = data.error || 'An error occurred';
            errorDiv.classList.add('show');
        }
    } catch (error) {
        errorDiv.textContent = 'Network error: ' + error.message;
        errorDiv.classList.add('show');
    }
});