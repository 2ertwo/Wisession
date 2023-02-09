class SingleHalfModel:
    def __init__(self, name, content):
        self.len = len(content)
        self.name = name
        self.default_answer = '这是' + name + '的测试答案，content中有' + str(self.len) + '个，'

    def re_deploy(self, content):
        self.len = len(content)
        self.default_answer = '这是' + self.name + '的测试答案，content中有' + str(self.len) + '个，'


class ManyModel:
    def __init__(self, single_half_modal_dict):
        self.single_half_model_dict = single_half_modal_dict

    def use_model(self, model_name, query):
        model_now = self.single_half_model_dict[model_name]
        return model_now.default_answer + '你刚刚的问题是：' + query
