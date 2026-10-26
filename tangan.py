"""Pelacakan dua penanda jari memakai HSV, ROI, dan jarak antartitik."""
import json
import os
import sys
from dataclasses import dataclass
from typing import Optional, Tuple

import cv2
import numpy as np

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

DEFAULT_CONFIG = {
    "kamera": 0,
    "roi_atas": 0.10,
    "roi_bawah": 0.95,
    "roi_kiri": 0.05,
    "roi_kanan": 0.95,
    "min_area": 35,
    "radius_sampel": 8,
    "index_h_min": 0,
    "index_h_max": 179,
    "index_s_min": 50,
    "index_s_max": 255,
    "index_v_min": 40,
    "index_v_max": 255,
    "jempol_h_min": 0,
    "jempol_h_max": 179,
    "jempol_s_min": 50,
    "jempol_s_max": 255,
    "jempol_v_min": 40,
    "jempol_v_max": 255,
    "index_terkalibrasi": False,
    "jempol_terkalibrasi": False,
    "jarak_buka": 0.25,
    "jarak_tutup": 0.07,
    "buka_terkalibrasi": False,
    "tutup_terkalibrasi": False,
}


def load_config():
    cfg = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, encoding="utf-8") as f:
                stored = json.load(f)
            if "index_terkalibrasi" in stored or "jempol_terkalibrasi" in stored:
                cfg.update(stored)
            else:
                # Jangan gunakan ambang kulit/solidity dari format kalibrasi lama
                # sebagai ambang warna penanda baru.
                cfg["kamera"] = stored.get("kamera", cfg["kamera"])
        except (ValueError, OSError) as exc:
            print(f"config.json tidak dapat dibaca ({exc}); pakai nilai default.")
    else:
        print("config.json belum ada. Jalankan kalibrasi.py terlebih dahulu.")
    return cfg


def save_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    print("Kalibrasi disimpan ke", CONFIG_PATH)


def kalibrasi_lengkap(cfg):
    return all(cfg.get(key, False) for key in (
        "index_terkalibrasi", "jempol_terkalibrasi",
        "buka_terkalibrasi", "tutup_terkalibrasi",
    ))


def buka_kamera(index=0):
    if sys.platform.startswith("win"):
        backend = cv2.CAP_DSHOW
    elif sys.platform == "darwin":
        backend = cv2.CAP_AVFOUNDATION
    else:
        backend = cv2.CAP_ANY
    cap = cv2.VideoCapture(index, backend)
    if not cap.isOpened():
        cap.release()
        return None
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    return cap


@dataclass
class Hasil:
    telunjuk: Optional[Tuple[int, int]] = None
    jempol: Optional[Tuple[int, int]] = None
    jarak_norm: float = 0.0
    mask: Optional[np.ndarray] = None
    mask_telunjuk: Optional[np.ndarray] = None
    mask_jempol: Optional[np.ndarray] = None

    @property
    def ada(self):
        return self.telunjuk is not None and self.jempol is not None

    @property
    def cx(self):
        return self.telunjuk[0] if self.telunjuk else 0

    @property
    def cy(self):
        return self.telunjuk[1] if self.telunjuk else 0


def _mask_warna(hsv, cfg, prefix):
    hmin, hmax = cfg[f"{prefix}_h_min"], cfg[f"{prefix}_h_max"]
    lower = np.array([hmin, cfg[f"{prefix}_s_min"], cfg[f"{prefix}_v_min"]])
    upper = np.array([hmax, cfg[f"{prefix}_s_max"], cfg[f"{prefix}_v_max"]])
    if hmin <= hmax:
        return cv2.inRange(hsv, lower, upper)
    # Hue OpenCV melingkar di 0/179; rentang seperti 175..4 perlu dua mask.
    low_side = cv2.inRange(hsv, np.array([0, lower[1], lower[2]]), upper)
    high_side = cv2.inRange(hsv, lower, np.array([179, upper[1], upper[2]]))
    return cv2.bitwise_or(low_side, high_side)


def _titik_terbesar(mask, min_area):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    contour = max(contours, key=cv2.contourArea)
    if cv2.contourArea(contour) < min_area:
        return None
    moments = cv2.moments(contour)
    if moments["m00"] == 0:
        return None
    return (
        int(moments["m10"] / moments["m00"]),
        int(moments["m01"] / moments["m00"]),
    )


