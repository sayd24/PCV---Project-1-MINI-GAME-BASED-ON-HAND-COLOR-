"""Mini-Golf dikontrol dua jari bertanda warna.

    python main.py              # pakai webcam (kalibrasi dulu: python kalibrasi.py)
    python main.py --keyboard   # tanpa kamera: <- -> bidik, tahan SPASI = kepal

KONTROL (dua penanda di dalam ROI biru pada jendela kamera)
  * Jari terbuka  : geser telunjuk kiri-kanan untuk membidik
  * Jari dirapatkan dan ditahan : isi power
  * Buka kembali  : tembak
"""
import argparse
import math
import time

import cv2
import pygame

from tangan import (Gestur, Hasil, PembacaGestur, buka_kamera, deteksi, gambar_hasil,
                    kalibrasi_lengkap, load_config)

W, H, FPS = 800, 600, 60
R_BOLA, R_LUBANG = 10, 14
START, LUBANG = (100, 500), (700, 100)
DINDING = [pygame.Rect(200, 150, 20, 300), pygame.Rect(400, 0, 20, 250),
           pygame.Rect(600, 200, 20, 400)]

FRIKSI = 0.98                    # per 1/60 detik (disesuaikan dengan dt)
BERHENTI_DI_BAWAH = 6.0          # px/detik
RESTITUSI = 0.8
MIN_POWER, MAX_POWER = 120.0, 1200.0     # px/detik
POWER_SPEED = 840.0              # satuan power per detik saat kepal ditahan
PANAH_MIN, PANAH_MAX = 40, 220
BATAL_JIKA_HILANG = 0.6          # detik
KECEPATAN_MASUK_LUBANG = 250.0   # px/detik


# --------------------------------------------------------------------------- #
# Fisika
# --------------------------------------------------------------------------- #
class Bola:
    def __init__(self, pos):
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(0, 0)

    @property
    def diam(self):
        return self.vel.length_squared() == 0

    def _pantul(self, normal):
        vn = self.vel.dot(normal)
        if vn < 0:
            self.vel = self.vel - (1 + RESTITUSI) * vn * normal

    def _tabrak_batas(self):
        if self.pos.x < R_BOLA:
            self.pos.x = R_BOLA
            self._pantul(pygame.Vector2(1, 0))
        elif self.pos.x > W - R_BOLA:
            self.pos.x = W - R_BOLA
            self._pantul(pygame.Vector2(-1, 0))
        if self.pos.y < R_BOLA:
            self.pos.y = R_BOLA
            self._pantul(pygame.Vector2(0, 1))
        elif self.pos.y > H - R_BOLA:
            self.pos.y = H - R_BOLA
            self._pantul(pygame.Vector2(0, -1))

    def _tabrak_rect(self, rect):
        terdekat = pygame.Vector2(max(rect.left, min(self.pos.x, rect.right)),
                                  max(rect.top, min(self.pos.y, rect.bottom)))
        delta = self.pos - terdekat
        jarak = delta.length()
        if jarak >= R_BOLA:
            return
        if jarak > 1e-9:
            normal = delta / jarak
            self.pos = terdekat + normal * R_BOLA
        else:                                  # pusat bola di dalam dinding: dorong keluar
            celah = {(-1, 0): self.pos.x - rect.left, (1, 0): rect.right - self.pos.x,
                     (0, -1): self.pos.y - rect.top, (0, 1): rect.bottom - self.pos.y}
            (nx, ny), g = min(celah.items(), key=lambda kv: kv[1])
            normal = pygame.Vector2(nx, ny)
            self.pos = self.pos + normal * (g + R_BOLA)
        self._pantul(normal)

    def langkah(self, dt):
        self.vel = self.vel * (FRIKSI ** (dt * 60))
        v = self.vel.length()
        if v < BERHENTI_DI_BAWAH:
            self.vel = pygame.Vector2(0, 0)
            return
        n = max(1, math.ceil(v * dt / (R_BOLA * 0.5)))      # cegah menembus dinding tipis
        for _ in range(n):
            self.pos = self.pos + self.vel * dt / n
            self._tabrak_batas()
            for d in DINDING:
                self._tabrak_rect(d)


