"""
Buggy Cars Rating - Overall Rating sayfası otomasyon testi
Tablo işlevleri ve sayfalama (pagination) Selenium ile test edilir.

Çalıştırma:  python overall_test.py
Sonuçlar hem ekrana yazılır hem de sonuclar.txt dosyasına kaydedilir.
Hata bulunan durumlarda hata_<no>_<ad>.png ekran görüntüsü alınır.
"""
import re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException

URL = "https://buggy.justtestit.org/overall"

driver = webdriver.Chrome()          # Chrome'u açar, sürücüyü otomatik indirir
driver.maximize_window()
wait = WebDriverWait(driver, 15)     # Bir eleman için en fazla 15 sn bekler

kayitlar = []       # Ekrana yazılan her satır (sonuclar.txt'ye de yazılır)
hatalar = []        # Bulunan hatalar
basarililar = []    # Hatasız geçen testler


# =====================================================================
# KAYIT FONKSİYONLARI
# =====================================================================

def log(metin):
    """Hem ekrana yazar hem de sonuclar.txt için saklar."""
    print(metin)
    kayitlar.append(metin)


def hata_ekle(baslik, aciklama, ekran_adi=None):
    """Hatayı listeye ekler, ekrana yazar, istenirse ekran görüntüsü alır."""
    no = len(hatalar) + 1
    if ekran_adi:
        driver.save_screenshot(f"hata_{no}_{ekran_adi}.png")
    hatalar.append((baslik, aciklama))
    log(f"  [HATA #{no}] {baslik}\n      {aciklama}")


def basarili(test_adi):
    basarililar.append(test_adi)
    log(f"  [GEÇTİ] {test_adi}")


# =====================================================================
# YARDIMCI FONKSİYONLAR
# =====================================================================

def tablo_yuklenene_kadar_bekle():
    """Angular veriyi sonradan getirdiği için satırlar gelene kadar bekler."""
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
    time.sleep(1.5)


def satirlar():
    return driver.find_elements(By.CSS_SELECTOR, "table tbody tr")


def basliklar():
    return [th.text.strip() for th in driver.find_elements(By.CSS_SELECTOR, "table thead th")]


def tabloyu_oku():
    """Tabloyu [{'Make': 'Lamborghini', 'Model': 'Diablo', 'Rank': '1', ...}, ...] olarak döndürür.
    Angular tabloyu yeniden çizerken elemanlar 'bayatlayabilir' (StaleElementReferenceException).
    Bu durumda okuma en fazla 3 kez tekrarlanır."""
    for deneme in range(3):
        try:
            tablo_yuklenene_kadar_bekle()
            b = basliklar()
            veriler = []
            for satir in satirlar():
                hucreler = [td.text.strip() for td in satir.find_elements(By.TAG_NAME, "td")]
                veriler.append(dict(zip(b, hucreler)))
            return veriler
        except StaleElementReferenceException:
            time.sleep(1)
    raise RuntimeError("Tablo 3 denemede de okunamadı")


def ileri_butonu():
    return driver.find_element(By.XPATH, "//a[normalize-space()='»']")


def geri_butonu():
    return driver.find_element(By.XPATH, "//a[normalize-space()='«']")


def sayfa_kutusu():
    # » butonundan hemen önce gelen input = sayfa numarası kutusu
    return driver.find_element(By.XPATH, "//a[normalize-space()='»']/preceding::input[1]")


def sayfa_bilgisi():
    """Sayfalama alanındaki 'page 2 of 5' yazısından (2, 5) değerini çıkarır."""
    alan = driver.find_element(By.XPATH, "//a[normalize-space()='»']/parent::*").text
    eslesme = re.search(r"page\s+(\d+)\s+of\s+(\d+)", alan)
    if eslesme:
        return int(eslesme.group(1)), int(eslesme.group(2))
    return None, None