def deteksi(frame, cfg) -> Hasil:
    tinggi, lebar = frame.shape[:2]
    x0 = int(lebar * cfg["roi_kiri"])
    x1 = int(lebar * cfg["roi_kanan"])
    y0 = int(tinggi * cfg["roi_atas"])
    y1 = int(tinggi * cfg["roi_bawah"])
    kosong = np.zeros((tinggi, lebar), np.uint8)
    if x1 <= x0 or y1 <= y0:
        raise ValueError("ROI tidak valid: pastikan batas kanan/bawah lebih besar.")

    roi = frame[y0:y1, x0:x1]
    hsv = cv2.cvtColor(cv2.GaussianBlur(roi, (5, 5), 0), cv2.COLOR_BGR2HSV)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    masks = []
    points = []
    for prefix in ("index", "jempol"):
        mask = _mask_warna(hsv, cfg, prefix)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        masks.append(mask)
        point = _titik_terbesar(mask, cfg["min_area"])
        points.append((point[0] + x0, point[1] + y0) if point else None)

    full_masks = []
    for mask in masks:
        full = kosong.copy()
        full[y0:y1, x0:x1] = mask
        full_masks.append(full)
    combined = cv2.max(full_masks[0], full_masks[1])

    jarak_norm = 0.0
    if points[0] is not None and points[1] is not None:
        jarak_norm = float(np.hypot(
            points[0][0] - points[1][0], points[0][1] - points[1][1]
        ) / max(x1 - x0, 1))
    return Hasil(points[0], points[1], jarak_norm, combined, *full_masks)


def gambar_hasil(frame, cfg, hasil: Hasil):
    h, w = frame.shape[:2]
    x0, x1 = int(w * cfg["roi_kiri"]), int(w * cfg["roi_kanan"])
    y0, y1 = int(h * cfg["roi_atas"]), int(h * cfg["roi_bawah"])
    cv2.rectangle(frame, (x0, y0), (x1 - 1, y1 - 1), (255, 200, 0), 2)
    for point, color, label in (
        (hasil.telunjuk, (0, 255, 0), "TELUNJUK"),
        (hasil.jempol, (255, 0, 255), "JEMPOL"),
    ):
        if point is not None:
            cv2.circle(frame, point, 9, color, 2)
            cv2.putText(frame, label, (point[0] + 10, point[1] - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)
    if hasil.ada:
        cv2.line(frame, hasil.telunjuk, hasil.jempol, (0, 255, 255), 2)


@dataclass
class Gestur:
    ada: bool = False
    x_norm: float = 0.5
    kepal: bool = False
    hilang_detik: float = 0.0
    arah_x: Optional[float] = None
    arah_y: Optional[float] = None


class PembacaGestur:
    """Terbuka = bidik; jari dirapatkan = tahan power; dibuka kembali = tembak."""
    KONFIRMASI = 3

    def __init__(self, cfg):
        self.kiri, self.kanan = cfg["roi_kiri"], cfg["roi_kanan"]
        self.jar_buka = float(cfg["jarak_buka"])
        self.jar_tutup = float(cfg["jarak_tutup"])
        if self.jar_buka <= self.jar_tutup:
            raise ValueError("Kalibrasi jarak terbuka harus lebih besar dari jarak tertutup.")
        gap = self.jar_buka - self.jar_tutup
        self.batas_tutup = self.jar_tutup + gap * 0.4
        self.batas_buka = self.jar_tutup + gap * 0.6
        self.kepal = False
        self._hitung = 0
        self._x = 0.5
        self._arah = (None, None)
        self._hilang_sejak = None

    def update(self, hasil: Hasil, lebar: int, t: float) -> Gestur:
        if not hasil.ada:
            if self._hilang_sejak is None:
                self._hilang_sejak = t
            return Gestur(False, self._x, self.kepal, t - self._hilang_sejak)
        pulih = self._hilang_sejak is not None
        self._hilang_sejak = None

        if pulih:
            self.kepal = hasil.jarak_norm <= (self.batas_tutup + self.batas_buka) / 2
            self._hitung = 0
        else:
            if hasil.jarak_norm < self.batas_tutup:
                calon = True
            elif hasil.jarak_norm > self.batas_buka:
                calon = False
            else:
                calon = self.kepal
            if calon != self.kepal:
                self._hitung += 1
                if self._hitung >= self.KONFIRMASI:
                    self.kepal, self._hitung = calon, 0
            else:
                self._hitung = 0

        rel = (hasil.telunjuk[0] / lebar - self.kiri) / max(self.kanan - self.kiri, 0.05)
        self._x = min(max((rel - 0.04) / 0.92, 0.0), 1.0)
        dx = hasil.telunjuk[0] - hasil.jempol[0]
        dy = hasil.telunjuk[1] - hasil.jempol[1]
        panjang = float(np.hypot(dx, dy))
        if panjang > 1e-6:
            self._arah = (dx / panjang, dy / panjang)
        return Gestur(True, self._x, self.kepal, 0.0, *self._arah)
