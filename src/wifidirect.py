"""
wifidirect.py
لایه ارتباط با Android WifiP2pManager از طریق pyjnius
مسئول: کشف گوشی‌های نزدیک، درخواست اتصال، و گرفتن IP گروه بعد از اتصال.
"""

from jnius import autoclass, PythonJavaClass, java_method
from android.permissions import request_permissions, Permission

PythonActivity = autoclass('org.kivy.android.PythonActivity')
Context = autoclass('android.content.Context')
WifiP2pManager = autoclass('android.net.wifi.p2p.WifiP2pManager')
IntentFilter = autoclass('android.content.IntentFilter')
WifiP2pConfig = autoclass('android.net.wifi.p2p.WifiP2pConfig')

WIFI_P2P_STATE_CHANGED_ACTION = "android.net.wifi.p2p.STATE_CHANGED"
WIFI_P2P_PEERS_CHANGED_ACTION = "android.net.wifi.p2p.PEERS_CHANGED"
WIFI_P2P_CONNECTION_CHANGED_ACTION = "android.net.wifi.p2p.CONNECTION_STATE_CHANGE"


class PeerListListener(PythonJavaClass):
    """کال‌بک جاوا برای دریافت لیست گوشی‌های پیدا شده"""
    __javainterfaces__ = ['android/net/wifi/p2p/WifiP2pManager$PeerListListener']
    __javacontext__ = 'app'

    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    @java_method('(Landroid/net/wifi/p2p/WifiP2pDeviceList;)V')
    def onPeersAvailable(self, peer_list):
        devices = peer_list.getDeviceList().iterator()
        result = []
        while devices.hasNext():
            d = devices.next()
            result.append({
                'name': d.deviceName,
                'address': d.deviceAddress,
                'status': d.status,
            })
        self.callback(result)


class ActionListener(PythonJavaClass):
    """کال‌بک عمومی برای موفقیت/شکست عملیات (discover، connect و ...)"""
    __javainterfaces__ = ['android/net/wifi/p2p/WifiP2pManager$ActionListener']
    __javacontext__ = 'app'

    def __init__(self, on_success=None, on_failure=None):
        super().__init__()
        self.on_success = on_success
        self.on_failure = on_failure

    @java_method('()V')
    def onSuccess(self):
        if self.on_success:
            self.on_success()

    @java_method('(I)V')
    def onFailure(self, reason):
        if self.on_failure:
            self.on_failure(reason)


class ConnectionInfoListener(PythonJavaClass):
    """کال‌بک برای گرفتن اطلاعات اتصال (IP گروه، Group Owner یا نه)"""
    __javainterfaces__ = ['android/net/wifi/p2p/WifiP2pManager$ConnectionInfoListener']
    __javacontext__ = 'app'

    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    @java_method('(Landroid/net/wifi/p2p/WifiP2pInfo;)V')
    def onConnectionInfoAvailable(self, info):
        is_owner = info.isGroupOwner
        owner_addr = None
        if info.groupOwnerAddress:
            owner_addr = info.groupOwnerAddress.getHostAddress()
        self.callback({'is_group_owner': is_owner, 'owner_address': owner_addr})


class WifiDirectManager:
    """
    رابط اصلی برای مدیریت Wi-Fi Direct.
    نکته: باید قبل از استفاده مجوزهای لازم گرفته بشه (ACCESS_FINE_LOCATION و ...)
    """

    def __init__(self):
        self.activity = PythonActivity.mActivity
        self.manager = self.activity.getSystemService(Context.WIFI_P2P_SERVICE)
        self.channel = self.manager.initialize(self.activity, self.activity.getMainLooper(), None)

    def request_permissions(self, callback=None):
        perms = [
            Permission.ACCESS_FINE_LOCATION,
            Permission.ACCESS_COARSE_LOCATION,
        ]
        # اندروید ۱۳+ نیاز به NEARBY_WIFI_DEVICES هم داره
        try:
            perms.append('android.permission.NEARBY_WIFI_DEVICES')
        except Exception:
            pass
        request_permissions(perms, callback)

    def discover_peers(self, on_success=None, on_failure=None):
        listener = ActionListener(on_success, on_failure)
        self.manager.discoverPeers(self.channel, listener)

    def request_peers(self, callback):
        listener = PeerListListener(callback)
        self.manager.requestPeers(self.channel, listener)

    def connect(self, device_address, on_success=None, on_failure=None):
        config = WifiP2pConfig()
        config.deviceAddress = device_address
        listener = ActionListener(on_success, on_failure)
        self.manager.connect(self.channel, config, listener)

    def request_connection_info(self, callback):
        listener = ConnectionInfoListener(callback)
        self.manager.requestConnectionInfo(self.channel, listener)
