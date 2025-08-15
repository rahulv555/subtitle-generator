import re
import cv2
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit, QLabel, QSizePolicy
from PyQt6.QtGui import QFont, QColor, QPainter, QImage, QPixmap
from PyQt6.QtCore import Qt


def parse_ass_styles(ass_text):
    styles = {}
    lines = ass_text.splitlines()
    style_section = False

    for line in lines:
        if line.strip().lower().startswith("[v4+ styles]"):
            style_section = True
            continue
        if style_section and line.strip().lower().startswith("format:"):
            continue
        if style_section and line.strip().lower().startswith("style:"):
            parts = line.split(",")
            if len(parts) >= 10:
                name = parts[0].split(":")[1].strip()
                font_name = parts[1].strip()
                font_size = int(float(parts[2].strip()))
                primary_color = parts[3].strip()
                outline_color = parts[4].strip()
                bold = parts[7].strip() == "-1"
                italic = parts[8].strip() == "-1"
                alignment = int(parts[11].strip()) if parts[11].strip().isdigit() else 2
                outline_width = int(parts[16].strip()) if len(parts) > 16 and parts[16].strip().isdigit() else 1
                shadow = int(parts[17].strip()) if len(parts) > 17 and parts[17].strip().isdigit() else 0

                styles[name] = {
                    "font": font_name,
                    "size": font_size,
                    "color": ass_color_to_qcolor(primary_color),
                    "outline_color": ass_color_to_qcolor(outline_color),
                    "bold": bold,
                    "italic": italic,
                    "alignment": alignment,
                    "outline_width": outline_width,
                    "shadow": shadow
                }
    return styles


def parse_inline_tags(text, base_style):
    chunks = []
    current_style = base_style.copy()

    parts = re.split(r'(\{\\.*?\})', text)
    for part in parts:
        if not part:
            continue
        if part.startswith("{\\") and part.endswith("}"):
            tags = part[1:-1].split("\\")[1:]
            for tag in tags:
                if tag.startswith("b"):
                    current_style["bold"] = tag[1:] == "1"
                elif tag.startswith("i"):
                    current_style["italic"] = tag[1:] == "1"
                elif tag.startswith("fn"):
                    current_style["font"] = tag[2:]
                elif tag.startswith("fs") and tag[2:].isdigit():
                    current_style["size"] = int(tag[2:])
                elif tag.startswith("c&H"):
                    current_style["color"] = ass_color_to_qcolor(tag[2:])
                elif tag.startswith("3c&H"):
                    current_style["outline_color"] = ass_color_to_qcolor(tag[3:])
            continue
        chunks.append((part, current_style.copy()))
    return chunks


def ass_color_to_qcolor(c):
    try:
        rgb = int(c.replace("&H", "").replace("&", ""), 16)
        b = rgb & 0xFF
        g = (rgb >> 8) & 0xFF
        r = (rgb >> 16) & 0xFF
        return QColor(r, g, b)
    except:
        return QColor("white")


class SubtitleLabel(QWidget):
    def __init__(self):
        super().__init__()
        self.chunks = []
        self.alignment = Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom
        

    def setChunksAndAlignment(self, chunks, alignment):
        self.chunks = chunks
        self.alignment = alignment
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        rect = self.rect()

        total_width = 0
        for text, style in self.chunks:
            font = QFont(style["font"], style["size"])
            font.setBold(style["bold"])
            font.setItalic(style["italic"])
            painter.setFont(font)
            total_width += painter.fontMetrics().horizontalAdvance(text)

        if self.alignment & Qt.AlignmentFlag.AlignHCenter:
            x = (rect.width() - total_width) // 2
        elif self.alignment & Qt.AlignmentFlag.AlignRight:
            x = rect.width() - total_width
        else:
            x = 0
        y = rect.height() - 20 if self.alignment & Qt.AlignmentFlag.AlignBottom else rect.height() // 2

        for text, style in self.chunks:
            font = QFont(style["font"], style["size"])
            font.setBold(style["bold"])
            font.setItalic(style["italic"])
            painter.setFont(font)

            outline_width = style.get("outline_width", 1)
            shadow = style.get("shadow", 0)

            if shadow > 0:
                painter.setPen(style["outline_color"])
                painter.drawText(x + shadow, y + shadow, text)

            if outline_width > 0:
                painter.setPen(style["outline_color"])
                for dx in range(-outline_width, outline_width + 1):
                    for dy in range(-outline_width, outline_width + 1):
                        if dx != 0 or dy != 0:
                            painter.drawText(x + dx, y + dy, text)

            painter.setPen(style["color"])
            painter.drawText(x, y, text)
            x += painter.fontMetrics().horizontalAdvance(text)


