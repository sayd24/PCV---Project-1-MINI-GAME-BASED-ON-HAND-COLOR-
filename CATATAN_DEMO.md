# Catatan Demo Mini-Golf Tangan

Catatan ini menjelaskan isi proyek dan urutan kerjanya. Tidak perlu menghafal setiap baris kode saat demo; pahami alur kamera, deteksi warna, pengenalan gerakan, lalu pengendalian bola.

## 1. Tujuan proyek

Proyek ini adalah game mini-golf sederhana yang arah bidik dan pukulannya dikendalikan dengan gerakan telunjuk dan jempol di depan kamera. Dua penanda dengan warna berbeda dipasang pada ujung jari agar posisi masing-masing mudah dilacak.

Game dibuat dengan **pengolahan citra klasik**, bukan machine learning. Program mengubah gambar kamera ke ruang warna HSV, menyaring warna penanda, lalu menghitung posisi titiknya. Hasil posisi dan jarak kedua jari diterjemahkan menjadi arah bidik dan gerakan menembak.

## 2. Isi folder

| File/folder | Kegunaan |
|---|---|
| `main.py` | Game, input kamera/keyboard, gerak bola, tabrakan, skor, dan tampilan. |
| `tangan.py` | Pembukaan kamera, konfigurasi, deteksi warna, hasil deteksi, dan pengenalan gestur. |
| `kalibrasi.py` | Mengambil warna penanda dan mengatur area deteksi melalui kamera. |
| `config.json` | Menyimpan kamera, batas warna HSV, ROI, dan jarak gestur hasil kalibrasi. |
| `requirements.txt` | Daftar pustaka Python yang diperlukan. |
| `assets/` | Gambar rumput, bola, lubang, tembok, dan panel UI. |

## 3. Alur program

1. Jalankan `kalibrasi.py` untuk memilih warna penanda dan mengukur jarak jari saat terbuka dan dirapatkan.
2. Kalibrasi disimpan ke `config.json`.
3. Saat `main.py` dimulai, program membaca konfigurasi dan membuka kamera.
4. Setiap frame kamera diproses untuk menemukan kedua penanda.
5. Posisi telunjuk mengatur arah, sedangkan jarak telunjuk-jempol menentukan gestur.
6. Game mengisi power ketika jari dirapatkan. Saat jari dibuka, bola ditembakkan.
7. Bola bergerak, melambat, dan memantul dari tembok. Jika masuk lubang, skor bertambah, waktu bertambah 20 detik, dan posisi ronde baru dipilih.
8. Permainan dimulai dengan 1 menit dan maksimal 9 pukulan. Setiap bola yang masuk menambah waktu 20 detik. Permainan selesai jika waktu habis atau semua pukulan digunakan.

## 4. Cara kerja pelacakan tangan

### Warna dan HSV

Di `tangan.py`, fungsi `_mask_warna()` memilih piksel yang berada dalam batas warna HSV dari konfigurasi. HSV memisahkan:

- **H (Hue):** jenis warna.
- **S (Saturation):** kuat atau pucatnya warna.
- **V (Value):** tingkat terang atau gelap.

Kalibrasi menyimpan batas minimum dan maksimum untuk H, S, dan V masing-masing penanda. OpenCV membuat mask: piksel yang sesuai menjadi putih, sementara yang tidak sesuai menjadi hitam. Hue pada OpenCV melingkar dari 179 kembali ke 0, jadi `_mask_warna()` menangani rentang yang melewati batas itu.

### Membersihkan mask dan mencari titik

Fungsi `deteksi()` melakukan langkah-langkah ini pada setiap frame:

1. Mengambil area gambar yang ditentukan ROI (area deteksi).
2. Menghaluskan gambar dengan Gaussian blur untuk mengurangi noise.
3. Mengubah BGR dari kamera ke HSV.
4. Membuat mask terpisah untuk telunjuk dan jempol.
5. Memakai operasi morfologi buka dan tutup untuk mengurangi bintik serta mengisi lubang kecil pada mask.
6. Memilih kontur terbesar yang melewati ukuran minimum.
7. Menghitung titik tengah kontur dengan momen.
8. Menghitung jarak antartitik dan mengembalikan hasil dalam objek `Hasil`.

ROI memperkecil area yang dicari agar warna serupa di latar lebih jarang terdeteksi dan pemrosesan lebih ringan. Penanda fisik tetap dibutuhkan; program tidak mengenali bentuk tangan atau tulang jari.

### Gestur

`PembacaGestur` mengubah hasil deteksi menjadi objek `Gestur` yang dipakai game. Jarak antarpenanda dibandingkan dengan jarak terbuka dan tertutup yang tersimpan:

- Jarak kecil berarti jari dirapatkan dan power diisi.
- Jarak besar berarti jari terbuka dan siap membidik atau menembak.
- Nilai di antara keduanya mempertahankan status sebelumnya agar gestur tidak mudah berubah karena sedikit noise.

