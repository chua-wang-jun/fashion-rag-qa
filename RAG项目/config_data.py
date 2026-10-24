md5_path="./md5.text"


#Chroma
collection_name="rag"
persist_directory="./chroma_db"


#spliter
chunk_size=150
chunk_overlap=20
separators=["\n\n","\n",",",".","，","。","!","?","",]
max_split_char_number=500   #文本分割的阈值

#
similarity_threshold=1

embedding_model_name="text-embedding-v4"
embedding_batch_size=10  # DashScope 文本嵌入单次最多 10 条
base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
chat_model_name="glm-5.3"

session_config = {
        "configurable": {
            "session_id": "user_001"  # 这里必须是 session_id
        }
    }
