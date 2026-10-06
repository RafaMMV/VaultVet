"""Shared pet photo appearance and project-relative file handling."""
from pathlib import Path
from uuid import uuid4
import shutil
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QImageReader, QPainter
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QWidget, QSizePolicy

ROOT = Path(__file__).resolve().parent.parent
PHOTO_STYLE = "background-color: #eeeeee; border: 1px solid #c8c8c8; border-radius: 6px; color: #666666;"

def resolve_photo(path):
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    rooted = ROOT / candidate
    return rooted if rooted.exists() else candidate

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".svg"}

def load_photo(path):
    """Validate both extension and actual file content before displaying."""
    source = resolve_photo(path)
    if source.suffix.lower() not in ALLOWED_EXTENSIONS or not source.is_file():
        return QPixmap()
    if source.suffix.lower() == ".svg":
        renderer = QSvgRenderer(str(source))
        if not renderer.isValid():
            return QPixmap()
        size = renderer.defaultSize()
        if size.isEmpty():
            return QPixmap()
        size.scale(512, 512, Qt.AspectRatioMode.KeepAspectRatio)
        pixmap = QPixmap(size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        return pixmap
    reader = QImageReader(str(source))
    actual_format = bytes(reader.format()).lower()
    expected = b"png" if source.suffix.lower() == ".png" else b"jpeg"
    if actual_format != expected:
        return QPixmap()
    return QPixmap.fromImage(reader.read())

def show_photo(label, path=None):
    label.clear()
    label.setText("Sem foto")
    label.setToolTip("")
    if path:
        pixmap = load_photo(path)
        if pixmap.isNull():
            label.setText("⚠\nImagem\nincompatível")
            label.setToolTip("Imagem incompatível ou indisponível. Use JPEG, PNG ou SVG válido.")
        else:
            label.setPixmap(pixmap.scaled(label.size(), Qt.AspectRatioMode.KeepAspectRatio,
                                          Qt.TransformationMode.SmoothTransformation))

def choose_photo(parent):
    path, _ = QFileDialog.getOpenFileName(parent, "Selecionar Foto do Pet", "",
                                         "Imagens (*.jpg *.jpeg *.png *.svg *.JPG *.JPEG *.PNG *.SVG)")
    if path and load_photo(path).isNull():
        QMessageBox.warning(parent, "Imagem incompatível",
                            "Use uma imagem JPEG, PNG ou SVG válida. O arquivo selecionado não foi carregado.")
        return None
    return path or None

def save_photo(path, pet_id):
    source = resolve_photo(path)
    if load_photo(path).isNull():
        raise ValueError("Imagem incompatível. Use JPEG, PNG ou SVG válido.")
    relative = Path("pet_photos") / f"pet_{pet_id}_{uuid4().hex}{source.suffix.lower()}"
    destination = ROOT / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return relative.as_posix()


class PatientPhotoArea(QWidget):
    """Reserve only the preview height and center it horizontally."""
    def __init__(self, label, parent=None):
        super().__init__(parent)
        self.label = label
        label.setParent(self)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumWidth(label.width())
        self.setFixedHeight(label.height())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.position_photo()

    def showEvent(self, event):
        super().showEvent(event)
        self.position_photo()

    def position_photo(self):
        area = self.contentsRect()
        photo_width, photo_height = self.label.width(), self.label.height()
        x = area.x() + (area.width() - photo_width) // 2
        y = area.y() + (area.height() - photo_height) // 2
        y = max(area.top(), min(y, area.bottom() + 1 - photo_height))
        self.label.move(x, y)
