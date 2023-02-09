import time

from django.db import models
from django.utils import timezone


class UserInfo(models.Model):
    id = models.IntegerField(verbose_name="用户号", auto_created=True, primary_key=True)
    username = models.CharField(verbose_name="用户名", max_length=32)
    password = models.CharField(verbose_name="密码", max_length=60)
    email = models.EmailField(verbose_name="邮箱")
    gender = models.IntegerField(verbose_name="性别", choices=((1, '男'),
                                                             (2, '女'),
                                                             (3, '未知')), default=3)
    describe = models.TextField(verbose_name="自我介绍")
    icon = models.ImageField(verbose_name="头像", default='default.jpg')
    create_time = models.DateTimeField(verbose_name="加入时间", default=timezone.now())


class CompanyInfo(models.Model):
    id = models.IntegerField(verbose_name="企业号", auto_created=True, primary_key=True)
    company_name = models.CharField(verbose_name="企业名", max_length=32)
    password = models.CharField(verbose_name="密码", max_length=60)
    type = models.IntegerField(verbose_name="企业类型", choices=((1, '学校'),
                                                             (2, '政府'),
                                                             (3, '企业'),
                                                             (4, '其他')))
    email = models.EmailField(verbose_name="邮箱")
    icon = models.ImageField(verbose_name="企业图标", default='default.jpg')
    create_time = models.DateTimeField(verbose_name="加入时间", default=timezone.now())


class ServiceInfo(models.Model):
    id = models.IntegerField(verbose_name="服务号", auto_created=True, primary_key=True)
    service_name = models.CharField(verbose_name="服务名", max_length=32)
    belong = models.ForeignKey(verbose_name="所属企业", to='CompanyInfo', to_field='id', on_delete=models.CASCADE)
    describe = models.TextField(verbose_name="描述")
    type = models.IntegerField(verbose_name="类型", choices=((1, '智能文档问答'),
                                                           (2, '外部接口问答')))
    icon = models.ImageField(verbose_name="图标", default='default.jpg')
    create_time = models.DateTimeField(verbose_name="创建时间", default=timezone.now())
    target_url = models.CharField(verbose_name="目标url", default='http://', max_length=200)
    url_token = models.CharField(verbose_name="密钥", default='secret', max_length=60)


class Subscribe(models.Model):
    user_id = models.ForeignKey(to='UserInfo', to_field='id', on_delete=models.CASCADE)
    service_id = models.ForeignKey(to='ServiceInfo', to_field='id', on_delete=models.CASCADE)


class QuestionAndAnswer(models.Model):
    id = models.IntegerField(auto_created=True, primary_key=True)
    question = models.TextField()
    answer = models.TextField()
    belong = models.ForeignKey(verbose_name="所属服务", to='ServiceInfo', to_field='id', on_delete=models.CASCADE)
    deployed = models.BooleanField(verbose_name="是否已部署", default=False)


class Notice(models.Model):
    id = models.IntegerField(auto_created=True, primary_key=True)
    from_service = models.ForeignKey(to='ServiceInfo', to_field='id', on_delete=models.CASCADE)
    text = models.TextField()
    create_time = models.DateTimeField(verbose_name="创建时间", default=timezone.now())


class Dialog(models.Model):
    id = models.IntegerField(auto_created=True, primary_key=True)
    user_id = models.ForeignKey(to='UserInfo', to_field='id', on_delete=models.CASCADE)
    service_id = models.ForeignKey(to='ServiceInfo', to_field='id', on_delete=models.CASCADE)
    by_user = models.BooleanField()
    text = models.TextField()
    create_time = models.DateTimeField(verbose_name="创建时间", default=timezone.now())


class PasswordReset(models.Model):
    email = models.EmailField(verbose_name="邮箱")
    create_time = models.BigIntegerField(verbose_name="请求时间", default=int(time.time()))
    random_str = models.CharField(verbose_name="链接随机字符", max_length=60)

# Create your models here.
