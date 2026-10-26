# Mini-Golf Tangan (pengolahan citra klasik, tanpa ML)

Input kamera melacak dua penanda berwarna yang berbeda: satu di telunjuk dan satu di jempol.
Warna dikalibrasi terpisah dalam HSV, lalu dicari hanya di dalam ROI. Garis dari penanda jempol
ke penanda telunjuk menjadi arah bidik; jarak kedua penanda menentukan apakah jari terbuka untuk
membidik atau dirapatkan untuk mengisi power.

## Jalankan
```
pip install -r requirements.txt
python kalibrasi.py        # sekali, di tempat & cahaya yang sama dengan saat main
python main.py             # main dengan kamera
python main.py --keyboard  # coba game tanpa kamera (<- ->, tahan SPASI)
```

## Kalibrasi (kalibrasi.py)
Pasang penanda berwarna yang kontras dan berbeda pada ujung telunjuk dan jempol tangan kanan.
Gunakan cahaya yang sama saat bermain, dan jaga agar kedua penanda tampak oleh kamera.

1. Klik kiri tepat pada penanda telunjuk; klik kanan tepat pada penanda jempol.
   Panel mask memperlihatkan telunjuk hijau dan jempol ungu. Ulangi klik bila warna tertangkap
   kurang tepat atau berubah karena pencahayaan.
2. Atur kotak biru dengan slider ROI atas/bawah/kiri/kanan. Kotak hanya perlu mencakup area
   gerak dua jari; kecilkan untuk menghindari warna lain di latar. `Area minimum` membuang bintik.
3. Buka/renggangkan kedua jari seperti posisi membidik, tunggu kedua titik terdeteksi, lalu tekan
   **o** untuk merekam jarak terbuka.
4. Dekatkan telunjuk dan jempol seperti posisi menahan power, lalu tekan **k** untuk merekam
   jarak rapat. Jarak terbuka harus jelas lebih besar.
5. Tekan **s** untuk menyimpan ke `config.json`. **Esc** keluar.

## Cara main
- Jari terbuka: panah mengikuti garis lurus dari jempol menuju telunjuk.
- Rapatkan telunjuk dan jempol lalu tahan: arah terkunci dan power terisi.
- Buka kembali: tembak.
- Setelah bola masuk lubang, posisi titik pukul dan lubang berpindah secara acak untuk ronde berikutnya.
- Rintangan tembok dibuat lebih banyak dengan susunan dan orientasi yang bervariasi.

## Aset game
Simpan gambar PNG transparan di folder `assets/` dengan nama berikut:
- `rumput.png` untuk tekstur rumput seluruh lapangan (ukuran akan disesuaikan ke jendela game).
- `bola.png` untuk bola.
- `lubang.png` untuk lubang.
- `tembok.png` untuk seluruh tembok.

Gambar akan disesuaikan ukurannya oleh game. Jika aset belum tersedia, game tetap menggunakan latar hijau atau bentuk sederhana sebagai pengganti.

## Jika bermasalah
| Gejala | Coba |
|---|---|
| Kamera gagal dibuka | ubah `"kamera"` di config.json (0, 1, 2) |
| Penanda tidak terlacak | klik ulang tepat di tengah penanda; pastikan warnanya beda dan ROI mencakup keduanya |
| Mask menangkap warna latar | rapatkan ROI menghindari latar; pilih warna penanda yang kontras; kalibrasi ulang |
| Mode terbuka/rapat sering salah | rekam ulang o dan k dengan selisih jarak yang lebih besar |
| Arah panah bergetar | gerakkan telunjuk lebih pelan dan pastikan penanda tidak tertutup jari |

## Catatan
- Deteksi memakai warna penanda, bukan warna kulit. Penanda fisik dengan warna berbeda diperlukan
  untuk mengetahui jari mana yang menjadi telunjuk dan jempol.
- Perubahan pencahayaan atau kamera dapat mengubah HSV; ulangi kalibrasi warna bila perlu.
- Kontur terbesar dari setiap warna dipakai sebagai titik jari. Hindari objek lain dengan warna
  serupa di dalam ROI.
