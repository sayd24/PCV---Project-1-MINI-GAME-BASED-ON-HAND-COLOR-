"""Kalibrasi warna penanda telunjuk/jempol, jarak gestur, dan ROI gerakan."""
import math

import cv2
import numpy as np

from tangan import (buka_kamera, deteksi, gambar_hasil, load_config,
                    save_config)

WINDOW = "Kalibrasi dua jari"
FONT = cv2.FONT_HERSHEY_SIMPLEX
DISP_W, DISP_H = 480, 360
TRACKBARS = (
    ("roi_atas", "ROI atas %", 95),
    ("roi_bawah", "ROI bawah %", 100),
    ("roi_kiri", "ROI kiri %", 95),
    ("roi_kanan", "ROI kanan %", 100),
    ("min_area", "Area minimum", 1000),
)


def rentang_warna_dari_klik(frame, x, y, radius=8):
    """Ambil warna dari pusat klik dengan toleransi untuk variasi pencahayaan."""
    hsv = cv2.cvtColor(cv2.GaussianBlur(frame, (5, 5), 0), cv2.COLOR_BGR2HSV)
    h, w = hsv.shape[:2]
    x, y = int(np.clip(x, 0, w - 1)), int(np.clip(y, 0, h - 1))
    patch = hsv[max(0, y - radius):min(h, y + radius + 1),
                max(0, x - radius):min(w, x + radius + 1)].reshape(-1, 3).astype(float)
    pusat = hsv[max(0, y - 2):min(h, y + 3),
                max(0, x - 2):min(w, x + 3)].reshape(-1, 3).astype(float)
    angles = pusat[:, 0] * (2 * math.pi / 180)
    hue_center = math.atan2(np.sin(angles).mean(), np.cos(angles).mean())
    center = (hue_center * 180 / (2 * math.pi)) % 180
    hue_delta = np.abs((pusat[:, 0] - center + 90) % 180 - 90)
    hue_width = int(np.clip(np.percentile(hue_delta, 90) + 3, 4, 12))
    cocok = patch[np.abs((patch[:, 0] - center + 90) % 180 - 90) <= hue_width * 2]
    if not len(cocok):
        cocok = pusat
    s_min = int(np.clip(np.percentile(cocok[:, 1], 10) - 35, 0, 255))
    s_max = int(np.clip(np.percentile(cocok[:, 1], 90) + 35, 0, 255))
    v_min = int(np.clip(np.percentile(cocok[:, 2], 10) - 40, 0, 255))
    v_max = int(np.clip(np.percentile(cocok[:, 2], 90) + 40, 0, 255))
    center_hue = int(round(center)) % 180
    return {
        "h_min": (center_hue - hue_width) % 180,
        "h_max": (center_hue + hue_width) % 180,
        "s_min": s_min, "s_max": s_max,
        "v_min": v_min, "v_max": v_max,
        "hue_center": center_hue,
    }


