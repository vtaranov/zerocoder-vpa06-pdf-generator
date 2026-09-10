#!/usr/bin/env python3
"""CLI-инструмент для генерации PDF-чека из CSV и HTML-шаблона."""

from __future__ import annotations

import argparse
import csv
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Sequence

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from weasyprint import HTML


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "output"
DEFAULT_DATA = DATA_DIR / "products.csv"
DEFAULT_TEMPLATE = TEMPLATES_DIR / "receipt.html"
DEFAULT_OUTPUT = OUTPUT_DIR / "sample_receipt.pdf"


@dataclass(frozen=True)
class Product:
    """Одна товарная позиция из CSV-файла."""

    product: str
    price: Decimal
    qty: int

    @property
    def total(self) -> Decimal:
        return self.price * self.qty


def money(value: Decimal) -> str:
    """Форматирует сумму с пробелами между разрядами и двумя копейками."""

    return f"{value:,.2f}".replace(",", " ").replace(".", ",")



def load_products(csv_path: Path) -> list[Product]:
    """Читает и проверяет товары из CSV в кодировке UTF-8."""

    if not csv_path.is_file():
        raise FileNotFoundError(f"CSV-файл не найден: {csv_path}")

    products: list[Product] = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        required_columns = {"product", "price", "qty"}
        missing = required_columns - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                "В CSV отсутствуют обязательные колонки: " + ", ".join(sorted(missing))
            )

        for row_number, row in enumerate(reader, start=2):
            product_name = (row.get("product") or "").strip()
            if not product_name:
                raise ValueError(f"Строка {row_number}: название товара не заполнено")

            try:
                price = Decimal((row.get("price") or "").strip()).quantize(Decimal("0.01"))
                qty = int((row.get("qty") or "").strip())
            except (InvalidOperation, ValueError) as error:
                raise ValueError(
                    f"Строка {row_number}: цена и количество должны быть числами"
                ) from error

            if price < 0:
                raise ValueError(f"Строка {row_number}: цена не может быть отрицательной")
            if qty <= 0:
                raise ValueError(f"Строка {row_number}: количество должно быть больше нуля")

            products.append(Product(product=product_name, price=price, qty=qty))

    if not products:
        raise ValueError("CSV-файл не содержит товарных позиций")
    return products


def render_html(
    template_path: Path,
    products: Sequence[Product],
    receipt_number: str,
    customer: str,
) -> str:
    """Подставляет данные в HTML-шаблон через Jinja2."""

    if not template_path.is_file():
        raise FileNotFoundError(f"HTML-шаблон не найден: {template_path}")

    environment = Environment(
        loader=FileSystemLoader(str(template_path.parent)),
        autoescape=select_autoescape(("html", "xml")),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    environment.filters["money"] = money
    template = environment.get_template(template_path.name)
    grand_total = sum((item.total for item in products), start=Decimal("0.00"))

    return template.render(
        items=products,
        item_count=len(products),
        grand_total=grand_total,
        receipt_number=receipt_number,
        receipt_date=datetime.now().strftime("%d.%m.%Y %H:%M"),
        customer=customer,
    )


def generate_pdf(
    csv_path: Path,
    template_path: Path,
    output_path: Path,
    receipt_number: str,
    customer: str,
) -> Path:
    """Генерирует PDF и возвращает абсолютный путь к нему."""

    products = load_products(csv_path)
    html_text = render_html(template_path, products, receipt_number, customer)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html_text, base_url=str(template_path.parent)).write_pdf(str(output_path))
    return output_path.resolve()


def open_pdf(pdf_path: Path) -> None:
    """Открывает PDF в системной программе Windows, macOS или Linux."""

    if sys.platform.startswith("win"):
        os.startfile(pdf_path)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.run(["open", str(pdf_path)], check=True)
    else:
        subprocess.run(["xdg-open", str(pdf_path)], check=True)


def choose_file(directory: Path, suffix: str, title: str) -> Path:
    """Показывает нумерованное меню выбора файла."""

    files = sorted(directory.glob(f"*{suffix}"))
    if not files:
        raise FileNotFoundError(f"В папке {directory} нет файлов {suffix}")

    print(f"\n{title}")
    for index, file_path in enumerate(files, start=1):
        print(f"  {index}. {file_path.name}")

    while True:
        answer = input("Введите номер: ").strip()
        if answer.isdigit() and 1 <= int(answer) <= len(files):
            return files[int(answer) - 1]
        print("Введите номер одного из вариантов списка.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Создаёт PDF-чек из CSV-файла и HTML-шаблона."
    )
    parser.add_argument("--data", type=Path, help="путь к CSV-файлу")
    parser.add_argument("--template", type=Path, help="путь к HTML-шаблону")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="путь к PDF")
    parser.add_argument("--receipt-number", default="VPA06-001", help="номер чека")
    parser.add_argument("--customer", default="Учебный покупатель", help="покупатель")
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="не открывать PDF после генерации (удобно для автотестов)",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    try:
        interactive = args.data is None and args.template is None and sys.stdin.isatty()
        if interactive:
            print("PDF Check Maker")
            csv_path = choose_file(DATA_DIR, ".csv", "Доступные CSV-файлы:")
            template_path = choose_file(TEMPLATES_DIR, ".html", "Доступные шаблоны:")
        else:
            csv_path = (args.data or DEFAULT_DATA).resolve()
            template_path = (args.template or DEFAULT_TEMPLATE).resolve()

        output_path = generate_pdf(
            csv_path=csv_path,
            template_path=template_path,
            output_path=args.output.resolve(),
            receipt_number=args.receipt_number,
            customer=args.customer,
        )
        print(f"Готово: PDF сохранён в {output_path}")

        if not args.no_open:
            open_pdf(output_path)
            print("PDF открыт в системной программе.")
        return 0
    except (FileNotFoundError, ValueError, OSError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
