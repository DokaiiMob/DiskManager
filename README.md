# DiskManager

DiskManager — это инструмент для управления дисками и создания резервных копий. Приложение предоставляет возможность анализа дискового пространства, очистки временных файлов, создания резервных копий важных данных, а также мониторинга системной информации в режиме реального времени.

## Основные функции

- **Просмотр информации о дисках**: Показывает подробную информацию о подключённых дисках, включая свободное и занятое пространство, файловую систему, тип диска и визуализацию использования.
- **Создание резервных копий**: Позволяет создавать резервные копии пользовательских папок в различных форматах (`zip`, `7z`) с возможностью шифрования и инкрементного копирования.
- **Очистка дискового пространства**: Автоматически находит и удаляет временные файлы и файлы большого размера, а также предоставляет возможность фильтрации по типам файлов.
- **Мониторинг системы**: Отображает текущую загрузку процессора, использование памяти и сетевой трафик.

## Требования

- **Python**: Python 3.8 или новее
- **Библиотеки**: Убедитесь, что следующие зависимости установлены:

  ```bash
  pip install PySide6 psutil py7zr reportlab
  ```

## Установка

1. Клонируйте репозиторий:

   ```bash
   git clone https://github.com/yourusername/diskmanager.git
   cd diskmanager
   ```

2. Установите зависимости:

   ```bash
   pip install -r requirements.txt
   ```

3. Запустите приложение:

   ```bash
   python main.py
   ```

## Использование

### Интерфейс приложения

1. **Информация о дисках**: Первая вкладка показывает список всех подключённых дисков. Нажмите кнопку «Обновить информацию о дисках», чтобы получить последние данные.
2. **Резервное копирование**: Вторая вкладка позволяет выбрать папки для резервного копирования, установить формат архива и опции шифрования.
3. **Очистка дисков**: Третья вкладка позволяет проанализировать дисковое пространство и удалить временные файлы.
4. **Системная информация**: Последняя вкладка показывает информацию о системе и использование ресурсов в режиме реального времени.

### Настройки

- **Язык**: Приложение поддерживает несколько языков, включая английский и русский. Язык можно изменить в настройках.
- **Тема**: В настройках можно переключаться между светлой и тёмной темами.

### Структура проекта

```plaintext
diskmanager/
├── dist/               # Сборка исполняемого файла
├── icons/              # Иконки для приложения и инсталлятора
├── logs/               # Логи приложения
├── translations/       # Файлы перевода
├── DiskManager.spec    # Конфигурационный файл для PyInstaller
├── DiskManagerInstaller.iss # Скрипт Inno Setup
├── main.py             # Основной файл приложения
├── workers.py          # Фоновая логика для резервного копирования и очистки
├── translator.py       # Логика для интернационализации
└── README.md           # Документация
```

## Поддержка

Если у вас возникли вопросы или проблемы, откройте новый [вопрос в репозитории](https://github.com/DokaiiMob/diskmanager/issues).

## Лицензия

Этот проект распространяется под лицензией MIT. Подробности см. в файле [LICENSE](LICENSE).


### Объяснение разделов:

- **Заголовок и краткое описание**: Краткое описание предназначения и возможностей приложения.
- **Требования**: Указаны минимальные версии Python и библиотек.
- **Установка**: Пошаговые инструкции для установки из исходного кода.
- **Использование**: Краткие инструкции по основным функциям.
- **Поддержка и лицензия**: Информация о том, где получить помощь и лицензия проекта.
