import logging
import base64
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Optional
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from pdf2image import convert_from_bytes
from barcode import EAN13
from barcode.writer import ImageWriter
from main.models import Template
from api.utils.styles import STYLES

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
IMAGES_DIR = BASE_DIR / "static" / "img"

class LabelService:
    def __init__(self):
        pass

    @staticmethod
    def mm_to_pt(mm: float) -> float:
        return float(mm) * 2.834645669

    def draw_debug(self, c: canvas.Canvas, spec: Dict[str, Any] = {}):
        page_w, page_h = c._pagesize
        c.rect(
            self.mm_to_pt(spec.get("x")),
            page_h - self.mm_to_pt(spec.get("y")) - self.mm_to_pt(spec.get("height")),
            self.mm_to_pt(spec.get("width")),
            self.mm_to_pt(spec.get("height")),
            stroke=1,
            fill=0,
        )

    def _draw_barcode(self, c: canvas.Canvas, barcode: str = "0000000000000", spec: Dict[str, Any] = {}):
        from reportlab.graphics.barcode import eanbc
        from reportlab.graphics.shapes import Drawing
        from reportlab.graphics import renderPDF

        scale = 0.75
        x = self.mm_to_pt(spec.get("x"))
        y = self.mm_to_pt(spec.get("y"))
        w = self.mm_to_pt(spec.get("width"))
        h = self.mm_to_pt(spec.get("height"))

        widget = eanbc.Ean13BarcodeWidget(barcode, barWidth=w / 95, barHeight=h)

        drawing = Drawing(w * scale, h * scale, transform=[scale, 0, 0, scale, 0, 0])
        drawing.add(widget)
        page_h = c._pagesize[1]
        renderPDF.draw(drawing, c, x, page_h - y - h)

    def draw_barcode(self, c: canvas.Canvas, barcode: str = "0000000000000", spec: Dict[str, Any] = {}):
        img_bytes = self._get_barcode_bytes(barcode)
        img = ImageReader(BytesIO(img_bytes))
        c.drawImage(
            img,
            self.mm_to_pt(spec.get("x")),
            c._pagesize[1] - self.mm_to_pt(spec.get("y")) - self.mm_to_pt(spec.get("height")),
            width=self.mm_to_pt(spec.get("width")),
            height=self.mm_to_pt(spec.get("height")),
            preserveAspectRatio=True,
            mask="auto",
        )

    def draw_img(self, c: canvas.Canvas, spec: Dict[str, Any] = {}):
        filename = spec.get("filename")
        img_bytes = self._get_img_bytes(filename)
        img = ImageReader(BytesIO(img_bytes))
        c.drawImage(
            img,
            self.mm_to_pt(spec.get("x")),
            c._pagesize[1] - self.mm_to_pt(spec.get("y")) - self.mm_to_pt(spec.get("height")),
            width=self.mm_to_pt(spec.get("width")),
            height=self.mm_to_pt(spec.get("height")),
            preserveAspectRatio=True,
            mask="auto",
        )

    def draw_text(
        self,
        c: canvas.Canvas,
        text: str = "Текст не заполнен",
        spec: Dict[str, Any] = {},
        override_styles: Dict[str, Any] = {}
    ):
        style_name = spec.get("style", "product__body_1")
        style_obj = self._build_style(style_name, override_styles)
        options = spec.get("options", {})
        p = Paragraph(text, style_obj)
        page_h = c._pagesize[1]
        textbox_w = self.mm_to_pt(spec.get("width"))
        textbox_h = self.mm_to_pt(spec.get("height"))
        w_wrap, h_wrap = p.wrap(textbox_w, textbox_h)

        if h_wrap > textbox_h:
            raw_styles = STYLES.get(style_name, STYLES["product__body_1"])
            base_fontsize = raw_styles.get("fontSize")
            current_fontsize = override_styles.get("fontSize", None) or base_fontsize
            min_fontsize = options.get("min_fontsize", None)
            logger.info(f"Text does not fit the textbox; reduce font or enlarge box:\r\n{text}")

            if min_fontsize and min_fontsize < current_fontsize:
                self.draw_text(
                    c,
                    text,
                    spec,
                    {
                        **override_styles,
                        "fontSize": current_fontsize - 0.5,
                        "leading": current_fontsize - 0.5
                    }
                )
                return

        x_pt = self.mm_to_pt(spec.get("x"))
        y_pt = page_h - self.mm_to_pt(spec.get("y")) - h_wrap
        p.drawOn(c, x_pt, y_pt)

    def draw_text_beta(self, c: canvas.Canvas, text: str, spec: dict, override_styles: dict = {}):
        style_name = spec.get("style", "product__body_1")
        options = spec.get("options", {})
        raw_styles = STYLES.get(style_name, STYLES["product__body_1"])
        base_fontsize = raw_styles.get("fontSize")
        current_fontsize = override_styles.get("fontSize", base_fontsize)
        min_fontsize = options.get("min_fontsize", None)
        textbox_w = self.mm_to_pt(spec.get("width"))
        textbox_h = self.mm_to_pt(spec.get("height"))
        max_height_probe = textbox_h * 100
        last_fit_height = None

        while True:
            style_obj = self._build_style(style_name, {**override_styles, "fontSize": current_fontsize, "leading": override_styles.get("leading", current_fontsize)})
            p = Paragraph(text, style_obj)
            w_wrap, h_wrap = p.wrap(textbox_w, max_height_probe)
            last_fit_height = h_wrap
            if h_wrap <= textbox_h:
                mode = "overflow"
                break
            if min_fontsize and current_fontsize > min_fontsize:
                current_fontsize -= 1
                continue
            else:
                mode = "overflow"
                break

        page_h = c._pagesize[1]
        x_pt = self.mm_to_pt(spec.get("x"))
        y_pt = page_h - self.mm_to_pt(spec.get("y")) - textbox_h
        frame = Frame(
            x_pt,
            y_pt,
            textbox_w,
            textbox_h,
            leftPadding=0,
            bottomPadding=0,
            rightPadding=0,
            topPadding=0,
            showBoundary=1
        )
        kif = KeepInFrame(textbox_w, textbox_h, [p], mode=mode, vAlign="MIDDLE", hAlign="LEFT")
        frame.addFromList([kif], c)

    def _build_style(self, style_name: str, override: Dict[str, Any] = {}) -> ParagraphStyle:
        raw = STYLES.get(style_name, STYLES["product__body_1"])
        merged = {**raw, **(override or {})}
        return ParagraphStyle(style_name, **merged)

    def _get_barcode_bytes(self, barcode: str) -> str:
        code = str(barcode)[:12]
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
        return buffer.getvalue()

    def _get_img_bytes(self, filename: str) -> str:
        path = (IMAGES_DIR / filename).resolve()
        with open(str(path), "rb") as f:
            data = f.read()
        return data

    def _create_canvas(self, page_w_mm: float, page_h_mm: float):
        page_w = self.mm_to_pt(page_w_mm)
        page_h = self.mm_to_pt(page_h_mm)
        buf = BytesIO()
        c = canvas.Canvas(buf, pagesize=(page_w, page_h))
        return c, buf

    def _finalize_pdf(self, c: canvas.Canvas, buf: BytesIO) -> bytes:
        c.showPage()
        c.save()
        pdf_bytes = buf.getvalue()
        buf.close()
        return pdf_bytes

    def _generate_label(
        self,
        page_w_mm: float,
        page_h_mm: float,
        layout: Dict[str, Any],
        payload: Dict[str, Any]
    ) -> bytes:
        c, buf = self._create_canvas(page_w_mm, page_h_mm)

        for key, spec in layout.items():
            try:
                value = payload.get(key)

                if spec.get("debug", False):
                    self.draw_debug(c, spec)

                if spec.get("type", None) == "image" and "filename" in spec:
                    self.draw_img(c, spec)
                elif spec.get("type", None) == "barcode":
                    self.draw_barcode(c, value, spec)
                else:
                    self.draw_text(c, value, spec)
            except Exception as e:
                logger.error(f"Error while drawing: {key}: {e}")

        pdf_bytes = self._finalize_pdf(c, buf)
        return pdf_bytes

    def _pdf_to_png_base64(self, pdf_bytes: bytes, dpi: int = 200) -> str:
        images = convert_from_bytes(pdf_bytes, dpi=dpi)

        if not images:
            logger.error("pdf2image returned no images")
            raise RuntimeError("pdf2image returned no images")

        img = images[0]
        png_buf = BytesIO()

        try:
            img.save(png_buf, dpi=(dpi, dpi), format="PNG")
            png_bytes = png_buf.getvalue()
        finally:
            png_buf.close()
            for im in images:
                try:
                    im.close()
                except:
                    pass

        return base64.b64encode(png_bytes).decode("utf-8")

    def generate_template_png_preview_base64(self, template, dpi: int = 200) -> str:
        payload = {k: k for k in template["elements"]}
        elements = {
            k: {kk: vv for kk, vv in v.items() if kk in ("x", "y", "style", "width", "height")} | {"debug": True}
            for k, v in template["elements"].items()
        }
        pdf_bytes = self._generate_label(template["width"], template["height"], elements, payload)
        return self._pdf_to_png_base64(pdf_bytes, dpi=dpi)

    def generate_pdf_preview_base64(self, template: Template, payload) -> str:
        pdf_bytes = self._generate_label(template.width, template.height, template.elements, payload)
        return base64.b64encode(pdf_bytes).decode("utf-8")

    def generate_png_preview_base64(self, template: Template, payload, dpi: int = 200) -> str:
        pdf_bytes = self._generate_label(template.width, template.height, template.elements, payload)
        return self._pdf_to_png_base64(pdf_bytes, dpi=dpi)

label_service = LabelService()
