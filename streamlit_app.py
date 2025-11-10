import streamlit as st
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
import time
import os
import glob
import tempfile

# 设置页面配置
st.set_page_config(
    page_title="工会知识问答系统",
    page_icon="🤝",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 知识库文件目录
KNOWLEDGE_BASE_DIR = "FILEUPLOAD"


def load_knowledge_base():
    """加载知识库目录下的所有txt文件内容"""
    knowledge_content = ""

    # 检查目录是否存在，不存在则创建
    os.makedirs(KNOWLEDGE_BASE_DIR, exist_ok=True)

    # 查找所有txt文件
    txt_files = glob.glob(os.path.join(KNOWLEDGE_BASE_DIR, "*.txt"))

    if not txt_files:
        return knowledge_content

    # 读取所有文件内容
    file_count = 0
    for file_path in txt_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    knowledge_content += f"\n--- 文件: {os.path.basename(file_path)} ---\n{content}\n"
                    file_count += 1
        except Exception as e:
            st.error(f"读取文件 {file_path} 时出错: {str(e)}")

    return knowledge_content, file_count


def save_uploaded_file(uploaded_file):
    """保存上传的文件到知识库目录"""
    try:
        file_path = os.path.join(KNOWLEDGE_BASE_DIR, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return True, file_path
    except Exception as e:
        return False, str(e)


def get_system_prompt(assistant_name, knowledge_content=""):
    """根据知识库内容生成系统提示词"""
    base_template = f"""你是一个专业的工会知识助手，你叫{assistant_name}。你的职责是帮助用户了解工会相关知识和政策。要求如下：

    1. 你专注于工会建设、职工权益、劳动法规、集体协商等方面的专业知识
    2. 你能够准确解读工会相关政策法规，并提供实用的建议
    3. 你的语气专业、友好、耐心，能够用通俗易懂的语言解释复杂的概念
    4. 对于不确定的问题，你会如实告知而不是随意猜测
    5. 你注重信息的准确性和权威性，会提醒用户重要政策的时效性

    你的专业知识涵盖以下领域：
    - 工会组织建设与运作
    - 职工权益保护
    - 劳动合同法规
    - 集体协商与集体合同
    - 劳动争议处理
    - 职工民主管理
    - 工会经费管理
    - 职工福利保障
    """

    # 如果有知识库内容，添加到系统提示中
    if knowledge_content:
        base_template += f"""

    以下是你需要了解的特定知识库内容，请基于这些信息来回答问题：
    {knowledge_content}

    注意：在回答时要准确引用相关知识，确保信息的可靠性。
    """

    return base_template


# 初始化聊天模型
@st.cache_resource
def init_chat_model():
    API_KEY = "sk-de451d9d19994ea0a7985b713379cc95"
    chat = ChatOpenAI(
        model_name="deepseek-chat",
        api_key=API_KEY,
        base_url="https://api.deepseek.com"
    )
    return chat


def main():
    # 加载知识库
    knowledge_content, file_count = load_knowledge_base()

    # 在侧边栏显示知识库状态和上传功能
    with st.sidebar:
        st.header("⚙️ 设置")
        assistant_name = st.text_input("助手名称", value="工会小助手")

        st.markdown("---")
        st.subheader("📚 知识库管理")

        # 文件上传功能
        uploaded_files = st.file_uploader(
            "上传工会知识文件 (TXT格式)",
            type=['txt'],
            accept_multiple_files=True,
            help="上传包含工会知识、政策法规的TXT文件"
        )

        if uploaded_files:
            for uploaded_file in uploaded_files:
                success, result = save_uploaded_file(uploaded_file)
                if success:
                    st.success(f"文件 '{uploaded_file.name}' 上传成功！")
                else:
                    st.error(f"文件 '{uploaded_file.name}' 上传失败: {result}")

            # 重新加载知识库
            if st.button("🔄 重新加载知识库"):
                knowledge_content, file_count = load_knowledge_base()
                st.rerun()

        # 显示当前知识库状态
        if file_count > 0:
            st.success(f"已加载 {file_count} 个知识库文件")

            # 显示文件列表
            with st.expander("查看已加载的文件"):
                txt_files = glob.glob(os.path.join(KNOWLEDGE_BASE_DIR, "*.txt"))
                for file_path in txt_files:
                    file_name = os.path.basename(file_path)
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.text(file_name)
                    with col2:
                        if st.button("删除", key=f"del_{file_name}"):
                            try:
                                os.remove(file_path)
                                st.rerun()
                            except:
                                st.error(f"删除文件 {file_name} 失败")
        else:
            st.info("暂无知识库文件，请上传包含工会知识的TXT文件")

        st.markdown("---")

        if st.button("🗑️ 清空聊天记录"):
            st.session_state.messages = [
                SystemMessagePromptTemplate.from_template(
                    get_system_prompt(assistant_name, knowledge_content)
                ).format()
            ]
            st.session_state.chat_history = []
            st.rerun()

        st.markdown("### 使用说明")
        st.markdown("""
        - 输入工会相关问题后按回车发送
        - 可以咨询以下类型问题：
          - 工会组建流程
          - 职工权益保护
          - 劳动法规解读
          - 集体协商指导
          - 劳动争议处理
        - 点击'清空聊天记录'重新开始对话
        - 上传TXT文件丰富知识库内容
        """)

    # 获取系统提示词
    system_prompt = get_system_prompt(assistant_name, knowledge_content)

    # 初始化会话状态
    if "messages" not in st.session_state:
        st.session_state.messages = [
            SystemMessagePromptTemplate.from_template(system_prompt).format()
        ]

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # 标题和描述
    st.title("🤝 工会知识问答系统")
    st.markdown("---")
    st.markdown("欢迎使用工会知识问答系统！我是**{}**，专注于为您提供专业的工会知识服务。".format(assistant_name))

    # 显示知识库加载状态
    if file_count > 0:
        st.success(f"✅ 已加载 {file_count} 个知识库文件，系统知识库已更新！")
    else:
        st.info("💡 提示：您可以在侧边栏上传包含工会知识的TXT文件来丰富系统知识库")

    # 常见问题快速提问
    st.subheader("💡 常见问题类型")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("工会组建"):
            st.session_state.quick_question = "如何组建企业工会？"
    with col2:
        if st.button("职工权益"):
            st.session_state.quick_question = "职工有哪些基本权益？"
    with col3:
        if st.button("集体协商"):
            st.session_state.quick_question = "集体协商的流程是什么？"

    # 显示聊天记录
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                with st.chat_message("user", avatar="👤"):
                    st.markdown(message["content"])
            else:
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(message["content"])

    # 用户输入
    user_input = st.chat_input("请输入您想了解的工会相关问题...")

    # 处理快速提问
    if hasattr(st.session_state, 'quick_question') and st.session_state.quick_question:
        user_input = st.session_state.quick_question
        del st.session_state.quick_question

    if user_input:
        # 处理退出命令
        if user_input.lower() in ['退出', 'exit', 'quit']:
            farewell_message = "感谢您使用工会知识问答系统！如有其他问题，欢迎随时咨询。"
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            st.session_state.chat_history.append({"role": "assistant", "content": farewell_message})
            st.rerun()
            st.stop()

        # 添加用户消息到显示
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        # 显示用户消息
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)

        # 添加到langchain消息列表
        st.session_state.messages.append(HumanMessage(content=user_input))

        # 显示AI回复（带加载动画）
        with st.chat_message("assistant", avatar="🤖"):
            message_placeholder = st.empty()
            message_placeholder.markdown("🤖 正在检索工会知识...")

            try:
                # 调用模型生成回复
                chat_model = init_chat_model()
                response = chat_model.invoke(st.session_state.messages)

                # 模拟打字机效果
                full_response = ""
                for chunk in response.content.split():
                    full_response += chunk + " "
                    message_placeholder.markdown(full_response + "▌")
                    time.sleep(0.05)

                message_placeholder.markdown(full_response)

                # 添加到聊天历史
                st.session_state.chat_history.append({"role": "assistant", "content": response.content})
                st.session_state.messages.append(AIMessage(content=response.content))

            except Exception as e:
                error_message = f"抱歉，系统出现错误：{str(e)}"
                message_placeholder.markdown(error_message)
                st.session_state.chat_history.append({"role": "assistant", "content": error_message})


if __name__ == "__main__":
    main()
