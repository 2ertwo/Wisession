import datetime
import os.path
import time

from django.http import JsonResponse
from django.shortcuts import render, HttpResponse, redirect
from django.http import HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
import random
import app01.forms as forms
import app01.models as models
from thirdSeason.settings import MEDIA_ROOT, MEDIA_URL
from django.db.models import Max, Count, Q, F
from django.contrib.auth.hashers import make_password, check_password

from app01.utils.send_mail import MS_obj
# from app01.utils.fake_paddleqa import ManyModel, SingleHalfModel
from app01.utils.paddleqa import ManyModel, SingleHalfModel
from app01.utils.sundries import get_60_random_text, send_request
from app01.utils.process_qapairs import process_qapair

model_dict = {}
for i in list(models.ServiceInfo.objects.all().values_list('id')):
    model_dict[str(i[0])] = SingleHalfModel(name=str(i[0]), content=process_qapair(list(
        models.QuestionAndAnswer.objects.filter(belong__id=i[0]).all().values_list('question', 'belong__id',
                                                                                   'answer'))))
FMM = ManyModel(model_dict)


def get_verify_code():
    animal_class = ['adults', 'children']
    chinese_class = {'adults': '成年人', 'children': '未成年人'}
    paths = {
        animal_name: os.path.join(MEDIA_ROOT, 'verify_picture', 'adults_children',
                                  'name_list_for_' + animal_name + '.txt')
        for animal_name in animal_class}
    class_of_each = random.choices(animal_class, k=9)
    answer_target = random.choice(class_of_each)
    pic_list = []
    answer_list = []
    count = 0
    for target_animal in class_of_each:
        if target_animal == answer_target:
            answer_list.append(count)
        count = count + 1
        file_target = open(paths[target_animal])
        target_list = file_target.readlines()
        file_target.close()
        pic_list.append(
            MEDIA_URL + 'verify_picture/adults_children/' + random.choice(target_list).strip() + '/')
    answer_str = ''
    answer_list.sort()
    for answer in answer_list:
        answer_str = answer_str + str(answer)
    print(answer_str)
    return {'target': chinese_class[answer_target], 'answer_list': answer_list, 'answer_str': answer_str,
            'pic_list': pic_list}


@csrf_exempt
def verify(request):
    answer = request.POST.get('answer')
    if answer == request.session['verify']['answer']:
        request.session['verify'] = {'is_verified': True, 'answer': None}
        return JsonResponse({'status': True})
    return JsonResponse({'status': False})


def login(request):
    form = forms.LoginModelForm()
    is_verified = False
    verify_code = get_verify_code()

    dictionary = {'is_verified': is_verified,
                  'verify_code': verify_code,
                  'form': form}
    if request.method == 'GET':
        request.session['verify'] = {'is_verified': False, 'answer': verify_code['answer_str']}
        return render(request, "login.html", dictionary)
    else:
        if request.session['verify']['is_verified']:
            dictionary['form'] = forms.LoginModelForm(request.POST)
            if dictionary['form'].is_valid():
                user_token = dictionary['form'].cleaned_data['username']
                user_object = models.UserInfo.objects.filter(
                    Q(username=user_token) | Q(email=user_token)).first()
                if not user_object:
                    dictionary['form'].add_error("password", "用户或密码错误")
                    return render(request, "login.html", dictionary)
                if not check_password(dictionary['form'].cleaned_data['password'], user_object.password):
                    dictionary['form'].add_error("password", "用户或密码错误")
                    return render(request, "login.html", dictionary)
                request.session["info"] = {"id": user_object.id, "name": user_object.username, "type": 0}
                return redirect('/user/message/')
        dictionary['is_verified'] = False
        return render(request, "login.html", dictionary)


