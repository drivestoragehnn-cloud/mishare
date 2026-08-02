"""
main.py
اپلیکیشن انتقال سریع فایل - Material Design 3 (آبی و سفید، کلاسیک گوگل)

جریان کار:
HomeScreen (ارسال/دریافت)
  -> PermissionScreen (چک بلوتوث/موقعیت/وای‌فای، دکمه روشن کردن)
    -> ConnectScreen (انتخاب QR یا بلوتوث)
      -> QRScanScreen / BluetoothListScreen
        -> SendTypeScreen (اپ/مدیا/فایل) [فقط مسیر ارسال]
          -> FilePickScreen
            -> TransferScreen (پیشرفت زنده)
              -> HistoryScreen
"""

import os
from datetime import datetime

from kivy.clock import Clock
from kivy.properties import StringProperty, NumericProperty
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivy.storage.jsonstore import JsonStore

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.list import MDList, OneLineIconListItem, IconLeftWidget
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.toolbar import MDTopAppBar

IS_ANDROID = os.environ.get('ANDROID_ARGUMENT') is not None

if IS_ANDROID:
    from wifidirect import WifiDirectManager
    from bluetooth_manager import BluetoothManager
    import transfer
else:
    WifiDirectManager = None
    BluetoothManager = None
    transfer = None

from qr_utils import generate_qr_image
from qr_scan_screen import QRScanScreen

HISTORY_FILE = 'transfer_history.json'
GOOGLE_BLUE = (0.259, 0.522, 0.957, 1)   # #4285F4
GOOGLE_BLUE_DARK = (0.10, 0.32, 0.85, 1)
WHITE = (1, 1, 1, 1)
LIGHT_BG = (0.97, 0.98, 1, 1)


# ---------------------------------------------------------------------------
# HOME
# ---------------------------------------------------------------------------
class HomeScreen(MDScreen):
    name = 'home'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.md_bg_color = LIGHT_BG
        root = MDBoxLayout(orientation='vertical')

        toolbar = MDTopAppBar(
            title='MIshare',
            elevation=0,
            md_bg_color=WHITE,
            specific_text_color=(0.1, 0.1, 0.1, 1),
        )
        root.add_widget(toolbar)

        body = MDBoxLayout(orientation='vertical', padding='24dp', spacing='20dp')

        logo_card = MDCard(
            size_hint=(1, None), height='140dp',
            radius=[24, 24, 24, 24], md_bg_color=GOOGLE_BLUE,
            padding='16dp',
        )
        logo_box = MDBoxLayout(orientation='vertical')
        logo_box.add_widget(MDLabel(
            text='⚡ سرعت واقعی، بدون اینترنت',
            theme_text_color='Custom', text_color=WHITE,
            font_style='H5', halign='center', bold=True
        ))
        logo_box.add_widget(MDLabel(
            text='با Wi-Fi Direct، صدها برابر سریع‌تر از بلوتوث',
            theme_text_color='Custom', text_color=WHITE,
            font_style='Subtitle1', halign='center'
        ))
        logo_card.add_widget(logo_box)
        body.add_widget(logo_card)

        buttons_row = MDBoxLayout(orientation='horizontal', spacing='16dp', size_hint_y=None, height='160dp')

        send_card = self._action_card('ارسال', 'send', 'export')
        recv_card = self._action_card('دریافت', 'receive', 'import')
        buttons_row.add_widget(send_card)
        buttons_row.add_widget(recv_card)
        body.add_widget(buttons_row)

        body.add_widget(MDBoxLayout())  # spacer

        bottom_row = MDBoxLayout(orientation='horizontal', spacing='12dp', size_hint_y=None, height='56dp')
        history_btn = MDFlatButton(text='تاریخچه', on_release=lambda _: self.goto('history'))
        bottom_row.add_widget(history_btn)
        body.add_widget(bottom_row)

        root.add_widget(body)
        self.add_widget(root)

    def _action_card(self, label, mode, icon):
        card = MDCard(
            orientation='vertical', radius=[20, 20, 20, 20],
            md_bg_color=WHITE, elevation=3, padding='12dp', ripple_behavior=True,
        )
        card.bind(on_release=lambda *_: self.start_flow(mode))
        icon_btn = MDIconButton(icon=icon, theme_text_color='Custom',
                                 text_color=GOOGLE_BLUE, icon_size='48dp',
                                 pos_hint={'center_x': 0.5})
        card.add_widget(icon_btn)
        card.add_widget(MDLabel(text=label, halign='center', bold=True,
                                 theme_text_color='Custom', text_color=(0.1, 0.1, 0.1, 1)))
        return card

    def start_flow(self, mode):
        app = MDApp.get_running_app()
        app.flow_mode = mode  # 'send' یا 'receive'
        self.goto('permissions')

    def goto(self, screen_name):
        self.manager.current = screen_name


