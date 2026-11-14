"""Marketplace scope filter: PC / gaming gear in, phones / TVs / home goods out.

Titles are real Amazon.in, Flipkart and Reliance Digital listings.
Run:  python -m unittest discover -s tests
"""

import unittest

from app.prices.scope import in_scope

KEEP = [
    # components and peripherals
    "MSI GeForce RTX 5060 8G Shadow 2X OC Graphic Card - NVIDIA GeForce RTX 5060 GPU, 8GB GDDR7 128-bit Memory",
    "Samsung 990 Pro 1 TB Desktop Black PCIe NVMe Internal Solid State Drive (SSD) (MZ-V9P1T0BW)",
    "Samsung 990 PRO w/Heatsink SSD 2TB PCIe 4.0 M.2 Internal Solid State Hard Drive, Fastest Speed for Gaming",
    "Logitech G502 X Wired Gaming Mouse - LIGHTFORCE Hybrid Optical-Mechanical Primary switches",
    "Logitech M90 Wired USB Mouse Black Wired Ambidextrous Optical Mouse",
    "ASUS TUF 68.58 cm (27 inch) Quad HD LED Backlit IPS Panel Gaming Monitor (TUF Gaming VG27AQ5A Monitor 27 QHD",
    "Logitech MX Keys S Wireless Keyboard and Mouse Combo, Graphite",
    "Ant Esports ICE-120AG Mid Tower Gaming Cabinet with Tempered Glass Side Panel",
    "Arctic MX-4 4g Thermal Paste for CPU Cooler",
    "TP-Link Archer AX23 Wi-Fi 6 Router",
    "150Mbps 802.11N USB Adapter Black",
    "USB WIFI Dongal ZEB-USB150WFI USB Adapter",
    "Tech_Wifi receiver USB Adapter",
    "Tenda W322E 300 Mbps PCI Wirless Card",
    "StyleNeste GS5 Pro Wave Play Limited Edition 64 GB with GTA San Andreas, 52 Emulators, Tekken, SmackDown",
    "Logitech C920 HD Pro Webcam",
    "ZEBRONICS Igloo 1, 2.0 USB Computer Speakers, 8 Watts, Multicolor LED, USB Powered",
    "Zebronics Juke Bar 9101 Pro Dolby 240 Watts 2.1 Computer Multimedia Speaker",
    # systems
    "Lenovo LOQ AMD Ryzen 7 250 | NVIDIA RTX 5060 8GB (16GB RAM/512GB SSD/FHD IPS/144Hz Refresh Rate",
    "ASUS Vivobook 15 (2026),Intel Core 3 304,Fingerprint Sensor,8GB RAM,512GB SSD,FHD,15.6\"(39.6 cm)",
    "HP 15s Laptop (Intel Core i5 12th Gen, 16GB RAM, 512GB Storage, Windows 11)",
    "Samsung Galaxy Book4 Pro NP940XGK-KG2IN Laptop (Intel Core Ultra 7-155H/16GB/512GB/Windows 11 Home/MSO/OLED)",
    # consoles, games and gaming accessories
    "Sony PlayStation5 Gaming Console (Slim)",
    "Sony DualSense Wireless Controller White (PlayStation 5)",
    "Assassin's Creed Black Flag Resynced | Standard Edition | PlayStation 5",
    "PS5 DISC Drive",
    "SONY PlayStation VR 2 Headset Motion Controller | Brand New PSVR2",
    "R36 Ultra Retro Handheld Game Console, with 64G Built-in 20000+ Games, 3000mAh Rechargeable",
    "EVOFOX Deck 2 Smartphone with Hall Effect Triggers & Joysticks, Key Mapping, RGB Handheld Gaming Console",
    "Tempered Glass Screen Protector for Nintendo Switch 2",
    "EvoFox One S V2 Universal 3-Mode Wireless Gaming Controller,1000Hz HallSense Precision Joysticks, BT, 2.4GHz & "
    "Wired, Macros, Fast Type-C Charging, PC, Mobile, Android TV, PS4 & Console Gaming",
    "Fanatec Officially Licensed Gran Turismo DD Pro PlayStation Sim Racing Steering Wheel, Base and Pedals",
    # headsets, including ones that mention phones
    "Sony INZONE H6 Air Open-Back Wired Gaming Headset for PC, PS5 & Mobile – Ultra-Lightweight Over-Ear Headphones",
    "daWg HeadBug G60 Lightweight Wireless Gaming Headphones, 20ms Ultra Low Latency (2.4GHz), Bluetooth v5.4",
    "RAPTOR SYNC X RGB Gaming Chair with Bluetooth Speakers, Massage, Footrest Gaming Chair",
    "Green Soul Vision Pro Multi-Functional Ergonomic Gaming Chair, with Premium Fabric, 4D Armrests",
]

