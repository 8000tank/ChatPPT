# chatbot.py

from abc import ABC, abstractmethod
from typing import Dict, TypedDict, List, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
import operator

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder  # 导入提示模板相关类
from langchain_core.messages import HumanMessage, AIMessage  # 导入消息类
from langchain_core.runnables.history import RunnableWithMessageHistory  # 导入带有消息历史的可运行类

from logger import LOG  # 导入日志工具
from chat_history import get_session_history


# 定义状态类型
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    next: str
    current_content: str
    reflection_round: int


class ChatBot(ABC):
    """
    聊天机器人基类，提供聊天功能。
    """

    def __init__(self, prompt_file="./prompts/chatbot.txt", session_id=None):
        self.prompt_file = prompt_file
        self.session_id = session_id or "default_session_id"
        self.prompt = self.load_prompt()
        # LOG.debug(f"[ChatBot Prompt]{self.prompt}")
        self.create_chatbot()

        # 初始化reviewer
        self.reviewer = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.5
        )
        
        # 创建reviewer的完整链
        self.reviewer_chain = (
            ChatPromptTemplate.from_messages([
                ("system", self.load_reviewer_prompt()),
                ("human", "{content}")
            ]) 
            | self.reviewer
        )

        # 创建反思工作流图
        self.reflection_graph = self.create_reflection_graph()

    def load_prompt(self):
        """
        从文件加载系统提示语。
        """
        try:
            with open(self.prompt_file, "r", encoding="utf-8") as file:
                return file.read().strip()
        except FileNotFoundError as e:
            raise FileNotFoundError(f"找不到提示文件 {self.prompt_file}!") from e

    def create_chatbot(self):
        """
        初始化聊天机器人，包括系统提示和消息历史记录。
        """
        # 创建聊天提示模板，包括系统提示和消息占位符
        system_prompt = ChatPromptTemplate.from_messages([
            ("system", self.prompt),  # 系统提示部分
            MessagesPlaceholder(variable_name="messages"),  # 消息占位符
        ])

        # 初始化 ChatOllama 模型，配置参数
        self.chatbot = system_prompt | ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.5,
            max_tokens=4096
        )

        # 将聊天机器人与消息历史记录关联
        # self.chatbot_with_history = RunnableWithMessageHistory(self.chatbot, get_session_history)

    def chat_with_history(self, user_input, session_id=None):
        """
        处理用户输入，生成包含聊天历史的回复。

        参数:
            user_input (str): 用户输入的消息
            session_id (str, optional): 会话的唯一标识符

        返回:
            str: AI 生成的回复
        """
        if session_id is None:
            session_id = self.session_id

        # 获取历史记录管理器
        history = get_session_history(session_id)

        # 手动添加用户消息
        history.add_message(HumanMessage(content=user_input))

        # 获取响应
        response = self.chatbot.invoke(
            [HumanMessage(content=user_input)],
            {"configurable": {"session_id": session_id}},
        )

        # 处理响应
        processed_content = self.process_response(response.content)

        # 手动添加处理后的 AI 响应到历史记录
        history.add_message(AIMessage(content=processed_content))

        LOG.debug(f"[ChatBot] {processed_content}")
        return processed_content

    def review_content(self, state: AgentState) -> AgentState:
        """Reviewer 评估内容"""
        LOG.info(f"\n[反思轮次 {state['reflection_round'] + 1}] 开始评估内容...")
        LOG.info(f"当前内容:\n{state['current_content']}")
        
        reviewer_response = self.reviewer_chain.invoke({
            "content": state["current_content"]
        })
        
        LOG.info(f"Reviewer 评估意见:\n{reviewer_response.content}")
        state["messages"].append(AIMessage(content=reviewer_response.content))
        return state

    def improve_content(self, state: AgentState) -> AgentState:
        """基于反馈改进内容"""
        feedback = state["messages"][-1].content
        LOG.info(f"\n[反思轮次 {state['reflection_round'] + 1}] 开始改进内容...")
        
        improvement_prompt = f"""
        基于以下反馈改进你的回答：
        {feedback}
        
        你的原始回答是：
        {state["current_content"]}
        
        请提供改进后的回答：
        """

        improved_response = self.chatbot.invoke(
            [HumanMessage(content=improvement_prompt)],
            {"configurable": {"session_id": self.session_id}}
        )

        state["current_content"] = improved_response.content
        state["reflection_round"] += 1
        
        LOG.info(f"改进后的内容:\n{state['current_content']}")
        LOG.info(f"完成第 {state['reflection_round']} 轮反思")
        return state

    def should_continue(self, state: AgentState) -> str:
        """决定是否继续反思"""
        return "end" if state["reflection_round"] >= 4 else "review"

    def create_reflection_graph(self) -> StateGraph:
        """创建反思工作流图"""
        workflow = StateGraph(AgentState)

        # 添加节点
        workflow.add_node("review", self.review_content)
        workflow.add_node("improve", self.improve_content)

        # 设置边和条件
        workflow.add_edge("review", "improve")
        workflow.add_conditional_edges(
            "improve",
            self.should_continue,
            {
                "review": "review",
                "end": END
            }
        )

        # 设置入口节点
        workflow.set_entry_point("review")

        return workflow.compile()

    def process_response(self, content: str) -> str:
        """
        使用 LangGraph 实现的反思机制处理响应

        Args:
            content: 原始响应内容

        Returns:
            str: 经过反思改进的响应内容
        """
        LOG.info("\n=== 开始反思过程 ===")
        LOG.info(f"原始响应:\n{content}")
        
        # 初始化状态
        initial_state = {
            "messages": [],
            "next": "review",
            "current_content": content,
            "reflection_round": 0
        }

        # 运行反思工作流
        try:
            final_state = self.reflection_graph.invoke(initial_state)
            LOG.info("\n=== 反思过程完成 ===")
            LOG.info(f"共进行 {final_state['reflection_round']} 轮反思")
            LOG.info(f"最终内容:\n{final_state['current_content']}")
            return final_state["current_content"]
        except Exception as e:
            LOG.error(f"[反思过程出错] {str(e)}")
            return content  # 如果反思过程出错，返回原始内容

    def load_reviewer_prompt(self) -> str:
        """
        加载 reviewer 的 prompt
        
        Returns:
            str: reviewer的prompt内容
        """
        try:
            reviewer_prompt_path = "./prompts/reflection_reviewer_prompt.md"
            with open(reviewer_prompt_path, "r", encoding="utf-8") as file:
                return file.read().strip()
        except FileNotFoundError as e:
            LOG.error(f"找不到reviewer提示文件: {reviewer_prompt_path}")
            raise FileNotFoundError(f"找不到reviewer提示文件: {reviewer_prompt_path}") from e
