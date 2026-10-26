import argparse
import math
import random
import time
from pathlib import Path

import cv2
import pygame

from tangan import (Gestur, Hasil, PembacaGestur, buka_kamera, deteksi, gambar_hasil,
                    kalibrasi_lengkap, load_config)

# Pengaturan game.
W, H, FPS = 800, 600, 60
R_BOLA, R_LUBANG = 10, 14
DINDING_PINGGIR = 20
DINDING_TEPI = [
    pygame.Rect(0, 0, W, DINDING_PINGGIR),
    pygame.Rect(0, H - DINDING_PINGGIR, W, DINDING_PINGGIR),
    pygame.Rect(0, DINDING_PINGGIR, DINDING_PINGGIR, H - DINDING_PINGGIR * 2),
    pygame.Rect(W - DINDING_PINGGIR, DINDING_PINGGIR,
                DINDING_PINGGIR, H - DINDING_PINGGIR * 2),
]
DINDING = [
    pygame.Rect(145, 82, 132, 18), pygame.Rect(92, 190, 18, 142),
    pygame.Rect(220, 228, 115, 18), pygame.Rect(158, 404, 155, 18),
    pygame.Rect(342, 36, 18, 158), pygame.Rect(378, 276, 112, 18),
    pygame.Rect(344, 382, 18, 150), pygame.Rect(475, 112, 145, 18),
    pygame.Rect(520, 185, 18, 132), pygame.Rect(438, 468, 138, 18),
    pygame.Rect(654, 66, 18, 148), pygame.Rect(610, 346, 132, 18),
    pygame.Rect(704, 428, 18, 126), pygame.Rect(80, 510, 18, 76),
    pygame.Rect(260, 108, 18, 72), pygame.Rect(570, 492, 110, 18),
]
ASSET_DIR = Path(__file__).resolve().parent / "assets"

FRIKSI = 0.98
BERHENTI_DI_BAWAH = 6.0
RESTITUSI = 0.8
MIN_POWER, MAX_POWER = 120.0, 1200.0
POWER_SPEED = 840.0
PANAH_MIN, PANAH_MAX = 40, 220
BATAL_JIKA_HILANG = 0.6
KECEPATAN_MASUK_LUBANG = 250.0


# Posisi ronde dan aset.
def posisi_spawn_aman(radius):
    batas_x = (radius + DINDING_PINGGIR + 8, W - radius - DINDING_PINGGIR - 8)
    batas_y = (radius + DINDING_PINGGIR + 8, H - radius - DINDING_PINGGIR - 8)
    for _ in range(500):
        posisi = pygame.Vector2(random.uniform(*batas_x), random.uniform(*batas_y))
        if not any(dinding.inflate(radius * 2, radius * 2).collidepoint(posisi)
                   for dinding in DINDING):
            return posisi
    raise RuntimeError("Tidak menemukan posisi spawn aman. Periksa susunan tembok.")


def spawn_ronde():
    for _ in range(500):
        mulai = posisi_spawn_aman(R_BOLA + 8)
        lubang = posisi_spawn_aman(R_LUBANG + 8)
        if mulai.distance_to(lubang) >= 320:
            return mulai, lubang
    raise RuntimeError("Tidak menemukan pasangan posisi spawn yang cukup berjauhan.")


def muat_aset(nama, ukuran):
    path = ASSET_DIR / nama
    if not path.is_file():
        return None
    gambar = pygame.image.load(str(path)).convert_alpha()
    return pygame.transform.smoothscale(gambar, ukuran)


# Fisika bola.
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
        if self.pos.x < DINDING_PINGGIR + R_BOLA:
            self.pos.x = DINDING_PINGGIR + R_BOLA
            self._pantul(pygame.Vector2(1, 0))
        elif self.pos.x > W - DINDING_PINGGIR - R_BOLA:
            self.pos.x = W - DINDING_PINGGIR - R_BOLA
            self._pantul(pygame.Vector2(-1, 0))
        if self.pos.y < DINDING_PINGGIR + R_BOLA:
            self.pos.y = DINDING_PINGGIR + R_BOLA
            self._pantul(pygame.Vector2(0, 1))
        elif self.pos.y > H - DINDING_PINGGIR - R_BOLA:
            self.pos.y = H - DINDING_PINGGIR - R_BOLA
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
        else:
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
        n = max(1, math.ceil(v * dt / (R_BOLA * 0.5)))
        for _ in range(n):
            self.pos = self.pos + self.vel * dt / n
            self._tabrak_batas()
            for d in DINDING:
                self._tabrak_rect(d)


