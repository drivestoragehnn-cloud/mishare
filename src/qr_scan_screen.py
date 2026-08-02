"""
qr_scan_screen.py
اسکرین اسکن QR کد با استفاده از دوربین (Camera Kivy) + pyzbar برای رمزگشایی.
اگه pyzbar در دسترس نبود (مثلا موقع تست دسکتاپ)، حالت "وارد کردن دستی کد" فعال میشه.
"""

from kivy.clock import Clock
from kivy.uix.camera import Camera
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.textfield import MDTextField

try:
    from pyzbar.pyzbar import decode as zbar_decode
    from PIL import Image as PILImage
    PYZBAR_AVAILABLE = True
except Exception:
    PYZBAR_AVAILABLE = False

from qr_utils import parse_qr_payload


class QRScanScreen(MDScreen):
    name = 'qr_scan'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.on_result_callback = None
        self.camera = None
        self._scan_event = None
        self._build_ui()

    def _build_ui(self):
        root = MDBoxLayout(orientation='vertical', padding='16dp', spacing='12dp')

        title = MDLabel(
            text='دوربین رو روی QR کد گوشی مقابل بگیر',
            halign='center', font_style='H6', size_hint_y=None, height='48dp'
        )
        root.add_widget(title)

        if PYZBAR_AVAILABLE:
            try:
                self.camera = Camera(play=True, resolution=(640, 480))
                root.add_widget(self.camera)
            except Exception:
                self.camera = None

        if not self.camera:
            note = MDLabel(
                text='دوربین در دسترس نیست (یا در حال تست دسکتاپ هستی).\nکد رو دستی وارد کن:',
                halign='center'
            )
            root.add_widget(note)
            self.manual_input = MDTextField(hint_text='کد دستگاه مقابل', size_hint_y=None, height='48dp')
            root.add_widget(self.manual_input)
            btn = MDRaisedButton(text='تایید کد دستی', pos_hint={'center_x': 0.5})
            btn.bind(on_release=self._submit_manual)
            root.add_widget(btn)

        back_btn = MDFlatButton(text='بازگشت', pos_hint={'center_x': 0.5})
        back_btn.bind(on_release=self._go_back)
        root.add_widget(back_btn)

        self.add_widget(root)

    def on_enter(self):
        if self.camera and PYZBAR_AVAILABLE:
            self._scan_event = Clock.schedule_interval(self._try_decode_frame, 0.7)

    def on_leave(self):
        if self._scan_event:
            self._scan_event.cancel()
            self._scan_event = None

    def _try_decode_frame(self, _dt):
        if not self.camera or not self.camera.texture:
            return
        try:
            texture = self.camera.texture
            size = texture.size
            pixels = texture.pixels
            img = PILImage.frombytes(mode='RGBA', size=size, data=pixels)
            results = zbar_decode(img)
            for r in results:
                text = r.data.decode('utf-8')
                payload = parse_qr_payload(text)
                if payload:
                    self._finish(payload)
                    return
        except Exception as e:
            print('QR decode error:', e)

    def _submit_manual(self, *_):
        text = self.manual_input.text.strip()
        payload = parse_qr_payload(text)
        if payload:
            self._finish(payload)
        else:
            self.manual_input.error = True

    def _finish(self, payload):
        if self._scan_event:
            self._scan_event.cancel()
        if self.on_result_callback:
            self.on_result_callback(payload)

    def _go_back(self, *_):
        from kivymd.app import MDApp
        MDApp.get_running_app().root.current = 'connect'