def register(request):
    form = forms.RegisterModelForm()
    is_verified = False
    verify_code = get_verify_code()

    dictionary = {'is_verified': is_verified,
                  'verify_code': verify_code,
                  'form': form}
    if request.method == 'GET':
        request.session['verify'] = {'is_verified': False, 'answer': verify_code['answer_str']}
        return render(request, "register.html", dictionary)
    else:
        if request.session['verify']['is_verified']:
            dictionary['form'] = forms.RegisterModelForm(request.POST)
            if dictionary['form'].is_valid():
                temp = dictionary['form'].cleaned_data
                del temp['password_again']
                temp['id'] = models.UserInfo.objects.all().aggregate(Max('id'))['id__max'] + 1
                user_object = models.UserInfo.objects.create(**temp)
                request.session["info"] = {"id": user_object.id, "name": user_object.username, "type": 0}
                return redirect('/user/message/')
        dictionary['is_verified'] = False
        return render(request, "register.html", dictionary)


def forget(request):
    form = forms.ForgetModelForm()
    verify_code = get_verify_code()

    dictionary = {'is_verified': False,
                  'verify_code': verify_code,
                  'form': form}
    if request.method == 'GET':
        request.session['verify'] = {'is_verified': False, 'answer': verify_code['answer_str']}
        return render(request, "forget.html", dictionary)
    else:
        if request.session['verify']['is_verified']:
            dictionary['form'] = forms.ForgetModelForm(request.POST)
            if dictionary['form'].is_valid():
                reset_obj = models.PasswordReset.objects.filter(email=dictionary['form'].cleaned_data['email']).first()
                text = '您好，你刚刚进行了密码找回，请访问下面的链接进行:http://43.139.21.149:1234/reset/' + reset_obj.random_str + '/'
                target = reset_obj.email
                MS_obj.send_txt([target], text, subject='重置密码', to='用户')
                return render(request, 'reset_info.html')
        dictionary['is_verified'] = False

        return render(request, "forget.html", dictionary)


def reset(request, random_str):
    reset_obj = models.PasswordReset.objects.filter(random_str=random_str).first()
    if not reset_obj:
        return page_not_found_404(request, None)
    if time.time() - reset_obj.create_time > 30 * 60:
        return page_not_found_404(request, None)
    reset_form = forms.ResetPasswordForm()
    if request.method == 'GET':
        return render(request, "reset.html", {'form': reset_form})
    else:
        reset_form = forms.ResetPasswordForm(request.POST)
        if reset_form.is_valid():
            models.UserInfo.objects.filter(email=reset_obj.email).update(password=reset_form.cleaned_data['password'])
            print(reset_form.cleaned_data['password'])
            return redirect('/login/')
        return render(request, "reset.html", {'form': reset_form})


def logout(request):
    request.session.clear()
    return redirect("/login/")


def page_not_found_404(request, exception):
    return render(request, '404.html')


def page_not_found_500(request, exception):
    return render(request, '500.html')


def user_message(request):
    subscribe_list = models.ServiceInfo.objects.filter(subscribe__user_id=request.session['info']['id']).all().values(
        'id')
    message_info = []
    for service_id in subscribe_list:
        message_info.append(
            models.Dialog.objects.filter(user_id=request.session['info']['id'], service_id=service_id['id']).order_by(
                "create_time").last())
    for message in message_info:
        if not message:
            message_info.remove(message)
    message_info.sort(key=lambda x: x.create_time, reverse=True)
    return render(request, "user_message.html", {'message_info': message_info})


def user_subscribe_list(request):
    subscribe_list = models.ServiceInfo.objects.filter(subscribe__user_id=request.session['info']['id']).all()
    return render(request, "user_subscribe_list.html", {'subscribe_list': subscribe_list})


def user_subscribe(request, service_id):
    sub_obj = models.Subscribe.objects.filter(service_id_id=service_id,
                                              user_id_id=request.session.get('info')['id']).first()
    if sub_obj:
        return JsonResponse({'status': False, 'to_show': '宁已经定阅了这个服务了'})
    else:
        models.Subscribe.objects.create(service_id_id=service_id, user_id_id=request.session.get('info')['id'])
        return JsonResponse({'status': True, 'to_show': '宁成功定阅了这个服务了'})