Perubahan status perlu terdeteksi selama beberapa frame (`KONFIRMASI = 3`) supaya satu frame yang keliru tidak langsung dianggap sebagai gerakan. Jika titik hilang, pembaca mencatat durasi kehilangan dan mempertahankan status sebentar.

Arah bidik dihitung dari garis jempol ke telunjuk. Posisi telunjuk juga dinormalisasi di dalam ROI untuk input horizontal keyboard dan kompatibilitas gestur.

## 5. Penjelasan `kalibrasi.py`

- `rentang_warna_dari_klik()` membaca sampel warna di sekitar klik. Hue dihitung melingkar, sedangkan S dan V diberi toleransi agar sedikit perubahan pencahayaan masih dapat diterima.
- `main()` membuka kamera dan menampilkan gambar kamera serta mask hasil deteksi.
- Tampilan kalibrasi dibagi dua: gambar kamera dengan titik/ROI dan mask warna (hijau untuk telunjuk, ungu untuk jempol).
- Klik **kiri** pada telunjuk untuk menyimpan warna telunjuk; klik **kanan** pada jempol untuk menyimpan warna jempol.
- Slider ROI membatasi area gerak yang diperiksa. `Area minimum` mengabaikan kontur yang terlalu kecil.
- Tekan **o** saat jari terbuka untuk merekam jaraknya.
- Tekan **k** saat jari dirapatkan untuk merekam jaraknya.
- Tekan **s** untuk menyimpan jika warna dan kedua jarak sudah direkam dengan jarak terbuka lebih besar daripada jarak tertutup.
- Tekan **Esc** untuk keluar.

Gunakan kondisi cahaya, posisi kamera, dan penanda yang sama saat kalibrasi dan bermain. Bila warna sering hilang atau latar ikut terdeteksi, kalibrasi ulang dan sesuaikan ROI.

## 6. Penjelasan `main.py`

### Pengaturan lapangan

`W` dan `H` mengatur ukuran area lapangan (800×600), sedangkan `HUD_HEIGHT` menambah ruang panel di atasnya. `FPS` mengatur target frame per detik. `R_BOLA` dan `R_LUBANG` menentukan radius objek untuk fisika. `DINDING` menyimpan persegi panjang rintangan di dalam lapangan; `DINDING_TEPI` menyimpan tembok pinggir. Ukuran dan posisi tembok bisa diubah di bagian pengaturan ini.

Konstanta seperti `FRIKSI`, `RESTITUSI`, `MIN_POWER`, dan `MAX_POWER` mengatur perlambatan, pantulan, serta kekuatan tembakan.

### Posisi ronde dan aset

- `posisi_spawn_aman(radius)` mencoba posisi acak di dalam tembok dan menolak posisi yang terlalu dekat dengan rintangan.
- `spawn_ronde()` mencari posisi awal dan lubang yang tidak terlalu berdekatan.
- `muat_aset(nama, ukuran)` memuat gambar dari `assets/` dan menyesuaikan ukurannya. Jika file tidak ada, fungsi mengembalikan `None`; game menggambar bentuk sederhana sebagai pengganti.

### Gerak dan tabrakan bola

Kelas `Bola` menyimpan posisi (`pos`) dan kecepatan (`vel`) sebagai `pygame.Vector2`.

- `diam` bernilai benar jika kecepatan bola nol.
- `_pantul(normal)` membalik komponen kecepatan yang menuju permukaan, dengan besar pantulan dipengaruhi `RESTITUSI`.
- `_tabrak_batas()` menjaga bola tetap di dalam batas tembok pinggir.
- `_tabrak_rect(rect)` mencari jarak bola ke rintangan persegi. Jika bertabrakan, bola didorong keluar lalu dipantulkan.
- `langkah(dt)` memperbarui kecepatan dan posisi. `dt` adalah lama frame, sehingga gerak mengikuti waktu, bukan hanya jumlah frame. Gerakan dibagi menjadi langkah kecil agar bola lebih sulit menembus tembok tipis.

### Sumber input

- `InputKamera` membaca konfigurasi, memeriksa kelengkapan kalibrasi, membuka kamera, membalik gambar secara horizontal, lalu mengirim frame ke `deteksi()` dan `PembacaGestur`. Preview menampilkan kamera dan mask agar deteksi bisa diperiksa.
- `InputKeyboard` menjadi alternatif tanpa kamera. Panah kiri/kanan mengubah arah bidik dan tombol spasi mengisi power.
- Keduanya menyediakan `baca()` dengan hasil bertipe `Gestur`, sehingga loop game tidak perlu mengetahui detail sumber input.
- `tutup()` melepas sumber daya ketika permainan selesai.

### Loop game

`jalankan()` menyiapkan jendela, font, posisi bola dan lubang, lalu berulang kali:

