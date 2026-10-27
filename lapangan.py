import math
import random

import pygame

from pengaturan import (
    BERHENTI_DI_BAWAH, DINDING, DINDING_PINGGIR, FRIKSI, H, R_BOLA, R_LUBANG,
    RESTITUSI, W,
)


def posisi_spawn_aman(radius):
    batas_x = (radius + DINDING_PINGGIR + 8, W - radius - DINDING_PINGGIR - 8)
    batas_y = (radius + DINDING_PINGGIR + 8, H - radius - DINDING_PINGGIR - 8)
    for _ in range(500):
        posisi = pygame.Vector2(random.uniform(*batas_x), random.uniform(*batas_y))
        if not any(d.inflate(radius * 2, radius * 2).collidepoint(posisi) for d in DINDING):
            return posisi
    raise RuntimeError("Tidak menemukan posisi spawn aman. Periksa susunan tembok.")


def spawn_ronde():
    for _ in range(500):
        mulai = posisi_spawn_aman(R_BOLA + 8)
        lubang = posisi_spawn_aman(R_LUBANG + 8)
        if mulai.distance_to(lubang) >= 320:
            return mulai, lubang
    raise RuntimeError("Tidak menemukan pasangan posisi spawn yang cukup berjauhan.")


class Bola:
    def __init__(self, pos):
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2()

    @property
    def diam(self):
        return self.vel.length_squared() == 0

    def _pantul(self, normal):
        vn = self.vel.dot(normal)
        if vn < 0:
            self.vel -= (1 + RESTITUSI) * vn * normal

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
        dekat = pygame.Vector2(max(rect.left, min(self.pos.x, rect.right)),
                               max(rect.top, min(self.pos.y, rect.bottom)))
        delta = self.pos - dekat
        jarak = delta.length()
        if jarak >= R_BOLA:
            return
        if jarak > 1e-9:
            normal = delta / jarak
            self.pos = dekat + normal * R_BOLA
        else:
            sisi = {
                (-1, 0): self.pos.x - rect.left, (1, 0): rect.right - self.pos.x,
                (0, -1): self.pos.y - rect.top, (0, 1): rect.bottom - self.pos.y,
            }
            (nx, ny), jarak = min(sisi.items(), key=lambda item: item[1])
            normal = pygame.Vector2(nx, ny)
            self.pos += normal * (jarak + R_BOLA)
        self._pantul(normal)

    def langkah(self, dt):
        self.vel *= FRIKSI ** (dt * 60)
        cepat = self.vel.length()
        if cepat < BERHENTI_DI_BAWAH:
            self.vel.update(0, 0)
            return
        langkah = max(1, math.ceil(cepat * dt / (R_BOLA * 0.5)))
        for _ in range(langkah):
            self.pos += self.vel * dt / langkah
            self._tabrak_batas()
            for dinding in DINDING:
                self._tabrak_rect(dinding)
