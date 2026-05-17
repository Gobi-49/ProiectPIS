import sys
import cv2

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
    QGroupBox,
    QFormLayout,
)

from effects import apply_effect_pipeline


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Photo & Webcam Effects App")
        self.resize(1200, 750)

        self.cap = None
        self.current_frame = None
        self.processed_frame = None

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        self.image_label = QLabel("Preview")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(800, 600)
        self.image_label.setStyleSheet("background-color: #222; color: white;")

        self.start_camera_button = QPushButton("Pornește webcam")
        self.start_camera_button.clicked.connect(self.start_camera)

        self.stop_camera_button = QPushButton("Oprește webcam")
        self.stop_camera_button.clicked.connect(self.stop_camera)

        self.open_image_button = QPushButton("Deschide imagine")
        self.open_image_button.clicked.connect(self.open_image)

        self.save_image_button = QPushButton("Export foto")
        self.save_image_button.clicked.connect(self.save_image)

        self.brightness_slider = self.create_slider(-100, 100, 0)
        self.contrast_slider = self.create_slider(50, 200, 100)
        self.saturation_slider = self.create_slider(0, 200, 100)
        self.grain_slider = self.create_slider(0, 50, 0)
        self.vignette_slider = self.create_slider(0, 100, 0)
        self.chromatic_slider = self.create_slider(0, 20, 0)
        self.pixel_slider = self.create_slider(1, 50, 1)
        self.vintage_slider = self.create_slider(0, 100, 0)

        controls = self.create_controls()

        main_layout = QHBoxLayout()
        main_layout.addWidget(self.image_label, stretch=4)
        main_layout.addWidget(controls, stretch=1)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def create_slider(self, minimum, maximum, value):
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(minimum)
        slider.setMaximum(maximum)
        slider.setValue(value)
        slider.valueChanged.connect(self.refresh_static_image)
        return slider

    def create_controls(self):
        panel = QWidget()
        layout = QVBoxLayout()

        layout.addWidget(self.start_camera_button)
        layout.addWidget(self.stop_camera_button)
        layout.addWidget(self.open_image_button)
        layout.addWidget(self.save_image_button)

        effects_group = QGroupBox("Efecte")
        form = QFormLayout()

        form.addRow("Brightness", self.brightness_slider)
        form.addRow("Contrast", self.contrast_slider)
        form.addRow("Saturation", self.saturation_slider)
        form.addRow("Film grain", self.grain_slider)
        form.addRow("Vignette", self.vignette_slider)
        form.addRow("Chromatic aberration", self.chromatic_slider)
        form.addRow("Pixelizare", self.pixel_slider)
        form.addRow("Vintage", self.vintage_slider)

        effects_group.setLayout(form)

        layout.addWidget(effects_group)
        layout.addStretch()

        panel.setLayout(layout)
        return panel

    def get_effect_values(self):
        brightness = self.brightness_slider.value()
        contrast = self.contrast_slider.value() / 100.0
        saturation = self.saturation_slider.value() / 100.0
        grain = self.grain_slider.value()
        vignette = self.vignette_slider.value() / 100.0
        chromatic = self.chromatic_slider.value()
        pixel_size = self.pixel_slider.value()
        vintage = self.vintage_slider.value() / 100.0

        return {
            "brightness": brightness,
            "contrast": contrast,
            "saturation": saturation,
            "grain": grain,
            "vignette": vignette,
            "chromatic": chromatic,
            "pixel_size": pixel_size,
            "vintage": vintage,
        }

    def start_camera(self):
        self.stop_camera()

        self.cap = cv2.VideoCapture(0)

        if not self.cap.isOpened():
            self.image_label.setText("Nu s-a putut deschide webcam-ul.")
            self.cap = None
            return

        self.timer.start(30)

    def stop_camera(self):
        self.timer.stop()

        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def update_frame(self):
        if self.cap is None:
            return

        ret, frame = self.cap.read()

        if not ret:
            return

        self.current_frame = frame

        params = self.get_effect_values()
        self.processed_frame = apply_effect_pipeline(frame, **params)

        self.display_frame(self.processed_frame)

    def open_image(self):
        self.stop_camera()

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Alege imagine",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp)"
        )

        if not file_path:
            return

        frame = cv2.imread(file_path)

        if frame is None:
            self.image_label.setText("Imaginea nu a putut fi încărcată.")
            return

        self.current_frame = frame
        self.refresh_static_image()

    def refresh_static_image(self):
        if self.cap is not None:
            return

        if self.current_frame is None:
            return

        params = self.get_effect_values()
        self.processed_frame = apply_effect_pipeline(self.current_frame, **params)
        self.display_frame(self.processed_frame)

    def display_frame(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w

        qt_image = QImage(
            rgb_frame.data,
            w,
            h,
            bytes_per_line,
            QImage.Format_RGB888
        )

        pixmap = QPixmap.fromImage(qt_image)
        pixmap = pixmap.scaled(
            self.image_label.width(),
            self.image_label.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        self.image_label.setPixmap(pixmap)

    def save_image(self):
        if self.processed_frame is None:
            self.image_label.setText("Nu există imagine de salvat.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvează imagine",
            "export.png",
            "PNG (*.png);;JPEG (*.jpg *.jpeg)"
        )

        if not file_path:
            return

        cv2.imwrite(file_path, self.processed_frame)


def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()