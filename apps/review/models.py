from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.users.models import CustomUser
from apps.makler.models import MaklerProfil


class Review(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    rieltor = models.ForeignKey(
        MaklerProfil,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    yulduz = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    matn = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Review'
        verbose_name_plural = 'Reviewlar'
        ordering = ['-created_at']
        unique_together = ['user', 'rieltor']

    def __str__(self):
        return f"{self.user} → {self.rieltor} — {self.yulduz}⭐"