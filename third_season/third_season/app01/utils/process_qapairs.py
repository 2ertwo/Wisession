import app01.models as models


def process_qapair(query):
    temp = list(query)
    dict_list = []
    for i in temp:
        temp = {'content': i[0], 'meta': {'name': str(i[1]),
                                          'answer': i[2]}}
        dict_list.append(temp)
    return dict_list


