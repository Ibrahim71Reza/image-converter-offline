from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QStatusBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from . import __app_name__, __version__
from .backends.base import ConversionOptions, ConversionResult, FormatInfo
from .converter import ConverterService


class DropListWidget(QListWidget):
    files_changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setAcceptDrops(True)
        self.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.setAlternatingRowColors(True)
        self.setToolTip("Drag image files here or click Add Files.")

    def dragEnterEvent(self, event):  # noqa: N802 - Qt API
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):  # noqa: N802 - Qt API
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):  # noqa: N802 - Qt API
        files = [Path(url.toLocalFile()) for url in event.mimeData().urls() if url.isLocalFile()]
        self.add_files(files)
        event.acceptProposedAction()

    def add_files(self, files: list[Path]) -> None:
        existing = {self.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.count())}
        added = False
        for path in files:
            if path.is_file() and str(path) not in existing:
                item = QListWidgetItem(str(path))
                item.setData(Qt.ItemDataRole.UserRole, str(path))
                self.addItem(item)
                added = True
        if added:
            self.files_changed.emit()

    def paths(self) -> list[Path]:
        return [Path(self.item(i).data(Qt.ItemDataRole.UserRole)) for i in range(self.count())]

    def remove_selected(self) -> None:
        for item in self.selectedItems():
            self.takeItem(self.row(item))
        self.files_changed.emit()

    def clear_all(self) -> None:
        self.clear()
        self.files_changed.emit()


