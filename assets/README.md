# Aset game

Letakkan gambar PNG transparan di folder ini:

- `rumput.png` untuk tekstur rumput seluruh lapangan.
- `bola.png` untuk bola.
- `lubang.png` untuk lubang.
- `tembok.png` untuk semua tembok.
- `babak.png`, `sisapukulan.png`, dan `waktu.png` untuk panel UI game.
- `font.ttf` (opsional) untuk font angka dan label UI.

Game otomatis menyesuaikan gambar aset ke ukuran yang digunakan. Jika `font.ttf` tidak ada, game memakai font bawaan Pygame. Panel UI berada di ruang atas jendela, di luar area lapangan 800×600.

Teks pada panel UI digambar oleh game, sehingga angka babak, pukulan, dan waktu dapat berubah.
