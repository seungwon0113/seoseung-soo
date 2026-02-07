from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views import View

from config.models import SiteSetting
from users.utils.permission import AdminPermission


class SiteSettingView(AdminPermission, View):
    template_name = 'admin/site_settings.html'

    def get(self, request: HttpRequest) -> HttpResponse:
        setting = SiteSetting.get_settings()
        return render(request, self.template_name, {'setting': setting})

    def post(self, request: HttpRequest) -> HttpResponse:
        setting = SiteSetting.get_settings()

        hero_title = request.POST.get('hero_title', '').strip()
        hero_subtitle = request.POST.get('hero_subtitle', '').strip()

        setting.hero_title = hero_title
        setting.hero_subtitle = hero_subtitle

        hero_image = request.FILES.get('hero_image')
        if hero_image:
            if setting.hero_image:
                setting.hero_image.delete(save=False)
            setting.hero_image = hero_image

        setting.save()
        messages.success(request, '메인 페이지 설정이 저장되었습니다.')
        return redirect('site-settings')
