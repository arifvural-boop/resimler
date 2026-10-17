# Beta Vinç – Gerçekçi Vinç Görselleri

betavinc.com'daki düz (flat) vektör portal ve pergel vinç çizimleri, Blender Cycles
ile fotoğraf gerçekliğinde, gölgesiz düz beyaz arka plan üzerinde render edildi. Marka renkleri ve "beta" logosu korundu.

Vinçler modellenmedi; Beta'nın gerçek ürün fotoğrafları (`kaynak/vinc_foto/`,
beyaz zemini temizlenmiş) sahnedeki gerçek ölçülü bir düzleme oturtulup, köşeleri kameraya
izdüşürülerek homografi ile perspektifli bükülüp eklendi (bom / kirişle aynı kaçış):

- Duvar tipi pergel → 2 ton zincirli vinç (`zincirli_vinc_2ton.png`)
- Kolon tipi pergel → kompakt vinç (`kompakt_vinc.png`)
- Yarı portal ve portal → halatlı vinç arabası (`halatli_vinc_araba.png`): kiriş raylarının
  üstünde, ön kirişin arkasında; halat bandı uzatılarak kanca ~2 m yüksekliğe indirildi

| Ürün | Orijinal | Gerçekçi |
|---|---|---|
| Duvar tipi pergel vinç | `orijinal/duvar_pergel.webp` | `gercekci/duvar_pergel.png` |
| Kolon tipi pergel vinç | `orijinal/kolon_pergel.webp` | `gercekci/kolon_pergel.png` |
| Yarı portal vinç | `orijinal/yari_portal.webp` | `gercekci/yari_portal.png` |
| Portal vinç | `orijinal/portal.webp` | `gercekci/portal.png` |

## Marka uyarlaması

- Beta turuncusu `#E99A2A` (yarı parlak endüstriyel boya + vernik)
- Antrasit `#3C424B` (araba, konsol, baş arabaları, motorlar)
- Kolon grisi `#5A626B`
- "beta" logosu: vinç gövdesinde, bom ve kiriş üzerinde beyaz plaka + koyu yazı

## Yeniden üretme

```bash
python3 -m venv venv && ./venv/bin/pip install bpy pillow   # Blender 5.2
./venv/bin/python kaynak/render_vincler.py portal gercekci/portal.png 160
# sahneler: duvar_pergel | kolon_pergel | yari_portal | portal
# hızlı önizleme: YUZDE=40 ... 24
# fabrika holü arka planı için: ORTAM=hol ...
```
