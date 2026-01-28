import qrcode

class QRCodeController:
    def generate_qr_code(self, data):
        """Generate a QR code for arbitrary payload (e.g. user QR token)"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(str(data))
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        return img
