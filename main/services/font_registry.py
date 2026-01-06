import logging
from pathlib import Path
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
FONTS_DIR = BASE_DIR / "static" / "fonts"


class FontRegistry:
    _registered = False

    @classmethod
    def register_fonts(cls):
        if cls._registered:
            return

        fonts = {
            "Tahoma": "tahoma.ttf",
            "Tahoma Bold": "tahoma_bold.ttf",
        }

        for name, file in fonts.items():
            try:
                pdfmetrics.registerFont(TTFont(name, str(FONTS_DIR / file)))
            except Exception as e:
                logger.exception(f"Не удалось зарегистрировать шрифт {name}: {e}")

        cls._registered = True
