import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from document_processor import process_documents
from vector_store import add_documents, get_collection_stats, clear_collection
from rag_chain import create_rag_chain, format_docs

st.set_page_config(
    page_title="GeoTeach 地理教学助手",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 GeoTeach 地理教学助手")

# 初始化session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "rag_chain" not in st.session_state:
    st.session_state.rag_chain = None
if "retriever" not in st.session_state:
    st.session_state.retriever = None

# 侧边栏
with st.sidebar:
    st.header("📚 文档管理")
    
    # 文档上传
    uploaded_files = st.file_uploader(
        "上传文档",
        type=['pdf', 'docx', 'txt', 'md'],
        accept_multiple_files=True,
        help="支持PDF、DOCX、TXT、Markdown格式"
    )
    
    if uploaded_files and st.button("处理上传的文档"):
        with st.spinner("正在处理文档..."):
            # 保存文件
            import os
            os.makedirs("data", exist_ok=True)
            for file in uploaded_files:
                file_path = os.path.join("data", file.name)
                with open(file_path, "wb") as f:
                    f.write(file.getbuffer())
            
            # 处理文档
            docs = process_documents("data")
            if docs:
                add_documents(docs)
                st.success(f"成功处理 {len(docs)} 个文档片段")
    
    st.divider()
    
    # 知识库状态
    st.header("📊 知识库状态")
    if st.button("刷新状态"):
        stats = get_collection_stats()
        st.metric("文档片段数量", stats.get("count", 0))
    
    st.divider()
    
    # 清空知识库
    st.header("⚠️ 危险操作")
    if st.button("清空知识库", type="secondary"):
        if st.checkbox("确认清空"):
            clear_collection()
            st.success("知识库已清空")
    
    st.divider()
    
    # 初始化RAG
    if st.button("初始化RAG系统"):
        with st.spinner("正在初始化..."):
            st.session_state.rag_chain, st.session_state.retriever = create_rag_chain()
            st.success("RAG系统初始化完成")

# 主界面
st.header("💬 对话")

# 显示历史消息
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# 用户输入
if prompt := st.chat_input("请输入你的问题"):
    # 检查RAG是否初始化
    if st.session_state.rag_chain is None:
        st.error("请先在侧边栏初始化RAG系统")
        st.stop()
    
    # 显示用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    
    # 获取回答
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            # 构建历史
            chat_history = []
            for msg in st.session_state.messages[:-1]:  # 排除当前问题
                if msg["role"] == "user":
                    chat_history.append(HumanMessage(content=msg["content"]))
                else:
                    chat_history.append(AIMessage(content=msg["content"]))
            
            # 调用RAG
            response = st.session_state.rag_chain.invoke({
                "question": prompt,
                "chat_history": chat_history
            })
            
            st.write(response)
            
            # 显示引用文档
            with st.expander("📎 查看引用的文档片段"):
                docs = st.session_state.retriever.invoke(prompt)
                for i, doc in enumerate(docs, 1):
                    st.markdown(f"**文档{i}** - {doc.metadata.get('source', '未知来源')}")
                    st.text(doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content)
                    st.divider()
    
    st.session_state.messages.append({"role": "assistant", "content": response})

# 底部信息
st.divider()
st.caption("GeoTeach RAG系统 - 使用Milvus + LangChain + Streamlit构建")
