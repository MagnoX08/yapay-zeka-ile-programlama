import random
import time
from collections import Counter
from typing import List


def bul(l):
    r = []
    for i in range(len(l)):
        for j in range(i + 1, len(l)):
            if l[i] == l[j] and l[i] not in r:
                r.append(l[i])
    return r


def bul_optimize(sayilar: List[int]) -> List[int]:
    """Birden fazla kez geçen elemanları, ilk görülme sırasına göre döndürür."""
    sayac = Counter(sayilar)  # Her elemanın kaç kez geçtiğini tek geçişte sayar
    gorulenler = set()
    tekrarlananlar: List[int] = []
    for eleman in sayilar:
        if sayac[eleman] > 1 and eleman not in gorulenler:
            gorulenler.add(eleman)
            tekrarlananlar.append(eleman)
    return tekrarlananlar


def sure_olc(fonksiyon, veri, tekrar=3):
    """Fonksiyonu 'tekrar' kez çalıştırır, süre listesini ve son sonucu döndürür."""
    sureler = []
    sonuc = None
    for _ in range(tekrar):
        baslangic = time.perf_counter()
        sonuc = fonksiyon(veri)
        sureler.append(time.perf_counter() - baslangic)
    return sureler, sonuc


# ---------- Doğruluk testleri ----------
test_girdileri = [
    [],
    [7],
    [1, 2, 3],
    [3, 1, 3, 2, 1],
    [4, 2, 2, 4, 3, 3],
]
try:
    for girdi in test_girdileri:
        assert bul(girdi) == bul_optimize(girdi), f"Sonuç farklı: {girdi}"
    dogruluk_kucuk = True
except AssertionError as hata:
    print("Test başarısız:", hata)
    dogruluk_kucuk = False

# ---------- Ana deney (5000 eleman) ----------
random.seed(42)  # Her çalıştırmada aynı test verisi
veriler = [random.randint(1, 1000) for _ in range(5000)]

TEKRAR = 3

eski_sureler, sonuc_eski = sure_olc(bul, veriler, TEKRAR)
yeni_sureler, sonuc_yeni = sure_olc(bul_optimize, veriler, TEKRAR)

eski_sure = sum(eski_sureler) / TEKRAR
yeni_sure = sum(yeni_sureler) / TEKRAR

try:
    assert sonuc_eski == sonuc_yeni, "Büyük veride sonuçlar farklı!"
    dogruluk_buyuk = True
except AssertionError as hata:
    print("Test başarısız:", hata)
    dogruluk_buyuk = False

dogruluk = dogruluk_kucuk and dogruluk_buyuk

# Sıfıra bölmeyi önle
hizlanma = eski_sure / max(yeni_sure, 1e-9)

# ---------- Farklı veri boyutları (konsol çıktısı) ----------
print("Farklı veri boyutlarında karşılaştırma (3 tekrar ortalaması):")
for n in (1000, 3000, 5000):
    random.seed(42)
    v = [random.randint(1, 1000) for _ in range(n)]
    e, s1 = sure_olc(bul, v, TEKRAR)
    y, s2 = sure_olc(bul_optimize, v, TEKRAR)
    assert s1 == s2
    e_ort, y_ort = sum(e) / TEKRAR, sum(y) / TEKRAR
    print(f"  {n:>5} eleman | eski: {e_ort:.6f} sn | yeni: {y_ort:.6f} sn | "
          f"hızlanma: {e_ort / max(y_ort, 1e-9):.1f} kat")

# ---------- Rapor ----------
yorum = (
    f"Eski kod her eleman cifti icin ic ice dongu ve liste icinde arama yaptigi icin "
    f"O(n^2) ve daha fazla maliyetlidir. Optimize kod Counter ve set kullanarak "
    f"yaklasik O(n) surede calisir. Sonuclar ve sirasi ayni kaldi, "
    f"bu yuzden kod hem dogru hem cok daha hizlidir."
)

rapor = f"""KOD PERFORMANS RAPORU
Veri sayisi: {len(veriler)}
Eski kod suresi: {eski_sure:.6f} saniye
Optimize kod suresi: {yeni_sure:.6f} saniye
Hizlanma: {hizlanma:.1f} kat
Dogruluk testi: {"BASARILI" if dogruluk else "BASARISIZ"}
Kisa yorum: {yorum}
"""

with open("performans_raporu.txt", "w", encoding="utf-8") as dosya:
    dosya.write(rapor)

print()
print(rapor)


'''
Hasan Ali ve Kayra

'''