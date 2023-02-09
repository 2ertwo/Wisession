from flask import Flask, request
from dialog import dialog
from user import User

import json
import sys

app = Flask(__name__)
user_dict = {}
TOKEN = '35AjumlW4bK7XJPFolFeyibf6SnBjSObvgFsWzL1ggJHenKraoMT94mv97Rb'


@app.route('/callback/', methods=['POST'])
def callback():
    post_data = json.loads(request.data.decode('utf-8'))
    app.logger.error(post_data)
    service_id = post_data['service_id']
    token = post_data['token']
    user_id = post_data['user_id']
    text = post_data['text']
    if token != TOKEN:
        return json.dumps({'status': 'error'})
    if not str(user_id) in user_dict.keys():
        user_dict[str(user_id)] = User(user_id)
    user = user_dict[str(user_id)]
    human_ans = text
    user.update_history(human_ans)
    robot_resp, session_id, resp_show = dialog(human_ans, user.user_id, user.session_id, user.history)
    user.session_id = session_id
    user.update_history(robot_resp)
    user_dict[str(user_id)] = user
    return json.dumps({'answer': resp_show})


@app.route('/test/', methods=['GET'])
def test():
    return 'test'
    
if __name__ == '__main__':
    app.run()