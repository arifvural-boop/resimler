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

## Yeniden üretme

```bash
python3 -m venv venv && ./venv/bin/pip install bpy pillow   # Blender 5.2
./venv/bin/python kaynak/render_vincler.py portal gercekci/portal.png 320
# sahneler: duvar_pergel | kolon_pergel | yari_portal | portal
# hızlı önizleme: YUZDE=40 ... 24
# fabrika holü arka planı için: ORTAM=hol ...
```
