from django.urls import path
from .views import (
    ReviewYaratishView,
    RieltorReviewlarView,
    RieltorReytingView,
    UserReviewlarView,
    IjobiyReviewlarView,
)

urlpatterns = [
    path('reviews/', ReviewYaratishView.as_view(), name='review-yaratish'),
    path('reviews/mening/', UserReviewlarView.as_view(), name='user-reviewlar'),

    # User paneli — "Mijozlar fikrlari" bo'limi (AllowAny, yulduz >= 4)
    path('reviews/ijobiy/', IjobiyReviewlarView.as_view(), name='ijobiy-reviewlar'),

    path('reviews/rieltor/<int:rieltor_id>/', RieltorReviewlarView.as_view(), name='rieltor-reviewlar'),
    # path('reviews/rieltor/<int:rieltor_id>/reyting/', RieltorReytingView.as_view(), name='rieltor-reyting'),
]
