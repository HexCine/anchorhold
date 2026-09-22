# AnchorHold: первый запуск

Сравните две HTML-сборки документации: исчезнувшие страницы и якоря, у которых изменился заголовок.

**[Скачать визуальное руководство EN/RU](https://github.com/HexCine/anchorhold/releases/download/v0.1.2/start.html)** — сохраните HTML и откройте в браузере. Код не отправляется на сервер.

## 1. Установка

Скачайте [anchorhold-0.1.2-source.zip](https://github.com/HexCine/anchorhold/releases/download/v0.1.2/anchorhold-0.1.2-source.zip), распакуйте и откройте терминал в корне проекта.
Требуется Python 3.11+. Создайте venv: `python -m venv .venv`. Активируйте `.venv/Scripts/Activate.ps1` (PowerShell) или `source .venv/bin/activate` (macOS/Linux). Либо используйте путь к Python окружения вместо `python`.

```sh
python -m pip install .
python -m anchorhold snapshot examples/before --output demo-baseline.json
```

## 2. Учебная проблема

```sh
python -m anchorhold check demo-baseline.json examples/shifted
```

Сдвинутая сборка возвращает 1: три старых якоря обозначают другие релизы. Сохранение прежних заголовков возвращает 0.

## 3. Контрольный пример

```sh
python -m anchorhold check demo-baseline.json examples/fixed --format json
```

Ожидается код 0. При коде 2 проверьте входные данные: полного вывода нет.
Примеры синтетические. Для повторного создания demo выберите новую папку.

## Свои данные

Соберите опубликованную и предложенную версии в разные папки. Проверьте заголовки и сохраните стабильные исторические якоря.

```sh
python -m anchorhold snapshot published-html --output baseline.json
python -m anchorhold check baseline.json candidate-html
```

Подставьте реальные пути вместо примеров. Текстовое изменение заголовка требует проверки. Инструмент не выполняет JavaScript сайта, не следует редиректам и не доказывает смысловое равенство.

Если файл не найден, проверьте текущую папку. Перед отправкой отчёта удалите
чувствительные имена, пути и host. В issue укажите версию, команду, ожидаемый
и фактический результат и минимальный обезличенный пример.

[Полное руководство](../README.md) · [Сообщить об ошибке](https://github.com/HexCine/anchorhold/issues)
