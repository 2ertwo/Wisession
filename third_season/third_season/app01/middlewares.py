from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect

import app01.models as models


class AuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.path_info == "/favicon.ico":
            return
        if request.path_info.startswith('/media/verify_picture/'):
            return
        if request.path_info.startswith('/static/'):
            return
        if request.path_info.startswith('/media/'):
            info_dict = request.session.get("info")
            if info_dict:
                return
        if request.path_info.startswith('/company/'):
            if request.path_info in ["/company/login/", "/company/register/", "/company/register/email_send/"]:
                return
            info_dict = request.session.get("info")
            if info_dict:
                if info_dict['type'] == 1:
                    return
            return redirect("/company/login/")
        if request.path_info in ["/login/", "/register/", "/forget/", "/verify/"] or request.path_info.startswith(
                '/reset/') or request.path_info.startswith('/static/img/verify_picture/'):
            return
        info_dict = request.session.get("info")
        if info_dict:
            if info_dict['type'] == 0:
                return
        return redirect("/login/")


class RightMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.path_info.startswith('/company/service/'):
            temp_flag = True
            for word in request.path_info.split('/'):
                if str.isdigit(word):
                    temp_flag = False
                    service_id = word
                    break
            if temp_flag:
                return
            owner_company = models.ServiceInfo.objects.filter(id=service_id).first().belong.id
            now_company = request.session['info']['id']
            if owner_company == now_company and request.session['info']['type'] == 1:
                return
            return redirect('/company/service/list/')
        return
