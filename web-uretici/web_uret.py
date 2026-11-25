import os
import re
import sys
import google.generativeai as genai

DOSYA_AYIRACLAR = {
    "index.html": "===INDEX.HTML===",
    "forgot_password.html": "===FORGOT_PASSWORD.HTML===",
    "signup.html": "===SIGNUP.HTML===",
}

SISTEM_MESAJI = """Sen kıdemli bir arayüz (UI/UX) ve ön yüz (Frontend) geliştiricisisin.
Kullanıcının tasarım talebine uygun, birbiriyle tutarlı karanlık temalı (Dark Mode), modern, mobil uyumlu (responsive) üç adet tam HTML sayfası üret.
Tüm CSS ve JavaScript kodlarını harici dosyalara bölmeden doğrudan ilgili HTML dosyalarının içine (<style> ve <script> etiketleriyle) göm.

Çıktı formatı için kesin kurallar:
1. Yanıtında yalnızca şu üç bölümü ve ayıraçları kullan; başında veya sonunda ekstra açıklama yazma:
===INDEX.HTML===
(buraya index.html kodunu yaz)
===FORGOT_PASSWORD.HTML===
(buraya forgot_password.html kodunu yaz)
===SIGNUP.HTML===
(buraya signup.html kodunu yaz)

2. Sayfalar arası bağlantılar (`href`) tam olarak `index.html`, `forgot_password.html` ve `signup.html` dosyalarına yönlensin.
3. Butonların üzerine gelindiğinde (`:hover`) belirgin parlama/ışık efekti oluştur.
4. JavaScript ile form gönderiminde (`submit`) boş alan kontrolü, geçerli e-posta formatı kontrolü ve şifre/şifre tekrar eşleşme kontrolü yap; şifre alanlarına göster/gizle butonu ekle.

Sayfa bileşenleri:
- `index.html`: E-posta alanı, şifre alanı (göster/gizle dahil), "Giriş Yap" butonu, "Şifremi Unuttum" bağlantısı (`forgot_password.html`) ve "Üye Ol" bağlantısı (`signup.html`).
- `forgot_password.html`: "Şifremi Unuttum" başlığı, e-posta adresi alanı, "Şifre sıfırlama bağlantısı gönder" butonu ve giriş sayfasına dön bağlantısı (`index.html`).
- `signup.html`: "Ad Soyad" alanı, e-posta alanı, şifre alanı (göster/gizle dahil), şifre tekrar alanı (göster/gizle dahil), "Üye Ol" butonu ve giriş sayfasına dön bağlantısı (`index.html`).
"""


def api_anahtarini_al() -> str:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key or api_key == "API ANAHTARINIZI BURAYA GİRİNİZ":
        print(
            "UYARI: Gemini API anahtari bulunamadi veya girilmedi! "
            "GEMINI_API_KEY ortam degiskenini ayarlayabilir veya anahtari simdi girebilirsin."
        )
        api_key = input("Gemini API Anahtari: ").strip()

    if not api_key:
        print("HATA: API anahtari bos birakildi. Islem durduruluyor.")
        sys.exit(1)

    return api_key


def markdown_temizle(metin: str) -> str:
    temiz = re.sub(r"^\s*```(?:html)?\s*\n?", "", metin.strip(), flags=re.IGNORECASE)
    temiz = re.sub(r"\n?\s*```\s*$", "", temiz, flags=re.IGNORECASE)
    return temiz.strip()


def yaniti_ayristir_ve_kaydet(yanit_metni: str) -> list[str]:
    kaydedilenler = []
    sirali_etiketler = list(DOSYA_AYIRACLAR.items())

    for i, (dosya_adi, baslangic_etiketi) in enumerate(sirali_etiketler):
        start_idx = yanit_metni.find(baslangic_etiketi)
        if start_idx == -1:
            raise ValueError(f"Yanıtta '{baslangic_etiketi}' ayracı bulunamadı.")

        icerik_baslangic = start_idx + len(baslangic_etiketi)
        end_idx = len(yanit_metni)

        for _, sonraki_etiket in sirali_etiketler[i + 1 :]:
            pos = yanit_metni.find(sonraki_etiket, icerik_baslangic)
            if pos != -1:
                end_idx = pos
                break

        ham_html = yanit_metni[icerik_baslangic:end_idx]
        saf_html = markdown_temizle(ham_html)

        with open(dosya_adi, "w", encoding="utf-8") as f:
            f.write(saf_html + "\n")

        kaydedilenler.append(dosya_adi)

    return kaydedilenler


def main() -> None:
    api_key = api_anahtarini_al()
    genai.configure(api_key=api_key)

    print("Tasarım talebini girin (bitirmek için Enter'a basın):")
    tasarim_talebi = input("> ").strip()

    if not tasarim_talebi:
        tasarim_talebi = (
            "Modern, profesyonel, karanlık temalı bir üyelik sistemi oluştur. "
            "Mor ve mavi neon renkler kullan. Login, Forgot Password ve Signup sayfaları "
            "aynı tasarım dilini kullansın. Sayfalar arasında geçişler çalışsın. "
            "Butonların üzerine gelindiğinde parlama efekti oluşsun."
        )

    model = genai.GenerativeModel(model_name="gemini-3.8-flash")
    response = model.generate_content(
        SISTEM_MESAJI + "\n\nKullanıcı talebi:\n" + tasarim_talebi,
        generation_config={"temperature": 0.5, "max_output_tokens": 16000},
    )

    sonuc = response.text or ""
    kaydedilen_dosyalar = yaniti_ayristir_ve_kaydet(sonuc)
    print("Üretilen ve kaydedilen dosyalar:", ", ".join(kaydedilen_dosyalar))


if __name__ == "__main__":
    main()