1. Menghitung waktu frame dan membaca tombol keluar.
2. Membaca gestur dari sumber input.
3. Memperbarui status permainan:
   - `bidik`: arah mengikuti input.
   - `isi`: arah dikunci dan power naik-turun di antara batas minimum dan maksimum.
   - `jalan`: bola bergerak.
   - `menang`: bola sudah masuk, skor bertambah, lalu ronde baru dimulai setelah jeda.
4. Memperbarui fisika dan mengecek apakah bola masuk lubang dengan kecepatan yang cukup rendah.
5. Menggambar latar, tembok, lubang, bola, panah bidik, indikator power, dan informasi permainan.

Blok `finally` memastikan kamera dan Pygame ditutup ketika game keluar, termasuk jika terjadi kesalahan saat loop berjalan.

`main()` membaca pilihan command line. Tanpa pilihan, game memakai kamera. `--keyboard` menjalankan game tanpa kamera. `--tanpa-preview` menyembunyikan jendela preview kamera.

Status bidik, power, jarak, dan petunjuk gerakan ditampilkan di sisi mask pada preview kamera. Preview kamera dan mask berukuran ringkas agar dapat ditaruh berdampingan dengan jendela game. Panel babak, sisa pukulan, dan waktu berada di ruang atas lapangan; area lapangan tetap 800×600. Font panel dapat diganti dengan menaruh `font.ttf` di `assets/`; nama file diatur oleh `HUD_FONT_FILE` di `main.py`, dan font bawaan dipakai jika file tersebut tidak ditemukan.

## 7. Isi `config.json`

| Kelompok nilai | Arti |
|---|---|
| `kamera` | Nomor perangkat kamera yang digunakan. |
| `roi_atas`, `roi_bawah`, `roi_kiri`, `roi_kanan` | Batas area deteksi, berupa nilai relatif 0 sampai 1. |
| `min_area` | Luas kontur minimum agar dianggap sebagai penanda. |
| `radius_sampel` | Ukuran area sampel saat warna diklik pada proses kalibrasi. |
| `index_h_*`, `index_s_*`, `index_v_*` | Batas warna penanda telunjuk dalam HSV. |
| `jempol_h_*`, `jempol_s_*`, `jempol_v_*` | Batas warna penanda jempol dalam HSV. |
| `*_terkalibrasi` | Penanda apakah warna dan jarak gestur sudah direkam. |
| `jarak_buka`, `jarak_tutup` | Jarak relatif kedua penanda saat jari terbuka dan dirapatkan. |

Sebaiknya ubah nilai ini melalui `kalibrasi.py`. Nilai HSV dapat berbeda jika kamera atau pencahayaan berubah.

## 8. Pustaka yang digunakan

- **OpenCV (`cv2`)**: membaca kamera, mengolah gambar, mengubah warna, dan mencari kontur.
- **NumPy**: mengolah array gambar dan perhitungan numerik.
- **Pygame**: jendela game, gambar, input keyboard, waktu frame, dan vektor fisika.
- **Modul standar Python**: `argparse` untuk pilihan jalankan, `random` untuk posisi ronde, `math` untuk perhitungan, `time` untuk waktu, dan `pathlib` untuk lokasi aset.

## 9. Urutan demo yang disarankan

1. Tunjukkan penanda berbeda pada telunjuk dan jempol.
2. Jalankan kalibrasi, klik kedua warna, rekam jarak terbuka dan rapat, lalu simpan.
3. Tunjukkan preview kamera dan mask untuk menjelaskan hasil segmentasi warna.
4. Jalankan game dan gerakkan telunjuk untuk membidik.
5. Rapatkan jari untuk mengisi power, lalu buka untuk menembak.
6. Tunjukkan bola memantul dari tembok dan masuk ke lubang.
7. Sebutkan bahwa versi keyboard dapat dipakai jika kamera tidak tersedia.

## 10. Pertanyaan yang mungkin muncul

**Apakah proyek ini menggunakan AI atau machine learning?**  
Tidak. Deteksi menggunakan ambang warna HSV dan operasi citra OpenCV; program tidak dilatih dengan dataset.

**Kenapa perlu penanda warna?**  
Kamera biasa tidak mengetahui telunjuk dan jempol hanya dari warna kulit. Dua warna penanda membantu program membedakan posisi kedua jari.

**Kenapa perlu kalibrasi ulang?**  
Nilai warna yang terlihat kamera dipengaruhi pencahayaan, kamera, dan posisi penanda.

**Apa fungsi ROI?**  
ROI membatasi area pencarian warna agar proses lebih ringan dan objek berwarna serupa di luar area gerak diabaikan.

**Bagaimana bola memantul?**  
Program mendeteksi tabrakan bola dengan batas atau persegi panjang tembok, lalu membalik komponen kecepatannya yang mengarah ke permukaan.

**Apa yang dilakukan saat aset gambar belum ada?**  
Game menggambar bola, lubang, atau tembok dengan bentuk sederhana sebagai pengganti.
