
from langchain_chroma import Chroma
import config_data as config


class VectorStoresService(object):
    def __init__(self,embedding):
        self.embedding = embedding
        self.vector_store=Chroma(
            collection_name=config.collection_name,
            embedding_function=self.embedding,
            persist_directory=config.persist_directory,

        )
    def get_retriever(self):
        #返回向量检索器，方便加入chain
        return self.vector_store.as_retriever(search_kwargs={"k":config.similarity_threshold})


if __name__=="__main__":
    from langchain_openai import OpenAIEmbeddings
    retrieve=VectorStoresService(OpenAIEmbeddings(
        model="text-embedding-v4",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        check_embedding_ctx_length=False
    )).get_retriever()
    res=retrieve.invoke("我180斤应该穿多大衣服")
    print(res)