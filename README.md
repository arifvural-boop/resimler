# Beta Vinç – Gerçekçi Vinç Görselleri

betavinc.com'daki düz (flat) vektör portal ve pergel vinç çizimleri, fabrika holü
ortamında fiziksel olarak modellenip Blender Cycles ile fotoğraf gerçekliğinde
render edildi. Marka renkleri ve "beta" logosu korundu.

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
python3 -m venv venv && ./venv/bin/pip install bpy   # Blender 5.2
./venv/bin/python kaynak/render_vincler.py portal gercekci/portal.png 160
# sahneler: duvar_pergel | kolon_pergel | yari_portal | portal
# hızlı önizleme: YUZDE=40 ... 24
```
