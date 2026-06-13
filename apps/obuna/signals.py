"""
Obuna app signallari.

Hozircha bu yerda og'ir biznes-logika yo'q — obunaning faolligi
`Obuna.faolmi` va `ObunaQuerySet.faol()` orqali real vaqtda hisoblanadi,
shuning uchun tugagan obunani majburan belgilash shart emas.

Kelajakda Payme/Click webhook'lari yoki Celery cron orqali muddati
o'tgan obunalarni `TUGAGAN` deb belgilash logikasi shu yerga qo'shiladi.
"""
