"""
调用对话机器人，进行对话
"""

# encoding:utf-8
import requests

# 以下KEY和ID属于私人，随时可能过期，感兴趣可以自己申请

APPKEY = "oER0lWVPopgRvYncTKHtybtc"
SECRETKEY = "qAQh1U0coefxSmeBlnuH99OhIuvHh8Vz"
SERVICEID = 'S76376'
SKILLID = '1250497'
# client_id 为官网获取的AK， client_secret 为官网获取的SK
host = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=%s&client_secret=%s' \
       % (APPKEY, SECRETKEY)
response = requests.get(host)

access_token = response.json()["access_token"]
url = 'https://aip.baidubce.com/rpc/2.0/unit/service/chat?access_token=' + access_token


def dialog(text, user_id, session_id='', history='', log_id='LOG_FOR_TEST'):
    post_data = "{\"log_id\":\"%s\",\"version\":\"2.0\",\"service_id\":\"%s\",\"session_id\":\"%s\"," \
                "\"request\":{\"query\":\"%s\",\"user_id\":\"%s\"}," \
                "\"dialog_state\":{\"contexts\":{\"SYS_REMEMBERED_SKILLS\":[\"%s\"]}}}"\
                %(log_id, SERVICEID, session_id, text, user_id, SKILLID)
    if len(history) > 0:
        post_data = "{\"log_id\":\"%s\",\"version\":\"2.0\",\"service_id\":\"%s\",\"session_id\":\"\"," \
                "\"request\":{\"query\":\"%s\",\"user_id\":\"%s\"}," \
                "\"dialog_state\":{\"contexts\":{\"SYS_REMEMBERED_SKILLS\":[\"%s\"], " \
                    "\"SYS_CHAT_HIST\":[%s]}}}" \
                %(log_id, SERVICEID, text, user_id, SKILLID, history)
    post_data = post_data.encode('utf-8')
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    response = requests.post(url, data=post_data, headers=headers)
    resp = response.json()
    ans = resp["result"]["response_list"][0]["action_list"][0]['say']
    option_list = [x['option'] for x in resp["result"]["response_list"][0]["action_list"][0]['refine_detail']['option_list']]
    new_ans = ans
    if len(option_list) != 0:
        for option in option_list[0:-1]:
            new_ans = new_ans + '\n' + option
    session_id = resp['result']['session_id']
    return ans, session_id, new_ans
