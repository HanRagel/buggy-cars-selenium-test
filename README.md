# Buggy Cars Rating – Selenium Test Otomasyonu

[Buggy Cars Rating](https://buggy.justtestit.org) web uygulamasının **Overall Rating** sayfasındaki tablo işlevleri ve sayfalama (pagination) özelliği için hazırlanmış manuel ve otomatik test çalışması.

> Yazılım Test ve Doğrulama dersi ödevi – Gökhan Rauf Yangel

## Kullanılan Teknolojiler

- Python 3
- Selenium WebDriver 4
- Google Chrome / ChromeDriver (Selenium Manager ile otomatik kurulur)

## Kurulum ve Çalıştırma

```bash
# Sanal ortam oluştur ve etkinleştir
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / macOS

# Bağımlılıkları kur
pip install -r requirements.txt

# Testleri çalıştır
python overall_test.py
```

Test sonuçları ekrana ve `sonuclar.txt` dosyasına yazılır. Hata bulunan durumlarda `hata_<no>_<ad>.png` adıyla ekran görüntüsü kaydedilir.

## Test Senaryoları

| No | Senaryo | Kontrol edilenler | Sonuç |
|----|---------|-------------------|-------|
| T1 | Tüm sayfaları » ile gezme | Görseller, boş hücreler, Rank/Votes sırası, sayfalar arası tekrar | ❌ Hata |
| T2 | Geri butonu | Son sayfadan ilk sayfaya « ile dönüş | ✅ Geçti |
| T3 | Sınır değerler | İlk sayfada «, son sayfada » davranışı | ❌ Hata |
| T4 | Sayfa numarası kutusu | Geçerli (3) ve geçersiz (10, 0, -1) değerler | ❌ Hata |
| T5 | Rank başlığına göre sıralama | Sayısal sıralama | ❌ Hata |
| T6 | Model bağlantısı | Doğru model sayfasının açılması | ✅ Geçti |

**Toplam:** 29 kontrol, 25 başarılı, 4 hata

## Bulunan Hatalar (Overall Rating)

| # | Hata | Önem |
|---|------|------|
| 1 | Lancia Ypsilon satırında araç görseli yüklenmiyor (`lancia-ypsilon.jpg` sunucuda yok) | Orta |
| 2 | Rank başlığına tıklanınca sıralama sayısal değil metinsel yapılıyor (1, 10, 11, 12, 13) | Yüksek |
| 3 | Sayfa kutusu toplam sayfadan büyük değeri kabul ediyor ("page 10 of 5", tablo boş) | Orta |
| 4 | Son sayfada » butonu aktif kalıyor ve 6. sayfaya gidiyor | Orta |

Manuel testte kayıt, giriş ve model sayfalarında bulunan 7 hata daha ile birlikte tüm bulgular, yeniden üretme adımları ve ekran görüntüleri test raporunda yer almaktadır.

## Proje Yapısı

```
├── overall_test.py      # Selenium test betiği
├── requirements.txt     # Python bağımlılıkları
├── rapor/               # Test raporu (PDF)
└── README.md
```

## Lisans

Bu proje [MIT Lisansı](LICENSE) ile lisanslanmıştır.
