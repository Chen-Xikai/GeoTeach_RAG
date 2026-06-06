import os
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from vector_store import get_retriever

# SiliconFlow配置
SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY", "sk-free")
SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1"
LLM_MODEL = "Qwen/Qwen2.5-7B-Instruct"

def format_docs(docs):
    """格式化文档片段"""
    formatted = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get('source', '未知来源')
        content = doc.page_content
        formatted.append(f"[文档{i}] 来源: {source}\n{content}")
    return "\n\n".join(formatted)

def get_llm():
    """获取LLM模型"""
    return ChatOpenAI(
        model=LLM_MODEL,
        openai_api_key=SILICONFLOW_API_KEY,
        openai_api_base=SILICONFLOW_BASE_URL,
        temperature=0.7
    )

def create_rag_chain():
    """创建RAG检索链"""
    retriever = get_retriever()
    llm = get_llm()
    
    # 带历史的Prompt模板
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个专业的地理教学助手。基于以下上下文回答问题。
如果上下文中没有相关信息，请说明无法根据提供的资料回答。

上下文:
{context}"""),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}")
    ])
    
    def retrieve_and_format(question):
        docs = retriever.invoke(question)
        return format_docs(docs)
    
    rag_chain = (
        {
            "context": lambda x: retrieve_and_format(x["question"]),
            "question": lambda x: x["question"],
            "chat_history": lambda x: x["chat_history"]
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return rag_chain, retriever
