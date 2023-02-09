# -*- coding: UTF-8 -*-
import time

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q

import app01.models as models

from django.contrib.auth.hashers import make_password, check_password

from app01.utils.sundries import get_60_random_text


class LoginModelForm(forms.ModelForm):
    class Meta:
        model = models.UserInfo
        fields = ["username", "password"]
        widgets = {
            "username": forms.TextInput(attrs={"type": "text", "placeholder": "用户名"}),
            "password": forms.TextInput(attrs={"type": "password", "placeholder": "密码"})
        }


class RegisterModelForm(forms.ModelForm):
    password_again = forms.CharField()
    password_again.label = '确认密码'
    password_again.widget = forms.TextInput(attrs={"type": "password", "placeholder": "密码"})

    class Meta:
        model = models.UserInfo
        fields = ["username", "email", "password"]
        widgets = {
            "username": forms.TextInput(attrs={"type": "text", "placeholder": "用户名"}),
            "email": forms.EmailInput(attrs={"type": "text", "placeholder": "邮箱"}),
            "password": forms.TextInput(attrs={"type": "password", "placeholder": "密码"})
        }

    def clean(self):
        pwd1 = self.cleaned_data.get('password')
        pwd2 = self.cleaned_data.get('password_again')
        company_name = self.cleaned_data.get('username')
        email = self.cleaned_data.get('email')
        search_result = models.UserInfo.objects.filter(Q(username=company_name) | Q(email=email)).first()  # | Q(email=email)
        if search_result:
            self.add_error('username', ValidationError('邮箱或用户名称已被占用'))
            self.add_error('email', ValidationError('邮箱或用户名称已被占用'))
        if pwd1 == pwd2:
            pwd = make_password(pwd1, None, 'pbkdf2_sha1')
            self.cleaned_data.update(password=pwd)
            return self.cleaned_data
        else:
            self.add_error('password_again', ValidationError('两次密码输入不同'))


class ForgetModelForm(forms.ModelForm):
    class Meta:
        model = models.UserInfo
        fields = ["email"]
        widgets = {
            "email": forms.EmailInput(attrs={"type": "text", "placeholder": "邮箱"})
        }

    def clean(self):
        email = self.cleaned_data.get('email')
        search_result = models.UserInfo.objects.filter(email=email).first()
        if not search_result:
            self.add_error('email', '该邮箱未注册')
            return self.cleaned_data
        new_search_result = models.PasswordReset.objects.filter(email=email).first()
        if new_search_result:
            if int(time.time()) - new_search_result.create_time > 30 * 60:
                new_search_result.delete()
            else:
                self.add_error('email', '30分钟之内发过该邮箱了')
                return self.cleaned_data
        models.PasswordReset.objects.create(email=email, random_str=get_60_random_text(), create_time=time.time())
        return self.cleaned_data


class EditPersonalInfo(forms.ModelForm):
    class Meta:
        model = models.UserInfo
        fields = ["username", "gender", "email", "describe"]
        widgets = {
            "username": forms.TextInput(attrs={"type": "text", "placeholder": "用户名", "class": "form-control"}),
            "email": forms.EmailInput(attrs={"type": "text", "placeholder": "邮箱", "class": "form-control"}),
            "describe": forms.TextInput(attrs={"type": "text", "placeholder": "个人简介", "class": "form-control"}),
        }


class ChangePasswordForm(forms.ModelForm):
    password_new = forms.CharField()
    password_new.label = '新密码'
    password_new.widget = forms.TextInput(attrs={"type": "password", "placeholder": "新密码", "class": "form-control"})

    class Meta:
        model = models.UserInfo
        fields = ["password"]
        labels = {"password": '原密码'}
        widgets = {
            "password": forms.TextInput(attrs={"type": "password", "placeholder": "原密码", "class": "form-control"})
        }


class ResetPasswordForm(forms.ModelForm):
    password_again = forms.CharField()
    password_again.label = '确认密码'
    password_again.widget = forms.TextInput(attrs={"type": "password", "placeholder": "密码"})

    class Meta:
        model = models.UserInfo
        fields = ["password"]
        widgets = {
            "password": forms.TextInput(attrs={"type": "password", "placeholder": "密码"})
        }

    def clean(self):
        pwd1 = self.cleaned_data.get('password')
        pwd2 = self.cleaned_data.get('password_again')
        if pwd1 == pwd2:
            pwd = make_password(pwd1, None, 'pbkdf2_sha1')
            self.cleaned_data.update(password=pwd)
            return self.cleaned_data
        else:
            self.add_error('password_again', ValidationError('两次密码输入不同'))


class CompanyLogin(forms.ModelForm):
    class Meta:
        model = models.CompanyInfo
        fields = ["company_name", "password"]
        labels = {"company_name": '企业名', "password": '密码'}
        widgets = {
            "company_name": forms.TextInput(
                attrs={"type": "text", "placeholder": "企业名", "class": "form-control", "autocomplete": "off"}),
            "password": forms.TextInput(
                attrs={"type": "password", "placeholder": "密码", "class": "form-control", "autocomplete": "off"})
        }


