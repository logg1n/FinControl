@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

REM Создание приложений
SET apps=users transactions analytics reports bot dashboard

FOR %%A IN (%apps%) DO (
    mkdir %%A
    cd %%A
    echo. > models.py
    echo. > views.py
    echo. > urls.py
    echo. > apps.py
    IF NOT "%%A"=="bot" (
        echo. > forms.py
        echo. > admin.py
        mkdir templates
        mkdir templates\%%A
    ) ELSE (
        mkdir handlers
        mkdir middlewares
        mkdir keyboards
        echo. > config.py
        echo. > main.py
        echo. > utils.py
    )
    cd..
)

REM Статические файлы
mkdir static

REM Общие шаблоны
mkdir templates
echo. > templates\base.html
echo. > templates\layout.html

REM Создаём папку filters и пустые файлы
mkdir transactions\filters
cd transactions\filters

echo. > __init__.py
echo # Базовые классы и интерфейсы для фильтров > base_filters.py
echo # Фильтры по сумме (больше, меньше, между, сортировка) > amount_filters.py
echo # Фильтры по дате (1 день, неделя, месяц, год, диапазон) > date_filters.py
echo # Фильтры по категории и подкатегории > category_filters.py
echo # Фильтры по валюте > currency_filters.py
echo # Фильтры по способу оплаты > payment_filters.py
echo # Фильтры по меткам > tag_filters.py

echo Структура проекта FinControl успешно создана.
pause
