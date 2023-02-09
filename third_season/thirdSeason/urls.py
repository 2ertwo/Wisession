"""thirdSeason URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path

from django.conf.urls import url


import app01.views

from django.views.static import serve
from thirdSeason.settings import MEDIA_ROOT,STATIC_URL,STATIC_ROOT

handler404 = app01.views.page_not_found_404
handler500 = app01.views.page_not_found_500

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", app01.views.login),
    path("register/", app01.views.register),
    path("forget/", app01.views.forget),
    path("verify/", app01.views.verify),

    path("reset/<str:random_str>/", app01.views.reset),

    path("user/logout/", app01.views.logout),
    path("user/message/", app01.views.user_message),
    path("user/subscribe_list/", app01.views.user_subscribe_list),
    path("user/subscribe/<int:service_id>/", app01.views.user_subscribe),
    path("user/unfollow/<int:service_id>/", app01.views.user_unfollow),
    path("user/notice/", app01.views.user_notice),
    path("user/about/", app01.views.user_about),
    path("user/personal_info/", app01.views.user_personal_info),
    path("user/personal_info/edit/", app01.views.user_personal_info_edit),
    path("user/edit_icon/", app01.views.user_edit_icon),
    path("user/dialog/<int:service_id>/", app01.views.user_dialog),
    path("user/change_password/", app01.views.user_change_password),
    path("user/qa/", app01.views.qa),
    path("user/save_question/", app01.views.save_question),

    path("user/search/", app01.views.search),

    path("company/login/", app01.views.company_login),
    path("company/register/", app01.views.company_register),
    path("company/register/email_send/", app01.views.company_register_email_send),
    path("company/main/", app01.views.company_main),
    path("company/logout/", app01.views.company_logout),
    path("company/edit_password/", app01.views.company_edit_password),
    path("company/edit/", app01.views.company_edit),
    path("company/edit_icon/", app01.views.company_edit_icon),
    path("company/service/list/", app01.views.company_service_list),
    path("company/service/new/", app01.views.company_service_new),
    path("company/service/edit/<int:service_id>/", app01.views.company_service_edit),
    path("company/service/set_url/", app01.views.company_service_set_url),
    path("company/service/reset_url/<int:service_id>/", app01.views.company_service_reset_url),
    path("company/service/delete/<int:service_id>/", app01.views.company_service_delete),
    path("company/service/icon/upload/", app01.views.service_icon_upload),
    path("company/service/icon/edit/<int:service_id>/", app01.views.service_icon_edit),
    path("company/service/question/upload/<int:service_id>/", app01.views.question_upload),
    path("company/service/question/add/<int:service_id>/", app01.views.company_service_question_add),
    path("company/service/question/list/<int:service_id>/<int:page>/", app01.views.company_service_question_list),
    path("company/service/question/delete/<int:service_id>/<int:question_id>/",app01.views.company_service_question_delete),
    path("company/service/deploy/<int:service_id>/preview/", app01.views.service_deploy_preview),
    path("company/service/deploy/<int:service_id>/deploy/", app01.views.service_deploy),
    path("company/service/notice/add/<int:service_id>/", app01.views.company_service_notice_add),
    path("company/service/notice/list/<int:service_id>/", app01.views.company_service_notice_list),
    path("company/service/notice/delete/<int:service_id>/<int:notice_id>/", app01.views.company_service_notice_delete),
    path("company/service/notice/edit/<int:service_id>/<int:notice_id>/", app01.views.company_service_notice_edit),
    path("company/help/", app01.views.company_help),

    re_path(r'^media/(?P<path>.*)/', serve, {"document_root": MEDIA_ROOT}),
    url(r'^static/(?P<path>.*)$', serve,{'document_root': STATIC_ROOT}, name='static'),

] 
