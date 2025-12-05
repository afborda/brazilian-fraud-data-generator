"""
Configuration module for device types and manufacturers.
"""

# Device types with realistic distribution
DEVICE_TYPES = {
    'SMARTPHONE_ANDROID': 55,
    'SMARTPHONE_IOS': 25,
    'DESKTOP_WINDOWS': 12,
    'DESKTOP_MAC': 4,
    'TABLET_ANDROID': 2,
    'TABLET_IOS': 2,
}

DEVICE_TYPES_LIST = list(DEVICE_TYPES.keys())
DEVICE_TYPES_WEIGHTS = list(DEVICE_TYPES.values())

# Device manufacturers by device type
DEVICE_MANUFACTURERS = {
    'SMARTPHONE_ANDROID': [
        'Samsung', 'Motorola', 'Xiaomi', 'LG', 'ASUS', 'Realme', 'POCO', 'OnePlus',
        'TCL', 'Nokia', 'Huawei', 'Honor', 'Google', 'Nothing', 'Sony'
    ],
    'SMARTPHONE_IOS': ['Apple'],
    'DESKTOP_WINDOWS': [
        'Dell', 'HP', 'Lenovo', 'ASUS', 'Acer', 'Positivo', 'Samsung', 'MSI',
        'Vaio', 'Avell', 'Multilaser'
    ],
    'DESKTOP_MAC': ['Apple'],
    'TABLET_ANDROID': [
        'Samsung', 'Xiaomi', 'Lenovo', 'Multilaser', 'TCL', 'Nokia', 'Huawei', 'Positivo'
    ],
    'TABLET_IOS': ['Apple'],
}

# Device models by manufacturer
DEVICE_MODELS = {
    'Samsung': [
        'Galaxy S24', 'Galaxy S24 Ultra', 'Galaxy S23', 'Galaxy A55', 'Galaxy A35',
        'Galaxy M55', 'Galaxy Z Fold 5', 'Galaxy Z Flip 5', 'Galaxy Tab S9',
        'Galaxy A15', 'Galaxy A25', 'Galaxy S23 FE', 'Galaxy A54'
    ],
    'Motorola': [
        'Edge 50', 'Edge 40', 'G84', 'G54', 'Razr 40', 'ThinkPhone', 'Moto G Stylus',
        'Moto G Power', 'Moto G Play', 'Edge 50 Pro', 'G34'
    ],
    'Xiaomi': [
        'Xiaomi 14', 'Redmi Note 13', 'Redmi 13C', 'POCO X6', 'Mi 14',
        'Redmi Note 12', 'Xiaomi Pad 6', 'Redmi 13', 'Xiaomi 14 Pro'
    ],
    'Apple': [
        'iPhone 16', 'iPhone 16 Pro', 'iPhone 15', 'iPhone 15 Pro', 'iPhone SE',
        'iPad Pro M4', 'iPad Air M2', 'MacBook Pro M3', 'MacBook Air M3', 'iMac M3',
        'iPhone 14', 'iPhone 13', 'iPad Mini', 'iPad 10th Gen'
    ],
    'LG': ['K62', 'K52', 'K42', 'Velvet'],
    'Dell': [
        'Inspiron 16', 'XPS 15', 'XPS 13', 'Latitude 7440', 'Vostro 3520',
        'Alienware m16', 'Latitude 5540', 'Precision 5680'
    ],
    'HP': [
        'Pavilion 15', 'Spectre x360', 'EliteBook 840', 'ProBook 450', 'Omen 16',
        'Victus 15', 'Envy x360', 'ZBook Fury'
    ],
    'Lenovo': [
        'IdeaPad Slim 5', 'ThinkPad X1 Carbon', 'Legion Pro 5', 'Yoga 9i',
        'ThinkBook 14', 'IdeaPad Gaming 3', 'ThinkPad T14'
    ],
    'ASUS': [
        'ZenBook 14', 'VivoBook 15', 'ROG Strix', 'TUF Gaming F15',
        'ProArt Studiobook', 'Zenfone 11', 'ROG Phone 8'
    ],
    'Acer': ['Aspire 5', 'Swift Go 14', 'Nitro 5', 'Predator Helios', 'Swift X'],
    'Positivo': ['Motion Q464C', 'Vision C14', 'Twist Tab', 'Motion C4128'],
    'Multilaser': ['M10 4G', 'M8 4G', 'Ultra U10', 'PC301'],
    'Realme': ['12 Pro+', 'C67', 'GT5 Pro', 'Narzo 70', '12 Pro', 'C55'],
    'POCO': ['X6 Pro', 'M6 Pro', 'F6', 'C65', 'X5 Pro'],
    'OnePlus': ['12', 'Nord 4', 'Open', '12R', 'Nord CE 4'],
    'TCL': ['40 NxtPaper', '50 SE', 'Tab 10 Gen 2', '30 5G', '50 5G'],
    'Nokia': ['G42 5G', 'C32', 'XR21', 'T21 Tablet', 'G22'],
    'Huawei': ['P60 Pro', 'Mate 60', 'Nova 12', 'MatePad Pro', 'Mate X5'],
    'Honor': ['Magic 6 Pro', '90', 'X9b', 'Pad 9', 'Magic V2'],
    'Google': ['Pixel 8', 'Pixel 8 Pro', 'Pixel 7a', 'Pixel Tablet', 'Pixel 8a'],
    'Nothing': ['Phone 2', 'Phone 2a', 'Phone 1'],
    'Sony': ['Xperia 1 V', 'Xperia 5 V', 'Xperia 10 V'],
    'MSI': ['Stealth 16', 'Raider GE78', 'Katana 15', 'Creator Z17', 'Titan GT'],
    'Vaio': ['FE 14', 'FE 15', 'SX14'],
    'Avell': ['A70', 'C65', 'Storm Two'],
}

# Operating systems by device type
OS_BY_DEVICE_TYPE = {
    'SMARTPHONE_ANDROID': ['Android 11', 'Android 12', 'Android 13', 'Android 14'],
    'SMARTPHONE_IOS': ['iOS 16', 'iOS 17', 'iOS 17.1', 'iOS 17.2', 'iOS 17.3', 'iOS 17.4'],
    'DESKTOP_WINDOWS': ['Windows 10', 'Windows 11'],
    'DESKTOP_MAC': ['macOS Sonoma', 'macOS Ventura', 'macOS Monterey'],
    'TABLET_ANDROID': ['Android 12', 'Android 13', 'Android 14'],
    'TABLET_IOS': ['iPadOS 16', 'iPadOS 17', 'iPadOS 17.1', 'iPadOS 17.2'],
}


def get_manufacturers_for_device_type(device_type: str) -> list:
    """Get list of manufacturers for a device type."""
    return DEVICE_MANUFACTURERS.get(device_type, ['Generic'])


def get_models_for_manufacturer(manufacturer: str) -> list:
    """Get list of models for a manufacturer."""
    return DEVICE_MODELS.get(manufacturer, ['Generic Model'])


def get_os_for_device_type(device_type: str) -> list:
    """Get list of operating systems for a device type."""
    return OS_BY_DEVICE_TYPE.get(device_type, ['Unknown OS'])


def get_device_category(device_type: str) -> str:
    """Get device category (SMARTPHONE, DESKTOP, TABLET) from device type."""
    return device_type.split('_')[0] if device_type else 'UNKNOWN'