class ASSPreview(QWidget):
    def __init__(self):
        super().__init__()
        self.styles = {}
        self.video_path = None

        main_layout = QVBoxLayout(self)

        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("Paste or load your ASS file contents...")
        self.editor.cursorPositionChanged.connect(self.update_preview)

        self.video_frame = QLabel()
        self.video_frame.setMinimumHeight(200)
        self.video_frame.setMaximumHeight(200)
        self.video_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.video_frame.setStyleSheet("background-color: black;")

        self.subtitle_label = SubtitleLabel()
        self.subtitle_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        frame_layout = QVBoxLayout()
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.addWidget(self.subtitle_label)
        self.video_frame.setLayout(frame_layout)

        main_layout.addWidget(self.editor)
        main_layout.addWidget(self.video_frame)

    def set_ass_text(self, text):
        self.editor.setPlainText(text)
        self.styles = parse_ass_styles(text)

    def set_video_preview(self, video_path):
        self.video_path = video_path
        cap = cv2.VideoCapture(video_path)
        ret, frame = cap.read()
        cap.release()
        if ret:
            h, w, _ = frame.shape
            crop_h = h // 3  # bottom third
            frame_bottom = frame[h - crop_h :, :, :]
            frame_bottom = cv2.cvtColor(frame_bottom, cv2.COLOR_BGR2RGB)

            # Convert to QImage
            qimg = QImage(
                frame_bottom.data,
                frame_bottom.shape[1],
                frame_bottom.shape[0],
                frame_bottom.strides[0],
                QImage.Format.Format_RGB888,
            )

            # Scale to fit the fixed label size, keeping aspect ratio
            pixmap = QPixmap.fromImage(qimg).scaled(
                self.video_frame.width(),
                self.video_frame.height(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            self.video_frame.setPixmap(pixmap)
    def update_preview(self):
        try:
            ass_text = self.editor.toPlainText()
            self.styles = parse_ass_styles(ass_text)
            
            cursor = self.editor.textCursor()
            cursor.select(cursor.SelectionType.LineUnderCursor)
            current_line = cursor.selectedText()

            if current_line.lower().startswith("dialogue:"):
                parts = current_line.split(",")
                if len(parts) >= 10:
                    style_name = parts[3].strip()
                    dialogue_text = ",".join(parts[9:])
                    print(style_name)
                    print(self.styles.get(style_name))
                    base_style = self.styles.get(style_name, {
                        "font": "Arial",
                        "size": 24,
                        "color": QColor("white"),
                        "outline_color": QColor("black"),
                        "bold": False,
                        "italic": False,
                        "alignment": 2,
                        "outline_width": 2,
                        "shadow": 1
                    })

                    chunks = parse_inline_tags(dialogue_text, base_style)
                    align_map = {
                        1: Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom,
                        2: Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom,
                        3: Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom,
                        4: Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                        5: Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                        6: Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                        7: Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                        8: Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                        9: Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop,
                    }
                    self.subtitle_label.setChunksAndAlignment(
                        chunks, align_map.get(base_style["alignment"], Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)
                    )
                    return

            self.subtitle_label.setChunksAndAlignment([], Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)
        except Exception as e:
            self.subtitle_label.setChunksAndAlignment([], Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)
            return

