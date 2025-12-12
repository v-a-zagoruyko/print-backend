import logging
from pathlib import Path
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
FONTS_DIR = BASE_DIR / "static" / "fonts"

def register_fonts():
    fonts = {
        "Tahoma": "tahoma.ttf",
        "Tahoma Bold": "tahoma_bold.ttf",
        "DejaVu Sans": "dejavu_sans.ttf",
        "DejaVu Sans Bold": "dejavu_sans_bold.ttf",
    }
    for name, file in fonts.items():
        try:
            pdfmetrics.registerFont(TTFont(name, str(FONTS_DIR / file)))
            logger.info(f"Шрифт {name} успешно зарегистрирован")
        except Exception as e:
            logger.exception(f"Не удалось зарегистрировать шрифт {name}: {e}")
            pass