# ---------------------------------------------------------------------------
# PERMISSIONS
# ---------------------------------------------------------------------------
class PermissionScreen(MDScreen):
    name = 'permissions'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.md_bg_color = LIGHT_BG
        self.status_labels = {}
        self._build()

    def _build(self):
        root = MDBoxLayout(orientation='vertical')
        root.add_widget(MDTopAppBar(title='آماده‌سازی', elevation=0,
                                     md_bg_color=WHITE, specific_text_color=(0.1, 0.1, 0.1, 1)))
        body = MDBoxLayout(orientation='vertical', padding='24dp', spacing='16dp')
        body.add_widget(MDLabel(
            text='قبل از اتصال، این موارد رو روشن کن:',
            font_style='H6', size_hint_y=None, height='40dp'
        ))

        self.checklist = MDList()
        for key, label in [('bluetooth', 'بلوتوث'), ('location', 'دسترسی موقعیت مکانی'), ('wifi', 'وای‌فای')]:
            item = OneLineIconListItem(text=f'{label}: در حال بررسی...')
            icon = IconLeftWidget(icon='progress-clock')
            item.add_widget(icon)
            self.status_labels[key] = (item, icon)
            self.checklist.add_widget(item)
        body.add_widget(self.checklist)

        btn_row = MDBoxLayout(orientation='horizontal', spacing='12dp', size_hint_y=None, height='56dp')
        enable_btn = MDRaisedButton(text='روشن کردن همه', md_bg_color=GOOGLE_BLUE)
        enable_btn.bind(on_release=self.enable_all)
        continue_btn = MDRaisedButton(text='ادامه', md_bg_color=GOOGLE_BLUE_DARK)
        continue_btn.bind(on_release=lambda _: self.goto_connect())
        btn_row.add_widget(enable_btn)
        btn_row.add_widget(continue_btn)
        body.add_widget(btn_row)

        back_btn = MDFlatButton(text='بازگشت', pos_hint={'center_x': 0.5})
        back_btn.bind(on_release=lambda _: setattr(self.manager, 'current', 'home'))
        body.add_widget(back_btn)

        root.add_widget(body)
        self.add_widget(root)

    def on_enter(self):
        self.refresh_status()

    def refresh_status(self):
        app = MDApp.get_running_app()
        bt_ok = wifi_ok = loc_ok = False
        if IS_ANDROID and app.bt_manager:
            bt_ok = app.bt_manager.is_enabled()
        if IS_ANDROID:
            loc_ok = getattr(app, 'location_granted', False)
            wifi_ok = True

        self._set_status('bluetooth', 'بلوتوث', bt_ok if IS_ANDROID else True)
        self._set_status('location', 'دسترسی موقعیت مکانی', loc_ok if IS_ANDROID else True)
        self._set_status('wifi', 'وای‌فای', wifi_ok if IS_ANDROID else True)

    def _set_status(self, key, label, ok):
        item, icon = self.status_labels[key]
        item.text = f"{label}: {'روشن ✅' if ok else 'خاموش ❌'}"
        icon.icon = 'check-circle' if ok else 'alert-circle'
        icon.theme_text_color = 'Custom'
        icon.text_color = (0.2, 0.7, 0.3, 1) if ok else (0.9, 0.3, 0.2, 1)

    def enable_all(self, *_):
        app = MDApp.get_running_app()
        if IS_ANDROID:
            if app.bt_manager and not app.bt_manager.is_enabled():
                app.bt_manager.request_enable()
            if app.wifi_manager:
                app.wifi_manager.request_permissions(lambda perms, grants: self._on_perm_result(grants))
            else:
                from android.permissions import request_permissions, Permission
                request_permissions(
                    [Permission.ACCESS_FINE_LOCATION, Permission.ACCESS_COARSE_LOCATION,
                     Permission.CAMERA, Permission.BLUETOOTH_CONNECT if hasattr(Permission, 'BLUETOOTH_CONNECT') else Permission.ACCESS_FINE_LOCATION],
                    lambda perms, grants: self._on_perm_result(grants)
                )
        Clock.schedule_once(lambda _dt: self.refresh_status(), 1.5)

    def _on_perm_result(self, grants):
        app = MDApp.get_running_app()
        app.location_granted = all(grants) if grants else False
        Clock.schedule_once(lambda _dt: self.refresh_status(), 0.5)

    def goto_connect(self):
        self.manager.current = 'connect'


