import qrcode

def create_upi_qr_code(upi_id, name, amount=None, note=None, output_file="upi_qr.png"):
    # Define UPI QR string format
    upi_string = f"upi://pay?pa={upi_id}&pn={name}"
    if amount:
        upi_string += f"&am={amount}"
    if note:
        upi_string += f"&tn={note}"

    # Generate the QR Code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(upi_string)
    qr.make(fit=True)

    # Save as image
    img = qr.make_image(fill="black", back_color="white")
    img.save(output_file)
    print(f"QR Code saved as {output_file}")

# Example usage
create_upi_qr_code(
    upi_id="jkaruppaswamy-1@okhdfcbank",  # Replace with your UPI ID
    name="Jothikumar karuppaswamy",
    amount="100.00",
    note="E-commerce Purchase"
)