# Input kamera dan keyboard.
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
        self.x = 0.41

    def baca(self) -> Gestur:
        k = pygame.key.get_pressed()
        if k[pygame.K_LEFT]:
            self.x = max(0.0, self.x - 0.004)
        if k[pygame.K_RIGHT]:
            self.x = min(1.0, self.x + 0.004)
        return Gestur(True, self.x, bool(k[pygame.K_SPACE]), 0.0)

    def tutup(self):
        pass


# Tampilan dan loop permainan.
def gambar_panah(layar, mulai, arah, panjang, warna):
    ujung = mulai + arah * panjang
    dasar = ujung - arah * 18
    tegak = pygame.Vector2(-arah.y, arah.x)
    pygame.draw.line(layar, warna, mulai, dasar, 5)
    pygame.draw.polygon(layar, warna, [ujung, dasar + tegak * 10, dasar - tegak * 10])


def jalankan(sumber, max_detik=None):
    pygame.init()
    layar = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Mini-Golf Tangan")
    jam = pygame.time.Clock()
    font, besar = pygame.font.SysFont(None, 26), pygame.font.SysFont(None, 54)

    posisi_awal, posisi_lubang = spawn_ronde()
    lubang = pygame.Vector2(posisi_lubang)
    bola = Bola(posisi_awal)
    arah = (lubang - bola.pos).normalize()
    kunci = pygame.Vector2(arah)
    state, power, naik = "bidik", MIN_POWER, 1
    pukulan, menang, waktu_menang = 0, 0, 0.0
    mulai = time.time()
    gambar_lapangan = muat_aset("rumput.png", (W, H))
    gambar_bola = muat_aset("bola.png", (R_BOLA * 2, R_BOLA * 2))
    gambar_lubang = muat_aset("lubang.png", (R_LUBANG * 2, R_LUBANG * 2))
    gambar_dinding = [muat_aset("tembok.png", d.size) for d in DINDING]
    gambar_tepi = [muat_aset("tembok.png", d.size) for d in DINDING_TEPI]

    try:
        while True:
            dt = min(jam.tick(FPS) / 1000.0, 0.05)
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                    return {"pukulan": pukulan, "menang": menang}
            g = sumber.baca()

            if state == "menang":
                if time.time() - waktu_menang > 2.5:
                    posisi_awal, posisi_lubang = spawn_ronde()
                    bola = Bola(posisi_awal)
                    lubang = pygame.Vector2(posisi_lubang)
                    arah = (lubang - bola.pos).normalize()
                    kunci = pygame.Vector2(arah)
                    pukulan, state = 0, "bidik"
            elif not bola.diam:
                state = "jalan"
            else:
                if state == "jalan":
                    state = "bidik"
                if state == "bidik":
                    if g.ada:
                        if g.arah_x is not None and g.arah_y is not None:
                            target = pygame.Vector2(g.arah_x, g.arah_y)
                        else:
                            a = math.radians(-180 + 360 * g.x_norm)
                            target = pygame.Vector2(math.cos(a), math.sin(a))
                        baru = arah * 0.25 + target * 0.75
                        if baru.length() > 1e-6:
                            arah = baru.normalize()
                    if g.ada and g.kepal:
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

            if gambar_lapangan:
                layar.blit(gambar_lapangan, (0, 0))
            else:
                layar.fill((0, 100, 0))
            for d, gambar in zip(DINDING_TEPI, gambar_tepi):
                if gambar:
                    layar.blit(gambar, d.topleft)
                else:
                    pygame.draw.rect(layar, (160, 82, 45), d)
            for d, gambar in zip(DINDING, gambar_dinding):
                if gambar:
                    layar.blit(gambar, d.topleft)
                else:
                    pygame.draw.rect(layar, (160, 82, 45), d)
            if gambar_lubang:
                layar.blit(gambar_lubang, gambar_lubang.get_rect(center=lubang))
            else:
                pygame.draw.circle(layar, (0, 0, 0), lubang, R_LUBANG)
            if gambar_bola:
                layar.blit(gambar_bola, gambar_bola.get_rect(center=bola.pos))
            else:
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