def user_unfollow(request, service_id):
    sub_obj = models.Subscribe.objects.filter(service_id_id=service_id,
                                              user_id_id=request.session.get('info')['id']).first()
    if not sub_obj:
        return JsonResponse({'status': True, 'to_show': '宁本来就没有定阅这个服务'})
    else:
        models.Subscribe.objects.filter(service_id_id=service_id, user_id_id=request.session.get('info')['id']).delete()
        return JsonResponse({'status': True, 'to_show': '宁成功取消定阅了这个服务了'})


def user_notice(request):
    subscribe_list = models.ServiceInfo.objects.filter(subscribe__user_id=request.session['info']['id']).all()
    notice_list = models.Notice.objects.filter(from_service__in=subscribe_list).order_by('-id').all()
    return render(request, "user_notice.html", {'notice_list': notice_list})


def user_about(request):
    return render(request, "user_about.html")


def user_personal_info(request):
    personal_info = models.UserInfo.objects.filter(id=request.session['info']['id']).first()
    edit_form = forms.EditPersonalInfo(instance=personal_info)
    dictionary = {'personal_info': personal_info,
                  'edit_form': edit_form}
    return render(request, "user_personal_info.html", dictionary)


@csrf_exempt
def user_personal_info_edit(request):
    personal_info = models.UserInfo.objects.filter(id=request.session['info']['id']).first()
    edit_form = forms.EditPersonalInfo(data=request.POST, instance=personal_info)
    if edit_form.is_valid():
        edit_form.save()
        return JsonResponse({"status": True})
    return JsonResponse({"status": False, 'error': edit_form.errors})


def user_dialog(request, service_id):
    dialog_history = models.Dialog.objects.filter(service_id=service_id, user_id=request.session['info']['id']).all()
    user_icon = models.UserInfo.objects.filter(id=request.session['info']['id']).first().icon.__str__()
    service_obj = models.ServiceInfo.objects.filter(id=service_id).first()
    return render(request, "user_dialog.html",
                  {'dialog_history': dialog_history, 'user_icon': user_icon, 'service_obj': service_obj})


def user_change_password(request):
    form = forms.ChangePasswordForm()
    return render(request, "user_change_password.html", {'form': form})


def user_edit_icon(request):
    icon_obj = request.FILES['file']
    photo_types = ['.jpg', '.png', '.jpeg']
    flag = False
    for photo_type in photo_types:
        if icon_obj.name.endswith(photo_type):
            flag = True
    if not flag:
        return HttpResponseBadRequest('不支持或错误的图片文件格式，请刷新以重新上传')
    icon_name = str(random.randint(1000000, 9999999)) + '-' + icon_obj.name
    models.UserInfo.objects.filter(id=request.session['info']['id']).update(icon=icon_name)
    with open(os.path.join(MEDIA_ROOT, 'avatars', icon_name), 'wb') as f:
        for chunk in icon_obj:
            f.write(chunk)
    return redirect('/user/personal_info/')


@csrf_exempt
def save_question(request):
    service_id = request.POST['service_id']
    query = request.POST['query']
    user_id = request.session.get('info')['id']
    id = models.Dialog.objects.all().aggregate(Max('id'))['id__max'] + 1
    models.Dialog.objects.create(by_user=True, text=query, service_id_id=service_id, user_id_id=user_id, id=id)
    return JsonResponse({'status': True})


@csrf_exempt
def qa(request):
    service_id = request.POST['service_id']
    query = request.POST['query']
    user_id = request.session.get('info')['id']
    service_obj = models.ServiceInfo.objects.filter(id=service_id).first()
    if service_obj.type == 1:
        answer = FMM.use_model(service_id, query)['documents'][0].meta['answer']
    else:
        answer = send_request(service_obj, user_id, query)
    id = models.Dialog.objects.all().aggregate(Max('id'))['id__max'] + 1
    models.Dialog.objects.create(by_user=False, text=answer, service_id_id=service_id, user_id_id=user_id, id=id,
                                 create_time=datetime.datetime.now())
    return JsonResponse({'status': True, 'answer': answer})


def search(request):
    key = request.GET.get('key')
    if key:
        search_result = models.ServiceInfo.objects.filter(service_name__contains=key)
    else:
        search_result = models.ServiceInfo.objects.all()[0:10]
    return render(request, 'search_result.html', {'search_result': search_result})


