import argparse
import math
import time

import pygame

from aset_game import gambar_panah, gambar_panel, muat_aset, muat_font, muat_panel
from input_kamera import InputKamera
from lapangan import Bola, spawn_ronde
from pengaturan import (
    BATAL_JIKA_HILANG, BATAS_PUKULAN, BONUS_WAKTU, DINDING, DINDING_TEPI, FPS,
    H, HUD_HEIGHT, HUD_POSITIONS, KECEPATAN_MASUK_LUBANG, MAX_POWER, MIN_POWER,
    PANAH_MAX, PANAH_MIN, POWER_SPEED, R_BOLA, R_LUBANG, W, WAKTU_AWAL,
)
def jalankan(sumber, max_detik=None):
    pygame.init()
    layar = pygame.display.set_mode((W, H + HUD_HEIGHT))
    pygame.display.set_caption("Mini-Golf Tangan")
    area = layar.subsurface((0, HUD_HEIGHT, W, H))
    jam = pygame.time.Clock()
    font, font_nilai = muat_font(18), muat_font(30)
    font.set_bold(True)
    font_nilai.set_bold(True)
    besar = muat_font(54)

    posisi_awal, posisi_lubang = spawn_ronde()
    lubang = pygame.Vector2(posisi_lubang)
    bola = Bola(posisi_awal)
    arah = (lubang - bola.pos).normalize()
    kunci = pygame.Vector2(arah)
    state, power, naik = "bidik", MIN_POWER, 1
    pukulan, total_pukulan, menang = 0, 0, 0
    bonus_waktu = 0.0
    waktu_menang = 0.0
    alasan_selesai = ""

    def hasil_akhir(sisa_waktu, status):
        return {
            "pukulan": total_pukulan,
            "menang": menang,
            "waktu_sisa": sisa_waktu,
            "bonus_waktu": bonus_waktu,
            "status": status,
        }

    gambar_lapangan = muat_aset("rumput.png", (W, H))
    gambar_bola = muat_aset("bola.png", (R_BOLA * 2, R_BOLA * 2))
    gambar_lubang = muat_aset("lubang.png", (R_LUBANG * 2, R_LUBANG * 2))
    gambar_dinding = [muat_aset("tembok.png", d.size) for d in DINDING]
    gambar_tepi = [muat_aset("tembok.png", d.size) for d in DINDING_TEPI]
    gambar_hud = [
        muat_panel("babak.png"),
        muat_panel("sisapukulan.png"),
        muat_panel("waktu.png"),
    ]
    mulai = time.monotonic()

    try:
        while True:
            dt = min(jam.tick(FPS) / 1000.0, 0.05)
            sekarang = time.monotonic()
            sisa_waktu = max(0.0, WAKTU_AWAL + bonus_waktu - (sekarang - mulai))
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                    return hasil_akhir(sisa_waktu, alasan_selesai or state)
            g = sumber.baca()

            if state != "selesai" and sisa_waktu <= 0:
                state, alasan_selesai = "selesai", "WAKTU HABIS"
            elif state == "menang":
                if sekarang - waktu_menang > 2.5:
                    if total_pukulan >= BATAS_PUKULAN:
                        state, alasan_selesai = "selesai", "BATAS PUKULAN TERCAPAI"
                    else:
                        posisi_awal, posisi_lubang = spawn_ronde()
                        bola = Bola(posisi_awal)
                        lubang = pygame.Vector2(posisi_lubang)
                        arah = (lubang - bola.pos).normalize()
                        kunci = pygame.Vector2(arah)
                        pukulan, state = 0, "bidik"
            elif state == "selesai":
                pass
            elif not bola.diam:
                state = "jalan"
            else:
                if state == "jalan":
                    if total_pukulan >= BATAS_PUKULAN:
                        state, alasan_selesai = "selesai", "BATAS PUKULAN TERCAPAI"
                    else:
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
                        total_pukulan += 1
                        state = "jalan"
                    else:
                        power += POWER_SPEED * dt * naik
                        if power >= MAX_POWER:
                            power, naik = MAX_POWER, -1
                        elif power <= MIN_POWER:
                            power, naik = MIN_POWER, 1

            if state not in ("menang", "selesai"):
                bola.langkah(dt)
                if bola.pos.distance_to(lubang) <= R_LUBANG and bola.vel.length() < KECEPATAN_MASUK_LUBANG:
                    bola.pos, bola.vel = pygame.Vector2(lubang), pygame.Vector2(0, 0)
                    state, menang, waktu_menang = "menang", menang + 1, sekarang
                    bonus_waktu += BONUS_WAKTU

            layar.fill((22, 36, 31))
            area.fill((28, 43, 27))
            if gambar_lapangan:
                area.blit(gambar_lapangan, (0, 0))
            else:
                pygame.draw.rect(area, (0, 100, 0), (0, 0, W, H))
            for d, gambar in zip(DINDING_TEPI, gambar_tepi):
                if gambar:
                    area.blit(gambar, d.topleft)
                else:
                    pygame.draw.rect(area, (160, 82, 45), d)
            for d, gambar in zip(DINDING, gambar_dinding):
                if gambar:
                    area.blit(gambar, d.topleft)
                else:
                    pygame.draw.rect(area, (160, 82, 45), d)
            if gambar_lubang:
                area.blit(gambar_lubang, gambar_lubang.get_rect(center=lubang))
            else:
                pygame.draw.circle(area, (0, 0, 0), lubang, R_LUBANG)
            if gambar_bola:
                area.blit(gambar_bola, gambar_bola.get_rect(center=bola.pos))
            else:
                pygame.draw.circle(area, (255, 255, 255), bola.pos, R_BOLA)

            if state in ("bidik", "isi"):
                p = (power - MIN_POWER) / (MAX_POWER - MIN_POWER) if state == "isi" else 0.0
                panjang = PANAH_MIN + (PANAH_MAX - PANAH_MIN) * p
                warna = (int(255 * p), int(220 * (1 - p)) + 35, 0) if state == "isi" else (255, 255, 0)
                gambar_panah(area, bola.pos + (kunci if state == "isi" else arah) * (R_BOLA + 4),
                             kunci if state == "isi" else arah, panjang, warna)
            if state == "isi":
                pygame.draw.rect(area, (110, 110, 110), (20, 20, 200, 20))
                pygame.draw.rect(area, (50, 220, 50), (20, 20, int(200 * p), 20))
                pygame.draw.rect(area, (255, 255, 255), (20, 20, 200, 20), 2)

            panel_ui = (
                ("Babak", str(menang + 1)),
                ("Sisa Pukulan", str(max(0, BATAS_PUKULAN - total_pukulan))),
                ("Waktu", f"{int(sisa_waktu) // 60:02}:{int(sisa_waktu) % 60:02}"),
            )
            for gambar, x, (judul, nilai) in zip(gambar_hud, HUD_POSITIONS, panel_ui):
                gambar_panel(layar, gambar, x, judul, nilai, font, font_nilai)
            if state == "menang":
                t = besar.render(f"HOLE IN! ({pukulan} pukulan)", True, (255, 215, 0))
                area.blit(t, t.get_rect(center=(W // 2, H // 2)))
            elif state == "selesai":
                t = besar.render("PERMAINAN SELESAI", True, (255, 215, 0))
                area.blit(t, t.get_rect(center=(W // 2, H // 2 - 25)))
                alasan = font.render("Tekan Esc untuk keluar", True, (255, 255, 255))
                area.blit(alasan, alasan.get_rect(center=(W // 2, H // 2 + 20)))
            pygame.display.flip()

            if max_detik is not None and sekarang - mulai > max_detik:
                return hasil_akhir(sisa_waktu, alasan_selesai or state)
    finally:
        sumber.tutup()
        pygame.quit()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tanpa-preview", action="store_true", help="sembunyikan jendela kamera")
    args = ap.parse_args()
    try:
        sumber = InputKamera(preview=not args.tanpa_preview)
    except RuntimeError as e:
        print("Error:", e)
        return
    print(jalankan(sumber))


if __name__ == "__main__":
    main()