class ConversionWorker(QThread):
    result_ready = Signal(object)
    progress_changed = Signal(int, int)
    finished_all = Signal()

    def __init__(self, files: list[Path], output_dir: Path, target_format: str, options: ConversionOptions) -> None:
        super().__init__()
        self.files = files
        self.output_dir = output_dir
        self.target_format = target_format
        self.options = options
        self.service = ConverterService()

    def run(self) -> None:
        total = len(self.files)
        for index, path in enumerate(self.files, start=1):
            result = self.service.convert_one(path, self.output_dir, self.target_format, self.options)
            self.result_ready.emit(result)
            self.progress_changed.emit(index, total)
        self.finished_all.emit()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.service = ConverterService()
        self.worker: ConversionWorker | None = None

        self.setWindowTitle(f"{__app_name__} {__version__}")
        self.resize(980, 720)

        self.file_list = DropListWidget()
        self.file_list.files_changed.connect(self.refresh_targets)

        self.target_combo = QComboBox()
        self.output_dir_label = QLabel(str(Path.cwd() / "converted"))
        self.output_dir_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setValue(92)

        self.overwrite_check = QCheckBox("Overwrite existing files")
        self.metadata_check = QCheckBox("Preserve metadata when possible")
        self.metadata_check.setChecked(True)
        self.animation_check = QCheckBox("Preserve animation when possible")
        self.animation_check.setChecked(True)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.progress = QProgressBar()
        self.progress.setValue(0)

        self._build_ui()
        self._build_menu()
        self.setStatusBar(QStatusBar())
        self.refresh_backend_status()
        self.refresh_targets()

    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)

        title = QLabel("Portable Offline Image Converter")
        title.setStyleSheet("font-size: 22px; font-weight: 700;")
        subtitle = QLabel("Batch convert images locally. Supported targets update based on the selected input file and installed backends.")
        subtitle.setWordWrap(True)

        add_button = QPushButton("Add Files")
        add_button.clicked.connect(self.add_files)
        folder_button = QPushButton("Choose Output Folder")
        folder_button.clicked.connect(self.choose_output_dir)
        remove_button = QPushButton("Remove Selected")
        remove_button.clicked.connect(self.file_list.remove_selected)
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.file_list.clear_all)

        file_buttons = QHBoxLayout()
        file_buttons.addWidget(add_button)
        file_buttons.addWidget(remove_button)
        file_buttons.addWidget(clear_button)
        file_buttons.addStretch(1)

        output_row = QHBoxLayout()
        output_row.addWidget(QLabel("Output folder:"))
        output_row.addWidget(self.output_dir_label, stretch=1)
        output_row.addWidget(folder_button)

        target_row = QHBoxLayout()
        target_row.addWidget(QLabel("Convert to:"))
        target_row.addWidget(self.target_combo, stretch=1)
        target_row.addWidget(QLabel("Quality:"))
        target_row.addWidget(self.quality_spin)

        checks = QHBoxLayout()
        checks.addWidget(self.metadata_check)
        checks.addWidget(self.animation_check)
        checks.addWidget(self.overwrite_check)
        checks.addStretch(1)

        convert_button = QPushButton("Convert Now")
        convert_button.setMinimumHeight(42)
        convert_button.clicked.connect(self.convert_now)
        self.convert_button = convert_button

        root.addWidget(title)
        root.addWidget(subtitle)
        root.addLayout(file_buttons)
        root.addWidget(self.file_list, stretch=3)
        root.addLayout(output_row)
        root.addLayout(target_row)
        root.addLayout(checks)
        root.addWidget(convert_button)
        root.addWidget(self.progress)
        root.addWidget(QLabel("Conversion log:"))
        root.addWidget(self.log, stretch=2)

        self.setCentralWidget(central)

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("File")
        add_action = QAction("Add Files", self)
        add_action.triggered.connect(self.add_files)
        file_menu.addAction(add_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        help_menu = self.menuBar().addMenu("Help")
        backends_action = QAction("Backend Status", self)
        backends_action.triggered.connect(self.show_backend_status)
        help_menu.addAction(backends_action)

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def refresh_backend_status(self) -> None:
        parts = []
        for status in self.service.backend_statuses():
            state = "ON" if status.available else "OFF"
            parts.append(f"{status.name}: {state}")
        self.statusBar().showMessage(" | ".join(parts))

    def show_backend_status(self) -> None:
        lines = []
        for status in self.service.backend_statuses():
            state = "Available" if status.available else "Missing"
            lines.append(f"{status.name}: {state} — reads {status.readable_count}, writes {status.writable_count}")
        QMessageBox.information(self, "Backend Status", "\n".join(lines))

    def show_about(self) -> None:
        QMessageBox.information(
            self,
            "About OmniImage Converter",
            "OmniImage Converter is an offline, portable desktop app for image conversion. "
            "It uses Pillow for common formats and ImageMagick/rawpy when available for wider coverage.",
        )

    def add_files(self) -> None:
        filenames, _ = QFileDialog.getOpenFileNames(self, "Choose image files")
        self.file_list.add_files([Path(name) for name in filenames])

    def choose_output_dir(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Choose output folder", self.output_dir_label.text())
        if directory:
            self.output_dir_label.setText(directory)

    def refresh_targets(self) -> None:
        current = self.target_combo.currentData()
        self.target_combo.clear()
        paths = self.file_list.paths()
        formats = self.service.supported_outputs_for(paths[0]) if paths else self.service.supported_outputs()
        for fmt in formats:
            self.target_combo.addItem(_format_display(fmt), fmt.key)
        if current:
            index = self.target_combo.findData(current)
            if index >= 0:
                self.target_combo.setCurrentIndex(index)

    def convert_now(self) -> None:
        files = self.file_list.paths()
        if not files:
            QMessageBox.warning(self, "No files", "Add at least one image file first.")
            return
        target = self.target_combo.currentData()
        if not target:
            QMessageBox.warning(self, "No target", "Choose a target format first.")
            return

        output_dir = Path(self.output_dir_label.text())
        options = ConversionOptions(
            quality=self.quality_spin.value(),
            overwrite=self.overwrite_check.isChecked(),
            preserve_metadata=self.metadata_check.isChecked(),
            preserve_animation=self.animation_check.isChecked(),
        )

        self.progress.setValue(0)
        self.progress.setMaximum(len(files))
        self.convert_button.setEnabled(False)
        self.log.append(f"Starting {len(files)} conversion(s) to {target}...")

        self.worker = ConversionWorker(files, output_dir, target, options)
        self.worker.result_ready.connect(self.add_result)
        self.worker.progress_changed.connect(self.update_progress)
        self.worker.finished_all.connect(self.finish_conversion)
        self.worker.start()

    def add_result(self, result: ConversionResult) -> None:
        state = "✅" if result.success else "❌"
        self.log.append(f"{state} {result.input_path.name} → {result.output_path} [{result.backend_name}] {result.message}")

    def update_progress(self, done: int, total: int) -> None:
        self.progress.setMaximum(total)
        self.progress.setValue(done)

    def finish_conversion(self) -> None:
        self.convert_button.setEnabled(True)
        self.log.append("Finished.")
        self.statusBar().showMessage("Conversion finished.")


def _format_display(fmt: FormatInfo) -> str:
    extensions = ", ".join(fmt.extensions[:4])
    if len(fmt.extensions) > 4:
        extensions += ", ..."
    return f"{fmt.label} ({extensions})"


def run() -> int:
    app = QApplication([])
    app.setApplicationName(__app_name__)
    window = MainWindow()
    window.show()
    return app.exec()
