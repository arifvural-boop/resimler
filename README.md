# Beta Vinç – Gerçekçi Vinç Görselleri

betavinc.com'daki düz (flat) vektör portal ve pergel vinç çizimleri, Blender Cycles
ile fotoğraf gerçekliğinde, gölgesiz düz beyaz arka plan üzerinde ve orijinal çizimlerdeki
gibi tam yandan görünüşle render edildi (eski 3/4 açı için: GORUNUS=capraz). Marka renkleri ve "beta" logosu korundu.

Vinçler modellenmedi; Beta'nın gerçek ürün fotoğrafları (`kaynak/vinc_foto/`,
beyaz zemini temizlenmiş) gerçek ölçüsünde eklendi. Sahne kamerası her fotoğrafın çekim
açısına göre ayarlandı: pergel bomu fotoğraftaki vinçle aynı açıya döndürüldü (duvar tipi
~10°, kolon tipi ~10°) ve kamera makineden bu açıyla, bom hizasından bakar (araba üst kenarı yatay), portallerde kamera araba fotoğrafı gibi ~9° yukarıdan bakar; dikeyler
mercek kaydırmayla dik tutuldu. Arabaların tekerlekleri bom alt flanşına / kiriş rayına oturur:

- Duvar tipi pergel → 2 ton zincirli vinç (`zincirli_vinc_2ton.png`)
- Kolon tipi pergel → aynı 2 ton zincirli vinç; iki pergelde de araba 3B (alt flanşta), caraskal fotoğrafı askıda
- Yarı portal ve portal → halatlı vinç arabası (`halatli_vinc_araba.png`): gerçek çift kirişli
  portal yapısı (ayaklar kirişe dik düzlemde A, raylar kirişe dik); araba iki kirişin rayına basar,
  kamera fotoğraf gibi kiriş doğrultusuna yakın (~8°) ve ~9° yukarıdan; halat bandı uzatıldı

| Ürün | Orijinal | Gerçekçi |
|---|---|---|
| Duvar tipi pergel vinç | `orijinal/duvar_pergel.webp` | `gercekci/duvar_pergel.png` |
| Kolon tipi pergel vinç | `orijinal/kolon_pergel.webp` | `gercekci/kolon_pergel.png` |
| Yarı portal vinç | `orijinal/yari_portal.webp` | `gercekci/yari_portal.png` |
| Portal vinç | `orijinal/portal.webp` | `gercekci/portal.png` |

## Fotoğraf kalitesi

- 3200×2400 çıktı, 320 örnek + OpenImageDenoise (albedo/normal, yüksek kalite)
- Ürün fotoğrafı stüdyo ışığı: sol üst ana softbox, sağ dolgu, arka kontur ışığı
- Boyada cila ve ince "portakal kabuğu" dokusu, fırçalanmış çelik pim ve cıvatalar

- Duvar tipi pergelde bina kolonu brüt beton dokulu (gözenek, akma lekesi, kalıp izi) ve zemine kadar

## Marka uyarlaması

- Beta turuncusu `#E99A2A` (yarı parlak endüstriyel boya + vernik)
- Antrasit `#3C424B` (araba, konsol, baş arabaları, motorlar)
- Kolon grisi `#5A626B`
- "beta" logosu: vinç gövdesinde, bom ve kiriş üzerinde beyaz plaka + koyu yazı

## Teknik resimler (`teknik/`)

A3 paftalar (ön görünüş, plan, kesit/detay, ölçüler, Beta antetli başlık kutusu):
`duvar_pergel_teknik`, `kolon_pergel_teknik`, `yari_portal_teknik`, `portal_teknik` (PDF + PNG) ve
hepsi tek dosyada `beta_vinc_teknik_resimler.pdf`. Ölçüler görselleştirme modelinden alınmıştır;
imalat ve statik hesap için onaylı proje esas alınır.

```bash
./venv/bin/pip install matplotlib
./venv/bin/python kaynak/teknik_resim.py teknik
```

## Kurumsal animasyon (`video/beta_vinc_yolculugu.mp4`)

"Bir vincin yolculuğu": tek kirişli köprülü vincin siparişten kuruluma hikâyesi; 1920×1080, 30 fps, ~73 sn,
Beta kurumsal renkleri ve logosuyla 2B flat motion graphics. Sahneler: açılış, 01 Sipariş, 02 Keşif ve Ölçü,
03 Mühendislik, 04 İmalat, 05 Sevkiyat, 06 Nakliye, 07 Kurulum ve Test, kapanış. Ses yok.

```bash
./venv/bin/pip install pycairo
./venv/bin/python kaynak/animasyon.py video/beta_vinc_yolculugu.mp4
./venv/bin/python kaynak/animasyon.py --kare 30 onizleme.png   # tek kare
```

## Instagram Reels (`video/beta_reels_tr.mp4`, `video/beta_reels_en.mp4`)

"30 saniyede bir vincin yolculuğu": 1080×1920 (9:16), 30 fps, 30 sn, 2B motion graphics, gerçek Beta logosu,
120 BPM'e oturan kesmeler ve telifsiz üretilmiş müzik. Türkçe ve İngilizce sürüm.

```bash
./venv/bin/python kaynak/reels.py tr video/beta_reels_tr.mp4
./venv/bin/python kaynak/reels.py en video/beta_reels_en.mp4
```

Kumanda sistemleri Reels'i (`video/beta_reels_kumanda_tr_en.mp4`, TR+EN tek video): butonyer, telsiz kumanda,
pano, frekans invertörü, PLC, güvenlik, devreye alma. Paylaşım metinleri: `video/aciklama_kumanda.md`.

```bash
./venv/bin/python kaynak/reels_kumanda.py video/beta_reels_kumanda_tr_en.mp4
```

## C raylı festoon kablo sistemi

Fotoğraflardaki C ray profili, turuncu plakalı kablo arabaları ve siyah kelepçeler çift kirişli köprülü vinçte
toplandı: `gercekci/festoon_kopru_vinc.png` (genel), `gercekci/festoon_detay.png` (ray boyunca yakın plan),
`gercekci/festoon_sistemi_pafta.png` (numaralı parça açıklamalı TR/EN tanıtım paftası).

```bash
./venv/bin/python kaynak/render_festoon.py genel gercekci/festoon_kopru_vinc.png 384
./venv/bin/python kaynak/render_festoon.py detay gercekci/festoon_detay.png 384
./venv/bin/python kaynak/festoon_pafta.py gercekci/festoon_sistemi_pafta.png
```

Vinçsiz bağımsız ürün görselleri: `gercekci/festoon_urun.png` (ray boyunca), `festoon_urun_yan.png` (önden),
`festoon_urun_araba.png` (araba yakın plan) — `render_festoon.py urun | urun_yan | urun_araba`.

## Yeniden üretme

```bash
python3 -m venv venv && ./venv/bin/pip install bpy pillow   # Blender 5.2
./venv/bin/python kaynak/render_vincler.py portal gercekci/portal.png 320
# sahneler: duvar_pergel | kolon_pergel | yari_portal | portal
# hızlı önizleme: YUZDE=40 ... 24
# fabrika holü arka planı için: ORTAM=hol ...
```
