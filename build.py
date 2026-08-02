#!/usr/bin/env python3
"""
build.py
اسکریپت خودکار بیلد اپلیکیشن اندروید.
این اسکریپت رو روی سیستم خودت (لینوکس/WSL/مک با دسترسی کامل اینترنت) اجرا کن.

کاری که انجام میده:
  ۱. چک می‌کنه Python3، pip، Java (JDK 17+)، و ابزارهای سیستمی لازم نصب باشن
  ۲. Buildozer و Cython رو نصب می‌کنه
  ۳. buildozer android debug رو اجرا می‌کنه که خودش SDK/NDK اندروید رو
     (اگه از قبل نصب نباشه) دانلود و نصب می‌کنه
  ۴. فایل APK نهایی رو در پوشه bin/ قرار میده و مسیرش رو نشون میده

اجرا: python3 build.py
"""

import os
import platform
import shutil
import subprocess
import sys

PROJECT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')

SYSTEM_PACKAGES_UBUNTU = [
    'git', 'zip', 'unzip', 'openjdk-17-jdk', 'python3-pip',
    'autoconf', 'libtool', 'pkg-config', 'zlib1g-dev',
    'libncurses5-dev', 'libncursesw5-dev', 'libtinfo5',
    'cmake', 'libffi-dev', 'libssl-dev',
]


def run(cmd, cwd=None, check=True):
    print(f"\n$ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd)
    if check and result.returncode != 0:
        print(f"❌ دستور با خطا مواجه شد: {' '.join(cmd)}")
        sys.exit(result.returncode)
    return result.returncode


def check_command(name):
    return shutil.which(name) is not None


def install_system_packages():
    system = platform.system()
    if system != 'Linux':
        print(f"⚠️  سیستم‌عامل شما {system} است. نصب خودکار پکیج‌های سیستمی فقط روی "
              "Linux (Ubuntu/Debian) پشتیبانی میشه. لطفاً مطمئن شو Java 17+، "
              "git، zip/unzip، و ابزارهای بیلد C از قبل نصب هستن.")
        return

    if not check_command('apt-get'):
        print("⚠️  apt-get پیدا نشد؛ لطفاً پکیج‌های لازم رو خودت با پکیج‌منیجر سیستمت نصب کن.")
        return

    print("📦 در حال نصب پکیج‌های سیستمی مورد نیاز (نیاز به sudo)...")
    run(['sudo', 'apt-get', 'update'])
    run(['sudo', 'apt-get', 'install', '-y'] + SYSTEM_PACKAGES_UBUNTU)


def install_python_packages():
    print("🐍 در حال نصب Buildozer و ابزارهای پایتونی...")
    run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
    run([sys.executable, '-m', 'pip', 'install', '--upgrade',
         'buildozer', 'cython==0.29.36', 'virtualenv'])


def build_apk(release=False):
    print("🔨 در حال بیلد APK (اولین بار ممکنه SDK/NDK دانلود بشه و طول بکشه)...")
    target = 'android release' if release else 'android debug'
    run(['buildozer'] + target.split(), cwd=PROJECT_DIR)

    bin_dir = os.path.join(PROJECT_DIR, 'bin')
    if os.path.isdir(bin_dir):
        apks = [f for f in os.listdir(bin_dir) if f.endswith('.apk')]
        if apks:
            print("\n✅ بیلد با موفقیت انجام شد. فایل‌های APK:")
            for apk in apks:
                print(f"   {os.path.join(bin_dir, apk)}")
            return
    print("⚠️  بیلد تمام شد ولی فایل APK پیدا نشد؛ لاگ بالا رو چک کن.")


def main():
    print("=== اسکریپت خودکار بیلد اپ انتقال فایل ===\n")

    skip_system = '--skip-system' in sys.argv
    release = '--release' in sys.argv

    if not skip_system:
        install_system_packages()
    else:
        print("⏭️  نصب پکیج‌های سیستمی رد شد (--skip-system)")

    install_python_packages()
    build_apk(release=release)


if __name__ == '__main__':
    main()
