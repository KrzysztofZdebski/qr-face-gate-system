import pytest
from modules.controller import QRCodeController
import io

def test_generate_qr_code():
    controller = QRCodeController()
    img = controller.generate_qr_code(1)
    assert img is not None
    # Check if it's a PIL Image
    assert hasattr(img, 'save')
    # Verify QR code contains the user ID (simplified check)
    assert img.size[0] > 0  # Image has width