def tablo_degisene_kadar_bekle(eski_ilk_satir):
    """Butona bastıktan sonra tablonun yenilenmesini bekler (en fazla 10 sn)."""
    try:
        WebDriverWait(driver, 10, ignored_exceptions=(StaleElementReferenceException, IndexError)).until(
            lambda d: tabloyu_oku()[0] != eski_ilk_satir)
        return True
    except Exception:
        return False


def pasif_mi(buton):
    """Butonun 'disabled' (pasif) sınıfına sahip olup olmadığını döndürür."""
    return "disabled" in (buton.get_attribute("class") or "")


def ileri_tikla_ve_bekle():
    ilk = tabloyu_oku()[0]
    ileri_butonu().click()
    return tablo_degisene_kadar_bekle(ilk)


def sayfaya_git(numara):
    kutu = sayfa_kutusu()
    kutu.clear()
    kutu.send_keys(str(numara), Keys.ENTER)
    time.sleep(2)


# =====================================================================
# SAYFA İÇİ KONTROLLER
# =====================================================================

def kontrol_gorseller(sayfa_no):
    """Her satırdaki araç görselinin gerçekten yüklenip yüklenmediğini kontrol eder.
    naturalWidth = 0 ise tarayıcı resmi yükleyememiş demektir."""
    hata_var = False
    for i, satir in enumerate(satirlar(), start=1):
        resimler = satir.find_elements(By.TAG_NAME, "img")
        if not resimler:
            hata_ekle("Araç görseli yok", f"Sayfa {sayfa_no}, satır {i}: görsel elemanı bulunamadı.")
            hata_var = True
            continue
        yuklendi = driver.execute_script(
            "return arguments[0].complete && arguments[0].naturalWidth > 0;", resimler[0])
        if not yuklendi:
            ad = " ".join(td.text.strip() for td in satir.find_elements(By.TAG_NAME, "td")[1:3])
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", satir)
            hata_ekle("Araç görseli yüklenmiyor",
                      f"Sayfa {sayfa_no}, satır {i} ({ad}): görsel adresi "
                      f"'{resimler[0].get_attribute('src')}' yüklenemedi.", f"gorsel_s{sayfa_no}")
            hata_var = True
    if not hata_var:
        basarili(f"Sayfa {sayfa_no}: tüm görseller yüklendi")


def kontrol_bos_hucreler(sayfa_no, veriler):
    """Make, Model, Rank, Votes, Engine boş mu; Rank ve Votes sayı mı?"""
    hata_var = False
    for i, satir in enumerate(veriler, start=1):
        for sutun in ["Make", "Model", "Rank", "Votes", "Engine"]:
            if sutun in satir and satir[sutun] == "":
                hata_ekle(f"Boş '{sutun}' sütunu",
                          f"Sayfa {sayfa_no}, satır {i} ({satir.get('Make')} {satir.get('Model')}).",
                          f"bos_{sutun}_s{sayfa_no}")
                hata_var = True
        for sutun in ["Rank", "Votes"]:
            if satir.get(sutun) and not satir[sutun].isdigit():
                hata_ekle(f"Hatalı '{sutun}' değeri",
                          f"Sayfa {sayfa_no}, satır {i}: '{satir[sutun]}' sayı değil.")
                hata_var = True
    if not hata_var:
        basarili(f"Sayfa {sayfa_no}: boş/hatalı hücre yok")


def kontrol_varsayilan_siralama(sayfa_no, veriler, beklenen_rank):
    """Varsayılan sıralamada Rank kesintisiz artmalı, Votes azalmalı."""
    hata_var = False
    onceki_oy = None
    for i, satir in enumerate(veriler, start=1):
        if not satir.get("Rank", "").isdigit():
            beklenen_rank += 1
            continue
        rank = int(satir["Rank"])
        if rank != beklenen_rank:
            hata_ekle("Yanlış Rank sırası",
                      f"Sayfa {sayfa_no}, satır {i}: Rank {beklenen_rank} beklenirken {rank} geldi.",
                      f"rank_s{sayfa_no}")
            hata_var = True
        beklenen_rank = rank + 1
        if satir.get("Votes", "").isdigit():
            oy = int(satir["Votes"])
            if onceki_oy is not None and oy > onceki_oy:
                hata_ekle("Oy sayısı sıralamayla uyumsuz",
                          f"Sayfa {sayfa_no}, satır {i}: {oy} oy, üstteki satırdan ({onceki_oy}) fazla.")
                hata_var = True
            onceki_oy = oy
    if not hata_var:
        basarili(f"Sayfa {sayfa_no}: Rank ve Votes sırası doğru")
    return beklenen_rank


