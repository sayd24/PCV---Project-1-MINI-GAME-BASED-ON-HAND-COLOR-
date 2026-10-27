import pygame

W, H, FPS = 800, 600, 120
HUD_HEIGHT = 118
HUD_PANEL_SIZE = (184, 110)
HUD_POSITIONS = (108, 308, 508)
PREVIEW_SIZE = (240, 180)
HUD_FONT_FILE = "font.ttf"

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

FRIKSI = 0.98
BERHENTI_DI_BAWAH = 6.0
RESTITUSI = 0.8
MIN_POWER, MAX_POWER = 120.0, 1200.0
POWER_SPEED = 840.0
PANAH_MIN, PANAH_MAX = 40, 220
BATAL_JIKA_HILANG = 0.6
KECEPATAN_MASUK_LUBANG = 250.0
WAKTU_AWAL = 60.0
BONUS_WAKTU = 20.0
BATAS_PUKULAN = 9
