import logging
from pathlib import Path
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
FONTS_DIR = BASE_DIR / "static" / "fonts"

def register_fonts():
    fonts = {
        "Georgia": "georgia.ttf",
        "TimesNewRoman": "timesnewroman_bold.ttf",
        "Malgun Gothic": "malgun-gothic.ttf",
        "Tahoma": "tahoma.ttf",
        "Tahoma Bold": "tahoma_bold.ttf",
        "Roboto Semibold": "roboto_semibold.ttf",
        "Roboto Medium": "roboto_medium.ttf",
    }
    for name, file in fonts.items():
        try:
            pdfmetrics.registerFont(TTFont(name, str(FONTS_DIR / file)))
            logger.info(f"Шрифт {name} успешно зарегистрирован")
        except Exception as e:
            logger.exception(f"Не удалось зарегистрировать шрифт {name}: {e}")
            pass