def company_login(request):
    form = forms.CompanyLogin()
    dictionary = {'form': form}
    if request.method == 'GET':
        return render(request, "company_login.html", dictionary)
    else:
        dictionary['form'] = forms.CompanyLogin(request.POST)
        if dictionary['form'].is_valid():
            company_token = dictionary['form'].cleaned_data['company_name']
            company_object = models.CompanyInfo.objects.filter(
                Q(company_name=company_token) | Q(email=company_token)).first()
            if not company_object:
                dictionary['form'].add_error("password", "企业名或密码错误")
                return render(request, "company_login.html", dictionary)
            if not check_password(dictionary['form'].cleaned_data['password'], company_object.password):
                dictionary['form'].add_error("password", "用户或密码错误")
                return render(request, "company_login.html", dictionary)
            request.session["info"] = {"id": company_object.id, "name": company_object.company_name, "type": 1}
            return redirect('/company/main/')
        return render(request, "company_login.html", dictionary)


def company_register(request):
    form = forms.CompanyRegister()
    dictionary = {'form': form}
    if request.method == 'GET':
        return render(request, "company_register.html", dictionary)
    else:
        dictionary['form'] = forms.CompanyRegister(request.POST)
        if dictionary['form'].is_valid():
            temp = dictionary['form'].cleaned_data
            email_code = request.session.get('email_code')
            if email_code != temp['email_code']:
                dictionary['form'].add_error("email_code", "验证码不一致")
                return render(request, "company_register.html", dictionary)
            del temp['password_again']
            del temp['email_code']
            temp['id'] = models.CompanyInfo.objects.all().aggregate(Max('id'))['id__max'] + 1
            company_object = models.CompanyInfo.objects.create(**temp)
            request.session["info"] = {"id": company_object.id, "name": company_object.company_name, "type": 1}
            return redirect('/company/main/')
        dictionary['form'].add_error("password_again", "两次密码不一致")
        return render(request, "company_register.html", dictionary)


@csrf_exempt
def company_register_email_send(request):
    email = request.POST['email']
    email_code = request.session.get('email_code')
    if email_code:
        return JsonResponse({'status': False})
    email_code = str(random.randint(100000, 999999))
    request.session['email_code'] = email_code
    request.session.set_expiry(60)
    MS_obj.send_txt([email], email_code, '注册验证码', '用户')
    return JsonResponse({'status': True})


def company_main(request):
    company_info = models.CompanyInfo.objects.filter(id=request.session['info']['id']).first()
    form = forms.CompanyEdit(instance=company_info)
    dictionary = {'company_info': company_info, 'form': form}
    return render(request, "company_main.html", dictionary)


def company_logout(request):
    request.session.clear()
    return redirect("/company/login/")


def company_edit_password(request):
    form = forms.CompanyPasswordEdit()
    dictionary = {'form': form}
    if request.method == 'GET':
        return render(request, "company_edit_password.html", dictionary)
    else:
        dictionary['form'] = forms.CompanyPasswordEdit(request.POST)
        if dictionary['form'].is_valid():
            temp = dictionary['form'].cleaned_data
            company_info = models.CompanyInfo.objects.filter(id=request.session['info']['id'])
            if check_password(temp['password'], company_info.first().password):
                company_info.update(password=temp['new_password'])
                return redirect('/company/main/')
            dictionary['form'].add_error('password', '错误的密码')
        return render(request, "company_edit_password.html", dictionary)


def company_edit(request):
    form = forms.CompanyEdit(request.POST)
    if form.is_valid():
        temp_name = form.cleaned_data['company_name']
        models.CompanyInfo.objects.filter(id=request.session['info']['id']).update(
            company_name=temp_name)
        temp = request.session['info']
        temp['name'] = temp_name
        request.session.clear()
        request.session['info'] = temp
        return JsonResponse({"status": True})
    return JsonResponse({"status": False, 'error': form.errors})


