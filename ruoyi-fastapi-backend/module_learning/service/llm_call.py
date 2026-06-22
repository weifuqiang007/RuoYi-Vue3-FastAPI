# module_learning/service/llm_call.py
"""
LLM 调用封装（基于 module_ai 的 AiUtil 复用）
三个函数：非流式 / JSON解析 / 流式，供四区 AI 功能调用
"""

import json
from collections.abc import AsyncGenerator

from agno.agent import Agent
from agno.run.agent import RunEvent
from sqlalchemy.ext.asyncio import AsyncSession

from utils.ai_util import AiUtil
from utils.crypto_util import CryptoUtil
from utils.common_util import CamelCaseUtil
from utils.llm_json_parser import parse_llm_json
from module_ai.dao.ai_model_dao import AiModelDao
from module_ai.entity.vo.ai_model_vo import AiModelModel


class AiCall:

    @classmethod
    async def _get_model_from_db(cls, query_db: AsyncSession, model_id: int,
                                 min_max_tokens: int | None = None):

        ai_model = await AiModelDao.get_ai_model_detail_by_id(query_db, model_id)
        if not ai_model:
            raise ValueError(f"模型不存在：{model_id}")
        model_config = AiModelModel(**CamelCaseUtil.transform_result(ai_model))
        real_api_key = CryptoUtil.decrypt(model_config.api_key)

        # 数据库配置优先，未配置则兜底 2000；JSON 结构化输出场景可通过 min_max_tokens 抬高下限，
        # 避免长内容被 max_tokens 截断而产出不完整 JSON。
        effective_max_tokens = model_config.max_tokens or 2000
        if min_max_tokens is not None:
            effective_max_tokens = max(effective_max_tokens, min_max_tokens)

        model = AiUtil.get_model_from_factory(
            provider=model_config.provider,
            model_code=model_config.model_code,
            model_name=model_config.model_name,
            api_key=real_api_key,
            base_url=model_config.base_url,
            temperature=model_config.temperature or 0.7,
            max_tokens=effective_max_tokens,
        )
        return model

    @classmethod
    async def call_llm_non_stream(cls,
                                  query_db: AsyncSession,
                                  model_id: int,
                                  prompt: str,
                                  system: str = None,
                                  min_max_tokens: int | None = None) -> str:
        """
            非流式 LLM 调用（完整输出）
            适用：四区 AI 分析，需要完整结果后再处理
            :param min_max_tokens: max_tokens 下限，传入则保证生效值 >= 该值（用于 JSON 结构化输出场景防截断）
        """
        model = await cls._get_model_from_db(query_db, model_id, min_max_tokens=min_max_tokens)
        agent = Agent(
            model=model,
            description=system or 'You are a helpful AI assistant.',
            markdown=True,
        )
        response = await agent.arun(prompt, stream=False)
        return response.content

    @classmethod
    async def call_llm_json(cls,
                            query_db: AsyncSession,
                            model_id: int,
                            prompt: str,
                            system: str = None) -> dict:
        """
            非流式调用 + JSON 解析
            适用：需要 LLM 返回结构化数据的场景（决策分析、反思评估等）
            结构化 JSON 输出字段多、内容长，强制 max_tokens 下限 4096，避免被截断成不完整 JSON。
        """
        raw_text = await cls.call_llm_non_stream(query_db, model_id, prompt, system, min_max_tokens=4096)
        return parse_llm_json(raw_text)


    @classmethod
    async def call_llm_stream(cls,
                              query_db: AsyncSession,
                              model_id: int,
                              prompt: str,
                              system: str = None,
                              session_id: str = None,
                              user_id: str = None) -> AsyncGenerator[str, None]:
        """
            流式 LLM 调用 → 返回 SSE 格式文本流
            每个 chunk 是一行 JSON：{"content": "...", "type": "content"}
            适用：AI 助手对话、苏格拉底式提问等实时交互场景
        """
        model = await cls._get_model_from_db(query_db, model_id)

        agent_kwargs = {
            'model': model,
            'description': system or 'You are a helpful AI assistant.',
            'markdown': True
        }
        if session_id and user_id:
            agent_kwargs['db'] = AiUtil.get_storage_engine()
            agent_kwargs['user_id'] = str(user_id)
            agent_kwargs['session_id'] = session_id
            agent_kwargs['add_history_to_context'] = True
            agent_kwargs['num_history_runs'] = 30

        agent = Agent(**agent_kwargs)

        try:
            yield json.dumps({'session_id':session_id, 'type':'meta'}) + '\n'

            response_stream = agent.arun(prompt, stream=True, stream_events=True)

            async for chunk in response_stream :
                content = None

                if chunk.event == RunEvent.run_started and chunk.run_id:
                    yield json.dumps({'run_id': chunk.run_id, 'type': 'run_info'}) + "\n"

                if chunk.event == RunEvent.run_content:
                    content = chunk.content

                if content:
                    yield json.dumps({'content': content, 'type': 'content'}) + '\n'

                if chunk.event == RunEvent.run_completed and chunk.metrics:
                    yield json.dumps({
                        'metrics': {
                            'input_tokens': chunk.metrics.input_tokens if chunk.metrics else None,
                            'output_tokens': chunk.metrics.output_tokens if chunk.metrics else None,
                        },
                        'type': 'metrics'
                    }) + '\n'

        except Exception as e:
            yield json.dumps({'error': str(e), 'type': 'error'}) + '\n'


