import json
import random
import string
import requests

from app01.utils.send_mail import MS_obj

service_infoed = []


def get_60_random_text():
    result = ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=60))
    return result


def send_request(service_obj, user_id, query):
    data = {
        'service_id': service_obj.id,
        'token': service_obj.url_token,
        'user_id': user_id,
        'text': query
    }
    try:
        res = requests.post(url=service_obj.target_url, data=json.dumps(data), headers={"Content-Type": "application/json"})
        return json.loads(res.text)['answer']
    except:
        if not service_obj.id in service_infoed:
            service_infoed.append(service_obj.id)
            MS_obj.send_txt([service_obj.belong.email], '您的服务ID:' + str(service_obj.id) + '未响应，请立即调试', subject='服务紧急通知',
                            to='服务提供者')
        return '未响应，已发送邮件到该服务所有者'