# ---------------------------------------------------------------------------
# CONNECT (انتخاب QR یا بلوتوث)
# ---------------------------------------------------------------------------
class ConnectScreen(MDScreen):
    name = 'connect'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.md_bg_color = LIGHT_BG
        self._build()

    def _build(self):
        root = MDBoxLayout(orientation='vertical')
        root.add_widget(MDTopAppBar(title='اتصال به گوشی مقابل', elevation=0,
                                     md_bg_color=WHITE, specific_text_color=(0.1, 0.1, 0.1, 1)))
        body = MDBoxLayout(orientation='vertical', padding='24dp', spacing='20dp')
        body.add_widget(MDLabel(text='چطور می‌خوای وصل بشی؟', font_style='H6',
                                 size_hint_y=None, height='40dp'))

        row = MDBoxLayout(orientation='horizontal', spacing='16dp', size_hint_y=None, height='150dp')

        qr_card = MDCard(orientation='vertical', radius=[20]*4, md_bg_color=WHITE,
                          elevation=3, padding='12dp', ripple_behavior=True)
        qr_card.bind(on_release=lambda *_: self.choose_qr())
        qr_card.add_widget(MDIconButton(icon='qrcode-scan', icon_size='44dp',
                                         theme_text_color='Custom', text_color=GOOGLE_BLUE,
                                         pos_hint={'center_x': 0.5}))
        qr_card.add_widget(MDLabel(text='با QR کد', halign='center', bold=True))
        row.add_widget(qr_card)

        bt_card = MDCard(orientation='vertical', radius=[20]*4, md_bg_color=WHITE,
                          elevation=3, padding='12dp', ripple_behavior=True)
        bt_card.bind(on_release=lambda *_: self.choose_bluetooth())
        bt_card.add_widget(MDIconButton(icon='bluetooth', icon_size='44dp',
                                         theme_text_color='Custom', text_color=GOOGLE_BLUE,
                                         pos_hint={'center_x': 0.5}))
        bt_card.add_widget(MDLabel(text='با بلوتوث', halign='center', bold=True))
        row.add_widget(bt_card)

        body.add_widget(row)

        self.status_label = MDLabel(text='', halign='center')
        body.add_widget(self.status_label)

        back_btn = MDFlatButton(text='بازگشت', pos_hint={'center_x': 0.5})
        back_btn.bind(on_release=lambda _: setattr(self.manager, 'current', 'permissions'))
        body.add_widget(back_btn)

        root.add_widget(body)
        self.add_widget(root)

    def choose_qr(self):
        app = MDApp.get_running_app()
        if app.flow_mode == 'receive':
            path = os.path.join(app.user_data_dir, 'my_qr.png')
            my_address = getattr(app, 'my_wifi_address', '192.168.49.1')
            generate_qr_image(my_address, 'MyPhone', path)
            self.manager.get_screen('qr_show').set_image(path)
            self.manager.current = 'qr_show'
        else:
            self.manager.current = 'qr_scan'

    def choose_bluetooth(self):
        self.manager.current = 'bt_list'


