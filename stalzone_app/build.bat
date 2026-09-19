@echo off
chcp 65001 > nul
echo =======================================================
echo          СБОРКА ПРИЛОЖЕНИЯ STALZONE AUCTION
echo =======================================================

:: 1. Умное определение окружения (Conda / venv / global)
if defined CONDA_PREFIX (
    :: Если батник запущен из окружения Conda (например, из Anaconda Prompt)
    set "PY_EXEC=%CONDA_PREFIX%\python.exe"
    set "PYI_EXEC=%CONDA_PREFIX%\Scripts\pyinstaller.exe"
    echo [] Обнаружено окружение Conda: %CONDA_DEFAULT_ENV%
) else if exist "venv\Scripts\python.exe" (
    :: Если рядом лежит обычная папка venv
    set "PY_EXEC=venv\Scripts\python.exe"
    set "PYI_EXEC=venv\Scripts\pyinstaller.exe"
    echo [] Обнаружено локальное окружение: venv
) else if exist "..\venv\Scripts\python.exe" (
    set "PY_EXEC=..\venv\Scripts\python.exe"
    set "PYI_EXEC=..\venv\Scripts\pyinstaller.exe"
    echo [*] Обнаружено локальное окружение: ..\venv
) else (
    :: Попытка использовать то, что сейчас доступно в PATH
    set "PY_EXEC=python"
    set "PYI_EXEC=pyinstaller"
    echo [!] Специфичное окружение не найдено, используется текущий Python
)
:: Проверка наличия PyInstaller
%PYI_EXEC% --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] PyInstaller не найден в выбранном окружении!
    echo Установите его командой: pip install pyinstaller
    pause
    exit /b 1
)

:: 2. Синхронизация базы и удаление лишних картинок
echo.
echo [] Запуск автоматической очистки базы и ассетов...
%PY_EXEC% clean_before_build.py
if errorlevel 1 (
    echo.
    echo [ERROR] Ошибка на этапе clean_before_build.py!
    pause
    exit /b 1
)

:: 3. Очистка старых билдов
echo.
echo [] Очистка кэша предыдущих сборок...
if exist "build" rd /s /q "build"
if exist "dist" rd /s /q "dist"
if exist "main" rd /s /q "main"
if exist "main.spec" del /f /q "main.spec"

:: 4. Компиляция PyInstaller
echo.
echo [*] Компиляция в единый EXE-файл...
%PYI_EXEC% --noconfirm --onefile --windowed ^
  --icon="app_icon.ico" ^
  --add-data "items_data.json;." ^
  --add-data "image;image" ^
  --add-data "app_icon.ico;." ^
  main.py

if errorlevel 1 (
    echo.
    echo =======================================================
    echo [ERROR] Ошибка сборки PyInstaller!
    echo =======================================================
    pause
    exit /b 1
)

:: 5. Удаление временных файлов
if exist "build" rd /s /q "build"
if exist "main.spec" del /f /q "main.spec"

echo.
echo =======================================================
echo [ГОТОВО] Сборка успешно завершена!
echo Файл приложения: dist\main.exe
echo =======================================================
pause