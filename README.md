# MINI GAME BASED ON HAND COLOR

- **Nama:** Muhammad Sayyid Tsabit
- **NRP:** 5024241013
- **Mata kuliah:** Pengolahan Sinyal Digital

Proyek ini adalah game mini-golf yang sepenuhnya dikendalikan dengan gerakan jari yang ditangkap kamera.

## Pengolahan citra dan video

Kamera menghasilkan video berupa rangkaian frame. Program memproses setiap frame menggunakan OpenCV. Frame dihaluskan untuk mengurangi noise, diubah dari BGR ke HSV, lalu dibatasi pada area deteksi (ROI). HSV digunakan agar warna penanda lebih mudah dipisahkan dari latar.

Program membuat mask berdasarkan rentang warna penanda telunjuk dan jempol yang disimpan saat kalibrasi. Mask dibersihkan dengan operasi morfologi, lalu kontur terbesar dicari untuk mendapatkan titik tengah masing-masing penanda. Jarak dan posisi titik dari frame digunakan untuk membaca gestur dan arah bidik.

Saat jari dirapatkan, kekuatan pukulan terisi. Saat jari dibuka kembali, bola ditembakkan. Gerakan bola dan tampilan permainan dijalankan menggunakan Pygame.

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

## Aset

Simpan gambar PNG di folder `assets/`:

- `rumput.png` untuk lapangan
- `bola.png` untuk bola
- `lubang.png` untuk lubang
- `tembok.png` untuk tembok
- `babak.png`, `sisapukulan.png`, dan `waktu.png` untuk panel informasi game

Panel babak, sisa pukulan, dan waktu berada di area atas jendela game; ukuran lapangannya tetap 800×600. Preview kamera dan mask berukuran 480×360, seperti saat kalibrasi, dan ditampilkan berdampingan dengan game. Nilai jarak pada preview dihitung dari deteksi frame yang sama, bukan dari ukuran tampilan preview.

Tambahkan `font.ttf` di folder `assets/` jika ingin memakai font khusus pada panel game. Jika tidak ada, game memakai font bawaan Pygame. Gambar aset yang tidak tersedia akan memakai tampilan sederhana sebagai pengganti.
