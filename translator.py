from PySide6 import QtCore

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
