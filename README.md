# Mini-Golf Tangan

Proyek ini adalah game mini-golf yang dimainkan dengan gerakan jari di depan kamera. Game juga bisa dicoba dengan keyboard.

## Cara kerja

Kamera melacak penanda dengan warna berbeda pada telunjuk dan jempol. OpenCV mengubah gambar ke HSV, lalu mencari warna penanda di area yang sudah dipilih. Posisi kedua penanda dipakai untuk menentukan arah bidik, sedangkan jaraknya dipakai untuk mengenali jari terbuka atau dirapatkan.

Saat jari dirapatkan, power terisi. Saat dibuka kembali, bola ditembakkan. Bola bergerak dan memantul dari tembok menggunakan simulasi sederhana di Pygame.

Permainan dimulai dengan waktu 1 menit dan batas 9 pukulan. Setiap bola yang masuk menambah waktu 20 detik. Permainan selesai jika waktu habis atau batas pukulan tercapai.

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
- `babak.png`, `sisapukulan.png`, dan `waktu.png` untuk panel informasi game

Panel babak, sisa pukulan, dan waktu berada di area atas jendela game; ukuran lapangannya tetap 800×600. Preview kamera dan mask dibuat ringkas dan ditampilkan berdampingan dengan game.

Tambahkan `font.ttf` di folder `assets/` jika ingin memakai font khusus pada panel game. Jika tidak ada, game memakai font bawaan Pygame. Gambar aset yang tidak tersedia akan memakai tampilan sederhana sebagai pengganti.
