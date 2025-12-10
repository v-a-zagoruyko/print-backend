import base64
from io import BytesIO
from barcode import EAN13
from barcode.writer import ImageWriter

def generate_barcode(barcode: str) -> str:
    code = barcode[:12]
    buffer = BytesIO()
    writer = ImageWriter()
    writer.dpi = 300
    EAN13(code, writer=writer).write(
        buffer,
        options={
            "quiet_zone": 0,
            "write_text": True,
            "foreground": "black",
            "background": "white",
            "module_width": 0.5,
        },
    )
    return base64.b64encode(buffer.getvalue()).decode()
