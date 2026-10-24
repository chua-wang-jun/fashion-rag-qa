import json
from langchain_core.chat_history import BaseChatMessageHistory
import os
from typing import Sequence

from langchain_core.messages import BaseMessage, message_to_dict, messages_from_dict


def get_history(session_id):
    print(f"正在读取历史记录，session_id: {session_id}")
    return FileChatMessageHistory(session_id,"./chat_history")

class FileChatMessageHistory(BaseChatMessageHistory):
    def __init__(self,session_id,storage_path):
        self.session_id=session_id
        self.storage_path=storage_path#不同会话存储文件，所在的文件路径
        #完整文件路径
        self.file_path=os.path.join(self.storage_path,session_id)
        #确保文件夹存在
        os.makedirs(os.path.dirname(self.file_path),exist_ok=True)

    def add_messages(self,messages: Sequence[BaseMessage]) -> None:
        #Sequence序列类似list，tuple
        all_messages=list(self.messages)#已有的消息列表
        all_messages.extend(messages)#新的和已有的融合成一个list
        new_messages = []
        for message in all_messages:
            d = message_to_dict(message)
            new_messages.append(d)

        #数据写入
        with open(self.file_path,"w",encoding="utf-8") as f:
            json.dump(new_messages,f)

#获得消息
    @property     #@property装饰器将messages方法变成成员属性
    def messages(self) ->list[BaseMessage]:
        try:
            with open(self.file_path,"r",encoding="utf-8") as f:
                messages_data=json.load(f)#读取，返回值是list[字典]
                return messages_from_dict(messages_data)
        except FileNotFoundError:
            return []

    def clear(self)->None:
        with open(self.file_path,"w",encoding="utf-8") as f:
            json.dump([],f)