class QRShowScreen(MDScreen):
    name = 'qr_show'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.md_bg_color = LIGHT_BG
        self.image_path = None
        self._build()

    def _build(self):
        from kivy.uix.image import Image
        root = MDBoxLayout(orientation='vertical')
        root.add_widget(MDTopAppBar(title='این کد رو نشون بده', elevation=0,
                                     md_bg_color=WHITE, specific_text_color=(0.1, 0.1, 0.1, 1)))
        body = MDBoxLayout(orientation='vertical', padding='24dp', spacing='16dp')
        body.add_widget(MDLabel(text='بذار طرف مقابل این QR رو با دوربینش اسکن کنه',
                                 halign='center', size_hint_y=None, height='40dp'))
        self.img_widget = Image(size_hint=(1, 1))
        body.add_widget(self.img_widget)

        wait_row = MDBoxLayout(orientation='horizontal', spacing='12dp', size_hint_y=None, height='56dp')
        continue_btn = MDRaisedButton(text='وصل شدم، ادامه', md_bg_color=GOOGLE_BLUE)
        continue_btn.bind(on_release=self._continue)
        wait_row.add_widget(continue_btn)
        body.add_widget(wait_row)

        back_btn = MDFlatButton(text='بازگشت', pos_hint={'center_x': 0.5})
        back_btn.bind(on_release=lambda _: setattr(self.manager, 'current', 'connect'))
        body.add_widget(back_btn)

        root.add_widget(body)
        self.add_widget(root)

    def set_image(self, path):
        self.image_path = path
        self.img_widget.source = path
        self.img_widget.reload()

    def _continue(self, *_):
        app = MDApp.get_running_app()
        if app.flow_mode == 'receive':
            self.manager.current = 'transfer'
            self.manager.get_screen('transfer').start_receiving()


class BluetoothListScreen(MDScreen):
    name = 'bt_list'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.md_bg_color = LIGHT_BG
        self._build()

    def _build(self):
        root = MDBoxLayout(orientation='vertical')
        root.add_widget(MDTopAppBar(title='گوشی‌های بلوتوث', elevation=0,
                                     md_bg_color=WHITE, specific_text_color=(0.1, 0.1, 0.1, 1),
                                     right_action_items=[['refresh', lambda x: self.refresh()]]))
        body = MDBoxLayout(orientation='vertical', padding='16dp', spacing='12dp')
        self.device_list = MDList()
        body.add_widget(self.device_list)
        back_btn = MDFlatButton(text='بازگشت', pos_hint={'center_x': 0.5})
        back_btn.bind(on_release=lambda _: setattr(self.manager, 'current', 'connect'))
        body.add_widget(back_btn)
        root.add_widget(body)
        self.add_widget(root)

    def on_enter(self):
        self.refresh()

    def refresh(self):
        self.device_list.clear_widgets()
        app = MDApp.get_running_app()
        if IS_ANDROID and app.bt_manager:
            devices = app.bt_manager.get_paired_devices()
        else:
            devices = [{'name': 'گوشی تستی ۱', 'address': '00:11:22:33:44:55'},
                       {'name': 'گوشی تستی ۲', 'address': '66:77:88:99:AA:BB'}]
        if not devices:
            self.device_list.add_widget(OneLineIconListItem(text='گوشی جفت‌شده‌ای پیدا نشد'))
            return
        for d in devices:
            item = OneLineIconListItem(text=f"{d['name']} ({d['address']})")
            item.bind(on_release=lambda inst, dev=d: self._select(dev))
            item.add_widget(IconLeftWidget(icon='cellphone'))
            self.device_list.add_widget(item)

    def _select(self, device):
        app = MDApp.get_running_app()
        app.connected_peer_ip = device.get('address')
        if app.flow_mode == 'send':
            self.manager.current = 'send_type'
        else:
            self.manager.current = 'transfer'
            self.manager.get_screen('transfer').start_receiving()