# =====================================================================
# TESTLER
# =====================================================================

def test_1_tum_sayfalari_gez():
    """İleri butonuyla tüm sayfaları gezer; her sayfada tabloyu kontrol eder."""
    log("\n=== TEST 1: Tüm sayfaları ileri butonuyla gezme ===")
    driver.get(URL)
    tablo_yuklenene_kadar_bekle()
    _, toplam = sayfa_bilgisi()
    log(f"  Toplam sayfa: {toplam}")

    gorulenler = {}       # (marka, model) -> ilk görüldüğü sayfa
    beklenen_rank = 1

    for beklenen_sayfa in range(1, toplam + 1):
        mevcut, _ = sayfa_bilgisi()
        if mevcut != beklenen_sayfa:
            hata_ekle("Yanlış sayfaya geçiş",
                      f"{beklenen_sayfa}. sayfa beklenirken {mevcut}. sayfa görünüyor.",
                      f"gecis_{beklenen_sayfa}")

        veriler = tabloyu_oku()
        log(f"\n  -- Sayfa {beklenen_sayfa}: {len(veriler)} satır --")
        kontrol_gorseller(beklenen_sayfa)
        kontrol_bos_hucreler(beklenen_sayfa, veriler)
        beklenen_rank = kontrol_varsayilan_siralama(beklenen_sayfa, veriler, beklenen_rank)

        tekrar = False
        for satir in veriler:
            anahtar = (satir.get("Make"), satir.get("Model"))
            if anahtar in gorulenler:
                hata_ekle("Aynı kayıt iki sayfada",
                          f"{anahtar[0]} {anahtar[1]}: sayfa {gorulenler[anahtar]} ve sayfa {beklenen_sayfa}.")
                tekrar = True
            else:
                gorulenler[anahtar] = beklenen_sayfa
        if not tekrar:
            basarili(f"Sayfa {beklenen_sayfa}: önceki sayfalarla tekrar eden kayıt yok")

        if beklenen_sayfa < toplam:
            ilk = veriler[0]
            ileri_butonu().click()
            if not tablo_degisene_kadar_bekle(ilk):
                hata_ekle("İleri butonu çalışmıyor",
                          f"Sayfa {beklenen_sayfa}'de » tıklandı ama tablo değişmedi.", "ileri")


def test_2_geri_butonu():
    """Son sayfaya » ile gidilir, sonra « ile geriye doğru her sayfa kontrol edilir."""
    log("\n=== TEST 2: Geri butonu ===")
    driver.get(URL)
    tablo_yuklenene_kadar_bekle()
    _, toplam = sayfa_bilgisi()
    for _ in range(toplam - 1):
        ileri_tikla_ve_bekle()
    mevcut, _ = sayfa_bilgisi()
    log(f"  » ile ulaşılan sayfa: {mevcut}")
    hata_var = False
    for beklenen in range(toplam - 1, 0, -1):
        geri = geri_butonu()
        if pasif_mi(geri):
            hata_ekle("Geri butonu pasif",
                      f"{beklenen + 1}. sayfada « butonu pasif (disabled) durumda; önceki sayfaya dönülemiyor.",
                      f"geri_pasif_{beklenen + 1}")
            hata_var = True
            break
        ilk = tabloyu_oku()[0]
        geri.click()
        tablo_degisene_kadar_bekle(ilk)
        mevcut, _ = sayfa_bilgisi()
        if mevcut != beklenen:
            hata_ekle("Geri butonu yanlış sayfaya gidiyor",
                      f"{beklenen}. sayfa beklenirken {mevcut}. sayfa açıldı.", f"geri_{beklenen}")
            hata_var = True
    if not hata_var:
        basarili("Geri butonu son sayfadan ilk sayfaya kadar doğru çalıştı")


