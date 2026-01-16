import json
import os
import httpx
from typing import Dict, List
from dataclasses import dataclass
from VectorStore import VectorStore
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


"""
步骤:
1. 获取embedding向量存储化和documents存储化的接口(向量对应的自然语言)
2. 通过embedding向量存储化接口获取相似度最高的topK个向量(embedding向量检索  ---> documents存储化)
3. 排序(
    prompt 向量化 --> embedding向量存储化接口检索 ---> 需要和向量数据库的documents的embedding向量做相似度比较[cos]  ---> documents存储化)
"""

@dataclass
class OutResult:
    """重排序结果类型"""
    index: int
    relevance_score: float
    document: Dict[str, str]
    

class EmbeddingRetrieve:
    """嵌入检索类"""

    def __init__(self, embedding_model: str):
        """
        初始化嵌入检索
        
        Args:
            embedding_model: 嵌入模型名称
        """
        self.__embedding_model = embedding_model
        self.__vectorStore = VectorStore()
    

    async def embed(self, query: str, documents: List[str]) -> List[float]:
        """
        获取查询和文档的嵌入向量（实际上是重排序分数）
        
        Args:
            query: 查询文本
            documents: 文档列表
            
        Returns:
            相关性分数列表
        """
        async with httpx.AsyncClient() as client:
            __response = await client.request(
                url=f'{os.getenv("EMBEDDING_BASE_URL")}/services/rerank/text-rerank/text-rerank',
                method="POST",
                headers={
                    "Authorization": f'Bearer {os.getenv("EMBEDDING_KEY")}',
                    "content-type": "application/json",
                },
                json={
                    "model": self.__embedding_model,
                    "input": {
                        "query": query,
                        "documents": documents
                    }
                }
            )


            __data = __response.json()
            print('Embedding Response Data:', __data)
            return [__result.relevance_score for __result in __data.output.results]
        
    
    async def retrieve(self, query: str, topK: int = 3):
        __query_embedding = await self.embed(query, [])
        return await self.__vectorStore.search(__query_embedding, topK)



def example():
    """重排序示例"""

    retriever = EmbeddingRetrieve(embedding_model="text-rerank-model")
    
    query = "什么是人工智能？"
    documents = [
        "机器学习是一种人工智能技术",
        "深度学习是机器学习的一个子领域",
        "Python是一种流行的编程语言"
    ]
    
    # 获取重排序分数
    relevance_scores = retriever.embed_sync(query, documents)
    print(f"重排序分数: {relevance_scores}")
    
    # 将分数与文档配对
    scored_docs = list(zip(relevance_scores, documents))
    
    # 按分数排序
    scored_docs.sort(reverse=True, key=lambda x: x[0])
    
    print("重排序结果:")
    for score, doc in scored_docs:
        print(f"分数: {score:.4f} - 文档: {doc}")


if __name__ == "__main__":
    example()