from zai import ZhipuAiClient

client = ZhipuAiClient(api_key="4b5e77c39fb0496ba421e3c5e12c55de.J6Zv191Bwcyo5Qkt")
response = client.embeddings.create(
    model="embedding-3", #填写需要调用的模型编码
    input=[
        "美食非常美味，服务员也很友好。",
        "这部电影既刺激又令人兴奋。",
        "阅读书籍是扩展知识的好方法。"
    ],
)
print(response)