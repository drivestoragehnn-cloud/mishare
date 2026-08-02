"""
transfer.py
انتقال فایل با سرعت بالا روی TCP (بعد از برقراری Wi-Fi Direct).
هم گیرنده (سرور) و هم فرستنده (کلاینت) اینجا پیاده‌سازی شده.
پروتکل ساده: [8 بایت طول اسم فایل][اسم فایل utf-8][8 بایت طول فایل][محتوای فایل]
تکرار برای هر فایل، و در پایان یک پیام END.
"""

import os
import socket
import struct
import threading
import time

PORT = 8988
CHUNK_SIZE = 1024 * 256  # 256KB - برای سرعت بالا روی Wi-Fi Direct


def _send_exact(sock, data):
    sock.sendall(data)


def send_files(host, file_paths, progress_callback=None, done_callback=None, port=PORT):
    """
    فرستنده: به host وصل میشه و فایل‌ها رو یکی‌یکی می‌فرسته.
    progress_callback(filename, sent_bytes, total_bytes, speed_mbps)
    done_callback(success: bool, message: str)
    """
    def _run():
        try:
            sock = socket.create_connection((host, port), timeout=15)
            sock.settimeout(None)

            for path in file_paths:
                filename = os.path.basename(path)
                filesize = os.path.getsize(path)
                fname_bytes = filename.encode('utf-8')

                _send_exact(sock, struct.pack('>Q', len(fname_bytes)))
                _send_exact(sock, fname_bytes)
                _send_exact(sock, struct.pack('>Q', filesize))

                sent = 0
                start_time = time.time()
                with open(path, 'rb') as f:
                    while True:
                        chunk = f.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        sock.sendall(chunk)
                        sent += len(chunk)
                        elapsed = max(time.time() - start_time, 0.001)
                        speed_mbps = (sent / elapsed) / (1024 * 1024) * 8
                        if progress_callback:
                            progress_callback(filename, sent, filesize, speed_mbps)

            # پایان انتقال - طول صفر یعنی تمام شد
            _send_exact(sock, struct.pack('>Q', 0))
            sock.close()
            if done_callback:
                done_callback(True, "انتقال با موفقیت انجام شد")
        except Exception as e:
            if done_callback:
                done_callback(False, f"خطا در ارسال: {e}")

    threading.Thread(target=_run, daemon=True).start()


def receive_files(save_dir, progress_callback=None, done_callback=None,
                   file_received_callback=None, port=PORT):
    """
    گیرنده: منتظر اتصال می‌مونه و فایل‌های دریافتی رو در save_dir ذخیره می‌کنه.
    file_received_callback(filepath) بعد از تکمیل هر فایل صدا زده میشه.
    """
    def _recv_exact(sock, n):
        buf = b''
        while len(buf) < n:
            chunk = sock.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("اتصال قطع شد")
            buf += chunk
        return buf

    def _run():
        os.makedirs(save_dir, exist_ok=True)
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('0.0.0.0', port))
        server.listen(1)
        try:
            conn, addr = server.accept()
            while True:
                name_len_data = _recv_exact(conn, 8)
                name_len = struct.unpack('>Q', name_len_data)[0]
                if name_len == 0:
                    break  # پایان انتقال

                filename = _recv_exact(conn, name_len).decode('utf-8')
                filesize = struct.unpack('>Q', _recv_exact(conn, 8))[0]

                filepath = os.path.join(save_dir, filename)
                received = 0
                start_time = time.time()
                with open(filepath, 'wb') as f:
                    while received < filesize:
                        to_read = min(CHUNK_SIZE, filesize - received)
                        chunk = conn.recv(to_read)
                        if not chunk:
                            raise ConnectionError("اتصال قطع شد وسط فایل")
                        f.write(chunk)
                        received += len(chunk)
                        elapsed = max(time.time() - start_time, 0.001)
                        speed_mbps = (received / elapsed) / (1024 * 1024) * 8
                        if progress_callback:
                            progress_callback(filename, received, filesize, speed_mbps)

                if file_received_callback:
                    file_received_callback(filepath)

            conn.close()
            if done_callback:
                done_callback(True, "دریافت با موفقیت انجام شد")
        except Exception as e:
            if done_callback:
                done_callback(False, f"خطا در دریافت: {e}")
        finally:
            server.close()

    threading.Thread(target=_run, daemon=True).start()
