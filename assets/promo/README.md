# Promo rasmlar

Bu papkaga rieltorlarga yuboriladigan promo/aksiya rasmlarini joylang.

## Obuna promo rasmi

Fayl nomi **aynan** shunday bo'lishi kerak:

```
obuna_promo.jpg
```

To'liq yo'l:

```
assets/promo/obuna_promo.jpg
```

Rasmni shu nom bilan qo'ysangiz, bot obuna promo xabarini shu rasm + matn (caption)
va "Obunalar sahifasiga o'tish" tugmasi bilan yuboradi.

> Eslatma: `.png` yoki boshqa formatdan foydalansangiz, kodda `PROMO_OBUNA_RASM`
> yo'lidagi fayl nomini mos ravishda o'zgartiring
> (`apps/obuna/notifications.py`).

---

## Uy bozori — Rieltorlarga xabar rasmi

Fayl nomi **aynan** shunday bo'lishi kerak:

```
bozor_rieltor_promo.jpg
```

To'liq yo'l:

```
assets/promo/bozor_rieltor_promo.jpg
```

Bu rasm `bozor_rieltorlarga_xabar` command orqali barcha rieltorlarga yuboriladi.
Rasm + caption (1024 belgigacha) + "Ilovani ochish" tugmasi bilan jo'natiladi.

---

## Uy bozori — Userlarga (mijozlar) xabar rasmi

Fayl nomi **aynan** shunday bo'lishi kerak:

```
bozor_user_promo.jpg
```

To'liq yo'l:

```
assets/promo/bozor_user_promo.jpg
```

Bu rasm `bozor_userlarga_xabar` command orqali barcha userlarga (role='user') yuboriladi.
Rasm + caption (1024 belgigacha) + "Ilovani ochish" tugmasi bilan jo'natiladi.

> Eslatma: `.png` formatida bo'lsa fayl nomidagi `.jpg` ni `.png` ga o'zgartiring:
> `apps/makler/management/commands/bozor_rieltorlarga_xabar.py` → `RASM_YOL`
> `apps/users/management/commands/bozor_userlarga_xabar.py` → `RASM_YOL`
