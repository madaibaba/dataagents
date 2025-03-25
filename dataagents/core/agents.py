# -*- coding: utf-8 -*-

from autogen import AssistantAgent, GroupChat, GroupChatManager
from typing import List, Dict

class AgentSystem:
    """智能体管理系统"""
    def __init__(self, llm_config: Dict):
        self.llm_config = llm_config
        self.agents = self._init_agents()
        self.group_chat = self._init_group_chat()
    
    def _init_agents(self) -> List[AssistantAgent]:
        """初始化五角色智能体"""
        return [
            AssistantAgent(
                name="Orchestrator",
                system_message=f"""您是数据治理协调员，职责包括：
1. 验证数据格式（使用 df 变量）
2. 协调处理流程
3. 监控任务状态
4. 生成最终报告""",
                llm_config=self.llm_config
            ),
            AssistantAgent(
                name="DataReader",
                system_message="处理CSV/JSON/Parquet格式数据，精通MinIO操作",
                llm_config=self.llm_config
            ),
            AssistantAgent(
                name="DataCleaner",
                system_message="使用Pandas进行数据清洗和脱敏",
                llm_config=self.llm_config
            ),
            AssistantAgent(
                name="QualityValidator",
                system_message="使用Great Expectations验证数据质量",
                llm_config=self.llm_config
            ),
            AssistantAgent(
                name="VisualizationExpert",
                system_message="生成交互式Plotly报告",
                llm_config=self.llm_config
            ),
            AssistantAgent(
                name="VisualizationExpert",
                system_message="生成交互式Plotly报告，保存为HTML文件到report目录",
                llm_config=self.llm_config
            )
        ]
    
    def _init_group_chat(self) -> GroupChat:
        """配置群组协作"""
        return GroupChat(
            agents=self.agents,
            messages=[],
            max_round=40,
            select_speaker_auto_llm_config=self.llm_config
        )
    
    def get_chat_manager(self):
        """获取群组管理器"""
        return GroupChatManager(
            groupchat=self.group_chat,
            llm_config=self.llm_config
        )