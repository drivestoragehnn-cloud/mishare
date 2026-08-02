"""
bluetooth_manager.py
لایه ارتباط با Android BluetoothAdapter از طریق pyjnius.
مسئول: روشن بودن بلوتوث، لیست گوشی‌های جفت‌شده (paired)، و اسکن گوشی‌های جدید.
"""

from jnius import autoclass, PythonJavaClass, java_method

BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
PythonActivity = autoclass('org.kivy.android.PythonActivity')


class BluetoothManager:
    def __init__(self):
        self.adapter = BluetoothAdapter.getDefaultAdapter()

    def is_supported(self):
        return self.adapter is not None

    def is_enabled(self):
        if not self.adapter:
            return False
        return self.adapter.isEnabled()

    def request_enable(self):
        """باز کردن دیالوگ سیستمی برای روشن کردن بلوتوث"""
        Intent = autoclass('android.content.Intent')
        activity = PythonActivity.mActivity
        intent = Intent(BluetoothAdapter.ACTION_REQUEST_ENABLE)
        activity.startActivityForResult(intent, 1)

    def get_paired_devices(self):
        """لیست گوشی‌هایی که قبلا جفت (pair) شده‌اند"""
        if not self.adapter or not self.adapter.isEnabled():
            return []
        devices = self.adapter.getBondedDevices().toArray()
        result = []
        for d in devices:
            result.append({'name': d.getName(), 'address': d.getAddress()})
        return result

    def start_discovery(self):
        """شروع اسکن گوشی‌های جدید (نتیجه از طریق BroadcastReceiver میاد - ساده‌سازی شده)"""
        if self.adapter and self.adapter.isEnabled():
            self.adapter.startDiscovery()

    def cancel_discovery(self):
        if self.adapter:
            self.adapter.cancelDiscovery()
