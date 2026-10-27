import time

import cv2
import numpy as np

from pengaturan import PREVIEW_SIZE, W
from tangan import Hasil, PembacaGestur, buka_kamera, deteksi, gambar_hasil, kalibrasi_lengkap, load_config


class InputKamera:
    def __init__(self, preview=True):
        self.cfg = load_config()
        if not kalibrasi_lengkap(self.cfg):
            raise RuntimeError("Kalibrasi dua jari belum lengkap. Jalankan python kalibrasi.py.")
        self.cap = buka_kamera(self.cfg["kamera"])
        if self.cap is None:
            raise RuntimeError('Kamera gagal dibuka. Ubah "kamera" di config.json (0, 1, 2...).')
        self.pembaca = PembacaGestur(self.cfg)
        self.preview = preview
        self.jendela_dibuka = False

    def baca(self):
        ok, frame = self.cap.read()
        if not ok:
            return self.pembaca.update(Hasil(), 640, time.time())
        frame = cv2.flip(frame, 1)
        hasil = deteksi(frame, self.cfg)
        gestur = self.pembaca.update(hasil, frame.shape[1], time.time())
        if self.preview:
            self._tampilkan(frame, hasil, gestur)
        return gestur

    def _tampilkan(self, frame, hasil, gestur):
        gambar_hasil(frame, self.cfg, hasil)
        status = ("TAHAN POWER" if gestur.kepal else "BIDIK") if gestur.ada else "dua penanda tidak terdeteksi"
        preview = cv2.resize(frame, PREVIEW_SIZE)
        mask = np.zeros_like(frame)
        if hasil.mask_telunjuk is not None:
            mask[hasil.mask_telunjuk > 0] = (0, 220, 0)
        if hasil.mask_jempol is not None:
            mask[hasil.mask_jempol > 0] = (220, 0, 220)
        mask = cv2.resize(mask, PREVIEW_SIZE)
        cv2.putText(mask, status, (8, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)
        cv2.putText(mask, f"Jarak: {hasil.jarak_norm:.3f}", (8, 52),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(mask, "Hijau: telunjuk | Ungu: jempol", (6, 151),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.32, (255, 255, 255), 1)
        cv2.putText(mask, "Rapatkan: isi power | Buka: tembak", (6, 172),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.29, (255, 255, 255), 1)
        cv2.imshow("Kamera", np.hstack((preview, mask)))
        if not self.jendela_dibuka:
            cv2.moveWindow("Kamera", W + 16, 0)
            self.jendela_dibuka = True
        cv2.waitKey(1)
        if cv2.getWindowProperty("Kamera", cv2.WND_PROP_VISIBLE) < 1:
            self.preview = False

    def tutup(self):
        self.cap.release()
        cv2.destroyAllWindows()
