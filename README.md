# PDF Check Maker

Учебный CLI-проект для урока VPa06. Программа читает товары из CSV, подставляет их в HTML-шаблон, рассчитывает суммы и создаёт PDF-чек.

## Возможности

- CSV в UTF-8 с колонками `product`, `price`, `qty`;
- HTML-шаблон с плейсхолдерами Jinja2;
- точный расчёт денежных сумм через `Decimal`;
- проверка входных данных и понятные сообщения об ошибках;
- поддержка кириллицы и длинных названий;
- интерактивное меню и аргументы командной строки;
- автоматическое открытие PDF в Windows, macOS и Linux;
- сохранение результата в `output`.

## Структура

```text
pdf-generator/
├── data/products.csv
├── output/
├── templates/receipt.html
├── tests/test_pdf_generator.py
├── OFFER.md
├── PROMPT.md
├── README.md
├── pdf_generator.py
└── requirements.txt
```

## Установка

Для macOS или Linux:

```bash
# Однократно на macOS, если Pango ещё не установлен:
brew install pango

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Для Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Запуск

Интерактивный режим с выбором файлов:

```bash
python pdf_generator.py
```

Контрольный запуск с явными параметрами:

```bash
python pdf_generator.py \
  --data data/products.csv \
  --template templates/receipt.html \
  --output output/sample_receipt.pdf \
  --receipt-number VPA06-001 \
  --customer "Виктор Таранов"
```

После успешной генерации PDF автоматически откроется. Для запуска без открытия файла добавьте `--no-open`.

## Проверка

```bash
python -m unittest discover -s tests -v
```

Составной промпт сохранён в `PROMPT.md`. Репозиторий проекта: [github.com/vtaranov/zerocoder-vpa06-pdf-generator](https://github.com/vtaranov/zerocoder-vpa06-pdf-generator).
