import sys
import os
import psutil
import platform
import shutil
import logging
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtCharts import QChart, QChartView, QPieSeries
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QListWidget, QListWidgetItem, QFileDialog, QMessageBox, QLabel,
    QProgressBar, QTabWidget, QCheckBox, QMenu, QMenuBar
)
from PySide6.QtGui import QAction, QIcon

# Define WorkerSignals class for threading
class WorkerSignals(QtCore.QObject):
    progress = QtCore.Signal(int)
    log = QtCore.Signal(str)
    finished = QtCore.Signal()

# Define BackupWorker class
class BackupWorker(QtCore.QObject):
    def __init__(self, selected_folders, destination, archive_format, encrypt, incremental):
        super().__init__()
        self.selected_folders = selected_folders
        self.destination = destination
        self.archive_format = archive_format
        self.encrypt = encrypt
        self.incremental = incremental
        self.signals = WorkerSignals()

    def run(self):
        total = len(self.selected_folders)
        for i, folder in enumerate(self.selected_folders, 1):
            # Simulate backup operation
            self.signals.log.emit(f"{tr('Backing up')} {folder}")
            # Update progress
            progress = int(i / total * 100)
            self.signals.progress.emit(progress)
            QtCore.QThread.sleep(1)  # Simulate time-consuming task
        self.signals.finished.emit()

# Define CleanupWorker class
class CleanupWorker(QtCore.QObject):
    def __init__(self, selected_files):
        super().__init__()
        self.selected_files = selected_files
        self.signals = WorkerSignals()

    def run(self):
        total = len(self.selected_files)
        for i, file in enumerate(self.selected_files, 1):
            # Simulate file deletion
            self.signals.log.emit(f"{tr('Deleting')} {file}")
            # Update progress
            progress = int(i / total * 100)
            self.signals.progress.emit(progress)
            QtCore.QThread.sleep(1)  # Simulate time-consuming task
        self.signals.finished.emit()

# Define Translator class
class Translator:
    def __init__(self, app):
        self.app = app
        self.translator = QtCore.QTranslator()
        self.current_language = 'en'  # Default to English

    def load_language(self, language_code):
        if language_code == 'ru':
            if self.translator.load("translations/translations_ru.qm"):
                self.app.installTranslator(self.translator)
                self.current_language = 'ru'
        else:
            self.app.removeTranslator(self.translator)
            self.current_language = 'en'

# Simple translation function
def tr(text):
    return QtCore.QCoreApplication.translate("MainWindow", text)

