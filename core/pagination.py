from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class ArizaPagination(PageNumberPagination):
    """
    Ariza ro'yxatlari uchun paginatsiya.

    Javob shakli eski frontend bilan mos (backward compatible):
      - `jami_soni` : jami ariza soni (avvalgi kalit saqlangan)
      - `arizalar`  : joriy sahifadagi arizalar (avvalgi kalit saqlangan)
    Qo'shimcha pagination metadatasi:
      - `keyingi` / `oldingi` : keyingi va oldingi sahifa URL'lari
      - `sahifa` / `jami_sahifa` : joriy va umumiy sahifalar soni

    So'rov: ?page=2&page_size=20
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'jami_soni': self.page.paginator.count,
            'jami_sahifa': self.page.paginator.num_pages,
            'sahifa': self.page.number,
            'keyingi': self.get_next_link(),
            'oldingi': self.get_previous_link(),
            'arizalar': data,
        })