def company_edit_icon(request):
    icon_obj = request.FILES['file']
    photo_types = ['.jpg', '.png', '.jpeg']
    flag = False
    for photo_type in photo_types:
        if icon_obj.name.endswith(photo_type):
            flag = True
    if not flag:
        return HttpResponseBadRequest('不支持或错误的图片文件格式，请刷新以重新上传')
    icon_name = str(random.randint(1000000, 9999999)) + '-' + icon_obj.name
    models.CompanyInfo.objects.filter(id=request.session['info']['id']).update(icon=icon_name)
    with open(os.path.join(MEDIA_ROOT, 'icon', icon_name), 'wb') as f:
        for chunk in icon_obj:
            f.write(chunk)
    return redirect('/company/main/')


def company_service_list(request):
    service_list = models.ServiceInfo.objects.filter(belong__id=request.session['info']['id']).all()
    return render(request, "company_service_list.html", {'service_list': service_list})


def company_service_new(request):
    step = request.GET.get('step')
    if not step:
        return redirect('/company/service/new/?step=1')
    step = int(step)
    if step == 1:
        form = forms.CompanyNewService()
        dictionary = {'form': form}
        if request.method == 'GET':
            return render(request, "company_service_new.html", dictionary)
        else:
            dictionary['form'] = forms.CompanyNewService(request.POST)
            if dictionary['form'].is_valid():
                temp = dictionary['form'].cleaned_data
                temp['belong'] = request.session['info']['id']
                request.session['nowCreatingService'] = temp
                return redirect('/company/service/new/?step=2')
            return render(request, "company_service_new.html", dictionary)
    elif step == 2:
        if not 'nowCreatingService' in request.session.keys():
            return redirect('/company/service/new/?step=1')
        finished = request.session['nowCreatingService']
        new_form = forms.NewServiceIcon()
        dictionary = {'finished': finished, 'new_form': new_form}
        return render(request, "company_service_new.html", dictionary)
    elif step == 3:
        if not 'nowCreatingService' in request.session.keys():
            return redirect('/company/service/new/?step=1')
        finished = request.session['nowCreatingService']
        finished['belong'] = models.CompanyInfo.objects.filter(id=finished['belong']).first()
        finished['id'] = models.ServiceInfo.objects.all().aggregate(Max('id'))['id__max'] + 1
        models.ServiceInfo.objects.create(**finished)
        service_created_id = finished['id']
        service_type = int(finished['type'])
        del request.session['nowCreatingService']
        if service_type == 1:
            return render(request, "company_service_new.html",
                          {'service_created_id': service_created_id, 'service_type': service_type})
        else:
            token = get_60_random_text()
            appended_form = forms.ServiceWithInterface({'now_id': service_created_id, 'url_token': token})
            models.ServiceInfo.objects.filter(id=service_created_id).update(url_token=token)
            return render(request, "company_service_new.html",
                          {'service_created_id': service_created_id, 'service_type': service_type,
                           'appended_form': appended_form})
    else:
        return redirect('/company/service/new/?step=1')


def company_help(request):
    return render(request, "company_help.html")


@csrf_exempt
def company_service_set_url(request):
    now_id = request.POST.get('now_id')
    target_url = request.POST.get('target_url')
    token = request.POST.get('url_token')
    models.ServiceInfo.objects.filter(id=now_id).update(target_url=target_url, url_token=token)
    return JsonResponse({'status': True})


def company_service_reset_url(request, service_id):
    service_obj = models.ServiceInfo.objects.filter(id=service_id).first()
    appended_form = forms.ServiceWithInterface(
        {'now_id': service_obj.id, 'target_url': service_obj.target_url, 'url_token': service_obj.url_token})
    return render(request, 'company_service_reset_url.html', {'appended_form': appended_form})


def company_service_edit(request, service_id):
    service_obj = models.ServiceInfo.objects.filter(id=service_id).first()
    form = forms.CompanyEditService(instance=service_obj)
    dictionary = {'form': form}
    if request.method == 'GET':
        return render(request, "company_service_edit.html", dictionary)
    else:
        dictionary['form'] = forms.CompanyEditService(request.POST)
        if dictionary['form'].is_valid():
            models.ServiceInfo.objects.filter(id=service_id).update(**dictionary['form'].cleaned_data)
            return redirect('/company/service/list/')
        return render(request, "company_service_edit.html", dictionary)


