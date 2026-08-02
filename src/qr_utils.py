"""
qr_utils.py
تولید QR کد (برای گیرنده که آدرسش رو نشون بده) و رمزگشایی QR اسکن‌شده (برای فرستنده).
فرمت داده داخل QR: "FASTSHARE|<mac_or_ip>|<device_name>"
"""

import os
import qrcode

QR_PREFIX = "FASTSHARE"


def generate_qr_image(payload_address, device_name, save_path):
    """یک تصویر QR کد می‌سازه و در save_path ذخیره می‌کنه، مسیر فایل رو برمی‌گردونه"""
    data = f"{QR_PREFIX}|{payload_address}|{device_name}"
    img = qrcode.make(data)
    img.save(save_path)
    return save_path


def parse_qr_payload(text):
    """
    متن خوانده‌شده از QR رو پارس می‌کنه.
    خروجی: dict {'address': ..., 'name': ...} یا None اگه فرمت درست نبود
    """
    try:
        prefix, address, name = text.split('|', 2)
        if prefix != QR_PREFIX:
            return None
        return {'address': address, 'name': name}
    except Exception:
        return None
