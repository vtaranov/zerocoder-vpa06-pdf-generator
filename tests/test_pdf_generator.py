from __future__ import annotations

import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from pdf_generator import DEFAULT_TEMPLATE, generate_pdf, load_products, money


class PdfGeneratorTests(unittest.TestCase):
    def test_money_uses_russian_number_format(self) -> None:
        self.assertEqual(money(Decimal("7650")), "7 650,00")

    def test_load_products_and_calculate_total(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "products.csv"
            csv_path.write_text(
                "product,price,qty\nТестовый товар,120.50,2\n",
                encoding="utf-8",
            )

            products = load_products(csv_path)

            self.assertEqual(len(products), 1)
            self.assertEqual(products[0].product, "Тестовый товар")
            self.assertEqual(products[0].total, Decimal("241.00"))

    def test_rejects_missing_required_column(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "invalid.csv"
            csv_path.write_text("product,price\nТовар,100\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "qty"):
                load_products(csv_path)

    def test_generate_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            csv_path = temp_path / "products.csv"
            pdf_path = temp_path / "result.pdf"
            csv_path.write_text(
                "product,price,qty\nТовар с кириллицей,99.90,3\n",
                encoding="utf-8",
            )

            result = generate_pdf(
                csv_path=csv_path,
                template_path=DEFAULT_TEMPLATE,
                output_path=pdf_path,
                receipt_number="TEST-001",
                customer="Тестовый покупатель",
            )

            self.assertEqual(result, pdf_path.resolve())
            self.assertTrue(pdf_path.read_bytes().startswith(b"%PDF-"))
            self.assertGreater(pdf_path.stat().st_size, 5_000)


if __name__ == "__main__":
    unittest.main()