def test_3_sinirlar():
    """İlk sayfada « ve son sayfada » butonu pasif olmalı ve sayfa değişmemeli."""
    log("\n=== TEST 3: Sınır değerler (ilk ve son sayfa) ===")
    driver.get(URL)
    tablo_yuklenene_kadar_bekle()
    _, toplam = sayfa_bilgisi()

    if pasif_mi(geri_butonu()):
        basarili("İlk sayfada « butonu pasif (tıklanamaz)")
    else:
        geri_butonu().click()
        time.sleep(2)
        mevcut, _ = sayfa_bilgisi()
        if mevcut != 1:
            hata_ekle("İlk sayfada geri butonu hatası",
                      f"1. sayfada « tıklanınca {mevcut}. sayfa göründü.", "sinir_geri")
        else:
            basarili("İlk sayfada « tıklanınca sayfa 1'de kalındı")

    for _ in range(toplam - 1):
        ileri_tikla_ve_bekle()
    if pasif_mi(ileri_butonu()):
        basarili("Son sayfada » butonu pasif (tıklanamaz)")
    else:
        ileri_butonu().click()
        time.sleep(2)
        mevcut, _ = sayfa_bilgisi()
        if mevcut != toplam:
            hata_ekle("Son sayfada ileri butonu hatası",
                      f"Son sayfa {toplam} iken » tıklanınca {mevcut}. sayfa göründü.", "sinir_ileri")
        else:
            basarili("Son sayfada » tıklanınca son sayfada kalındı")


def test_4_sayfa_kutusu():
    """Sayfa kutusuna geçerli ve geçersiz değerler yazılır."""
    log("\n=== TEST 4: Sayfa numarası kutusu ===")
    driver.get(URL)
    satir_sayisi = len(tabloyu_oku())
    _, toplam = sayfa_bilgisi()

    # Geçerli değer: 3
    sayfaya_git(3)
    veriler = tabloyu_oku()
    beklenen_ilk = 2 * satir_sayisi + 1
    if veriler[0].get("Rank", "").isdigit() and int(veriler[0]["Rank"]) == beklenen_ilk:
        basarili(f"Kutuya 3 yazınca 3. sayfa açıldı (ilk Rank {beklenen_ilk})")
    else:
        hata_ekle("Sayfa kutusu yanlış sayfaya götürüyor",
                  f"Kutuya 3 yazıldı; ilk Rank {beklenen_ilk} olmalıydı, {veriler[0].get('Rank')} geldi.",
                  "kutu_3")

    # Geçersiz değerler: toplamdan büyük, 0 ve negatif
    for deger in [toplam + 5, 0, -1]:
        try:
            driver.get(URL)
            tablo_yuklenene_kadar_bekle()
            sayfaya_git(deger)
            mevcut, t = sayfa_bilgisi()
            satir_adedi = len(satirlar())
            log(f"  Kutuya {deger} yazıldı -> 'page {mevcut} of {t}', tabloda {satir_adedi} satır")
            if mevcut is None or mevcut < 1 or mevcut > t or satir_adedi == 0:
                hata_ekle(f"Sayfa kutusu geçersiz değeri ({deger}) kabul ediyor",
                          f"Kutuya {deger} yazıldı; sayfalama 'page {mevcut} of {t}' gösteriyor, "
                          f"tabloda {satir_adedi} satır var.", f"kutu_{deger}")
            else:
                basarili(f"Kutuya {deger} yazılınca geçerli bir sayfada kalındı ({mevcut})")
        except Exception as e:
            log(f"  [ÇALIŞMADI] Kutuya {deger} yazma: {type(e).__name__} - {str(e).splitlines()[0] if str(e) else ''}")


