import os
from datetime import datetime
from pathlib import Path

import streamlit as st

import config_data as config
from document_loader import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE,
    DocumentParseError,
    extract_document_text,
)
from knowledge_base import KnowledgeBaseService


MAX_BATCH_FILES = 10
DATA_DIR = Path(__file__).resolve().parent / "data"

st.set_page_config(
    page_title="服饰知识库管理中心",
    page_icon="👗",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at 88% 2%, rgba(235, 204, 199, 0.36), transparent 24rem),
            linear-gradient(180deg, #faf8f5 0%, #ffffff 36rem);
    }
    .block-container { max-width: 1180px; padding-top: 2.2rem; padding-bottom: 3rem; }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #17212f 0%, #243247 100%);
    }
    [data-testid="stSidebar"] * { color: #f7f4ef; }
    [data-testid="stSidebar"] code {
        color: #f7f4ef !important;
        background: rgba(255,255,255,.10) !important;
        padding: .12rem .35rem;
        border-radius: 6px;
    }
    .kb-hero {
        color: #fff;
        padding: 2.2rem 2.4rem;
        border-radius: 26px;
        background:
            radial-gradient(circle at 88% 20%, rgba(234, 194, 176, 0.34), transparent 17rem),
            linear-gradient(125deg, #172131 0%, #26374e 58%, #553f3b 120%);
        box-shadow: 0 18px 45px rgba(27, 36, 50, 0.16);
        margin-bottom: 1.15rem;
    }
    .kb-eyebrow {
        display: inline-block;
        padding: .34rem .72rem;
        border: 1px solid rgba(255,255,255,.24);
        border-radius: 999px;
        color: #f1ddd2;
        font-size: .78rem;
        letter-spacing: .08em;
    }
    .kb-hero h1 { margin: .72rem 0 .45rem; font-size: 2.28rem; line-height: 1.25; }
    .kb-hero p { max-width: 760px; margin: 0; color: #dce4ee; line-height: 1.78; }
    .kb-pills { margin-top: 1.1rem; display: flex; flex-wrap: wrap; gap: .55rem; }
    .kb-pill {
        padding: .35rem .72rem;
        border-radius: 999px;
        background: rgba(255,255,255,.10);
        color: #fff;
        font-size: .82rem;
    }
    .flow-step {
        min-height: 112px;
        padding: 1rem 1.05rem;
        border: 1px solid #e9e4dd;
        border-radius: 18px;
        background: rgba(255,255,255,.88);
        box-shadow: 0 8px 20px rgba(36, 42, 52, .045);
    }
    .flow-step .num {
        display: inline-flex;
        width: 1.72rem;
        height: 1.72rem;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        background: #172131;
        color: #fff;
        font-size: .76rem;
        font-weight: 700;
    }
    .flow-step h4 { margin: .62rem 0 .24rem; color: #1d2735; font-size: 1rem; }
    .flow-step p { margin: 0; color: #697384; font-size: .84rem; line-height: 1.55; }
    [data-testid="stMetric"] {
        padding: 1rem 1.05rem;
        border: 1px solid #e9e4dd;
        border-radius: 18px;
        background: rgba(255,255,255,.92);
        box-shadow: 0 7px 18px rgba(36, 42, 52, .04);
    }
    [data-testid="stExpander"], [data-testid="stFileUploaderDropzone"] {
        border-color: #e3ddd5 !important;
        border-radius: 16px !important;
    }
    .stTabs [data-baseweb="tab-list"] { gap: .4rem; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 12px 12px 0 0;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False, ttl=1800, max_entries=30)
def parse_uploaded_file(file_name: str, file_bytes: bytes) -> dict:
    """缓存解析结果，避免页面重跑时反复读取大文件。"""
    try:
        return {
            "text": extract_document_text(file_name, file_bytes),
            "error": None,
        }
    except DocumentParseError as exc:
        return {"text": "", "error": str(exc)}
    except Exception as exc:
        return {"text": "", "error": f"解析失败：{exc}"}


def get_service() -> KnowledgeBaseService:
    if "service" not in st.session_state:
        st.session_state["service"] = KnowledgeBaseService()
    return st.session_state["service"]


def get_data_dir_size() -> int:
    return sum(path.stat().st_size for path in DATA_DIR.glob("**/*") if path.is_file())


def format_size(size_bytes: float) -> str:
    if size_bytes < 1024:
        return f"{size_bytes:.0f} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / 1024 / 1024:.2f} MB"


def refresh_library_stats() -> dict:
    stats = get_service().get_library_stats()
    stats["storage_bytes"] = get_data_dir_size()
    stats["storage_size"] = format_size(stats["storage_bytes"])
    st.session_state["library_stats"] = stats
    return stats


def show_results(results: list[dict]) -> None:
    if not results:
        return
    st.subheader("本次处理结果")
    for item in results:
        if item["ok"]:
            st.success(f"{item['file']}：{item['message']}")
        else:
            st.error(f"{item['file']}：{item['message']}")


SAMPLE_DOC_INFO = {
    "尺码推荐.txt": ("📏", "尺码", "身高体重、围度测量与不同体型的选码建议"),
    "洗涤养护.txt": ("🧺", "养护", "常见面料洗护、去渍与收纳方法"),
    "颜色选择.txt": ("🎨", "配色", "肤色配色、场景用色与穿搭色彩法则"),
    "商品选购指南.txt": ("🛍️", "选购", "服装品类、版型、预算与购买决策清单"),
    "面料材质指南.txt": ("🧵", "面料", "棉麻、羊毛、真丝和化纤的优缺点与适用场景"),
    "版型与身材穿搭.txt": ("📐", "版型", "身材特征、廓形选择与松量建议"),
    "场景穿搭建议.txt": ("🧥", "场景", "通勤、约会、旅行、运动和正式场合穿搭"),
    "售后与退换指南.txt": ("↩️", "售后", "退换货检查、尺码换货与售后沟通说明"),
    "常见商品FAQ.txt": ("💬", "问答", "色差、库存、物流、发票和商品瑕疵等高频问题"),
}

api_key_ready = bool(os.getenv("OPENAI_API_KEY"))
sample_files = sorted(DATA_DIR.glob("*.txt"))


st.markdown(
    """
    <section class="kb-hero">
        <span class="kb-eyebrow">FASHION RAG · KNOWLEDGE OPS</span>
        <h1>服饰知识库管理中心</h1>
        <p>把尺码、面料、穿搭与售后资料整理成可检索的智能知识库。上传后自动完成文本提取、内容切分与向量化，为服装客服问答提供可追溯的参考依据。</p>
        <div class="kb-pills">
            <span class="kb-pill">TXT / DOCX / PDF</span>
            <span class="kb-pill">批量入库</span>
            <span class="kb-pill">内容去重</span>
            <span class="kb-pill">Chroma 持久化</span>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)

flow_cols = st.columns(4)
for column, number, title, description in zip(
    flow_cols,
    ("01", "02", "03", "04"),
    ("上传资料", "解析内容", "智能切分", "写入知识库"),
    (
        "选择一份或多份服饰文档",
        "读取正文、表格和可复制文字",
        "按段落与语义边界组织片段",
        "生成向量并持久化到本地",
    ),
):
    with column:
        st.markdown(
            f"""
            <div class="flow-step">
                <span class="num">{number}</span>
                <h4>{title}</h4>
                <p>{description}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.write("")

metric_cols = st.columns(4)
with metric_cols[0]:
    st.metric("支持格式", "3 种")
    st.caption("TXT · DOCX · PDF")
with metric_cols[1]:
    st.metric("批量上限", f"{MAX_BATCH_FILES} 份/次")
    st.caption("单份不超过 10 MB")
with metric_cols[2]:
    st.metric("示例资料", f"{len(sample_files)} 份")
    st.caption("覆盖服饰客服核心主题")
with metric_cols[3]:
    st.metric("服务状态", "已就绪" if api_key_ready else "待配置")
    st.caption("OPENAI_API_KEY")

if not api_key_ready:
    st.warning(
        "当前终端未检测到 OPENAI_API_KEY。你仍可上传并预览文档，"
        "但执行向量化入库前需要先配置 DashScope 兼容 API Key。"
    )

with st.sidebar:
    st.markdown("## 👗 知识运营台")
    st.caption("面向服装商品智能问答的知识资料管理入口")
    st.divider()
    st.markdown("**运行状态**")
    st.write("API Key：" + ("✅ 已配置" if api_key_ready else "⚠️ 未配置"))
    st.write("向量库：" + f"`{config.collection_name}`")
    st.write("数据目录：" + f"{len(sample_files)} 份示例资料")
    st.divider()
    st.markdown("**入库规范**")
    st.markdown(
        f"""
        - 单文件 ≤ {MAX_FILE_SIZE // (1024 * 1024)} MB
        - 单次最多 {MAX_BATCH_FILES} 份
        - 相同正文自动跳过
        - 扫描版 PDF 需先 OCR
        """
    )
    st.divider()
    st.markdown("**资料建议**")
    st.caption("优先使用来源明确、时效清晰、按主题拆分的文档。商品政策应注明适用店铺与有效日期。")


upload_tab, overview_tab, samples_tab, guide_tab = st.tabs(
    ["📤 上传入库", "📚 知识库概览", "🗂️ 示例资料", "📖 使用指南"]
)

with upload_tab:
    st.header("上传服饰知识文档")
    st.caption("支持一次上传多份文件；系统会先展示提取预览，再由你确认是否写入知识库。")

    uploaded_files = st.file_uploader(
        "拖放或选择知识文档",
        type=[suffix.lstrip(".") for suffix in sorted(ALLOWED_EXTENSIONS)],
        accept_multiple_files=True,
        help=f"单份不超过 {MAX_FILE_SIZE // (1024 * 1024)} MB，单次最多 {MAX_BATCH_FILES} 份。",
    )

    template_text = """【文档主题】
【适用商品】如：女装上衣、牛仔裤、羊毛大衣
【更新时间】YYYY-MM-DD
【来源/适用范围】

一、核心规则
1. 用清晰、可执行的短句描述规则。
2. 尺码与政策数据必须注明适用范围。

二、常见问题
Q：用户可能如何提问？
A：给出明确答案、例外情况与引导动作。

三、注意事项
- 不要写入无法核验的绝对化承诺。
- 商品参数以商品详情页和商家最终确认为准。
"""
    st.download_button(
        "下载知识文档模板",
        data=template_text,
        file_name="服饰知识文档模板.txt",
        mime="text/plain",
        help="按模板整理资料，可提高检索和回答质量。",
    )

    if not uploaded_files:
        st.info("尚未选择文件。可以先从“示例资料”页导入内置文档，快速搭建演示知识库。")
    else:
        if len(uploaded_files) > MAX_BATCH_FILES:
            st.warning(f"本次只处理前 {MAX_BATCH_FILES} 份文件，其余文件请分批上传。")
            uploaded_files = uploaded_files[:MAX_BATCH_FILES]

        parsed_files = []
        st.subheader("文件预览")
        for index, uploaded_file in enumerate(uploaded_files, start=1):
            file_bytes = uploaded_file.getvalue()
            parsed = parse_uploaded_file(uploaded_file.name, file_bytes)
            parsed_files.append(
                {
                    "file": uploaded_file,
                    "text": parsed["text"],
                    "error": parsed["error"],
                }
            )

            with st.container(border=True):
                title_col, format_col, size_col, status_col = st.columns([4, 1.2, 1.2, 1.2])
                with title_col:
                    st.markdown(f"#### {index:02d} · {uploaded_file.name}")
                with format_col:
                    st.caption("格式")
                    st.write(f"**{Path(uploaded_file.name).suffix.upper().lstrip('.')}**")
                with size_col:
                    st.caption("大小")
                    st.write(f"**{format_size(len(file_bytes))}**")
                with status_col:
                    st.caption("状态")
                    st.write("**可入库**" if not parsed["error"] else "**需检查**")

                if parsed["error"]:
                    st.error(parsed["error"])
                else:
                    st.caption(
                        f"已提取 {len(parsed['text']):,} 个字符，"
                        "以下为内容预览，最终将按配置自动切分。"
                    )
                    with st.expander("查看提取内容"):
                        preview = parsed["text"][:3000]
                        if len(parsed["text"]) > 3000:
                            preview += "\n\n……（仅展示前 3000 个字符）"
                        st.text_area(
                            "文档内容预览",
                            value=preview,
                            height=220,
                            disabled=True,
                            label_visibility="collapsed",
                            key=f"preview_{index}",
                        )

        valid_files = [item for item in parsed_files if item["text"] and not item["error"]]
        st.write("")
        ready_col, note_col = st.columns([1, 3])
        with ready_col:
            ingest_clicked = st.button(
                "开始批量入库",
                type="primary",
                width="stretch",
                disabled=not api_key_ready or not valid_files,
            )
        with note_col:
            st.caption(
                f"{len(valid_files)} 份文件可入库，{len(parsed_files) - len(valid_files)} 份需处理。"
                "已入库过的相同正文会自动跳过。"
            )

        if ingest_clicked:
            results = []
            try:
                service = get_service()
                progress = st.progress(0, text="正在连接向量库...")
                for index, item in enumerate(valid_files, start=1):
                    file_name = item["file"].name
                    progress.progress(
                        (index - 1) / len(valid_files),
                        text=f"正在处理：{file_name}",
                    )
                    try:
                        message = service.upload_by_str(item["text"], file_name)
                        results.append({"file": file_name, "ok": True, "message": message})
                    except Exception as exc:
                        results.append(
                            {"file": file_name, "ok": False, "message": f"写入失败：{exc}"}
                        )
                progress.progress(1.0, text="处理完成")
                refresh_library_stats()
            except Exception as exc:
                st.error(f"知识库服务初始化失败：{exc}")
            else:
                st.session_state["upload_results"] = results

        show_results(st.session_state.get("upload_results", []))

with overview_tab:
    st.header("知识库概览")
    st.caption("查看当前 Chroma 集合中的文档数、文本片段数、最近入库时间和资料清单。")

    if not api_key_ready:
        st.warning("知识库统计需要初始化嵌入模型，请先配置 OPENAI_API_KEY。")

    if st.button(
        "刷新知识库统计",
        type="primary",
        disabled=not api_key_ready,
        key="refresh_stats",
    ):
        try:
            with st.spinner("正在读取知识库..."):
                refresh_library_stats()
            st.toast("知识库统计已更新")
        except Exception as exc:
            st.error(f"读取知识库失败：{exc}")

    stats = st.session_state.get("library_stats")
    if stats:
        try:
            last_ingested = datetime.strptime(
                stats["last_update"], "%Y-%m-%d %H:%M:%S"
            )
            last_date = f"{last_ingested.month}月{last_ingested.day}日"
            last_caption = f"{last_ingested.year}年 · {last_ingested:%H:%M}"
        except (TypeError, ValueError):
            last_date = "—"
            last_caption = "无更新时间"
        stat_cols = st.columns(4)
        stat_cols[0].metric("知识文档", f"{stats['document_count']} 份")
        stat_cols[1].metric("文本片段", f"{stats['chunk_count']:,} 个")
        stat_cols[2].metric("本地存储", stats.get("storage_size", "—"))
        stat_cols[3].metric("最近入库", last_date)
        stat_cols[3].caption(last_caption)

        st.subheader("已入库资料")
        if stats["documents"]:
            st.dataframe(
                stats["documents"],
                column_config={
                    "source": "文档名称",
                    "chunks": st.column_config.NumberColumn("片段数", format="%d"),
                    "last_update": "最近入库时间",
                },
                hide_index=True,
                width="stretch",
            )
        else:
            st.info("知识库目前为空，请上传文档或导入示例资料。")
    else:
        st.info("当前页面尚未加载统计。点击“刷新知识库统计”查看实时数据。")

with samples_tab:
    st.header("内置服饰示例资料")
    st.caption(
        "以下内容仅用于演示 RAG 客服能力。具体商品参数、价格、库存和售后政策，"
        "应以商品详情页及商家最终确认为准。"
    )

    if sample_files:
        sample_cols = st.columns(2)
        for index, sample_path in enumerate(sample_files):
            icon, category, description = SAMPLE_DOC_INFO.get(
                sample_path.name,
                ("📄", "资料", "服饰知识文档"),
            )
            sample_text = sample_path.read_text(encoding="utf-8")
            with sample_cols[index % 2]:
                with st.container(border=True):
                    st.subheader(f"{icon} {sample_path.stem}")
                    st.caption(f"{category} · {description}")
                    st.write(f"{len(sample_text):,} 个字符")
                    with st.expander("查看内容摘要"):
                        st.text(sample_text[:1600])
    else:
        st.warning("data 目录下暂无可导入的 TXT 示例资料。")

    st.write("")
    import_clicked = st.button(
        "导入全部示例资料",
        type="primary",
        disabled=not api_key_ready or not sample_files,
    )
    st.caption("相同内容已入库时会自动跳过，重复点击不会产生重复向量。")

    if import_clicked:
        results = []
        try:
            service = get_service()
            progress = st.progress(0, text="正在导入示例资料...")
            for index, sample_path in enumerate(sample_files, start=1):
                progress.progress(
                    (index - 1) / len(sample_files),
                    text=f"正在处理：{sample_path.name}",
                )
                try:
                    text = sample_path.read_text(encoding="utf-8")
                    message = service.upload_by_str(text, f"data/{sample_path.name}")
                    results.append(
                        {"file": sample_path.name, "ok": True, "message": message}
                    )
                except Exception as exc:
                    results.append(
                        {
                            "file": sample_path.name,
                            "ok": False,
                            "message": f"写入失败：{exc}",
                        }
                    )
            progress.progress(1.0, text="导入完成")
            refresh_library_stats()
        except Exception as exc:
            st.error(f"知识库服务初始化失败：{exc}")
        else:
            st.session_state["sample_results"] = results
            st.toast("示例资料处理完成")

    show_results(st.session_state.get("sample_results", []))

with guide_tab:
    st.header("知识文档编写与运营指南")
    left, right = st.columns([1.4, 1], gap="large")

    with left:
        st.subheader("推荐的内容结构")
        st.markdown(
            """
            1. **主题单一**：一份文档聚焦一个主题，例如只写尺码或只写洗涤。
            2. **标题明确**：使用“商品品类 + 问题”命名，便于识别与更新。
            3. **规则可执行**：优先写数字、条件、例外和处理动作。
            4. **来源可核验**：保留更新时间、适用商品范围和店铺政策版本。
            5. **问答成对**：高频问题可采用 Q/A 结构，检索命中更稳定。
            """
        )
        st.subheader("适合放入客服知识库的资料")
        st.markdown(
            """
            - 商品尺码表、测量方式和选码建议
            - 面料成分、触感、弹性和适用季节
            - 洗护标签、去渍与收纳说明
            - 退换货、换码、补件和质检流程
            - 库存、色差、物流、发票等 FAQ
            """
        )

    with right:
        st.subheader("入库前检查")
        st.checkbox("文档中的尺码、价格和政策已核对", key="check_fact")
        st.checkbox("已注明适用商品与更新时间", key="check_scope")
        st.checkbox("扫描版 PDF 已完成 OCR", key="check_ocr")
        st.checkbox("文件不包含真实密钥或个人敏感信息", key="check_secret")
        st.info(
            "知识库不是商品数据库。商品级别的实时库存和价格，"
            "仍应接业务 API 查询，避免仅靠文档生成结果。"
        )

    st.divider()
    with st.expander("为什么相同内容上传后没有新增片段？"):
        st.write(
            "系统会对提取后的完整正文计算 MD5。只要正文完全一致，就会跳过本次入库；"
            "修改正文后再次上传，才会生成新的记录。"
        )
    with st.expander("Word 或 PDF 中的图片能识别吗？"):
        st.write(
            "当前仅提取 Word 正文、Word 表格和 PDF 中可复制的文字。"
            "图片中的尺码表需要先转为文字，扫描版 PDF 需要先做 OCR。"
        )
    with st.expander("如何更新已经过期的知识？"):
        st.write(
            "当前版本采用内容去重入库，没有提供单文档删除按钮。"
            "更新制度前建议先备份 chroma_db，再通过知识库维护脚本或重建集合清理旧内容，"
            "最后上传最新版本。"
        )

st.divider()
st.caption(
    f"服饰智能客服 · 知识库管理中心 | 当前集合：{config.collection_name} | "
    f"单文件上限：{MAX_FILE_SIZE // (1024 * 1024)} MB"
)
