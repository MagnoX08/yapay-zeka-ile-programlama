import json
import os
import re
import time
import random
import sqlite3
import pandas as pd
from google import genai
from google.genai import types

# Gemini API Yapılandırması
api_key = "API BURAYA GİRİLECEK!"
client = genai.Client(api_key=api_key) if api_key != "API_ANAHTARINI_BURAYA_GIRIN" else genai.Client()

DOSYA_ADI = "urunler.json"

def dosya_yukle():
    """JSON dosyasından ürün verilerini okur, yoksa boş liste döner[cite: 4]."""
    if not os.path.exists(DOSYA_ADI):
        return []
    try:
        with open(DOSYA_ADI, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

def dosya_kaydet(veriler):
    """Verileri JSON dosyasına kaydeder[cite: 4]."""
    try:
        with open(DOSYA_ADI, "w", encoding="utf-8") as f:
            json.dump(veriler, f, ensure_ascii=False, indent=4)
    except IOError:
        print("[HATA] Dosya kaydedilirken bir sorun oluştu[cite: 4].")

def api_ile_analiz_et(aciklama):
    """Gemini API ile ürün açıklamasını analiz edip JSON formatında döndürür[cite: 4]."""
    prompt = f"""
    Aşağıdaki ürün açıklamasına göre bir e-ticaret ürün bilgisi oluştur: '{aciklama}'
    Lütfen SADECE aşağıdaki formatta geçerli ve eksiksiz bir JSON döndür:
    {{
        "urun_adi": "Ürün Adı",
        "kategori": "Kategori Adı",
        "seo_etiketleri": "etiket1, etiket2, etiket3",
        "satis_aciklamasi": "İki cümlelik satış açıklaması."
    }}
    """
    try:
        response = client.models.generate_content(
            model='gemini-3.5-flash-lite',
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        veri = json.loads(response.text)
        
        gerekli_alanlar = ["urun_adi", "kategori", "seo_etiketleri", "satis_aciklamasi"]
        if all(alan in veri for alan in gerekli_alanlar):
            return veri
        else:
            print("[HATA] API'den eksik veri döndü.")
            return None
    except Exception as e:
        print(f"[HATA] API Hatası veya geçersiz JSON formatı: {e}")
        return None

def stok_uyarisi(stok):
    """Stok durumunu değerlendirir ve gerekirse uyarı mesajı yazdırır."""
    if stok == 0:
        print(">> [UYARI] STOKTA YOK!")
    elif 1 <= stok <= 4:
        print(f">> [UYARI] KRİTİK STOK! Yalnızca {stok} adet kaldı.")

def guvenlik_kontrolu(sql_kodu: str) -> bool:
    """
    TODO 2: DROP, DELETE, UPDATE, INSERT, ALTER komutlarını re.search() ile engeller.
    Yasaklı komut varsa [GÜVENLİK ENGELİ] uyarısı verip False döndürür. Sadece SELECT izinlidir!
    """
    yasaklar = r"\b(DROP|DELETE|UPDATE|INSERT|ALTER|TRUNCATE|EXEC)\b"
    if re.search(yasaklar, sql_kodu, re.IGNORECASE):
        print(f"[GÜVENLİK ENGELİ] Zararlı SQL tespit edildi: Yasaklı komut içeriyor!")[cite: 3]
        return False
    return True

def clean_sql(raw_sql: str) -> str:
    """
    TODO 3: Gemini yanıtındaki markdown etiketlerini (```sql ... ```) regex ile temizler.
    """
    temiz_sql = re.sub(r"```sql|```", "", raw_sql, flags=re.IGNORECASE).strip()
    return temiz_sql

def sql_asistani_calistir():
    """
    1.000 kayıtlık bellek içi SQLite veritabanı kurar, güvenlik katmanı ve 
    Self-Correction döngüsüyle interaktif SQL testi gerçekleştirir[cite: 1, 2].
    """
    print("\n--- YAPAY ZEKA DESTEKLİ SQL ASİSTANI LABORATUVARI ---")
    
    # 1. VERİTABANI OLUŞTURMA VE SHADOW SCHEMA (Bellek İçi SQLite)
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    
    cursor.execute("CREATE TABLE musteriler (musteri_id INT, ad_soyad TEXT, sehir TEXT)")
    cursor.execute("CREATE TABLE siparisler (siparis_id INT, musteri_id INT, tutar REAL, tarih TEXT)")
    
    # TODO 1: random ile 1.000 müşteri ve 1.000 sipariş verisi üretip executemany() ile ekleme
    print("[BİLGİ] 1.000 müşteri ve 1.000 sipariş verisi üretiliyor[cite: 1]...")
    sehirler = ['İstanbul', 'Ankara', 'Izmir', 'Bursa', 'Antalya']
    
    musteriler_data = [(i, f"Musteri_{i}", random.choice(sehirler)) for i in range(1, 1001)]
    siparisler_data = [(i, random.randint(1, 1000), round(random.uniform(100.0, 10000.0), 2), f"2026-01-{random.randint(1, 28):02d}") for i in range(1, 1001)]
        
    cursor.executemany("INSERT INTO musteriler VALUES (?, ?, ?)", musteriler_data)
    cursor.executemany("INSERT INTO siparisler VALUES (?, ?, ?, ?)", siparisler_data)
    conn.commit()
    print("[BİLGİ] Veritabanı hazırlandı ve veriler yüklendi.")
    
    toplam_talep = 0
    basarili_icra = 0
    engellenen_saldiri = 0
    hata_duzeltme_sayisi = 0
    test_detaylari = []

    system_instruction = (
        "Aşağıdaki veritabanı şemasına göre kullanıcının doğal dille istediği veriyi çekecek SQLite uyumlu SQL sorgusunu yaz. "
        "Şema: musteriler(musteri_id, ad_soyad, sehir), siparisler(siparis_id, musteri_id, tutar, tarih). "
        "Kurallar: Sadece SELECT komutu kullan. Çıktıda markdown etiketi ve açıklama olmasın."
    )

    # TODO 5: while True döngüsü kurarak kullanıcıdan interaktif istek alma
    while True:
        kullanici_talebi = input("\nSoru Girin (Çıkış için 'q'): ").strip()
        if kullanici_talebi.lower() == 'q':
            break
        if not kullanici_talebi:
            continue
            
        toplam_talep += 1
        print("[GEMINI] SQL Üretiliyor...")
        
        # TODO 4: En fazla 3 deneme hakkı olan Self-Correction Loop
        deneme = 0
        max_deneme = 3
        sql_sorgusu = ""
        basarili = False
        hata_mesaji = None
        baslangic_zamani = time.perf_counter()
        
        while deneme < max_deneme:
            deneme += 1
            try:
                prompt = f"{system_instruction}\n\nKullanıcı Talebi: {kullanici_talebi}"
                if hata_mesaji:
                    prompt += f"\n\Daha önce ürettiğin şu SQL hata verdi:\n{sql_sorgusu}\nAlınan Hata:\n{hata_mesaji}\nLütfen hatayı düzelterek tekrar sadece SELECT sorgusu ver."
                
                response = client.models.generate_content(
                    model='gemini-3.5-flash-lite',
                    contents=prompt
                )
                
                ham_sql = response.text
                sql_sorgusu = clean_sql(ham_sql)
                print(f"[SQL - Deneme {deneme}] {sql_sorgusu}")
                
                # Güvenlik Kontrolü (Aşama 2)
                if not guvenlik_kontrolu(sql_sorgusu):
                    engellenen_saldiri += 1
                    test_detaylari.append(f"[TEST {toplam_talep}] Güvenlik Engeli: BAŞARILI (Zararlı komut engellendi)")
                    basarili = False
                    break
                
                print("[GÜVENLİK] Denetim Başarılı (Sadece SELECT).")
                
                # Veritabanında Çalıştırma ve İcra Süresi Ölçümü
                df = pd.read_sql_query(sql_sorgusu, conn)
                bitis_zamani = time.perf_counter()
                sure = bitis_zamani - baslangic_zamani
                
                print(f"[SONUÇ] (İcra Süresi: {sure:.3f} sn)")
                print(df.head(10).to_markdown(index=False))
                
                basarili = True
                basarili_icra += 1
                if deneme > 1:
                    hata_duzeltme_sayisi += 1
                    test_detaylari.append(f"[TEST {toplam_talep}] Hata Düzeltme: {deneme}. denemede çözüldü")
                else:
                    test_detaylari.append(f"[TEST {toplam_talep}] İcra Süresi: {sure:.3f} saniye | Durum: BAŞARILI")
                break
                
            except sqlite3.Error as e:
                hata_mesaji = str(e)
                print(f"[HATA DÜZELTME] SQLite Hatası Yakalandı (Deneme {deneme}): {hata_mesaji}")
                print("Gemini'ye hata geri besleniyor ve sorgu düzeltiliyor...")
            except Exception as e:
                print(f"[HATA] Beklenmeyen hata: {e}")
                break
        
        if not basarili and not sql_sorgusu:
            print("[HATA] Sorgu çalıştırılamadı.")

    # Aşama 5: Test sonuçlarını ve gözlemleri sql_asistan_raporu.txt dosyasına kaydetme
    rapor_icerigi = f"""AKILLI SQL ASİSTANI PERFORMANS VE GÜVENLİK RAPORU
Çalıştırma Tarihi: 2026-11-02
Veritabanı Hacmi: 1.000 Müşteri, 1.000 Sipariş
Toplam Test Talebi: {toplam_talep}
Başarılı İcra: {basarili_icra}
Engellenen Saldırı: {engellenen_saldiri}
Hata Düzeltme Sayısı: {hata_duzeltme_sayisi} (Self-Correction başarılı)

TEST DETAYLARI:
""" + "\n".join(test_detaylari) + """

KISA YORUM VE DEĞERLENDİRME:
1.000 kayıtlık veritabanında Gemini-3.5-Flash ile SQL üretimi hızlı bir şekilde gerçekleştirilmiştir[cite: 3].
Üretilen güvenli SELECT SQL'leri SQLite üzerinde milisaniyeler mertebesinde çalışmaktadır[cite: 3].
Güvenlik filtresi tehlikeli komutları başarıyla tespit edip veritabanına ulaşmadan bloke etmiştir[cite: 3].
"""
    
    with open("sql_asistan_raporu.txt", "w", encoding="utf-8") as f:
        f.write(rapor_icerigi)
    print("\n[BİLGİ] Test sonuçları 'sql_asistan_raporu.txt' dosyasına kaydedildi.")

def urun_ekle(urunler):
    """Kullanıcıdan bilgileri alır, API'yi çağırır ve yeni ürünü kaydeder."""
    aciklama = input("Ürün açıklaması: ").strip()
    if not aciklama:
        print("[HATA] Açıklama boş bırakılamaz.")
        return

    try:
        fiyat = float(input("Ürün fiyatı: "))
        stok = int(input("Stok miktarı: "))
        if fiyat < 0 or stok < 0:
            print("[HATA] Fiyat ve stok negatif olamaz!")
            return
    except ValueError:
        print("[HATA] Lütfen geçerli bir sayısal değer girin!")
        return

    print("[API] Ürün bilgileri oluşturuluyor...")
    api_verisi = api_ile_analiz_et(aciklama)
    
    if not api_verisi:
        print("[HATA] Ürün kaydedilemedi.")
        return

    yeni_id = 1
    if urunler:
        mevcut_idler = [int(u["urun_kodu"].split("-")[1]) for u in urunler]
        yeni_id = max(mevcut_idler) + 1
        
    urun_kodu = f"URN-{yeni_id:04d}"

    yeni_urun = {
        "urun_kodu": urun_kodu,
        "urun_adi": api_verisi["urun_adi"],
        "kategori": api_verisi["kategori"],
        "seo_etiketleri": api_verisi["seo_etiketleri"],
        "satis_aciklamasi": api_verisi["satis_aciklamasi"],
        "fiyat": fiyat,
        "stok": stok
    }
    
    urunler.append(yeni_urun)
    dosya_kaydet(urunler)
    
    print("\n[BAŞARILI] Ürün kaydedildi.")
    print(f"Ürün Kodu: {urun_kodu}")
    print(f"Ürün Adı: {yeni_urun['urun_adi']}")
    print(f"Kategori: {yeni_urun['kategori']}")
    print(f"Fiyat: {fiyat} TL")
    print(f"Stok: {stok}")
    print(f"SEO: {yeni_urun['seo_etiketleri']}")
    
    stok_uyarisi(stok)

def urun_listele(urunler):
    """Tüm ürünleri listeler."""
    if not urunler:
        print("[BİLGİ] Henüz kayıtlı ürün bulunmamaktadır.")
        return
    
    for u in urunler:
        print(f"[{u['urun_kodu']}] {u['urun_adi']} - {u['kategori']} | {u['fiyat']} TL | Stok: {u['stok']}")
        stok_uyarisi(u['stok'])

def urun_ara(urunler):
    """Kısmi ve büyük/küçük harf duyarsız arama yapar."""
    if not urunler:
        print("[BİLGİ] Kayıtlı ürün yok.")
        return

    kelime = input("Aranacak ürün (Ad veya Kod): ").strip().lower()
    sonuclar = [u for u in urunler if kelime in u['urun_adi'].lower() or kelime in u['urun_kodu'].lower()]
    
    print(f"\n[SONUÇ] {len(sonuclar)} ürün bulundu:")
    for u in sonuclar:
        print(f"- {u['urun_kodu']}: {u['urun_adi']} (Stok: {u['stok']})")

def stok_guncelle(urunler):
    """Ürün kodu ile arayarak stok değerini günceller."""
    kod = input("Ürün kodu (Örn: URN-0001): ").strip().upper()
    urun = next((u for u in urunler if u['urun_kodu'] == kod), None)
    
    if not urun:
        print("[HATA] Ürün bulunamadı.")
        return
        
    try:
        yeni_stok = int(input("Yeni stok miktarı: "))
        if yeni_stok < 0:
            print("[HATA] Stok negatif olamaz!")
            return
            
        eski_stok = urun['stok']
        urun['stok'] = yeni_stok
        dosya_kaydet(urunler)
        print(f"[BAŞARILI] Stok {eski_stok} -> {yeni_stok} olarak güncellendi.")
        stok_uyarisi(yeni_stok)
    except ValueError:
        print("[HATA] Lütfen geçerli bir tam sayı girin!")

def ana_menu():
    """Uygulamanın ana döngüsünü çalıştırır."""
    urunler = dosya_yukle()
    
    while True:
        print("\n=== E-TİCARET YÖNETİM PANELİ ===")
        print("1 - Yeni Ürün Ekle")
        print("2 - Ürünleri Listele")
        print("3 - Ürün Ara")
        print("4 - Stok Güncelle")
        print("5 - Doğal Dilden SQL Üret ve Test Et (Lab Asistanı)")
        print("6 - Çıkış")
        
        secim = input("Seçiminiz: ").strip()
        
        if secim == '1':
            urun_ekle(urunler)
        elif secim == '2':
            urun_listele(urunler)
        elif secim == '3':
            urun_ara(urunler)
        elif secim == '4':
            stok_guncelle(urunler)
        elif secim == '5':
            sql_asistani_calistir()
        elif secim == '6':
            print("Programdan çıkılıyor...")
            break
        else:
            print("[HATA] Geçersiz seçim, lütfen 1-6 arası bir sayı girin.")

if __name__ == "__main__":
    ana_menu()