def main():
    cfg = load_config()
    cap = buka_kamera(cfg["kamera"])
    if cap is None:
        print('Kamera gagal dibuka! Ubah "kamera" di config.json (0, 1, 2...).')
        return

    cv2.namedWindow(WINDOW)
    for key, label, maximum in TRACKBARS:
        cv2.createTrackbar(label, WINDOW, int(round(cfg[key] * 100)) if key.startswith("roi_")
                           else int(cfg[key]), maximum, lambda _value: None)

    status = {"klik": None, "kursor": None}

    def on_mouse(event, x, y, _flags, _param):
        if x >= DISP_W:
            return
        status["kursor"] = (x, y)
        if event in (cv2.EVENT_LBUTTONDOWN, cv2.EVENT_RBUTTONDOWN):
            status["klik"] = (x, y, "index" if event == cv2.EVENT_LBUTTONDOWN else "jempol")

    cv2.setMouseCallback(WINDOW, on_mouse)
    pesan = "Klik KIRI tepat pada penanda TELUNJUK."
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("Gagal membaca frame dari kamera.")
                break
            frame = cv2.flip(frame, 1)
            tinggi, lebar = frame.shape[:2]

            if status["klik"] is not None:
                px, py, prefix = status["klik"]
                status["klik"] = None
                x, y = int(px * lebar / DISP_W), int(py * tinggi / DISP_H)
                sample = rentang_warna_dari_klik(frame, x, y, cfg["radius_sampel"])
                for key, value in sample.items():
                    if key != "hue_center":
                        cfg[f"{prefix}_{key}"] = value
                cfg[f"{prefix}_terkalibrasi"] = True
                label = "TELUNJUK" if prefix == "index" else "JEMPOL"
                pesan = f"Warna {label} direkam (Hue {sample['hue_center']})."

            for key, label, _maximum in TRACKBARS:
                value = cv2.getTrackbarPos(label, WINDOW)
                cfg[key] = value / 100 if key.startswith("roi_") else value
            cfg["roi_kanan"] = max(cfg["roi_kanan"], cfg["roi_kiri"] + 0.05)
            cfg["roi_bawah"] = max(cfg["roi_bawah"], cfg["roi_atas"] + 0.05)
            cfg["roi_kanan"] = min(cfg["roi_kanan"], 1.0)
            cfg["roi_bawah"] = min(cfg["roi_bawah"], 1.0)

            hasil = deteksi(frame, cfg)
            annotated = frame.copy()
            gambar_hasil(annotated, cfg, hasil)
            left = cv2.resize(annotated, (DISP_W, DISP_H))

            mask_color = np.zeros((tinggi, lebar, 3), np.uint8)
            if hasil.mask_telunjuk is not None:
                mask_color[hasil.mask_telunjuk > 0] = (0, 220, 0)
            if hasil.mask_jempol is not None:
                mask_color[hasil.mask_jempol > 0] = (220, 0, 220)
            right = cv2.resize(mask_color, (DISP_W, DISP_H))
            cv2.putText(left, pesan[:62], (8, 22), FONT, 0.48, (255, 255, 255), 1)
            status_index = "OK" if cfg["index_terkalibrasi"] else "BELUM"
            status_jempol = "OK" if cfg["jempol_terkalibrasi"] else "BELUM"
            jarak = f"{hasil.jarak_norm:.3f}" if hasil.ada else "--"
            cv2.putText(left, f"Telunjuk {status_index} | Jempol {status_jempol} | jarak {jarak}",
                        (8, 44), FONT, 0.45, (0, 255, 255), 1)
            cv2.putText(left, "o=rekam terbuka | k=rekam rapat | s=simpan | Esc=keluar",
                        (8, DISP_H - 12), FONT, 0.43, (255, 255, 255), 1)
            cv2.putText(right, "Mask: hijau=telunjuk, ungu=jempol",
                        (8, 22), FONT, 0.45, (255, 255, 255), 1)
            cv2.imshow(WINDOW, np.hstack((left, right)))

            key = cv2.waitKey(1) & 0xFF
            if key == ord("o"):
                if hasil.ada:
                    cfg["jarak_buka"] = hasil.jarak_norm
                    cfg["buka_terkalibrasi"] = True
                    pesan = f"Jarak terbuka direkam: {hasil.jarak_norm:.3f}."
                else:
                    pesan = "Kedua penanda harus terlihat untuk merekam jarak."
            elif key == ord("k"):
                if hasil.ada:
                    cfg["jarak_tutup"] = hasil.jarak_norm
                    cfg["tutup_terkalibrasi"] = True
                    pesan = f"Jarak rapat direkam: {hasil.jarak_norm:.3f}."
                else:
                    pesan = "Kedua penanda harus terlihat untuk merekam jarak."
            elif key == ord("s"):
                if not cfg["index_terkalibrasi"] or not cfg["jempol_terkalibrasi"]:
                    pesan = "Sampel warna telunjuk dan jempol harus direkam dulu."
                elif not cfg["buka_terkalibrasi"] or not cfg["tutup_terkalibrasi"]:
                    pesan = "Rekam posisi terbuka (o) dan rapat (k) dulu."
                elif cfg["jarak_buka"] <= cfg["jarak_tutup"] + 0.025:
                    pesan = "Jarak terbuka harus lebih besar dari jarak rapat (beri jarak jelas)."
                else:
                    save_config(cfg)
                    pesan = "Kalibrasi tersimpan ke config.json."
            elif key == 27:
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
