import os
import shutil
import psutil
import logging
from PySide6 import QtCore

class WorkerSignals(QtCore.QObject):
    progress = QtCore.Signal(int)
    log = QtCore.Signal(str)
    finished = QtCore.Signal()

class BackupWorker(QtCore.QObject):
    def __init__(self, folders, destination, archive_format='zip', encrypt=False, incremental=False):
        super().__init__()
        self.folders = folders
        self.destination = destination
        self.archive_format = archive_format
        self.encrypt = encrypt
        self.incremental = incremental
        self.signals = WorkerSignals()
        self._is_running = True

    def run(self):
        logging.info("Начало резервного копирования.")
        self.signals.log.emit("Начало резервного копирования...")
        total_folders = len(self.folders)
        for i, folder in enumerate(self.folders, 1):
            if not self._is_running:
                self.signals.log.emit("Резервное копирование отменено пользователем.")
                logging.info("Резервное копирование отменено пользователем.")
                self.signals.finished.emit()
                return
            folder_name = os.path.basename(folder.rstrip(os.sep))
            archive_name = f"{folder_name}_backup.{self.archive_format}"
            archive_path = os.path.join(self.destination, archive_name)
            try:
                if self.archive_format == 'zip':
                    shutil.make_archive(base_name=os.path.splitext(archive_path)[0],
                                        format='zip',
                                        root_dir=folder)
                elif self.archive_format == '7z':
                    import py7zr
                    with py7zr.SevenZipFile(archive_path, 'w', password='password' if self.encrypt else None) as archive:
                        archive.writeall(folder, arcname=folder_name)
                # Добавьте другие форматы по мере необходимости
                self.signals.log.emit(f"Создан архив: {archive_path}")
                logging.info(f"Создан архив: {archive_path}")
            except Exception as e:
                self.signals.log.emit(f"Ошибка при создании архива для {folder}: {e}")
                logging.error(f"Ошибка при создании архива для {folder}: {e}")
            percent = int((i / total_folders) * 100)
            self.signals.progress.emit(percent)
        self.signals.log.emit("Резервное копирование завершено.")
        logging.info("Резервное копирование завершено.")
        self.signals.finished.emit()

    def stop(self):
        self._is_running = False

class CleanupWorker(QtCore.QObject):
    def __init__(self, files):
        super().__init__()
        self.files = files
        self.signals = WorkerSignals()
        self._is_running = True

    def run(self):
        logging.info("Начало очистки файлов.")
        self.signals.log.emit("Начало очистки файлов...")
        total_files = len(self.files)
        deleted_files = 0
        for i, file in enumerate(self.files, 1):
            if not self._is_running:
                self.signals.log.emit("Очистка отменена пользователем.")
                logging.info("Очистка отменена пользователем.")
                self.signals.finished.emit()
                return
            try:
                os.remove(file)
                deleted_files += 1
                self.signals.log.emit(f"Удалено: {file}")
                logging.info(f"Удалено: {file}")
            except PermissionError:
                self.signals.log.emit(f"Не удалось удалить {file}: Файл занят другим процессом.")
                logging.error(f"Не удалось удалить {file}: Файл занят другим процессом.")
            except Exception as e:
                self.signals.log.emit(f"Не удалось удалить {file}: {e}")
                logging.error(f"Не удалось удалить {file}: {e}")
            percent = int((i / total_files) * 100)
            self.signals.progress.emit(percent)
        self.signals.log.emit("Очистка завершена.")
        logging.info(f"Очистка завершена. Удалено {deleted_files} из {total_files} файлов.")
        self.signals.finished.emit()

    def stop(self):
        self._is_running = False