def company_service_delete(request, service_id):
    if models.ServiceInfo.objects.filter(id=service_id).first().belong.id == request.session['info']['id']:
        models.ServiceInfo.objects.filter(id=service_id).delete()
    return redirect('/company/service/list/')


def company_service_question_add(request, service_id):
    service_obj = models.ServiceInfo.objects.filter(id=service_id).first()
    return render(request, "company_service_question_add.html", {'service_obj': service_obj})


def company_service_question_delete(request, service_id, question_id):
    models.QuestionAndAnswer.objects.filter(id=question_id, belong__id=service_id).delete()
    return redirect('/company/service/question/list/' + str(service_id) + '/1/')


def service_icon_edit(request, service_id):
    icon_obj = request.FILES['file']
    photo_types = ['.jpg', '.png', '.jpeg']
    flag = False
    for photo_type in photo_types:
        if icon_obj.name.endswith(photo_type):
            flag = True
    if not flag:
        return HttpResponseBadRequest('不支持或错误的图片文件格式，请刷新以重新上传')
    icon_name = str(random.randint(1000000, 9999999)) + '-' + icon_obj.name
    models.ServiceInfo.objects.filter(id=service_id).update(icon=icon_name)
    with open(os.path.join(MEDIA_ROOT, 'logo', icon_name), 'wb') as f:
        for chunk in icon_obj:
            f.write(chunk)
    return redirect('/company/service/list/')


def service_icon_upload(request):
    photo_types = ['.jpg', '.png', '.jpeg']
    finished = request.session['nowCreatingService']
    icon_obj = request.FILES['file']
    flag = False
    for photo_type in photo_types:
        if icon_obj.name.endswith(photo_type):
            flag = True
    if not flag:
        return HttpResponseBadRequest('不支持或错误的图片文件格式，请刷新以重新上传')
    finished['icon'] = str(random.randint(1000000, 9999999)) + '-' + icon_obj.name
    with open(os.path.join(MEDIA_ROOT, 'logo', finished['icon']), 'wb') as f:
        for chunk in icon_obj:
            f.write(chunk)
    request.session['nowCreatingService'] = finished
    return HttpResponse('good')


def question_upload(request, service_id):
    txt_obj = request.FILES['file']
    if not txt_obj.name.endswith('.txt'):
        return HttpResponseBadRequest('不支持或错误的文档格式')
    service_questions_old = models.QuestionAndAnswer.objects.filter(belong__id=service_id).values('question',
                                                                                                  'answer').all()
    service_questions_new = []
    the_lines = txt_obj.readlines()
    for i in range(len(the_lines)):
        if i % 2 == 0 and i != 0:
            service_questions_new.append({'question': question, 'answer': answer})
        temp = the_lines[i].decode().strip()
        if i % 2 == 0:
            if temp.startswith('q:'):
                question = temp[2:]
            else:
                return HttpResponseBadRequest('文档格式错误，行首缺失“q:”')
        else:
            if temp.startswith('a:'):
                answer = temp[2:]
            else:
                return HttpResponseBadRequest('文档格式错误，行首缺失“a:”')
    service_questions_new.append({'question': question, 'answer': answer})
    service_questions_new = list(service_questions_old) + service_questions_new
    service_questions_append = []
    has_seen = set([tuple(i.items()) for i in list(service_questions_old)])
    for i in service_questions_new:
        temp = tuple(i.items())
        if not temp in has_seen:
            has_seen.add(temp)
            service_questions_append.append(i)
    service_obj = models.ServiceInfo.objects.filter(id=service_id).first()
    for qa in service_questions_append:
        qa['id'] = models.QuestionAndAnswer.objects.all().aggregate(Max('id'))['id__max'] + 1
        qa['belong'] = service_obj
        models.QuestionAndAnswer.objects.create(**qa)
    return HttpResponse('good')