# --------------------------------------------------------------------------- #
# Sumber input (game hanya butuh .baca() -> Gestur)
# --------------------------------------------------------------------------- #
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

    def baca(self) -> Gestur:
        ok, frame = self.cap.read()
        if not ok:
            return self.pembaca.update(Hasil(), 640, time.time())
        frame = cv2.flip(frame, 1)
        hasil = deteksi(frame, self.cfg)
        g = self.pembaca.update(hasil, frame.shape[1], time.time())
        if self.preview:
            gambar_hasil(frame, self.cfg, hasil)
            status = ("TAHAN POWER" if g.kepal else "BIDIK") if g.ada else "dua penanda tidak terdeteksi"
            cv2.putText(frame, f"{status}  jarak={hasil.jarak_norm:.3f}", (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.imshow("Kamera", frame)
            cv2.waitKey(1)
        return g

    def tutup(self):
        self.cap.release()
        cv2.destroyAllWindows()


class InputKeyboard:
    def __init__(self):
        self.x = 0.41            # kira-kira mengarah ke lubang

    def baca(self) -> Gestur:
        k = pygame.key.get_pressed()
        if k[pygame.K_LEFT]:
            self.x = max(0.0, self.x - 0.004)
        if k[pygame.K_RIGHT]:
            self.x = min(1.0, self.x + 0.004)
        return Gestur(True, self.x, bool(k[pygame.K_SPACE]), 0.0)

    def tutup(self):
        pass


# --------------------------------------------------------------------------- #
# Tampilan
# --------------------------------------------------------------------------- #
def gambar_panah(layar, mulai, arah, panjang, warna):
    ujung = mulai + arah * panjang
    dasar = ujung - arah * 18
    tegak = pygame.Vector2(-arah.y, arah.x)
    pygame.draw.line(layar, warna, mulai, dasar, 5)
    pygame.draw.polygon(layar, warna, [ujung, dasar + tegak * 10, dasar - tegak * 10])


# --------------------------------------------------------------------------- #
# Loop game
# --------------------------------------------------------------------------- #
def jalankan(sumber, max_detik=None):
    pygame.init()
    layar = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Mini-Golf Tangan")
    jam = pygame.time.Clock()
    font, besar = pygame.font.SysFont(None, 26), pygame.font.SysFont(None, 54)

    lubang = pygame.Vector2(LUBANG)
    bola = Bola(START)
    arah = (lubang - bola.pos).normalize()
    kunci = pygame.Vector2(arah)
    state, power, naik = "bidik", MIN_POWER, 1
    pukulan, menang, waktu_menang = 0, 0, 0.0
    mulai = time.time()

    try:
        while True:
            dt = min(jam.tick(FPS) / 1000.0, 0.05)
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                    return {"pukulan": pukulan, "menang": menang}
            g = sumber.baca()

            # ---------------- logika tembakan ----------------
            if state == "menang":
                if time.time() - waktu_menang > 2.5:
                    bola, pukulan, state = Bola(START), 0, "bidik"
            elif not bola.diam:
                state = "jalan"
            else:
                if state == "jalan":
                    state = "bidik"
                if state == "bidik":
                    if g.ada:
                        if g.arah_x is not None and g.arah_y is not None:
                            # Arah bidik mengikuti garis dari jempol (belakang) ke telunjuk (depan).
                            target = pygame.Vector2(g.arah_x, g.arah_y)
                        else:
                            # Input keyboard tetap memakai posisi horizontal sebagai arah.
                            a = math.radians(-180 + 360 * g.x_norm)
                            target = pygame.Vector2(math.cos(a), math.sin(a))
                        baru = arah * 0.25 + target * 0.75
                        if baru.length() > 1e-6:
                            arah = baru.normalize()
                    if g.ada and g.kepal:
                        # Kunci arah terbaru sebelum mulai mengisi power.
                        kunci = pygame.Vector2(arah)
                        state, power, naik = "isi", MIN_POWER, 1
                elif state == "isi":
                    if g.hilang_detik > BATAL_JIKA_HILANG:
                        state = "bidik"
                    elif not g.kepal:
                        bola.vel = kunci * power
                        pukulan += 1
                        state = "jalan"
                    else:
                        power += POWER_SPEED * dt * naik
                        if power >= MAX_POWER:
                            power, naik = MAX_POWER, -1
                        elif power <= MIN_POWER:
                            power, naik = MIN_POWER, 1

            if state != "menang":
                bola.langkah(dt)
                if bola.pos.distance_to(lubang) <= R_LUBANG and bola.vel.length() < KECEPATAN_MASUK_LUBANG:
                    bola.pos, bola.vel = pygame.Vector2(lubang), pygame.Vector2(0, 0)
                    state, menang, waktu_menang = "menang", menang + 1, time.time()

            # ---------------- gambar ----------------
            layar.fill((0, 100, 0))
            for d in DINDING:
                pygame.draw.rect(layar, (160, 82, 45), d)
            pygame.draw.circle(layar, (0, 0, 0), lubang, R_LUBANG)
            pygame.draw.circle(layar, (255, 255, 255), bola.pos, R_BOLA)

            if state in ("bidik", "isi"):
                p = (power - MIN_POWER) / (MAX_POWER - MIN_POWER) if state == "isi" else 0.0
                panjang = PANAH_MIN + (PANAH_MAX - PANAH_MIN) * p
                warna = (int(255 * p), int(220 * (1 - p)) + 35, 0) if state == "isi" else (255, 255, 0)
                gambar_panah(layar, bola.pos + (kunci if state == "isi" else arah) * (R_BOLA + 4),
                             kunci if state == "isi" else arah, panjang, warna)
            if state == "isi":
                pygame.draw.rect(layar, (110, 110, 110), (20, 20, 200, 20))
                pygame.draw.rect(layar, (50, 220, 50), (20, 20, int(200 * p), 20))
                pygame.draw.rect(layar, (255, 255, 255), (20, 20, 200, 20), 2)

            mode_teks = {"bidik": "BIDIK", "isi": "TAHAN POWER",
                         "jalan": "BOLA BERGERAK", "menang": "MENANG"}[state]
            info = f"Pukulan: {pukulan}   Mode: {mode_teks}   Jari: {'terdeteksi' if g.ada else 'HILANG'}"
            layar.blit(font.render(info, True, (255, 255, 255)), (20, H - 55))
            layar.blit(font.render("Geser telunjuk = bidik | rapatkan jari = tahan power | buka = tembak",
                                   True, (230, 230, 230)), (20, H - 28))
            if state == "menang":
                t = besar.render(f"HOLE IN! ({pukulan} pukulan)", True, (255, 215, 0))
                layar.blit(t, t.get_rect(center=(W // 2, H // 2)))
            pygame.display.flip()

            if max_detik is not None and time.time() - mulai > max_detik:
                return {"pukulan": pukulan, "menang": menang}
    finally:
        sumber.tutup()
        pygame.quit()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keyboard", action="store_true", help="tanpa kamera")
    ap.add_argument("--tanpa-preview", action="store_true", help="sembunyikan jendela kamera")
    args = ap.parse_args()
    try:
        sumber = InputKeyboard() if args.keyboard else InputKamera(preview=not args.tanpa_preview)
    except RuntimeError as e:
        print("Error:", e)
        return
    print(jalankan(sumber))


if __name__ == "__main__":
    main()