DROP = [
    # phones
    "Samsung Galaxy S25 Ultra 5G AI Smartphone (Titanium Silverblue, 12GB RAM, 256GB Storage), 200MP Camera",
    "Samsung Galaxy M07 Mobile (Black, 4GB RAM, 64GB Storage) | MediaTek Helio G99 | AnTuTu 624K | IP54| 50MP Camera",
    "Samsung Galaxy A56 5G Mobile (Awesome Midnight Blue, 8GB, 128GB) | Segment Most Complete Triple Camera | 50MP",
    "Samsung Galaxy F06 5G, Bahama Blue (4GB, 128GB)",
    "Galaxy S25 5G Snapdragon (Silver Shadow, 128 GB)",
    "Galaxy F07 (Green, 64 GB) 4 GB RAM",
    "Samsung Galaxy F70 Pro 5G (Alpha Black, 128 GB) (6 GB RAM)",
    "Samsung Galaxy A07 4G 64 GB, 4 GB RAM, Black, Mobile Phone",
    "Lava Bold N2 Lite (Nilgiri Blue, 3 GB RAM, 64 GB Storage) | 6.75\" HD+ Display | 13MP AI Dual Rear Camera",
    "Asus Pad 30.98 cm (12.2 inch) Wi-Fi Tablet, 256 GB, 8 GB RAM, Pure White, T3201M5A-TL005DW",
    # phone accessories
    "SKINFACTORY VIVO X60 Premium Mobile Skin",
    "wrap craft VIVO V60 5G Premium Vinyl BACK 50 Mobile Skin",
    "Roxel Edge To Edge Screen Guard for VIVO X60",
    "Back Cover for Samsung Galaxy J2 Pro Back Case",
    "Flip Cover for Samsung Galaxy J7 Pro",
    "Samsung S25 Pro Silicone Mobile Case, Blue",
    "YCHROZE Edge To Edge Tempered Glass for OPPO A74 5G,REALME 8 5G,REALME 7,REALME 6,SAMSUNG Galaxy A52",
    "Samsung 45 W GaN 3 A Wall Charger for Mobile",
    "Samsung 25 W Adapter, Type-C, Fast Charging, Zero Standby Power Consumption, GAN Technology, Without Cable",
    "Stuffcool 20000 mAh Power Bank, Superpower Black",
    "Ambrane AeroSyncQ B MagSafe Qi2 Wireless Charger, Black",
    # TVs, home audio, appliances
    "Crystal 4K Vision AI 138 cm (55 inch) Ultra HD (4K) LED Smart Tizen TV 2026 Edition with 30W Speakers",
    "Samsung HW-Q990H/XL 756W 11.1.4ch Wireless Atmos Surround Soundbar 756 W Bluetooth Soundbar",
    "Tribit XSound Plus 2 Bluetooth Speaker, 30W, IPX7, 24H Playtime",
    "pTron Funk Wave v1 16 W Bluetooth Soundbar Speaker, Stereo Sound, RGB Lights, Metal Grill, Soundbar for Phone/Laptop",
    "boAt Aavante 2.0 150, 2.0 CH, 16W Signature Sound, RGB LEDs, Dual Full-Range Drivers, Upto 5H Battery, TWS",
    "Samsung 301 L 2 Star 5-in-1 Convertible Frost Free Double Door Refrigerator, RT31H4522S8/HL, Elegant Inox",
    "Top Loading Washing Machine Cover for 7 to 8 Kg",
    "SeGold USB Type C Cable 3.1 A 3 m Braided Nylon BL-A2C-3M-480-IC01",
    # bags
    "Small 19 L Laptop Backpack AP4600 Backpack, Quick-access pockets, Water-repellent, Stylish & Lightweight",
    "TUF Gaming VP5700 Waterproof Bag Waterproof Backpack",
]


class Scope(unittest.TestCase):
    def test_keeps_pc_and_gaming_gear(self):
        for title in KEEP:
            with self.subTest(title=title):
                self.assertTrue(in_scope(title))

    def test_drops_non_pc_products(self):
        for title in DROP:
            with self.subTest(title=title):
                self.assertFalse(in_scope(title))


if __name__ == "__main__":
    unittest.main()