def company_service_question_list(request, service_id, page):
    if page <= 0:
        return redirect("/company/service/question/list/" + str(service_id) + "/1/")
    service_obj = models.ServiceInfo.objects.filter(id=service_id).first()
    all_qa = models.QuestionAndAnswer.objects.filter(belong__id=service_id).all()[(page - 1) * 20:(page * 20)]
    count = models.QuestionAndAnswer.objects.filter(belong__id=service_id).all().aggregate(Count('id'))['id__count']
    if page > (count // 20 + 1):
        return redirect("/company/service/question/list/" + str(service_id) + "/" + str(count // 20 + 1) + "/")
    return render(request, 'company_service_question_list.html',
                  {'service_obj': service_obj, 'all_qa': all_qa, 'count': count, 'page': page})


def service_deploy_preview(request, service_id):
    service_obj = models.ServiceInfo.objects.filter(id=service_id).first()
    count_qa = models.QuestionAndAnswer.objects.filter(belong__id=service_id).values('deployed').annotate(
        count=Count('id')).order_by('deployed')
    new_qa = models.QuestionAndAnswer.objects.filter(belong__id=service_id, deployed=False).all()[0:5]
    old_qa = models.QuestionAndAnswer.objects.filter(belong__id=service_id, deployed=True).all()[0:5]
    return render(request, 'company_service_deploy_preview.html',
                  {'service_obj': service_obj, 'count_qa': count_qa, 'new_qa': new_qa, 'old_qa': old_qa})


def service_deploy(request, service_id):
    qa = list(models.QuestionAndAnswer.objects.filter(belong__id=service_id).all().values_list('question', 'belong__id',
                                                                                               'answer'))
    content = process_qapair(qa)
    if str(service_id) in model_dict.keys():
        model_dict[str(service_id)] = SingleHalfModel(name=str(i[0]), content=content)
    else:
        model_dict[str(service_id)].re_deploy(content=content)
    models.QuestionAndAnswer.objects.filter(belong__id=service_id).update(deployed=True)
    return JsonResponse({'status': True})


def company_service_notice_add(request, service_id):
    service_obj = models.ServiceInfo.objects.filter(id=service_id).first()
    form = forms.Notice()
    dictionary = {'form': form}
    if request.method == 'GET':
        return render(request, "company_service_notice_add.html", dictionary)
    else:
        dictionary['form'] = forms.Notice(request.POST)
        if dictionary['form'].is_valid():
            temp = dictionary['form'].cleaned_data
            temp['from_service'] = service_obj
            temp['id'] = models.Notice.objects.all().aggregate(Max('id'))['id__max'] + 1
            temp['create_time'] = datetime.datetime.now().__str__()
            models.Notice.objects.create(**temp)
            return redirect('/company/service/list/')
        return render(request, "company_service_notice_add.html", dictionary)


def company_service_notice_list(request, service_id):
    service_obj = models.ServiceInfo.objects.filter(id=service_id).first()
    all_notice = models.Notice.objects.filter(from_service=service_id).all()
    return render(request, 'company_service_notice_list.html', {'service_obj': service_obj, 'all_notice': all_notice})


def company_service_notice_delete(request, service_id, notice_id):
    models.Notice.objects.filter(id=notice_id).delete()
    return redirect('/company/service/notice/list/' + str(service_id) + '/')


def company_service_notice_edit(request, service_id, notice_id):
    service_obj = models.ServiceInfo.objects.filter(id=service_id).first()
    notice_obj = models.Notice.objects.filter(id=notice_id).first()
    form = forms.Notice(instance=notice_obj)
    dictionary = {'form': form, 'service_obj': service_obj}
    if request.method == 'GET':
        return render(request, "company_service_notice_edit.html", dictionary)
    else:
        dictionary['form'] = forms.Notice(request.POST)
        if dictionary['form'].is_valid():
            models.Notice.objects.filter(id=notice_id).update(text=dictionary['form'].cleaned_data['text'])
            return redirect('/company/service/notice/list/' + str(service_id) + '/')
        return render(request, "company_service_notice_edit.html", dictionary)
