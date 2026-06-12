from django.db import models


class Viloyat(models.Model):
    """Shahar / viloyat — masalan: Toshkent shahar, Andijon viloyati."""
    nomi = models.CharField(max_length=100, unique=True)
    tartib = models.PositiveIntegerField(default=0, help_text="Ro'yxatdagi tartibi")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Viloyat'
        verbose_name_plural = 'Viloyatlar'
        ordering = ['tartib', 'nomi']

    def __str__(self):
        return self.nomi


class MulkTuri(models.Model):
    """Mulk turi — Kvartira, Hovli, Offis, Dalahovli, Bo'sh yer."""
    kod = models.CharField(max_length=30, unique=True)
    nomi = models.CharField(max_length=100)
    tartib = models.PositiveIntegerField(default=0, help_text="Ro'yxatdagi tartibi")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Mulk turi'
        verbose_name_plural = 'Mulk turlari'
        ordering = ['tartib', 'nomi']

    def __str__(self):
        return self.nomi


class Hudud(models.Model):
    nomi = models.CharField(max_length=100)
    shahar = models.CharField(max_length=100, default='Toshkent')  # eski maydon — moslik uchun
    viloyat = models.ForeignKey(
        Viloyat,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='hududlar'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Hudud'
        verbose_name_plural = 'Hududlar'
        ordering = ['nomi']

    def __str__(self):
        if self.viloyat_id:
            return f"{self.nomi} — {self.viloyat.nomi}"
        return f"{self.nomi} — {self.shahar}"