def test_5_rank_basligi_siralama():
    """Rank başlığına tıklanınca değerler sayısal olarak sıralanmalı."""
    log("\n=== TEST 5: Rank başlığına göre sıralama ===")
    driver.get(URL)
    tablo_yuklenene_kadar_bekle()
    log(f"  Tablo başlıkları: {basliklar()}")
    baslik = driver.find_element(By.XPATH, "//thead//th[normalize-space()='Rank']")
    linkler = baslik.find_elements(By.TAG_NAME, "a")
    (linkler[0] if linkler else baslik).click()
    time.sleep(2)
    ranklar = [int(s["Rank"]) for s in tabloyu_oku() if s.get("Rank", "").isdigit()]
    log(f"  Tıklamadan sonraki Rank sırası: {ranklar}")
    # Artan sayısal sıralamada ilk sayfada en küçük değerler (1, 2, 3, ...) olmalı.
    # Azalan sıralamada ise en büyük değerler büyükten küçüğe olmalı; ikisi de kabul edilir.
    artan = list(range(1, len(ranklar) + 1))
    azalan_dogru = ranklar == sorted(ranklar, reverse=True) and 1 not in ranklar
    if not (ranklar == artan or azalan_dogru):
        hata_ekle("Rank sıralaması sayısal değil",
                  f"Rank başlığına tıklanınca ilk sayfada {ranklar} görüntülendi; "
                  f"sayısal sıralamada {artan} olmalıydı. Değerler metin olarak "
                  f"karşılaştırıldığı için '10', '2'den önce geliyor.", "rank_baslik")
    else:
        basarili("Rank başlığı sayısal sıralama yaptı")


def test_6_model_linki():
    """Tablodaki model adına tıklanınca o modelin sayfası açılmalı."""
    log("\n=== TEST 6: Model bağlantısı ===")
    driver.get(URL)
    tablo_yuklenene_kadar_bekle()
    model_sutunu = basliklar().index("Model")
    ilk_satir_hucreleri = satirlar()[0].find_elements(By.TAG_NAME, "td")
    model_linki = ilk_satir_hucreleri[model_sutunu].find_element(By.TAG_NAME, "a")
    model_adi = model_linki.text.strip()
    model_linki.click()
    try:
        # Adres değişene ve sayfa gövdesinde model adı görünene kadar en fazla 15 sn bekle
        WebDriverWait(driver, 15, ignored_exceptions=(StaleElementReferenceException,)).until(
            lambda d: "/overall" not in d.current_url
            and model_adi in d.find_element(By.TAG_NAME, "body").text)
        log(f"  Açılan adres: {driver.current_url}")
        basarili(f"'{model_adi}' bağlantısı doğru model sayfasını açtı")
    except Exception:
        hata_ekle("Model bağlantısı yanlış sayfaya gidiyor",
                  f"'{model_adi}' tıklandı; 15 sn içinde açılan sayfada ({driver.current_url}) "
                  f"bu model adı görüntülenmedi.", "model_link")


# =====================================================================
# ÇALIŞTIR
# =====================================================================

testler = [test_1_tum_sayfalari_gez, test_2_geri_butonu, test_3_sinirlar,
           test_4_sayfa_kutusu, test_5_rank_basligi_siralama, test_6_model_linki]

try:
    for test in testler:
        try:
            test()
        except Exception as e:
            # Bir test çökerse diğerleri yine çalışsın
            log(f"  [ÇALIŞMADI] {test.__name__}: {type(e).__name__} - {str(e).splitlines()[0] if str(e) else ''}")
finally:
    driver.quit()
    ozet = [f"\n{'=' * 60}",
            f"ÖZET: {len(basarililar)} kontrol geçti, {len(hatalar)} hata bulundu",
            "=" * 60]
    for i, (baslik, aciklama) in enumerate(hatalar, 1):
        ozet.append(f"Hata #{i}: {baslik}\n   Açıklama: {aciklama}")
    print("\n".join(ozet))
    with open("sonuclar.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(kayitlar + ozet))
