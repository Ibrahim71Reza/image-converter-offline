from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QAction, QKeySequence
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
from .file_discovery import expand_input_paths
from .reports import write_csv_report


class DropListWidget(QListWidget):
    files_changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setAcceptDrops(True)
        self.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.setAlternatingRowColors(True)
        self.setToolTip("Drag image files or folders here, or click Add Files / Add Folder.")

    def dragEnterEvent(self, event):  # noqa: N802 - Qt API
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):  # noqa: N802 - Qt API
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):  # noqa: N802 - Qt API
        paths = [Path(url.toLocalFile()) for url in event.mimeData().urls() if url.isLocalFile()]
        self.add_files(expand_input_paths(paths, recursive=True))
        event.acceptProposedAction()

    def add_files(self, files: list[Path]) -> None:
        existing = {self.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.count())}
        added = False
        for path in files:
            if path.is_file():
                key = str(path.expanduser().resolve())
                if key not in existing:
                    item = QListWidgetItem(key)
                    item.setData(Qt.ItemDataRole.UserRole, key)
                    self.addItem(item)
                    existing.add(key)
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
    finished_all = Signal(object)

    def __init__(self, files: list[Path], output_dir: Path, target_format: str, options: ConversionOptions) -> None:
        super().__init__()
        self.files = files
        self.output_dir = output_dir
        self.target_format = target_format
        self.options = options
        self.service = ConverterService()
        self._cancel_requested = False

    def cancel(self) -> None:
        self._cancel_requested = True

    def run(self) -> None:
        total = len(self.files)
        results: list[ConversionResult] = []
        for index, path in enumerate(self.files, start=1):
            if self._cancel_requested:
                break
            result = self.service.convert_one(path, self.output_dir, self.target_format, self.options)
            results.append(result)
            self.result_ready.emit(result)
            self.progress_changed.emit(index, total)
        self.finished_all.emit(results)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.service = ConverterService()
        self.worker: ConversionWorker | None = None
        self.last_results: list[ConversionResult] = []

        self.setWindowTitle(f"{__app_name__} {__version__}")
        self.resize(1020, 760)

        self.file_list = DropListWidget()
        self.file_list.files_changed.connect(self.refresh_targets)

        self.target_combo = QComboBox()
        self.output_dir_label = QLabel(str(Path.cwd() / "converted"))
        self.output_dir_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setValue(92)

        self.recursive_check = QCheckBox("Add folders recursively")
        self.recursive_check.setChecked(True)
        self.overwrite_check = QCheckBox("Overwrite existing files")
        self.metadata_check = QCheckBox("Preserve metadata when possible")
        self.metadata_check.setChecked(True)
        self.animation_check = QCheckBox("Preserve animation when possible")
        self.animation_check.setChecked(True)
        self.report_check = QCheckBox("Write CSV report")
        self.report_check.setChecked(True)

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

        title = QLabel("OmniImage Converter")
        title.setStyleSheet("font-size: 24px; font-weight: 700;")
        subtitle = QLabel(
            "Portable offline batch image conversion. Target formats update to the formats supported by all files in the current batch."
        )
        subtitle.setWordWrap(True)

        add_button = QPushButton("Add Files")
        add_button.clicked.connect(self.add_files)
        folder_button = QPushButton("Add Folder")
        folder_button.clicked.connect(self.add_folder)
        choose_output_button = QPushButton("Choose Output Folder")
        choose_output_button.clicked.connect(self.choose_output_dir)
        open_output_button = QPushButton("Open Output")
        open_output_button.clicked.connect(self.open_output_dir)
        remove_button = QPushButton("Remove Selected")
        remove_button.clicked.connect(self.file_list.remove_selected)
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.file_list.clear_all)

        file_buttons = QHBoxLayout()
        file_buttons.addWidget(add_button)
        file_buttons.addWidget(folder_button)
        file_buttons.addWidget(remove_button)
        file_buttons.addWidget(clear_button)
        file_buttons.addStretch(1)
        file_buttons.addWidget(self.recursive_check)

        output_row = QHBoxLayout()
        output_row.addWidget(QLabel("Output folder:"))
        output_row.addWidget(self.output_dir_label, stretch=1)
        output_row.addWidget(choose_output_button)
        output_row.addWidget(open_output_button)

        target_row = QHBoxLayout()
        target_row.addWidget(QLabel("Convert to:"))
        target_row.addWidget(self.target_combo, stretch=1)
        target_row.addWidget(QLabel("Quality:"))
        target_row.addWidget(self.quality_spin)

        checks = QHBoxLayout()
        checks.addWidget(self.metadata_check)
        checks.addWidget(self.animation_check)
        checks.addWidget(self.overwrite_check)
        checks.addWidget(self.report_check)
        checks.addStretch(1)

        self.convert_button = QPushButton("Convert Now")
        self.convert_button.setMinimumHeight(42)
        self.convert_button.clicked.connect(self.convert_now)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setMinimumHeight(42)
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_conversion)

        action_row = QHBoxLayout()
        action_row.addWidget(self.convert_button, stretch=3)
        action_row.addWidget(self.cancel_button, stretch=1)

        root.addWidget(title)
        root.addWidget(subtitle)
        root.addLayout(file_buttons)
        root.addWidget(self.file_list, stretch=3)
        root.addLayout(output_row)
        root.addLayout(target_row)
        root.addLayout(checks)
        root.addLayout(action_row)
        root.addWidget(self.progress)
        root.addWidget(QLabel("Conversion log:"))
        root.addWidget(self.log, stretch=2)

        self.setCentralWidget(central)

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("File")
        add_action = QAction("Add Files", self)
        add_action.setShortcut(QKeySequence.StandardKey.Open)
        add_action.triggered.connect(self.add_files)
        file_menu.addAction(add_action)

        add_folder_action = QAction("Add Folder", self)
        add_folder_action.triggered.connect(self.add_folder)
        file_menu.addAction(add_folder_action)

        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        help_menu = self.menuBar().addMenu("Help")
        backends_action = QAction("Backend Status", self)
        backends_action.triggered.connect(self.show_backend_status)
        help_menu.addAction(backends_action)

        formats_action = QAction("Supported Formats", self)
        formats_action.triggered.connect(self.show_supported_formats)
        help_menu.addAction(formats_action)

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

    def show_supported_formats(self) -> None:
        outputs = self.service.supported_outputs()
        lines = [_format_display(fmt) for fmt in outputs]
        QMessageBox.information(self, "Supported Output Formats", "\n".join(lines) or "No output formats found.")

    def show_about(self) -> None:
        QMessageBox.information(
            self,
            "About OmniImage Converter",
            "OmniImage Converter is an offline, portable desktop app for image conversion. "
            "It uses rawpy for camera RAW when installed, ImageMagick for wide-format coverage, "
            "and Pillow for common formats and fallback conversion.",
        )

    def add_files(self) -> None:
        filenames, _ = QFileDialog.getOpenFileNames(self, "Choose image files")
        self.file_list.add_files([Path(name) for name in filenames])

    def add_folder(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Choose folder")
        if directory:
            files = expand_input_paths([Path(directory)], recursive=self.recursive_check.isChecked())
            self.file_list.add_files(files)

    def choose_output_dir(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Choose output folder", self.output_dir_label.text())
        if directory:
            self.output_dir_label.setText(directory)

    def open_output_dir(self) -> None:
        path = Path(self.output_dir_label.text()).expanduser().resolve()
        path.mkdir(parents=True, exist_ok=True)
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=False)
        else:
            subprocess.run(["xdg-open", str(path)], check=False)

    def refresh_targets(self) -> None:
        current = self.target_combo.currentData()
        self.target_combo.clear()
        paths = self.file_list.paths()
        formats = self.service.supported_outputs_for_paths(paths)
        for fmt in formats:
            self.target_combo.addItem(_format_display(fmt), fmt.key)
        if current:
            index = self.target_combo.findData(current)
            if index >= 0:
                self.target_combo.setCurrentIndex(index)
        self.statusBar().showMessage(f"{len(paths)} file(s) queued. {len(formats)} common target format(s) available.")

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

        self.last_results = []
        self.progress.setValue(0)
        self.progress.setMaximum(len(files))
        self.convert_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.log.append(f"Starting {len(files)} conversion(s) to {target}...")

        self.worker = ConversionWorker(files, output_dir, target, options)
        self.worker.result_ready.connect(self.add_result)
        self.worker.progress_changed.connect(self.update_progress)
        self.worker.finished_all.connect(self.finish_conversion)
        self.worker.start()

    def cancel_conversion(self) -> None:
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.log.append("Cancel requested. The current file will finish, then the batch will stop.")
            self.cancel_button.setEnabled(False)

    def add_result(self, result: ConversionResult) -> None:
        self.last_results.append(result)
        state = "✅" if result.success else "❌"
        self.log.append(
            f"{state} {result.input_path.name} → {result.output_path} [{result.backend_name}] "
            f"{result.message} ({result.elapsed_seconds:.2f}s)"
        )

    def update_progress(self, done: int, total: int) -> None:
        self.progress.setMaximum(total)
        self.progress.setValue(done)

    def finish_conversion(self, results: list[ConversionResult]) -> None:
        self.convert_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        if self.report_check.isChecked() and results:
            report_path = Path(self.output_dir_label.text()) / "omniimage_report.csv"
            write_csv_report(report_path, results)
            self.log.append(f"Report written: {report_path}")
        succeeded = sum(1 for result in results if result.success)
        failed = sum(1 for result in results if not result.success)
        self.log.append(f"Finished. Success: {succeeded}; Failed: {failed}.")
        self.statusBar().showMessage(f"Conversion finished. Success: {succeeded}; Failed: {failed}.")


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
