"""LLM 调用层验收测试"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_json_parser import parse_llm_json, safe_parse_llm_json


def json_parser():
    """测试 JSON 解析器（不需要网络）"""
    assert parse_llm_json('{"key": "value"}') == {"key": "value"}

    parsed = parse_llm_json('```json\n{"key": "value"}\n```')
    assert parsed["key"] == "value"

    parsed = parse_llm_json('好的，以下是结果：\n{"key": "value"}')
    assert parsed["key"] == "value"

    result = safe_parse_llm_json("not json at all", default={"fallback": True})
    assert result == {"fallback": True}

    try:
        parse_llm_json("")
        assert False, "应该抛异常"
    except ValueError:
        pass

    print("✅ JSON 解析器测试通过")


async def llm_non_stream():
    """测试非流式调用（需要数据库连接）"""
    # 先加载 .env.test 环境变量，否则 config.database 读不到数据库配置
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env.test'))

    from config.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        from module_learning.service.llm_call import AiCall
        model_id = 1
        result = await AiCall.call_llm_non_stream(db, model_id, "请说一句话")
        print(f"非流式调用: {result}")
        result = await AiCall.call_llm_json(db, model_id, "请输出 JSON，包含 name 和 age。只输出 JSON。")
        print(f"JSON 调用: {result}")
    print("✅ LLM 非流式调用测试通过")


if __name__ == '__main__':
    json_parser()
    # 取消注释下面的行来测试真实的 LLM 调用（需要数据库连接）
    import asyncio
    asyncio.run(llm_non_stream())