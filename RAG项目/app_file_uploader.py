import streamlit as st

from document_loader import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE,
    DocumentParseError,
    extract_document_text,
)
from knowledge_base import KnowledgeBaseService


st.title("知识库更新服务")
st.caption(
    f"支持 TXT、Word（DOCX）和 PDF，单个文件不超过 "
    f"{MAX_FILE_SIZE // (1024 * 1024)} MB。"
)

uploaded_file = st.file_uploader(
    "请上传知识文档",
    type=[suffix.lstrip(".") for suffix in sorted(ALLOWED_EXTENSIONS)],
    accept_multiple_files=False,
)

if "service" not in st.session_state:
    st.session_state["service"] = KnowledgeBaseService()

if uploaded_file is not None:
    file_size_mb = uploaded_file.size / 1024 / 1024
    st.subheader(f"文件：{uploaded_file.name}")
    st.caption(f"格式：{uploaded_file.type or '未知'}｜大小：{file_size_mb:.2f} MB")

    if st.button("开始解析并入库", type="primary"):
        try:
            with st.spinner("正在解析文档并写入向量库..."):
                text = extract_document_text(
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                )
                result = st.session_state["service"].upload_by_str(
                    text,
                    uploaded_file.name,
                )
            st.success(result)
            st.caption(f"提取文本：{len(text)} 个字符")
        except DocumentParseError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"知识库写入失败：{exc}")
