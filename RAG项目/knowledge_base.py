import hashlib
import os
import config_data as config
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from datetime import datetime

from langchain_openai import OpenAIEmbeddings


def check_md5(md5_str:str):
    """检查传入的md5字符串是否已经被处理过"""
    if not os.path.exists(config.md5_path):
        open(config.md5_path, 'w',encoding='utf-8').close()
        return False
    else:
        for line in open(config.md5_path, 'r', encoding='utf-8').readlines():
            line = line.strip()#处理空格和回车
            if md5_str == line:
                return True
        return False





def save_md5(md5_str:str):
    """将传入的MD5字符串记录保存"""
    with open(config.md5_path, 'a', encoding='utf-8') as f:
        f.write(md5_str+'\n')



def get_string_md5(input_str:str,encoding='utf-8'):
    """将字符串转化为MD5字符串"""
    #将字符串转化为字符数组
    str_bytes = input_str.encode(encoding=encoding)

    md5_obj=hashlib.md5()#得到md5提取器
    md5_obj.update(str_bytes)#传入即将要转换的字节数组
    md5_hex=md5_obj.hexdigest()#得到16进制字符串
    return md5_hex


class KnowledgeBaseService(object):
    #如果文件夹不存在就创建，存在就跳过
    os.makedirs(config.persist_directory, exist_ok=True)

    def __init__(self):
        self.chroma = Chroma(
            collection_name=config.collection_name,
            embedding_function=OpenAIEmbeddings(
                model="text-embedding-v4",
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                check_embedding_ctx_length = False
            ),
            persist_directory=config.persist_directory,
        )
        #文本分割器
        self.spliter = RecursiveCharacterTextSplitter(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            separators=config.separators,
            length_function=len,
        )

    def upload_by_str(self,data,file_name):
        md5_hex=get_string_md5(data)

        if check_md5(md5_hex):
            return "内容已存在知识库中"
        if len(data)>config.max_split_char_number:
            knowledge_chunks:list[str]=self.spliter.split_text(data)
        else:
            knowledge_chunks=[data]
        metadata={
            "source":file_name,
            "create_time":datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "operator":"小王"
        }
        self.chroma.add_texts(
            knowledge_chunks,
            metadata=[metadata for _ in knowledge_chunks],
        )
        save_md5(md5_hex)

        return "内容已经成功入库"



if __name__ == '__main__':
    service = KnowledgeBaseService()
    r=service.upload_by_str("周杰伦111222222","testfile")
    print(r)
