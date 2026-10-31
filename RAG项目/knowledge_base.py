import hashlib
import os
from collections import Counter
from datetime import datetime

import config_data as config
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


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
                model=config.embedding_model_name,
                base_url=config.base_url,
                check_embedding_ctx_length=False,
                chunk_size=config.embedding_batch_size,
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

    def upload_by_str(self, data, file_name):
        if not data.strip():
            return "文档内容为空，未写入知识库"

        md5_hex = get_string_md5(data)
        if check_md5(md5_hex):
            return "【加入失败】内容已存在知识库中"

        if len(data) > config.max_split_char_number:
            chunks = self.spliter.split_text(data)
        else:
            chunks = [data]

        knowledge_chunks = [chunk.strip() for chunk in chunks if chunk.strip()]
        if not knowledge_chunks:
            return "文档中没有可入库的文字内容"

        metadata = {
            "source": file_name,
            "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "operator": "小王",
        }

        batch_size = max(1, int(config.embedding_batch_size))
        for start in range(0, len(knowledge_chunks), batch_size):
            batch = knowledge_chunks[start:start + batch_size]
            end = start + len(batch)
            ids = [f"{md5_hex}-{index:05d}" for index in range(start, end)]
            self.chroma.add_texts(
                texts=batch,
                metadatas=[metadata.copy() for _ in batch],
                ids=ids,
            )

        save_md5(md5_hex)
        return f"内容已经成功入库，共 {len(knowledge_chunks)} 个文本片段"

    def get_library_stats(self):
        """汇总当前向量库的文档数、片段数和最近入库时间。"""
        result = self.chroma.get(include=["metadatas"])
        ids = result.get("ids") or []
        metadatas = result.get("metadatas") or []

        source_counts = Counter()
        source_times = {}
        for metadata in metadatas:
            metadata = metadata or {}
            source = metadata.get("source") or "未命名文档"
            source_counts[source] += 1
            create_time = metadata.get("create_time") or ""
            if create_time > source_times.get(source, ""):
                source_times[source] = create_time

        documents = [
            {
                "source": source,
                "chunks": chunk_count,
                "last_update": source_times.get(source, "—"),
            }
            for source, chunk_count in source_counts.items()
        ]
        documents.sort(key=lambda item: item["last_update"], reverse=True)
        last_update = max(source_times.values(), default="—")

        return {
            "chunk_count": len(ids),
            "document_count": len(source_counts),
            "last_update": last_update or "—",
            "documents": documents,
        }



if __name__ == '__main__':
    service = KnowledgeBaseService()
    r=service.upload_by_str("周杰伦111222222","testfile")
    print(r)
