[app]
title = MIshare
package.name = mishare
package.domain = org.mishare

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

version = 1.0

requirements = python3,kivy==2.2.1,kivymd==1.2.0,pyjnius,plyer,qrcode,pillow,android

orientation = portrait
fullscreen = 0

android.permissions = ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,ACCESS_WIFI_STATE,CHANGE_WIFI_STATE,ACCESS_NETWORK_STATE,CHANGE_NETWORK_STATE,INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,NEARBY_WIFI_DEVICES,BLUETOOTH,BLUETOOTH_ADMIN,BLUETOOTH_CONNECT,BLUETOOTH_SCAN,CAMERA

android.api = 33
android.minapi = 23
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a

android.allow_backup = True
android.accept_sdk_license = True

# پین کردن یه نسخه release قدیمی‌تر از python-for-android (نه شاخه master/develop و نه آخرین ریلیز)
# چون نسخه‌های جدیدتر (از جمله آخرین ریلیز) سعی می‌کنن پایتون ۳.۱۴ رو دانلود کنن که ماژول
# remote_debugging ش روی اندروید کامپایل نمیشه (باگ شناخته‌شده در p4a).
# این نسخه (ژانویه ۲۰۲۴) مال قبل از عرضه پایتون ۳.۱۴ هست و پایتون ۳.۱۱ رو استفاده می‌کنه.
p4a.branch = v2024.01.21

[buildozer]
log_level = 2
warn_on_root = 1