# ---------------------------------------------------------------------------
# SEND TYPE (اپ / مدیا / فایل)
# ---------------------------------------------------------------------------
class SendTypeScreen(MDScreen):
    name = 'send_type'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.md_bg_color = LIGHT_BG
        self._build()

    def _build(self):
        root = MDBoxLayout(orientation='vertical')
        root.add_widget(MDTopAppBar(title='چی می‌فرستی؟', elevation=0,
                                     md_bg_color=WHITE, specific_text_color=(0.1, 0.1, 0.1, 1)))
        body = MDBoxLayout(orientation='vertical', padding='24dp', spacing='20dp')

        grid = MDGridLayout(cols=3, spacing='12dp', size_hint_y=None, height='140dp')
        for label, icon, kind in [
            ('اپلیکیشن', 'android', 'app'),
            ('مدیا', 'image-multiple', 'media'),
            ('فایل', 'file-document', 'file'),
        ]:
            card = MDCard(orientation='vertical', radius=[16]*4, md_bg_color=WHITE,
                           elevation=3, padding='8dp', ripple_behavior=True)
            card.bind(on_release=lambda *_, k=kind: self.choose(k))
            card.add_widget(MDIconButton(icon=icon, icon_size='36dp',
                                          theme_text_color='Custom', text_color=GOOGLE_BLUE,
                                          pos_hint={'center_x': 0.5}))
            card.add_widget(MDLabel(text=label, halign='center'))
            grid.add_widget(card)
        body.add_widget(grid)

        back_btn = MDFlatButton(text='بازگشت', pos_hint={'center_x': 0.5})
        back_btn.bind(on_release=lambda _: setattr(self.manager, 'current', 'connect'))
        body.add_widget(back_btn)

        root.add_widget(body)
        self.add_widget(root)

    def choose(self, kind):
        app = MDApp.get_running_app()
        app.send_kind = kind
        self.manager.current = 'file_pick'


