from langchain_core.documents import Document
from langchain_core.runnables import RunnablePassthrough, RunnableLambda, RunnableWithMessageHistory
from langchain_core.output_parsers import StrOutputParser
# 删除了错误的 from openai.types.live import session_config

from vector_stores import VectorStoresService
from langchain_openai import OpenAIEmbeddings
import config_data as config
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from file_history_store import get_history


class RagService(object):
    def __init__(self):

        self.vector_service = VectorStoresService(
            OpenAIEmbeddings(
                model=config.embedding_model_name,
                base_url=config.base_url,
                check_embedding_ctx_length=False
            )
        )
        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", "以我的参考资料为主，简洁和专业的回答用户问题。参考资料{context}，"
                           "如果参考资料中没有提到，请回答不知道"),
                ("system", "并且我提供用户历史会话如下"),
                MessagesPlaceholder("history"),
                ("user", "请回答用户提问{query}")  # 这里改成了 query 避免和系统的 input 冲突
            ]
        )
        self.chat_model = ChatOpenAI(
            model_name=config.chat_model_name,
            openai_api_base=config.base_url
        )
        self.chain = self.get_chain()

    def get_chain(self):

        def print_prompt(prompt):
            print("=" * 20)
            print(prompt.to_string())
            print("=" * 20)
            return prompt

        retriever = self.vector_service.get_retriever()

        def format_document(docs: list[Document]):
            if not docs:
                return "没有相关参考资料"
            formatted_str = ""
            for doc in docs:
                formatted_str += f"文档片段：{doc.page_content}\n文档元数据：{doc.metadata}\n\n"
            return formatted_str

        # 终极防呆提取函数



        chain = (
            # 1. assign 会自动保留原有的 input 和 history，并新增 context 和 query
                RunnablePassthrough.assign(
                    # 这里的 lambda 直接提取 "input" 键的值
                    context=(
                            RunnableLambda(lambda x: x["input"])
                            | retriever
                            | RunnableLambda(format_document)
                    ),
                    # 顺便把提取出来的纯文本赋值给 query，给 Prompt 用
                    query=RunnableLambda(lambda x: x["input"])
                )
                | self.prompt_template
                | RunnableLambda(print_prompt)
                | self.chat_model
                | StrOutputParser()
        )

        conversation_chain = RunnableWithMessageHistory(
            chain,
            get_history,
            input_messages_key="input",
            history_messages_key="history",
        )

        return conversation_chain


if __name__ == "__main__":
    session_config = {
        "configurable": {
            "session_id": "user_001"  # 这里必须是 session_id
        }
    }
    rsg=RagService()

    res =rsg.chain.invoke({"input": "根据历史记录我体重多少斤"}, config=session_config)
    print(res)
