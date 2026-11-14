"""Regression tests for cross-store product matching, built from real listings.

Run:  python -m unittest discover -s tests
"""

import unittest

from app.prices.matcher import build_groups, conflict, features, normalise
from app.prices.models import Offer


def same(a: str, b: str) -> bool:
    return not conflict(features(a), features(b))


class Normalise(unittest.TestCase):
    def test_gpu_model_keeps_following_word_separate(self):
        # regression: "RTX 5060 Windforce" once became "rtx 5060windforce"
        self.assertIn("rtx 5060 windforce", normalise("Gigabyte RTX 5060 Windforce OC"))
        self.assertIn("rtx 5060 8gb", normalise("MSI RTX 5060 8G Shadow"))

    def test_variants_and_aliases(self):
        self.assertIn("rtx 5060 ti", normalise("RTX5060Ti"))
        self.assertIn("ps5", normalise("Sony PlayStation 5 Console"))
        self.assertIn("g502x", normalise("Logitech G502 X Plus"))

    def test_memory_kits(self):
        self.assertIn("2x16gb", normalise("32GB (16GB x 2) DDR5"))
        self.assertIn("2x16gb", normalise("32GB (2 x 16GB) DDR5"))
        self.assertIn("1x32gb", normalise("32GB (32GBX1) DDR5"))


class Matching(unittest.TestCase):
    def test_same_product_different_wording(self):
        self.assertTrue(same("MSI RTX 5060 Ventus 2X OC 8GB GDDR7 Graphics Card",
                             "MSI GeForce RTX 5060 8G Ventus 2X OC Graphic Card - NVIDIA GeForce RTX 5060 GPU, 8GB GDDR7"))
        self.assertTrue(same("Sony PS5 Console with ASTRO's Playroom Game",
                             "SONY PS5 Console (CFI-2116A01Y) 1 TB with ASTRO's PLAYROOM"))
        self.assertTrue(same("Logitech G502 Hero Gaming Mouse", "Logitech G502 Hero High Performance Gaming Mouse"))

    def test_different_product_lines(self):
        self.assertFalse(same("MSI RTX 5060 Shadow 2X OC 8GB", "MSI RTX 5060 Ventus 2X OC 8GB"))
        self.assertFalse(same("Gigabyte RTX 5060 Ti Eagle OC 8GB", "Gigabyte RTX 5060 Ti Aero OC 8GB"))
        self.assertFalse(same("Gigabyte RTX 5060 Gaming OC 8GB Graphics Card", "Gigabyte RTX 5060 Eagle OC 8GB Graphics Card"))

    def test_variants_never_merge(self):
        self.assertFalse(same("ZOTAC RTX 5060 Twin Edge 8GB", "ZOTAC RTX 5060 Ti Twin Edge 8GB"))
        self.assertFalse(same("Sony PS5 Console", "Sony PS5 Digital Console"))
        self.assertFalse(same("Logitech G502 X Wired Gaming Mouse", "Logitech G502 Hero Gaming Mouse"))
        self.assertFalse(same("Logitech G502 Hero Gaming Mouse", "Logitech G502 Lightspeed Wireless Gaming Mouse"))

    def test_models_and_capacities(self):
        self.assertFalse(same("AMD Ryzen 7 9800X3D Processor", "AMD Ryzen 7 7800X3D Processor"))
        self.assertFalse(same("ZOTAC RTX 5060 Ti AMP 16GB", "ZOTAC RTX 5060 Ti AMP 8GB"))
        self.assertFalse(same("Corsair Vengeance 32GB (32GBX1) DDR5 6000MHz", "Corsair Vengeance DDR5 32GB (2 x 16GB) 6000MHz"))
        self.assertFalse(same("XPG Lancer Blade 32GB (32GBX1) DDR5", "XPG Lancer Blade 64GB (32GB x 2) DDR5"))

    def test_accessory_is_not_the_console(self):
        self.assertFalse(same("PS5 DISC Drive", "Sony PlayStation5 Gaming Console (Slim)"))


class ProductType(unittest.TestCase):
    def kind(self, title):
        return features(title).kind

    def test_first_device_word_wins(self):
        self.assertEqual(self.kind("NINTENDO Switch 2 Gaming Console | The Ultimate 3-in-1 with Joy-Con controllers"), "console")
        self.assertEqual(self.kind("Sony DualSense Wireless Controller for PS5 console"), "controller")
        self.assertEqual(self.kind("Super Mario Bros Wonder Nintendo Switch 2 Games With Free Key Chain | Switch 2 Console"), "game")
        self.assertEqual(self.kind("Cosmic Byte Game Controller for PC"), "controller")
        self.assertEqual(self.kind("Logitech G640 Mouse Pad"), "mousepad")

    def test_systems_and_components(self):
        self.assertEqual(self.kind("Lenovo LOQ i7 13650HX 16 GB/512 GB SSD/RTX 4050 Gaming Laptop"), "laptop")
        self.assertEqual(self.kind("Pulse Gaming 5060 (Intel Core i5-14400F · RTX 5060 8GB · 16GB DDR5 · 1TB SSD)"), "prebuilt")
        self.assertEqual(self.kind("Xbox Series X 1TB SSD Console"), "console")
        self.assertEqual(self.kind("Corsair Vengeance 32GB DDR5 6000MHz RAM"), "ram")
        self.assertEqual(self.kind("MSI RTX 5060 Ventus 2X OC 8GB GDDR7 Graphics Card"), "gpu")


class Grouping(unittest.TestCase):
    def offer(self, store, title, price, **kw):
        return Offer(store=store, title=title, url=f"https://{store}.example/{abs(hash(title))}", price=price, **kw)

    def test_groups_across_stores_and_picks_cheapest_in_stock(self):
        offers = [
            self.offer("amazon", "MSI GeForce RTX 5060 8G Ventus 2X OC Graphic Card", 62000, in_stock=True, rating=4.6, rating_count=500),
            self.offer("mdcomputers", "MSI RTX 5060 Ventus 2X OC 8GB GDDR7 Graphics Card", 59999),
            self.offer("primeabgb", "MSI RTX 5060 Ventus 2X OC 8GB GDDR7", 41000, in_stock=False),
            self.offer("vedant", "MSI RTX 5060 Shadow 2X OC 8GB GDDR7", 60500),
        ]
        groups = build_groups("rtx 5060", offers)
        ventus = next(g for g in groups if "Ventus" in g.title)
        self.assertEqual(ventus.store_count, 3)
        self.assertEqual(ventus.best.store, "mdcomputers")  # out-of-stock ₹41k must not win
        self.assertEqual(ventus.savings, 62000 - 59999)
        self.assertTrue(any("Shadow" in g.title and g.store_count == 1 for g in groups))

    def test_exact_model_ranks_above_variant(self):
        offers = [
            self.offer("amazon", "ZOTAC RTX 5060 Ti Twin Edge 8GB GDDR7 Graphics Card", 55000),
            self.offer("flipkart", "ZOTAC RTX 5060 Twin Edge 8GB GDDR7 Graphics Card", 45000),
        ]
        groups = build_groups("rtx 5060", offers)
        self.assertNotIn(" Ti ", f" {groups[0].title} ")


if __name__ == "__main__":
    unittest.main()