class CompanyRegister(forms.ModelForm):
    password_again = forms.CharField()
    password_again.label = '再输入一次密码'
    password_again.widget = forms.TextInput(
        attrs={"type": "password", "placeholder": "再输入一次密码", "class": "form-control"})

    email_code = forms.CharField()
    email_code.label = '邮箱验证码'
    email_code.widget = forms.TextInput(
        attrs={"type": "text", "placeholder": "邮箱验证码", "class": "form-control"})

    class Meta:
        model = models.CompanyInfo
        fields = ['company_name', 'type', 'password', 'email']
        widgets = {
            "company_name": forms.TextInput(
                attrs={"type": "text", "placeholder": "企业名", "class": "form-control", "autocomplete": "off"}),
            "type": forms.Select(attrs={"class": "form-select"}),
            "password": forms.TextInput(attrs={"type": "password", "placeholder": "密码", "class": "form-control"}),
            "email": forms.EmailInput(
                attrs={"type": "email", "placeholder": "邮箱", "class": "form-control", "id": "email_zone"}),
            "email_code": forms.TextInput(attrs={"type": "password", "placeholder": "邮箱验证码", "class": "form-control"})
        }

    field_order = ['company_name', 'type', 'email', 'email_code', 'password', 'password_again']

    def clean(self):
        pwd1 = self.cleaned_data.get('password')
        pwd2 = self.cleaned_data.get('password_again')
        company_name = self.cleaned_data.get('company_name')
        email = self.cleaned_data.get('email')
        search_result = models.CompanyInfo.objects.filter(Q(company_name=company_name) | Q(email=email)).first()  # | Q(email=email)
        if search_result:
            raise ValidationError('邮箱或企业名称已被占用')
        if pwd1 == pwd2:
            pwd = make_password(pwd1, None, 'pbkdf2_sha1')
            self.cleaned_data.update(password=pwd)
            return self.cleaned_data
        else:
            raise ValidationError('两次密码输入不同')


class CompanyPasswordEdit(forms.ModelForm):
    new_password = forms.CharField()
    new_password.label = '输入新密码'
    new_password.widget = forms.TextInput(
        attrs={"type": "password", "placeholder": "新密码", "class": "form-control"})

    new_password_again = forms.CharField()
    new_password_again.label = '再次输入新密码'
    new_password_again.widget = forms.TextInput(
        attrs={"type": "password", "placeholder": "再次输入新密码", "class": "form-control"})

    class Meta:
        model = models.CompanyInfo
        fields = ['password']
        widgets = {
            "password": forms.TextInput(attrs={"type": "password", "placeholder": "输入密码", "class": "form-control"})
        }

    field_order = ['password', 'new_password', 'new_password_again']

    def clean(self):
        new_pwd1 = self.cleaned_data.get('new_password')
        new_pwd2 = self.cleaned_data.get('new_password_again')
        if new_pwd1 == new_pwd2:
            new_pwd = make_password(new_pwd1, None, 'pbkdf2_sha1')
            self.cleaned_data.update(new_password=new_pwd)
            return self.cleaned_data
        else:
            self.add_error('new_password_again', ValidationError('两次密码输入不同'))


class CompanyNewService(forms.ModelForm):
    class Meta:
        model = models.ServiceInfo
        fields = ["service_name", "type", "describe"]
        labels = {"service_name": "服务名", "type": "服务类型", "describe": "描述"}
        widgets = {
            "service_name": forms.TextInput(attrs={"type": "text", "placeholder": "服务名", "class": "form-control"}),
            "type": forms.Select(attrs={"class": "form-select"}),
            "describe": forms.Textarea(
                attrs={"type": "text", "placeholder": "服务描述", "class": "form-control", "rows": "6"})}


class ServiceWithInterface(forms.ModelForm):
    now_id = forms.CharField()
    now_id.label = '当前服务id'
    now_id.widget = forms.TextInput(attrs={"class": "form-control-plaintext"})

    class Meta:
        model = models.ServiceInfo
        fields = ["target_url", "url_token"]
        labels = {"target_url": "目标url", "url_token": "描述"}
        widgets = {
            "target_url": forms.TextInput(attrs={"type": "text", "placeholder": "目标url", "class": "form-control"}),
            "url_token": forms.TextInput(
                attrs={"class": "form-control-plaintext"})}

    field_order = ['now_id', 'target_url', 'url_token']


class CompanyEditService(forms.ModelForm):
    class Meta:
        model = models.ServiceInfo
        fields = ["service_name", "describe"]
        labels = {"service_name": "服务名", "describe": "描述"}
        widgets = {
            "service_name": forms.TextInput(attrs={"type": "text", "placeholder": "服务名", "class": "form-control"}),
            "describe": forms.Textarea(
                attrs={"type": "text", "placeholder": "服务描述", "class": "form-control", "rows": "6"})
        }


class NewServiceIcon(forms.ModelForm):
    class Meta:
        model = models.ServiceInfo
        fields = ["icon"]
        widgets = {
            "icon": forms.FileField()
        }


class Notice(forms.ModelForm):
    class Meta:
        model = models.Notice
        fields = ['text']
        labels = {"text": "这里写详细全文"}
        widgets = {
            'text': forms.Textarea(
                attrs={"type": "text", "placeholder": "详细", "class": "form-control", "rows": "6"})
        }


class CompanyEdit(forms.ModelForm):
    class Meta:
        model = models.CompanyInfo
        fields = ["company_name"]
        labels = {"company_name": '企业名'}
        widgets = {
            "company_name": forms.TextInput(
                attrs={"type": "text", "placeholder": "企业名", "class": "form-control", "autocomplete": "off"})
        }
