# -*- coding: UTF-8 -*-
import time

import paddle
import os
from pipelines.document_stores import FAISSDocumentStore
from pipelines.utils import convert_files_to_dicts, fetch_archive_from_http, print_answers, print_documents
from pipelines.nodes import ErnieReader, ErnieRanker, DensePassageRetriever
from pipelines import SemanticSearchPipeline

from thirdSeason import settings

model_dict = {
    'base': 768,
    'medium': 768,
    'mini': 384,
    'micro': 384,
    'nano': 312
}


class SingleHalfModel:
    def __init__(self, name, content
                 , device='cpu'
                 , index_name='faiss_index'
                 , max_seq_len_query=64
                 , max_seq_len_passage=256
                 , retriever_batch_size=16
                 , model_name=settings.MODEL_NAME):
        self.name = name
        self.use_gpu = True if device == "gpu" else False
        self.index_name = index_name + '_' + self.name
        self.max_seq_len_query = max_seq_len_query
        self.max_seq_len_passage = max_seq_len_passage
        self.retriever_batch_size = retriever_batch_size

        self.faiss_document_store = "faiss_document_store_" + self.name + ".db"

        self.model_name = "rocketqa-zh-" + model_name + "-query-encoder"
        self.model_embedding_dim = model_dict[model_name]

        if os.path.exists(self.index_name) and os.path.exists(self.faiss_document_store):
            # connect to existed FAISS Index
            self.document_store = FAISSDocumentStore.load(self.index_name)
            self.retriever = DensePassageRetriever(
                document_store=self.document_store,
                query_embedding_model=self.model_name,
                passage_embedding_model=self.model_name,
                max_seq_len_query=self.max_seq_len_query,
                max_seq_len_passage=self.max_seq_len_passage,
                batch_size=self.retriever_batch_size,
                use_gpu=self.use_gpu,
                embed_title=False,
            )
        else:
            dicts = content

            if os.path.exists(self.index_name):
                os.remove(self.index_name)
            if os.path.exists(self.faiss_document_store):
                os.remove(self.faiss_document_store)

            self.document_store = FAISSDocumentStore(embedding_dim=self.model_embedding_dim,
                                                     faiss_index_factory_str="Flat",
                                                     sql_url="sqlite:///" + self.faiss_document_store)
            self.document_store.write_documents(dicts)

            self.retriever = DensePassageRetriever(
                document_store=self.document_store,
                query_embedding_model=self.model_name,
                passage_embedding_model=self.model_name,
                max_seq_len_query=self.max_seq_len_query,
                max_seq_len_passage=self.max_seq_len_passage,
                batch_size=self.retriever_batch_size,
                use_gpu=self.use_gpu,
                embed_title=False,
            )

            # update Embedding
            self.document_store.update_embeddings(self.retriever)

            # save index
            self.document_store.save(self.index_name)

    def re_deploy(self, content):
        self.document_store.delete_documents()
        self.document_store.write_documents(content)
        self.document_store.update_embeddings(self.retriever)
        self.document_store.save(self.index_name)


class ManyModel:
    def __init__(self, single_half_model_dict, device='cpu',
                 pipeline_params={"Retriever": {"top_k": 50}, "Ranker": {"top_k": 1}}):
        self.use_gpu = True if device == "gpu" else False
        self.single_half_model_dict = single_half_model_dict
        self.ranker = ErnieRanker(model_name_or_path="rocketqa-zh-dureader-cross-encoder", use_gpu=self.use_gpu)
        self.pipeline_params = pipeline_params

    def use_model(self, model_name, query):
        model_now = self.single_half_model_dict[model_name]
        pipe = SemanticSearchPipeline(model_now.retriever, self.ranker)
        prediction = pipe.run(query=query, params=self.pipeline_params)
        print_documents(prediction, print_name=False, print_meta=True)
        return prediction


if __name__ == '__main__':
    s = time.time()
    SHM01 = SingleHalfModel(name='01', doc_dir=os.path.join('data', '01'))
    SHM02 = SingleHalfModel(name='02', doc_dir=os.path.join('data', '01'))
    ManyModel = ManyModel(single_half_modal_dict={'01': SHM01, '02': SHM02})
    e = time.time()
    print(e - s)
    s = e
    p11 = ManyModel.use_model('01', '如何办理企业养老保险')
    e = time.time()
    print(e - s)
    s = e
    p21 = ManyModel.use_model('02', '承包商要求员工必须自己承担社保全部费用，不然就走人，怎么办')
    e = time.time()
    print(e - s)
