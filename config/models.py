import os
import uuid

from django.db import models

from config.basemodel import BaseModel


def site_image_upload_path(instance: 'SiteSetting', filename: str) -> str:
    ext = filename.split('.')[-1]
    new_filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('site', 'images', new_filename)


class SiteSetting(BaseModel):
    hero_image = models.ImageField(
        upload_to=site_image_upload_path,
        blank=True,
        null=True,
        verbose_name='메인 Hero 이미지',
    )
    hero_title = models.CharField(
        max_length=100,
        default='New Season',
        blank=True,
        verbose_name='Hero 타이틀',
    )
    hero_subtitle = models.CharField(
        max_length=200,
        default='가장 사랑받는 아이템을 만나보세요.',
        blank=True,
        verbose_name='Hero 서브타이틀',
    )

    class Meta:
        db_table = 'site_settings'
        verbose_name = '사이트 설정'
        verbose_name_plural = '사이트 설정'

    @classmethod
    def get_settings(cls) -> 'SiteSetting':
        setting, _ = cls.objects.get_or_create(pk=1)
        return setting