"""Browsable categories, trending searches and the queries behind "Best offers"."""

CATEGORIES = [
    {"id": "consoles", "label": "Consoles", "query": "gaming console",
     "chips": ["PS5 Pro", "PS5 Slim", "Xbox Series X", "Nintendo Switch 2", "Meta Quest 3"]},
    {"id": "gpu", "label": "Graphics Cards", "query": "graphics card",
     "chips": ["RTX 5060", "RTX 5060 Ti", "RTX 5070", "RTX 5070 Ti", "RTX 5080", "RX 9060 XT", "RX 9070 XT"]},
    {"id": "cpu", "label": "Processors", "query": "ryzen processor",
     "chips": ["Ryzen 5 7600", "Ryzen 7 7800X3D", "Ryzen 7 9800X3D", "Core i5 14600K", "Core Ultra 7 265K"]},
    {"id": "motherboard", "label": "Motherboards", "query": "b650 motherboard",
     "chips": ["B650 motherboard", "B850 motherboard", "X870 motherboard", "B760 motherboard", "Z890 motherboard"]},
    {"id": "ram", "label": "RAM", "query": "ddr5 ram 32gb",
     "chips": ["DDR5 32GB 6000MHz", "DDR5 16GB", "DDR4 16GB 3200MHz", "Corsair Vengeance DDR5"]},
    {"id": "ssd", "label": "Storage", "query": "nvme ssd 1tb",
     "chips": ["Samsung 990 Pro", "WD Black SN850X", "Crucial P3 Plus", "NVMe SSD 2TB"]},
    {"id": "monitor", "label": "Monitors", "query": "gaming monitor 27 inch",
     "chips": ["27 inch 1440p 165Hz monitor", "24 inch 144Hz monitor", "4K gaming monitor", "OLED gaming monitor"]},
    {"id": "laptop", "label": "Gaming Laptops", "query": "gaming laptop rtx",
     "chips": ["RTX 5050 laptop", "RTX 5060 laptop", "ASUS TUF gaming laptop", "Lenovo LOQ"]},
    {"id": "keyboard", "label": "Keyboards", "query": "mechanical gaming keyboard",
     "chips": ["Keychron K2", "Razer BlackWidow", "Logitech G Pro X keyboard", "Cosmic Byte keyboard"]},
    {"id": "mouse", "label": "Mice", "query": "gaming mouse",
     "chips": ["Logitech G502 X", "G Pro X Superlight 2", "Razer DeathAdder V3", "Logitech G304"]},
    {"id": "headset", "label": "Headsets", "query": "gaming headset",
     "chips": ["HyperX Cloud III", "SteelSeries Arctis Nova", "Logitech G435", "Razer BlackShark V2"]},
    {"id": "controller", "label": "Controllers", "query": "gaming controller",
     "chips": ["DualSense controller", "Xbox wireless controller", "8BitDo controller", "Cosmic Byte controller"]},
    {"id": "psu", "label": "Power Supplies", "query": "power supply 750w",
     "chips": ["650W power supply", "750W gold power supply", "850W power supply"]},
    {"id": "case", "label": "Cabinets", "query": "gaming cabinet",
     "chips": ["Lian Li cabinet", "NZXT H5", "Ant Esports cabinet", "Deepcool cabinet"]},
    {"id": "chair", "label": "Gaming Chairs", "query": "gaming chair", "chips": ["Green Soul chair", "Cellbell chair"]},
]

TRENDING = [
    "PS5 Slim", "RTX 5070", "Ryzen 7 9800X3D", "Nintendo Switch 2", "Logitech G502 X",
    "Samsung 990 Pro 2TB", "HyperX Cloud III", "RTX 5060 Ti", "DualSense controller", "Xbox Series X",
]

# (query, category) pairs scanned for the Best Offers page
DEAL_QUERIES = [
    ("ps5 console", "consoles"),
    ("nintendo switch 2", "consoles"),
    ("rtx 5060", "gpu"),
    ("rtx 5070", "gpu"),
    ("ryzen 7 9800x3d", "cpu"),
    ("ryzen 5 7600", "cpu"),
    ("gaming mouse logitech", "mouse"),
    ("gaming headset", "headset"),
    ("gaming monitor 27 inch", "monitor"),
    ("mechanical keyboard", "keyboard"),
    ("nvme ssd 1tb", "ssd"),
    ("ddr5 ram 32gb", "ram"),
    ("dualsense controller", "controller"),
]
