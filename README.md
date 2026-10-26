# Mini-Golf Tangan

Proyek ini adalah game mini-golf yang dimainkan dengan gerakan jari di depan kamera. Game juga bisa dicoba dengan keyboard.

## Cara kerja

Kamera melacak penanda dengan warna berbeda pada telunjuk dan jempol. OpenCV mengubah gambar ke HSV, lalu mencari warna penanda di area yang sudah dipilih. Posisi kedua penanda dipakai untuk menentukan arah bidik, sedangkan jaraknya dipakai untuk mengenali jari terbuka atau dirapatkan.

Saat jari dirapatkan, power terisi. Saat dibuka kembali, bola ditembakkan. Bola bergerak dan memantul dari tembok menggunakan simulasi sederhana di Pygame.

## Menjalankan

Pasang dependensi:

```bash
pip install -r requirements.txt
```

Kalibrasi penanda dan kamera:

```bash
python kalibrasi.py
```

Jalankan game:

```bash
python main.py
```

Untuk mencoba tanpa kamera:

```bash
python main.py --keyboard
```

Pada mode keyboard, gunakan panah kiri/kanan untuk membidik dan tahan spasi untuk mengisi power. Tekan Esc untuk keluar.

## Aset

Simpan gambar PNG di folder `assets/`:

- `rumput.png` untuk lapangan
- `bola.png` untuk bola
- `lubang.png` untuk lubang
- `tembok.png` untuk tembok

Jika gambar tidak tersedia, game menggunakan tampilan sederhana sebagai pengganti.