def resource_path(relative_path):
    """Gets the absolute path to the resource, works for scripts and for frozen executables"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Define log directory
log_dir = resource_path("logs")
try:
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
except Exception as e:
    print(f"Не удалось создать директорию для логов: {e}")
    log_dir = os.path.abspath(".")  # Use current directory
    logging.basicConfig(
        filename='disk_manager.log',
        filemode='a',
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    logging.error(f"Не удалось создать директорию для логов: {e}")
else:
    # Set up logging
    logging.basicConfig(
        filename=os.path.join(log_dir, 'disk_manager.log'),
        filemode='a',
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

class SystemTrayIcon(QtWidgets.QSystemTrayIcon):
    def __init__(self, icon, parent=None):
        super().__init__(icon, parent)
        self.setToolTip("Disk Manager")
        menu = QMenu(parent)
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(QtWidgets.QApplication.quit)
        menu.addAction(exit_action)
        self.setContextMenu(menu)

class DiskInfoTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Refresh button
        refresh_btn = QPushButton(tr("Refresh Disk Info"))
        refresh_btn.setIcon(QIcon.fromTheme("view-refresh"))
        refresh_btn.clicked.connect(self.display_disk_info)
        layout.addWidget(refresh_btn)

        # Table for disk info
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            tr("Disk"), tr("Mount Point"), tr("FS"), tr("Total (GB)"),
            tr("Used (GB)"), tr("Free (GB)"), tr("Usage (%)"), tr("Type")
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.table)

        # Disk usage charts
        self.charts_layout = QHBoxLayout()
        layout.addLayout(self.charts_layout)

        self.setLayout(layout)
        self.display_disk_info()

    def display_disk_info(self):
        logging.info("Обновление информации о дисках.")
        self.table.setRowCount(0)

        # Remove old charts
        while self.charts_layout.count():
            item = self.charts_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        disks = psutil.disk_partitions()
        for disk in disks:
            try:
                # Attempt to get disk usage
                usage = psutil.disk_usage(disk.mountpoint)
                disk_type = tr("Removable") if 'removable' in disk.opts else tr("Internal")
                row_position = self.table.rowCount()
                self.table.insertRow(row_position)
                self.table.setItem(row_position, 0, QtWidgets.QTableWidgetItem(disk.device))
                self.table.setItem(row_position, 1, QtWidgets.QTableWidgetItem(disk.mountpoint))
                self.table.setItem(row_position, 2, QtWidgets.QTableWidgetItem(disk.fstype))
                self.table.setItem(row_position, 3, QtWidgets.QTableWidgetItem(f"{usage.total / (1024**3):.2f}"))
                self.table.setItem(row_position, 4, QtWidgets.QTableWidgetItem(f"{usage.used / (1024**3):.2f}"))
                self.table.setItem(row_position, 5, QtWidgets.QTableWidgetItem(f"{usage.free / (1024**3):.2f}"))
                self.table.setItem(row_position, 6, QtWidgets.QTableWidgetItem(f"{usage.percent}"))
                self.table.setItem(row_position, 7, QtWidgets.QTableWidgetItem(disk_type))

                # Create chart
                chart = QChart()
                pie = QPieSeries()
                pie.append(tr("Used"), usage.used)
                pie.append(tr("Free"), usage.free)
                pie.setLabelsVisible(True)
                pie.setHoleSize(0.4)

                # Set font for slices
                for slice in pie.slices():
                    slice.setLabelFont(QtGui.QFont("Arial", 10))

                chart.addSeries(pie)
                chart.setTitle(f'{tr("Disk")}: {disk.device}')

                # Set font for chart
                chart.setFont(QtGui.QFont("Arial", 10))

                chart_view = QChartView(chart)
                chart_view.setRenderHint(QtGui.QPainter.Antialiasing)
                chart_view.setMinimumSize(200, 200)
                self.charts_layout.addWidget(chart_view)

            except Exception as e:
                logging.error(f"Error getting usage for disk {disk.device} at {disk.mountpoint}: {e}")
                row_position = self.table.rowCount()
                self.table.insertRow(row_position)
                self.table.setItem(row_position, 0, QtWidgets.QTableWidgetItem(disk.device))
                self.table.setItem(row_position, 1, QtWidgets.QTableWidgetItem(tr("No Access")))
                for col in range(2, 8):
                    self.table.setItem(row_position, col, QtWidgets.QTableWidgetItem("-"))

        logging.info("Информация о дисках обновлена.")

class BackupTab(QWidget):
    def __init__(self):
        super().__init__()
        self.thread = None
        self.worker = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Поле поиска
        search_layout = QHBoxLayout()
        search_label = QLabel(tr("Search:"))
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.textChanged.connect(self.filter_backup_list)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Список папок для резервного копирования
        self.backup_list = QtWidgets.QListWidget()
        self.backup_list.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        user_folders = ["Documents", "Downloads", "Desktop", "Pictures", "Music", "Videos"]
        user_path = os.path.expanduser("~")
        for folder in user_folders:
            path = os.path.join(user_path, folder)
            if os.path.exists(path):
                item = QListWidgetItem(f"{tr(folder)} -> {path}")
                item.setCheckState(QtCore.Qt.Unchecked)
                self.backup_list.addItem(item)
        layout.addWidget(self.backup_list)

        # Кнопки выбора и начала резервного копирования
        btn_layout = QHBoxLayout()
        select_all_btn = QPushButton(tr("Select All"))
        select_all_btn.setIcon(QIcon.fromTheme("select-all"))
        select_all_btn.clicked.connect(self.select_all)
        deselect_all_btn = QPushButton(tr("Deselect All"))
        deselect_all_btn.setIcon(QIcon.fromTheme("edit-clear"))
        deselect_all_btn.clicked.connect(self.deselect_all)
        btn_layout.addWidget(select_all_btn)
        btn_layout.addWidget(deselect_all_btn)
        layout.addLayout(btn_layout)

        # Опции резервного копирования
        options_layout = QHBoxLayout()
        self.format_combo = QtWidgets.QComboBox()
        self.format_combo.addItems(['zip', '7z'])
        self.encrypt_checkbox = QCheckBox(tr("Encrypt Archives"))
        self.incremental_checkbox = QCheckBox(tr("Incremental Backup"))
        options_layout.addWidget(QLabel(tr("Archive Format:")))
        options_layout.addWidget(self.format_combo)
        options_layout.addWidget(self.encrypt_checkbox)
        options_layout.addWidget(self.incremental_checkbox)
        layout.addLayout(options_layout)

        backup_btn = QPushButton(tr("Start Backup"))
        backup_btn.setIcon(QIcon.fromTheme("document-save"))
        backup_btn.clicked.connect(self.start_backup)
        layout.addWidget(backup_btn)

        # Прогресс-бар
        self.progress = QProgressBar()
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        # Логирование
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)

        self.setLayout(layout)

    def filter_backup_list(self, text):
        for index in range(self.backup_list.count()):
            item = self.backup_list.item(index)
            item.setHidden(text.lower() not in item.text().lower())

    def select_all(self):
        for index in range(self.backup_list.count()):
            item = self.backup_list.item(index)
            item.setCheckState(QtCore.Qt.Checked)

    def deselect_all(self):
        for index in range(self.backup_list.count()):
            item = self.backup_list.item(index)
            item.setCheckState(QtCore.Qt.Unchecked)

    def start_backup(self):
        selected_folders = []
        for index in range(self.backup_list.count()):
            item = self.backup_list.item(index)
            if item.checkState() == QtCore.Qt.Checked:
                folder_path = item.text().split(" -> ")[1]
                selected_folders.append(folder_path)

        if not selected_folders:
            QMessageBox.warning(self, tr("Backup"), tr("Please select at least one folder for backup."))
            logging.warning("Попытка начать резервное копирование без выбранных папок.")
            return

        destination = QFileDialog.getExistingDirectory(self, tr("Choose Backup Destination"))
        if not destination:
            logging.info("Резервное копирование отменено пользователем.")
            return

        # Получение опций
        archive_format = self.format_combo.currentText()
        encrypt = self.encrypt_checkbox.isChecked()
        incremental = self.incremental_checkbox.isChecked()

        # Запуск резервного копирования в отдельном потоке
        self.thread = QtCore.QThread()
        self.worker = BackupWorker(selected_folders, destination, archive_format, encrypt, incremental)
        self.worker.moveToThread(self.thread)

        # Соединение сигналов и слотов
        self.thread.started.connect(self.worker.run)
        self.worker.signals.progress.connect(self.update_progress)
        self.worker.signals.log.connect(self.log_message)
        self.worker.signals.finished.connect(self.thread.quit)
        self.worker.signals.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

        self.thread.finished.connect(lambda: QMessageBox.information(self, tr("Backup"), tr("Backup Completed")))

    def update_progress(self, value):
        self.progress.setValue(value)

    def log_message(self, message):
        self.log.append(message)

class CleanupTab(QWidget):
    def __init__(self):
        super().__init__()
        self.thread = None
        self.worker = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Поле поиска
        search_layout = QHBoxLayout()
        search_label = QLabel(tr("Search:"))
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.textChanged.connect(self.filter_cleanup_list)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Кнопка анализа дискового пространства
        analyze_btn = QPushButton(tr("Analyze Disk Space"))
        analyze_btn.setIcon(QIcon.fromTheme("system-search"))
        analyze_btn.clicked.connect(self.analyze_disk_space)
        layout.addWidget(analyze_btn)

        # Список файлов для очистки
        self.cleanup_list = QListWidget()
        self.cleanup_list.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        layout.addWidget(self.cleanup_list)

        # Кнопка очистки выбранных файлов
        cleanup_btn = QPushButton(tr("Start Cleanup"))
        cleanup_btn.setIcon(QIcon.fromTheme("edit-delete"))
        cleanup_btn.clicked.connect(self.cleanup_disk_space)
        layout.addWidget(cleanup_btn)

        # Прогресс-бар
        self.progress = QProgressBar()
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        # Логирование
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)

        # Опции очистки
        options_layout = QHBoxLayout()
        self.filetype_checkbox = QCheckBox(tr("Filter by File Types"))
        self.filetypes_input = QtWidgets.QLineEdit()
        self.filetypes_input.setPlaceholderText("e.g., .tmp,.log")
        options_layout.addWidget(self.filetype_checkbox)
        options_layout.addWidget(self.filetypes_input)
        layout.addLayout(options_layout)

        # Опция удаления больших файлов
        self.large_files_checkbox = QCheckBox(tr("Delete Large Files (>)"))
        self.large_files_input = QtWidgets.QLineEdit()
        self.large_files_input.setPlaceholderText("e.g., 100MB")
        options_layout2 = QHBoxLayout()
        options_layout2.addWidget(self.large_files_checkbox)
        options_layout2.addWidget(self.large_files_input)
        layout.addLayout(options_layout2)

        self.setLayout(layout)

    def filter_cleanup_list(self, text):
        for index in range(self.cleanup_list.count()):
            item = self.cleanup_list.item(index)
            item.setHidden(text.lower() not in item.text().lower())

    def analyze_disk_space(self):
        logging.info("Начало анализа дискового пространства.")
        self.cleanup_list.clear()
        self.log.append(tr("Analyzing temporary files..."))
        temp_files = []
        temp_dirs = [os.getenv('TEMP'), os.path.expanduser('~\\AppData\\Local\\Temp')]

        # Получение фильтров
        filetypes = []
        if self.filetype_checkbox.isChecked():
            filetypes = [ft.strip() for ft in self.filetypes_input.text().split(',') if ft.strip()]
        
        max_size = None
        if self.large_files_checkbox.isChecked():
            size_str = self.large_files_input.text().upper()
            try:
                if size_str.endswith('MB'):
                    max_size = int(size_str.rstrip('MB')) * 1024**2
                elif size_str.endswith('GB'):
                    max_size = int(size_str.rstrip('GB')) * 1024**3
                elif size_str.endswith('KB'):
                    max_size = int(size_str.rstrip('KB')) * 1024
                else:
                    max_size = int(size_str)  # Assume bytes
            except ValueError:
                QMessageBox.warning(self, tr("Cleanup"), tr("Invalid size format for large files."))
                logging.warning("Некорректный формат размера для больших файлов.")
                return

        for temp_dir in temp_dirs:
            if temp_dir and os.path.exists(temp_dir):
                for root_dir, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root_dir, file)
                        # Применение фильтров
                        if filetypes and not any(file.endswith(ft) for ft in filetypes):
                            continue
                        if max_size:
                            try:
                                if os.path.getsize(file_path) < max_size:
                                    continue
                            except OSError:
                                continue
                        temp_files.append(file_path)

        for file in temp_files:
            item = QListWidgetItem(file)
            item.setCheckState(QtCore.Qt.Checked)
            self.cleanup_list.addItem(item)

        self.log.append(f"{tr('Found')} {len(temp_files)} {tr('temporary files')}.")
        logging.info(f"Найдено {len(temp_files)} временных файлов.")

    def cleanup_disk_space(self):
        selected_files = []
        for index in range(self.cleanup_list.count()):
            item = self.cleanup_list.item(index)
            if item.checkState() == QtCore.Qt.Checked:
                selected_files.append(item.text())

        if not selected_files:
            QMessageBox.warning(self, tr("Cleanup"), tr("Please select files to delete."))
            logging.warning("Попытка очистить дисковое пространство без выбранных файлов.")
            return

        confirm = QMessageBox.question(
            self,
            tr("Cleanup"),
            tr("Are you sure you want to delete {} files?").format(len(selected_files)),
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm == QMessageBox.No:
            logging.info("Очистка диска отменена пользователем.")
            return

        # Запуск очистки в отдельном потоке
        self.thread = QtCore.QThread()
        self.worker = CleanupWorker(selected_files)
        self.worker.moveToThread(self.thread)

        # Соединение сигналов и слотов
        self.thread.started.connect(self.worker.run)
        self.worker.signals.progress.connect(self.update_progress)
        self.worker.signals.log.connect(self.log_message)
        self.worker.signals.finished.connect(self.thread.quit)
        self.worker.signals.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

        self.thread.finished.connect(lambda: QMessageBox.information(self, tr("Cleanup"), tr("Cleanup Completed")))

    def update_progress(self, value):
        self.progress.setValue(value)

    def log_message(self, message):
        self.log.append(message)

class SystemInfoTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Текстовое поле с системной информацией
        self.system_info_text = QTextEdit()
        self.system_info_text.setReadOnly(True)
        layout.addWidget(self.system_info_text)

        # Реальное время мониторинга
        self.cpu_label = QLabel(tr("CPU Usage:"))
        self.memory_label = QLabel(tr("Memory Usage:"))
        self.network_label = QLabel(tr("Network Usage:"))
        layout.addWidget(self.cpu_label)
        layout.addWidget(self.memory_label)
        layout.addWidget(self.network_label)

        # Визуализация использования ресурсов
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setMaximum(100)
        layout.addWidget(QLabel(tr("CPU Usage:")))
        layout.addWidget(self.cpu_progress)

        self.memory_progress = QProgressBar()
        self.memory_progress.setMaximum(100)
        layout.addWidget(QLabel(tr("Memory Usage:")))
        layout.addWidget(self.memory_progress)

        self.network_label_detail = QLabel(tr("Network Usage:"))
        layout.addWidget(self.network_label_detail)

        # Таймер для обновления информации
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_system_info)
        self.timer.start(1000)  # Обновление каждую секунду

        self.setLayout(layout)
        self.display_system_info()

    def display_system_info(self):
        info = f"""
{tr("System")}: {platform.system()}
{tr("Node Name")}: {platform.node()}
{tr("Version")}: {platform.version()}
{tr("Platform")}: {platform.platform()}
{tr("Processor")}: {platform.processor()}
{tr("Architecture")}: {platform.architecture()[0]}
{tr("CPU Cores")}: {psutil.cpu_count(logical=False)}
{tr("CPU Threads")}: {psutil.cpu_count(logical=True)}
{tr("Memory")}: {round(psutil.virtual_memory().total / (1024**3), 2)} GB
        """
        self.system_info_text.setPlainText(info)

    def update_system_info(self):
        cpu_usage = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        memory_usage = memory.percent

        net_io = psutil.net_io_counters()
        bytes_sent = net_io.bytes_sent
        bytes_recv = net_io.bytes_recv
        network_usage = f"{tr('Sent')}: {self.format_bytes(bytes_sent)} | {tr('Received')}: {self.format_bytes(bytes_recv)}"

        self.cpu_label.setText(f"{tr('CPU Usage:')} {cpu_usage}%")
        self.cpu_progress.setValue(cpu_usage)
        self.memory_label.setText(f"{tr('Memory Usage:')} {memory_usage}%")
        self.memory_progress.setValue(memory_usage)
        self.network_label.setText(f"{tr('Network Usage:')} {network_usage}")

    def format_bytes(self, num):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if num < 1024.0:
                return f"{num:.2f} {unit}"
            num /= 1024.0
        return f"{num:.2f} PB"

class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, translator):
        super().__init__()
        self.translator = translator
        self.setWindowTitle(tr("Settings"))
        self.setModal(True)
        self.resize(400, 200)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Темы оформления
        theme_label = QLabel(tr("Choose Theme:"))
        layout.addWidget(theme_label)

        self.theme_combo = QtWidgets.QComboBox()
        self.theme_combo.addItems([tr("Light"), tr("Dark")])
        layout.addWidget(self.theme_combo)

        # Выбор языка
        language_label = QLabel(tr("Choose Language:"))
        layout.addWidget(language_label)

        self.language_combo = QtWidgets.QComboBox()
        self.language_combo.addItems(["English", "Русский"])
        layout.addWidget(self.language_combo)

        # Кнопки
        btn_layout = QHBoxLayout()
        save_btn = QPushButton(tr("Save"))
        save_btn.clicked.connect(self.save_settings)
        cancel_btn = QPushButton(tr("Cancel"))
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        # Кнопки экспорта и импорта настроек
        export_btn = QPushButton(tr("Export Settings"))
        export_btn.clicked.connect(self.export_settings)
        import_btn = QPushButton(tr("Import Settings"))
        import_btn.clicked.connect(self.import_settings)
        btn_layout2 = QHBoxLayout()
        btn_layout2.addWidget(export_btn)
        btn_layout2.addWidget(import_btn)
        layout.addLayout(btn_layout2)

        self.setLayout(layout)

        # Загрузка текущих настроек
        self.load_settings()

    def load_settings(self):
        settings = QtCore.QSettings("DiskManager", "Settings")
        theme = settings.value("theme", "Light")
        language = settings.value("language", "English")
        index = self.theme_combo.findText(tr(theme))
        if index != -1:
            self.theme_combo.setCurrentIndex(index)
        lang_index = self.language_combo.findText(language)
        if lang_index != -1:
            self.language_combo.setCurrentIndex(lang_index)

    def save_settings(self):
        selected_theme = self.theme_combo.currentText()
        selected_language = self.language_combo.currentText()

        # Сохранение настроек
        settings = QtCore.QSettings("DiskManager", "Settings")
        settings.setValue("theme", selected_theme)
        settings.setValue("language", selected_language)

        # Обновление перевода
        if selected_language == "Русский":
            self.translator.load_language('ru')
        else:
            self.translator.load_language('en')

        logging.info(f"Настройки изменены: Тема - {selected_theme}, Язык - {selected_language}")
        self.accept()

    def export_settings(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, tr("Export Settings"), "", "INI Files (*.ini)", options=options)
        if file_path:
            settings = QtCore.QSettings("DiskManager", "Settings")
            settings.sync()
            shutil.copy("disk_manager.log", file_path)
            QMessageBox.information(self, tr("Export"), tr("Settings exported successfully."))
            logging.info(f"Настройки экспортированы в {file_path}")

    def import_settings(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, tr("Import Settings"), "", "INI Files (*.ini)", options=options)
        if file_path:
            settings = QtCore.QSettings("DiskManager", "Settings")
            imported_settings = QtCore.QSettings(file_path, QtCore.QSettings.IniFormat)
            for key in imported_settings.allKeys():
                settings.setValue(key, imported_settings.value(key))
            QMessageBox.information(self, tr("Import"), tr("Settings imported successfully."))
            logging.info(f"Настройки импортированы из {file_path}")
            self.load_settings()

class MainWindow(QMainWindow):
    def __init__(self, translator):
        super().__init__()
        self.translator = translator
        self.setWindowTitle(tr("Disk Management and Backup Tool"))
        self.setGeometry(100, 100, 1000, 700)
        self.init_ui()

    def init_ui(self):
        # Создание вкладок
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.disk_info_tab = DiskInfoTab()
        self.backup_tab = BackupTab()
        self.cleanup_tab = CleanupTab()
        self.system_info_tab = SystemInfoTab()

        self.tabs.addTab(self.disk_info_tab, tr("Disk Information"))
        self.tabs.addTab(self.backup_tab, tr("Disk Backup"))
        self.tabs.addTab(self.cleanup_tab, tr("Disk Cleanup"))
        self.tabs.addTab(self.system_info_tab, tr("System Information"))

        # Создание меню
        self.create_menu()

        # Создание панели инструментов
        self.create_toolbar()

        # Создание строки состояния
        self.status = self.statusBar()
        self.status.showMessage(tr("Ready"))

        # Создание системного трея
        self.tray_icon = SystemTrayIcon(QIcon.fromTheme("applications-system"), self)
        self.tray_icon.show()

        # Загрузка настроек
        self.load_settings()

    def create_menu(self):
        menubar = self.menuBar()

        # Меню "File"
        file_menu = menubar.addMenu(tr("File"))
        exit_action = QAction(tr("Exit"), self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setIcon(QIcon.fromTheme("application-exit"))
        exit_action.triggered.connect(QtWidgets.QApplication.quit)
        file_menu.addAction(exit_action)

        # Меню "Settings"
        settings_menu = menubar.addMenu(tr("Settings"))
        settings_action = QAction(tr("Settings"), self)
        settings_action.setIcon(QIcon.fromTheme("preferences-system"))
        settings_action.triggered.connect(self.open_settings)
        settings_menu.addAction(settings_action)

        # Меню "Help"
        help_menu = menubar.addMenu(tr("Help"))
        about_action = QAction(tr("About"), self)
        about_action.setIcon(QIcon.fromTheme("help-about"))
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_toolbar(self):
        toolbar = self.addToolBar("Main Toolbar")

        refresh_action = QAction(QIcon.fromTheme("view-refresh"), tr("Refresh Disk Info"), self)
        refresh_action.triggered.connect(self.disk_info_tab.display_disk_info)
        toolbar.addAction(refresh_action)

        backup_action = QAction(QIcon.fromTheme("document-save"), tr("Start Backup"), self)
        backup_action.triggered.connect(self.backup_tab.start_backup)
        toolbar.addAction(backup_action)

        cleanup_action = QAction(QIcon.fromTheme("edit-delete"), tr("Start Cleanup"), self)
        cleanup_action.triggered.connect(self.cleanup_tab.cleanup_disk_space)
        toolbar.addAction(cleanup_action)

    def open_settings(self):
        dialog = SettingsDialog(self.translator)
        if dialog.exec():
            self.apply_settings()

    def apply_settings(self):
        self.apply_theme()
        self.update_ui_texts()

    def apply_theme(self):
        settings = QtCore.QSettings("DiskManager", "Settings")
        theme = settings.value("theme", "Light")
        if tr(theme) == tr("Dark"):
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QPushButton {
                    background-color: #3c3c3c;
                    color: #ffffff;
                }
                QTextEdit, QListWidget, QTableWidget {
                    background-color: #3c3c3c;
                    color: #ffffff;
                }
                QProgressBar {
                    background-color: #3c3c3c;
                    color: #ffffff;
                }
                QMenuBar {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QMenu {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
            """)
        else:
            self.setStyleSheet("")
        logging.info(f"Тема применена: {theme}")

    def update_ui_texts(self):
        # Обновление текстов во всех виджетах
        self.setWindowTitle(tr("Disk Management and Backup Tool"))
        self.tabs.setTabText(0, tr("Disk Information"))
        self.tabs.setTabText(1, tr("Disk Backup"))
        self.tabs.setTabText(2, tr("Disk Cleanup"))
        self.tabs.setTabText(3, tr("System Information"))

        # Обновление меню
        menubar = self.menuBar()
        menubar.clear()
        self.create_menu()

        # Обновление панели инструментов
        self.create_toolbar()

    def load_settings(self):
        settings = QtCore.QSettings("DiskManager", "Settings")
        theme = settings.value("theme", "Light")
        language = settings.value("language", "English")
        # Установка языка
        if language == "Русский":
            self.translator.load_language('ru')
        else:
            self.translator.load_language('en')
        # Применение темы
        self.apply_theme()

    def show_about(self):
        QMessageBox.information(
            self,
            tr("About"),
            tr("About Program"),
            QMessageBox.Ok
        )

class Translator:
    def __init__(self, app):
        self.app = app
        self.translator = QtCore.QTranslator()
        self.current_language = 'en'  # По умолчанию английский

    def load_language(self, language_code):
        if language_code == 'ru':
            if self.translator.load("translations/translations_ru.qm"):
                self.app.installTranslator(self.translator)
                self.current_language = 'ru'
        else:
            self.app.removeTranslator(self.translator)
            self.current_language = 'en'

def tr(text):
    # Простая функция перевода для демонстрации
    # В реальном приложении используйте QCoreApplication.translate
    return QtCore.QCoreApplication.translate("MainWindow", text)

def main():
    app = QApplication(sys.argv)

    # Настройка QSettings
    QtCore.QCoreApplication.setOrganizationName("DiskManager")
    QtCore.QCoreApplication.setApplicationName("DiskManager")

    # Инициализация переводчика
    translator = Translator(app)

    window = MainWindow(translator)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