# ---------------------------------------------------------------------------
# FILE PICK
# ---------------------------------------------------------------------------
class FilePickScreen(MDScreen):
    name = 'file_pick'

    EXT_MAP = {
        'app': ['*.apk'],
        'media': ['*.jpg', '*.jpeg', '*.png', '*.mp4', '*.mp3', '*.mkv', '*.gif'],
        'file': ['*.*'],
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.md_bg_color = LIGHT_BG
        self.chooser = None
        self._build()

    def _build(self):
        self.root_box = MDBoxLayout(orientation='vertical')
        self.root_box.add_widget(MDTopAppBar(title='انتخاب فایل', elevation=0,
                                              md_bg_color=WHITE, specific_text_color=(0.1, 0.1, 0.1, 1)))
        self.body = MDBoxLayout(orientation='vertical', padding='12dp', spacing='12dp')
        self.root_box.add_widget(self.body)
        self.add_widget(self.root_box)

    def on_enter(self):
        app = MDApp.get_running_app()
        self.body.clear_widgets()
        filters = self.EXT_MAP.get(getattr(app, 'send_kind', 'file'), ['*.*'])
        self.chooser = FileChooserListView(path=os.path.expanduser('~'), filters=filters,
                                            multiselect=True)
        self.body.add_widget(self.chooser)

        btn_row = MDBoxLayout(orientation='horizontal', spacing='12dp', size_hint_y=None, height='56dp')
        send_btn = MDRaisedButton(text='ارسال', md_bg_color=GOOGLE_BLUE)
        send_btn.bind(on_release=self._send)
        back_btn = MDFlatButton(text='بازگشت')
        back_btn.bind(on_release=lambda _: setattr(self.manager, 'current', 'send_type'))
        btn_row.add_widget(back_btn)
        btn_row.add_widget(send_btn)
        self.body.add_widget(btn_row)

    def _send(self, *_):
        if not self.chooser or not self.chooser.selection:
            return
        self.manager.current = 'transfer'
        self.manager.get_screen('transfer').start_sending(self.chooser.selection)


# ---------------------------------------------------------------------------
# TRANSFER (پیشرفت زنده)
# ---------------------------------------------------------------------------
class TransferScreen(MDScreen):
    name = 'transfer'
    current_filename = StringProperty('در انتظار...')
    progress_value = NumericProperty(0)
    speed_text = StringProperty('0.0 Mbps')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.md_bg_color = LIGHT_BG
        self._build()

    def _build(self):
        root = MDBoxLayout(orientation='vertical')
        root.add_widget(MDTopAppBar(title='در حال انتقال', elevation=0,
                                     md_bg_color=WHITE, specific_text_color=(0.1, 0.1, 0.1, 1)))
        body = MDBoxLayout(orientation='vertical', padding='24dp', spacing='16dp')

        self.filename_label = MDLabel(text=self.current_filename, halign='center',
                                       size_hint_y=None, height='40dp')
        body.add_widget(self.filename_label)

        self.progress_bar = MDProgressBar(value=0, size_hint_y=None, height='12dp')
        body.add_widget(self.progress_bar)

        self.speed_label = MDLabel(text=self.speed_text, halign='center',
                                    size_hint_y=None, height='30dp')
        body.add_widget(self.speed_label)

        body.add_widget(MDBoxLayout())  # spacer

        back_btn = MDFlatButton(text='بازگشت به خانه', pos_hint={'center_x': 0.5})
        back_btn.bind(on_release=lambda _: setattr(self.manager, 'current', 'home'))
        body.add_widget(back_btn)

        root.add_widget(body)
        self.add_widget(root)

        self.bind(current_filename=lambda _, v: setattr(self.filename_label, 'text', v))
        self.bind(progress_value=lambda _, v: setattr(self.progress_bar, 'value', v))
        self.bind(speed_text=lambda _, v: setattr(self.speed_label, 'text', v))

    def start_sending(self, paths):
        app = MDApp.get_running_app()
        target_ip = getattr(app, 'connected_peer_ip', '192.168.49.1')

        def progress(filename, sent, total, speed):
            def upd(_dt):
                self.current_filename = filename
                self.progress_value = (sent / total) * 100
                self.speed_text = f'{speed:.1f} Mbps'
            Clock.schedule_once(upd)

        def done(success, message):
            def fin(_dt):
                app.add_history_entry(paths, success, message)
                self.manager.current = 'history'
            Clock.schedule_once(fin)

        if IS_ANDROID:
            transfer.send_files(target_ip, paths, progress, done)
        else:
            print(f"[شبیه‌سازی دسکتاپ] ارسال به {target_ip}: {paths}")
            Clock.schedule_once(lambda _dt: done(True, 'شبیه‌سازی موفق'), 1)

    def start_receiving(self):
        app = MDApp.get_running_app()
        save_dir = os.path.join(app.user_data_dir, 'received')
        self.current_filename = 'در انتظار دریافت فایل...'

        def progress(filename, received, total, speed):
            def upd(_dt):
                self.current_filename = filename
                self.progress_value = (received / total) * 100
                self.speed_text = f'{speed:.1f} Mbps'
            Clock.schedule_once(upd)

        def file_received(filepath):
            print('فایل دریافت شد:', filepath)

        def done(success, message):
            def fin(_dt):
                app.add_history_entry(['فایل دریافتی'], success, message)
                self.manager.current = 'history'
            Clock.schedule_once(fin)

        if IS_ANDROID:
            transfer.receive_files(save_dir, progress, done, file_received)
        else:
            print(f"[شبیه‌سازی دسکتاپ] در انتظار دریافت در {save_dir}")


# ---------------------------------------------------------------------------
# HISTORY
# ---------------------------------------------------------------------------
class HistoryScreen(MDScreen):
    name = 'history'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.md_bg_color = LIGHT_BG
        self._build()

    def _build(self):
        root = MDBoxLayout(orientation='vertical')
        root.add_widget(MDTopAppBar(title='تاریخچه', elevation=0,
                                     md_bg_color=WHITE, specific_text_color=(0.1, 0.1, 0.1, 1)))
        body = MDBoxLayout(orientation='vertical', padding='16dp', spacing='8dp')
        self.list_view = MDList()
        body.add_widget(self.list_view)
        back_btn = MDFlatButton(text='بازگشت به خانه', pos_hint={'center_x': 0.5})
        back_btn.bind(on_release=lambda _: setattr(self.manager, 'current', 'home'))
        body.add_widget(back_btn)
        root.add_widget(body)
        self.add_widget(root)

    def on_enter(self):
        app = MDApp.get_running_app()
        self.list_view.clear_widgets()
        history = app.load_history()
        for entry in reversed(history):
            names = ', '.join(os.path.basename(p) for p in entry['files'])
            status = 'موفق ✅' if entry['success'] else 'ناموفق ❌'
            item = OneLineIconListItem(text=f"{names}  —  {entry['time']}  —  {status}")
            item.add_widget(IconLeftWidget(icon='file-check' if entry['success'] else 'file-alert'))
            self.list_view.add_widget(item)
        if not history:
            self.list_view.add_widget(OneLineIconListItem(text='هنوز انتقالی انجام نشده'))


# ---------------------------------------------------------------------------
# APP
# ---------------------------------------------------------------------------
class FastShareApp(MDApp):
    def build(self):
        self.title = 'MIshare'
        self.theme_cls.primary_palette = 'Blue'
        self.theme_cls.theme_style = 'Light'
        self.theme_cls.accent_palette = 'Blue'

        self.flow_mode = 'send'
        self.send_kind = 'file'
        self.connected_peer_ip = '192.168.49.1'
        self.my_wifi_address = '192.168.49.1'
        self.location_granted = False

        if IS_ANDROID:
            try:
                self.wifi_manager = WifiDirectManager()
            except Exception as e:
                print('WifiDirectManager init failed:', e)
                self.wifi_manager = None
            try:
                self.bt_manager = BluetoothManager()
            except Exception as e:
                print('BluetoothManager init failed:', e)
                self.bt_manager = None
        else:
            self.wifi_manager = None
            self.bt_manager = None

        self.store = JsonStore(os.path.join(self.user_data_dir, HISTORY_FILE))

        sm = ScreenManager(transition=SlideTransition())
        sm.add_widget(HomeScreen())
        sm.add_widget(PermissionScreen())
        sm.add_widget(ConnectScreen())
        sm.add_widget(QRShowScreen())
        sm.add_widget(QRScanScreen())
        sm.add_widget(BluetoothListScreen())
        sm.add_widget(SendTypeScreen())
        sm.add_widget(FilePickScreen())
        sm.add_widget(TransferScreen())
        sm.add_widget(HistoryScreen())

        qr_scan = sm.get_screen('qr_scan')
        qr_scan.on_result_callback = self._on_qr_scanned

        sm.current = 'home'
        return sm

    def _on_qr_scanned(self, payload):
        self.connected_peer_ip = payload['address']
        if self.flow_mode == 'send':
            self.root.current = 'send_type'
        else:
            self.root.current = 'transfer'
            self.root.get_screen('transfer').start_receiving()

    def load_history(self):
        if self.store.exists('history'):
            return self.store.get('history')['entries']
        return []

    def add_history_entry(self, files, success, message):
        entries = self.load_history()
        entries.append({
            'files': files,
            'success': success,
            'message': message,
            'time': datetime.now().strftime('%Y-%m-%d %H:%M'),
        })
        self.store.put('history', entries=entries)


if __name__ == '__main__':
    FastShareApp().run()
