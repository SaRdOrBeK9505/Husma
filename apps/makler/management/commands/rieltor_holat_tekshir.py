"""
Rieltorlarning faol/nofaol holatini va sababini tekshiruvchi diagnostika buyrug'i.

Ishlatish:
    # Barcha nofaol rieltorlar sababi bilan:
    python manage.py rieltor_holat_tekshir

    # Bitta rieltorni telegram_id yoki telefon bo'yicha batafsil tekshirish:
    python manage.py rieltor_holat_tekshir --telegram_id 123456789
    python manage.py rieltor_holat_tekshir --phone +998901234567
    python manage.py rieltor_holat_tekshir --id 5

    # Obuna sotib olgan, lekin nofaol rieltorlarni topish (muammoli holat):
    python manage.py rieltor_holat_tekshir --muammoli
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.makler.models import MaklerProfil
from apps.obuna.models import Obuna


def nofaol_sababi(rieltor) -> str:
    """Rieltor nega nofaol ekanini matn ko'rinishida qaytaradi."""
    now = timezone.now()

    if rieltor.bloklangan:
        return "Admin BLOKLAGAN (verify_holat=rejected)"

    bepul_bor = bool(rieltor.bepul_muddat_tugash and now <= rieltor.bepul_muddat_tugash)
    if bepul_bor:
        return "FAOL — bepul sinov muddati ichida"

    if rieltor.obuna_faol:
        return "FAOL — to'langan obunasi bor"

    # Bu yerga tushdi = nofaol. Sababni aniqlashtiramiz.
    obunalar = list(rieltor.obunalar.all().select_related('tarif'))
    if not obunalar:
        return "NOFAOL — hech qachon obuna sotib olmagan, bepul muddat tugagan"

    # Obunalar bor, lekin faoli yo'q. Holatlar bo'yicha ajratamiz.
    kutilmoqda = [o for o in obunalar if o.holat == Obuna.Holat.KUTILMOQDA]
    faol_belgi = [o for o in obunalar if o.holat == Obuna.Holat.FAOL]
    tugagan = [o for o in obunalar if o.holat == Obuna.Holat.TUGAGAN]

    # holat=FAOL, lekin tugash_vaqti o'tgan (task hali TUGAGAN ga o'tkazmagan)
    faol_muddati_otgan = [
        o for o in faol_belgi
        if o.tugash_vaqti is None or now >= o.tugash_vaqti
    ]

    if kutilmoqda:
        return (
            f"NOFAOL — {len(kutilmoqda)} ta obuna KUTILMOQDA holatida "
            f"(to'lov tasdiqlanmagan! Payme/Multicard callback kelmagan bo'lishi mumkin)"
        )
    if faol_muddati_otgan:
        eng_yangi = max(faol_muddati_otgan, key=lambda o: o.tugash_vaqti or now)
        return (
            f"NOFAOL — obuna holati=FAOL, lekin tugash_vaqti o'tib ketgan "
            f"({eng_yangi.tugash_vaqti}) — muddati tugagan"
        )
    if tugagan:
        return f"NOFAOL — barcha obunalar TUGAGAN ({len(tugagan)} ta), muddati bitgan"

    return "NOFAOL — noma'lum sabab (obunalar bor, lekin faol emas)"


class Command(BaseCommand):
    help = "Rieltorlar faol/nofaol holati va sababini tekshiradi"

    def add_arguments(self, parser):
        parser.add_argument('--telegram_id', type=int, help="Bitta rieltorni telegram_id bo'yicha")
        parser.add_argument('--phone', type=str, help="Bitta rieltorni telefon bo'yicha")
        parser.add_argument('--id', type=int, help="Bitta rieltorni profil ID bo'yicha")
        parser.add_argument(
            '--muammoli', action='store_true',
            help="Faqat obuna sotib olgan, lekin nofaol rieltorlarni ko'rsatish",
        )

    def handle(self, *args, **opts):
        qs = MaklerProfil.objects.select_related('user').prefetch_related('obunalar__tarif')

        # ---- Bitta rieltorni batafsil tekshirish ----
        if opts.get('telegram_id'):
            qs = qs.filter(user__telegram_id=opts['telegram_id'])
            return self._batafsil(qs)
        if opts.get('phone'):
            qs = qs.filter(user__phone=opts['phone'])
            return self._batafsil(qs)
        if opts.get('id'):
            qs = qs.filter(id=opts['id'])
            return self._batafsil(qs)

        # ---- Commulative hisobot ----
        jami = qs.count()
        faol_soni = 0
        nofaol_royxat = []
        muammoli_royxat = []  # obuna sotib olgan, lekin nofaol

        for r in qs:
            if r.faol:
                faol_soni += 1
                continue
            sabab = nofaol_sababi(r)
            nofaol_royxat.append((r, sabab))
            # muammoli = obunalar bor, lekin nofaol
            if r.obunalar.filter(holat__in=[Obuna.Holat.FAOL, Obuna.Holat.TUGAGAN, Obuna.Holat.KUTILMOQDA]).exists():
                muammoli_royxat.append((r, sabab))

        self.stdout.write(self.style.SUCCESS(f"\n=== UMUMIY: {jami} rieltor, {faol_soni} faol, {len(nofaol_royxat)} nofaol ===\n"))

        royxat = muammoli_royxat if opts.get('muammoli') else nofaol_royxat
        if opts.get('muammoli'):
            self.stdout.write(self.style.WARNING(
                f"Obuna bilan bog'liq muammoli (nofaol) rieltorlar: {len(muammoli_royxat)}\n"
            ))

        for r, sabab in royxat:
            tid = r.user.telegram_id if r.user else '—'
            ism = r.user.full_name if r.user else '—'
            style = self.style.ERROR if 'KUTILMOQDA' in sabab or 'o\'tib ketgan' in sabab else self.style.NOTICE
            self.stdout.write(style(f"[id={r.id}] {ism} (tg={tid}): {sabab}"))

    def _batafsil(self, qs):
        r = qs.first()
        if not r:
            self.stdout.write(self.style.ERROR("Rieltor topilmadi"))
            return
        now = timezone.now()
        self.stdout.write(self.style.SUCCESS(f"\n=== Rieltor id={r.id} — {r.user} ==="))
        self.stdout.write(f"user.is_active     : {r.user.is_active}")
        self.stdout.write(f"verify_holat       : {r.verify_holat}")
        self.stdout.write(f"bloklangan         : {r.bloklangan}")
        self.stdout.write(f"bepul_muddat_tugash: {r.bepul_muddat_tugash} (hozir: {now})")
        self.stdout.write(f"obuna_faol         : {r.obuna_faol}")
        self.stdout.write(f"obuna_tugash       : {r.obuna_tugash}")
        self.stdout.write(self.style.WARNING(f">>> FAOL: {r.faol}"))
        self.stdout.write(f">>> Sabab: {nofaol_sababi(r)}\n")

        self.stdout.write("Obunalar tarixi:")
        for o in r.obunalar.all().select_related('tarif').prefetch_related('tolovlar'):
            self.stdout.write(
                f"  - obuna#{o.id} tarif={o.tarif.nomi} holat={o.holat} "
                f"boshlanish={o.boshlanish_vaqti} tugash={o.tugash_vaqti} faolmi={o.faolmi}"
            )
            for t in o.tolovlar.all():
                self.stdout.write(
                    f"      tolov#{t.id} provayder={t.provayder} holat={t.holat} "
                    f"summa={t.summa} tolangan={t.tolangan_vaqt}"
                )
