from pathlib import Path

import numpy as np
import pygame

from pengaturan import HUD_FONT_FILE, HUD_PANEL_SIZE

ASSET_DIR = Path(__file__).resolve().parent / "assets"


def muat_aset(nama, ukuran):
    path = ASSET_DIR / nama
    if not path.is_file():
        return None
    gambar = pygame.image.load(str(path)).convert_alpha()
    return pygame.transform.smoothscale(gambar, ukuran)


def muat_panel(nama):
    path = ASSET_DIR / nama
    if not path.is_file():
        return None
    gambar = pygame.image.load(str(path)).convert_alpha()
    alpha = pygame.surfarray.array_alpha(gambar)
    isi = np.flatnonzero(np.count_nonzero(alpha > 32, axis=0) > gambar.get_width() * 0.12)
    if isi.size:
        atas = max(0, int(isi[0]) - 28)
        bawah = min(gambar.get_height(), int(isi[-1]) + 17)
        gambar = gambar.subsurface((0, atas, gambar.get_width(), bawah - atas)).copy()
    return pygame.transform.smoothscale(gambar, HUD_PANEL_SIZE)


def muat_font(ukuran):
    path = ASSET_DIR / HUD_FONT_FILE
    return pygame.font.Font(str(path) if path.is_file() else None, ukuran)


def gambar_panel(layar, gambar, x, judul, nilai, font, font_nilai):
    if gambar:
        layar.blit(gambar, (x, 4))
    tengah_x = x + HUD_PANEL_SIZE[0] * 0.64
    for teks, jenis_font, y in (
        (judul, font, 3 + HUD_PANEL_SIZE[1] * 0.41),
        (nilai, font_nilai, 3 + HUD_PANEL_SIZE[1] * 0.64),
    ):
        tulisan = jenis_font.render(teks, True, (255, 244, 214))
        rect = tulisan.get_rect(center=(tengah_x, y))
        layar.blit(jenis_font.render(teks, True, (48, 23, 9)), rect.move(1, 2))
        layar.blit(tulisan, rect)


def gambar_panah(layar, mulai, arah, panjang, warna):
    ujung = mulai + arah * panjang
    dasar = ujung - arah * 18
    tegak = pygame.Vector2(-arah.y, arah.x)
    pygame.draw.line(layar, warna, mulai, dasar, 5)
    pygame.draw.polygon(layar, warna, [ujung, dasar + tegak * 10, dasar - tegak * 10])
