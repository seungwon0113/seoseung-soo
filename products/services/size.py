from typing import List

from products.models import Size


class SizeService:
    @staticmethod
    def get_all_sizes() -> List[Size]:
        return list(Size.objects.all().order_by('name'))

    @staticmethod
    def get_size_by_id(size_id: int) -> Size | None:
        try:
            return Size.objects.get(id=size_id)
        except Size.DoesNotExist:
            return None
