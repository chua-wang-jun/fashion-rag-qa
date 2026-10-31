import os
import re
import uuid

import streamlit as st

from file_history_store import get_history
from rag import RagService


WELCOME_MESSAGE = (
    "你好，我是你的 AI 服饰顾问。我可以帮你选尺码、判断版型、搭配颜色，"
    "也可以解答面料洗护、商品选购和售后问题。为了让建议更准确，请尽量告诉我"
    "商品款式、身高体重或常穿尺码，以及使用场景。"
)

CAPABILITIES = [
    ("📏", "尺码与版型", "结合身高、体重、围度与松量偏好给出选码建议"),
    ("🎨", "色彩与搭配", "根据肤色、场景和风格偏好组合穿搭"),
    ("🧵", "面料与洗护", "解释材质特性、穿着体验和日常护理方式"),
    ("↩️", "选购与售后", "梳理商品检查、尺码换货和售后处理思路"),
]

QUICK_PROMPTS = [
    ("📏 帮我选尺码", "我身高 175cm、体重 80kg，想买一件偏宽松的男装夹克，应该选什么尺码？"),
    ("🎨 找到适合的颜色", "我的肤色偏黄，想买通勤衬衫，什么颜色更显精神？"),
    ("🧵 了解面料", "纯棉、羊毛和聚酯纤维分别适合什么季节，日常怎么洗护？"),
    ("🧥 按身材选版型", "我肩比较宽、胯比较窄，想穿得利落一些，适合什么版型的上衣和裤子？"),
]

SESSION_ID_PATTERN = re.compile(r"^user_[0-9a-f]{12}$")


