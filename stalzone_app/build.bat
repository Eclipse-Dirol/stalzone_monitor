@echo off
chcp 65001 > nul
echo =======================================================
echo          СБОРКА ПРИЛОЖЕНИЯ STALZONE AUCTION
echo =======================================================

:: 1. Проверка наличия виртуального окружения
if exist "venv\Scripts\python.exe" (
    set "PY_EXEC=venv\Scripts\python.exe"
    set "PYI_EXEC=venv\Scripts\pyinstaller.exe"
    echo [*] Используется виртуальное окружение: venv
) else if exist "..\venv\Scripts\python.exe" (
    set "PY_EXEC=..\venv\Scripts\python.exe"
    set "PYI_EXEC=..\venv\Scripts\pyinstaller.exe"
    echo [*] Используется виртуальное окружение: ..\venv
) else (
    set "PY_EXEC=python"
    set "PYI_EXEC=pyinstaller"
    echo [!] venv не найден, используется системный Python
)

:: 2. Синхронизация базы и удаление лишних картинок
echo.
echo [*] Запуск автоматической очистки базы и ассетов...
%PY_EXEC% clean_before_build.py
if errorlevel 1 (
    echo.
    echo [ERROR] Ошибка на этапе очистки базы clean_before_build.py!
    pause
    exit /b 1
)

:: 3. Полная очистка старых папок и кэша сборщика
echo.
echo [*] Удаление кэша предыдущих сборок...
if exist "build" rd /s /q "build"
if exist "dist" rd /s /q "dist"
if exist "main" rd /s /q "main"
if exist "main.spec" del /f /q "main.spec"

:: 4. Компиляция проекта в один автономный EXE-файл
echo.
echo [*] Компиляция PyInstaller (режим --onefile)...
%PYI_EXEC% --noconfirm --onefile --windowed ^
  --icon="app_icon.ico" ^
  --add-data "items_data.json;." ^
  --add-data "image;image" ^
  --add-data "app_icon.ico;." ^
  main.py

if errorlevel 1 (
    echo.
    echo =======================================================
    echo [ERROR] Во время сборки PyInstaller произошла ошибка!
    echo =======================================================
    pause
    exit /b 1
)

:: 5. Очистка временного мусора после завершения
if exist "build" rd /s /q "build"
if exist "main.spec" del /f /q "main.spec"

echo.
echo =======================================================
echo [ГОТОВО] Сборка успешно завершена!
echo Исполняемый файл: dist\main.exe
echo =======================================================
pause