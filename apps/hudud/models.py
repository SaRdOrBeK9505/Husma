from django.db import models


class Hudud(models.Model):
    nomi = models.CharField(max_length=100)
    shahar = models.CharField(max_length=100, default='Toshkent')  # kelajak uchun
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Hudud'
        verbose_name_plural = 'Hududlar'
        ordering = ['nomi']

    def __str__(self):
        return f"{self.nomi} — {self.shahar}"