st.set_page_config(
    page_title="AI 服饰顾问",
    page_icon="👗",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at 90% 2%, rgba(228, 191, 180, 0.35), transparent 25rem),
            linear-gradient(180deg, #faf8f5 0%, #ffffff 36rem);
    }
    .block-container { max-width: 1080px; padding-top: 2rem; padding-bottom: 6rem; }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #17212f 0%, #28374c 100%);
    }
    [data-testid="stSidebar"] * { color: #f7f4ef; }
    .qa-hero {
        color: #fff;
        padding: 2rem 2.25rem;
        border-radius: 26px;
        background:
            radial-gradient(circle at 88% 18%, rgba(234, 194, 176, 0.34), transparent 17rem),
            linear-gradient(125deg, #172131 0%, #26374e 58%, #553f3b 120%);
        box-shadow: 0 18px 45px rgba(27, 36, 50, 0.16);
        margin-bottom: 1.2rem;
    }
    .qa-kicker {
        display: inline-block;
        padding: .34rem .72rem;
        border: 1px solid rgba(255,255,255,.24);
        border-radius: 999px;
        color: #f1ddd2;
        font-size: .76rem;
        letter-spacing: .08em;
    }
    .qa-hero h1 { margin: .68rem 0 .42rem; font-size: 2.25rem; line-height: 1.25; }
    .qa-hero p { max-width: 750px; margin: 0; color: #dce4ee; line-height: 1.78; }
    .qa-pills { margin-top: 1rem; display: flex; flex-wrap: wrap; gap: .55rem; }
    .qa-pill {
        padding: .34rem .7rem;
        border-radius: 999px;
        background: rgba(255,255,255,.10);
        color: #fff;
        font-size: .8rem;
    }
    .qa-cap {
        min-height: 126px;
        padding: 1rem 1.05rem;
        border: 1px solid #e9e4dd;
        border-radius: 18px;
        background: rgba(255,255,255,.9);
        box-shadow: 0 8px 20px rgba(36, 42, 52, .045);
    }
    .qa-cap .icon { font-size: 1.35rem; }
    .qa-cap h4 { margin: .55rem 0 .3rem; color: #1d2735; font-size: 1rem; }
    .qa-cap p { margin: 0; color: #697384; font-size: .84rem; line-height: 1.6; }
    [data-testid="stChatMessage"] {
        border: 1px solid #ece7e0;
        border-radius: 18px;
        padding: .55rem .8rem;
        background: rgba(255,255,255,.94);
        box-shadow: 0 6px 16px rgba(36, 42, 52, .035);
    }
    [data-testid="stChatInput"] textarea { font-size: .96rem; }
    .qa-section-title { margin: 1.25rem 0 .15rem; color: #1d2735; font-size: 1rem; font-weight: 700; }
    .qa-section-note { margin-bottom: .8rem; color: #788191; font-size: .85rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


def create_session_id() -> str:
    return f"user_{uuid.uuid4().hex[:12]}"


def load_session_messages(session_id: str) -> list[dict]:
    """从本地会话文件恢复页面消息，忽略无法映射的系统消息。"""
    messages = [{"role": "assistant", "content": WELCOME_MESSAGE}]
    for message in get_history(session_id).messages:
        if message.type in {"human", "user"}:
            role = "user"
        elif message.type in {"ai", "assistant"}:
            role = "assistant"
        else:
            continue
        if isinstance(message.content, str) and message.content.strip():
            messages.append({"role": role, "content": message.content})
    return messages


def initialize_session() -> None:
    session_id = st.session_state.get("chat_session_id")
    requested_id = st.query_params.get("session_id")

    if not session_id and isinstance(requested_id, str):
        if SESSION_ID_PATTERN.fullmatch(requested_id):
            session_id = requested_id
    if not session_id:
        session_id = create_session_id()

    st.session_state["chat_session_id"] = session_id
    st.query_params["session_id"] = session_id
    if "qa_messages" not in st.session_state:
        st.session_state["qa_messages"] = load_session_messages(session_id)
    st.session_state.pop("pending_prompt", None)


if (
    "qa_messages" not in st.session_state
    or "chat_session_id" not in st.session_state
):
    initialize_session()
else:
    st.query_params["session_id"] = st.session_state["chat_session_id"]

api_key_ready = bool(os.getenv("OPENAI_API_KEY"))

with st.sidebar:
    st.markdown("## 👗 AI 服饰顾问")
    st.caption("懂尺码、懂搭配，也懂面料与养护")
    st.divider()
    st.markdown("**服务状态**")
    st.write("AI 服务：" + ("✅ 已就绪" if api_key_ready else "⚠️ 未配置"))
    st.caption("会话记录保存在本机，不会在页面展示密钥。")

    st.divider()
    st.markdown("**提问越具体，建议越准确**")
    st.markdown(
        """
        - 商品：品类、版型、面料
        - 身体：身高、体重、围度
        - 场景：通勤、约会、旅行
        - 偏好：合身、宽松、显高
        """
    )
    st.divider()
    st.caption("实时库存、价格、物流和最终售后政策，以商品页和商家确认为准。")


st.markdown(
    """
    <section class="qa-hero">
        <span class="qa-kicker">FASHION INTELLIGENCE · AI STYLIST</span>
        <h1>找到适合你的那一件</h1>
        <p>从尺码判断到色彩搭配，从面料选择到洗护建议，把你的需求告诉 AI 服饰顾问，获得清晰、可执行的穿搭与选购建议。</p>
        <div class="qa-pills">
            <span class="qa-pill">尺码推荐</span>
            <span class="qa-pill">版型分析</span>
            <span class="qa-pill">场景穿搭</span>
            <span class="qa-pill">面料养护</span>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)

capability_cols = st.columns(4)
for column, (icon, title, description) in zip(capability_cols, CAPABILITIES):
    with column:
        st.markdown(
            f"""
            <div class="qa-cap">
                <div class="icon">{icon}</div>
                <h4>{title}</h4>
                <p>{description}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

if not api_key_ready:
    st.warning(
        "当前终端未检测到 OPENAI_API_KEY，暂时无法生成回答。"
        "请配置 DashScope 兼容 API Key 后刷新页面。"
    )

st.markdown('<div class="qa-section-title">不知道怎么问？试试这些</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="qa-section-note">点击问题可直接开始咨询，也可以在下方输入自己的问题。</div>',
    unsafe_allow_html=True,
)

prompt_columns = st.columns(2)
for index, (label, question) in enumerate(QUICK_PROMPTS):
    with prompt_columns[index % 2]:
        if st.button(
            label,
            help=question,
            width="stretch",
            disabled=not api_key_ready,
            key=f"quick_prompt_{index}",
        ):
            st.session_state["pending_prompt"] = question
            st.rerun()

st.divider()

for message in st.session_state["qa_messages"]:
    avatar = "👗" if message["role"] == "assistant" else None
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

prompt = st.chat_input(
    "描述你的身高、常穿尺码、场景或商品问题...",
    disabled=not api_key_ready,
)
if st.session_state.get("pending_prompt"):
    prompt = st.session_state.pop("pending_prompt")

if prompt:
    st.session_state["qa_messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="👗"):
        try:
            if "rag" not in st.session_state:
                st.session_state["rag"] = RagService()

            runtime_config = {
                "configurable": {
                    "session_id": st.session_state["chat_session_id"],
                }
            }
            with st.spinner("正在整理服饰建议..."):
                response_stream = st.session_state["rag"].chain.stream(
                    {"input": prompt},
                    runtime_config,
                )
                response = st.write_stream(response_stream)

            if not response:
                response = "抱歉，本次没有生成有效回答，请换一种问法再试。"
                st.warning(response)
            st.session_state["qa_messages"].append(
                {"role": "assistant", "content": response}
            )
        except Exception as exc:
            print(f"[QA_SERVICE_ERROR] {type(exc).__name__}")
            st.error(
                "AI 服务暂时不可用，请稍后重试。"
                "如果问题持续出现，请联系管理员检查模型配置。"
            )

st.caption(
    "AI 建议仅供参考。商品尺码、库存、价格、物流与售后结果，"
    "请以商品详情页和商家最终确认为准。"
)
