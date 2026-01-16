import asyncio
import math
from typing import List, TypedDict


class VectorStoreItem(TypedDict):
    """向量存储项类型定义"""
    embedding: List[float]
    document: str


class VectorStore:
    """向量存储类"""
    
    def __init__(self):
        """初始化向量存储"""
        self.vector_store: List[VectorStoreItem] = []

    def add_item(self, item: VectorStoreItem) -> None:
        """
        添加向量项到存储
        
        Args:
            item: 包含嵌入向量和文档的字典
        """
        self.vector_store.append(item)
    
    async def search(self, query_embedding: List[float], top_k: int = 3) -> List[str]:
        """
        搜索与查询向量最相似的文档
        
        Args:
            query_embedding: 查询向量
            top_k: 返回的顶部相似文档数量
            
        Returns:
            最相似文档的列表
        """
        # 计算每个向量的相似度并排序
        scored_items = []
        
        for item in self.vector_store:
            similarity = self.__cosine_similarity(query_embedding, item['embedding'])
            scored_items.append({
                'document': item['document'],
                'similarity': similarity
            })
        
        # 按相似度降序排序并获取前top_k个
        scored_items.sort(key=lambda x: x['similarity'], reverse=True)
        top_items = scored_items[:top_k]
        
        # 提取文档内容
        return [item['document'] for item in top_items]
    
    @staticmethod
    def __cosine_similarity(v1: List[float], v2: List[float]) -> float:
        """
        计算两个向量的余弦相似度
        
        Args:
            v1: 向量1
            v2: 向量2
            
        Returns:
            余弦相似度值，范围[-1, 1]
        """
        # 使用numpy进行更高效的计算（如果可用）
        try:
            import numpy as np
            v1_np = np.array(v1)
            v2_np = np.array(v2)
            dot_product = np.dot(v1_np, v2_np)
            norm_v1 = np.linalg.norm(v1_np)
            norm_v2 = np.linalg.norm(v2_np)
            
            if norm_v1 == 0 or norm_v2 == 0:
                return 0.0
            return float(dot_product / (norm_v1 * norm_v2))
        except ImportError:
            # 纯Python实现
            dot_product = sum(a * b for a, b in zip(v1, v2))
            norm_v1 = math.sqrt(sum(a * a for a in v1))
            norm_v2 = math.sqrt(sum(b * b for b in v2))
            
            if norm_v1 == 0 or norm_v2 == 0:
                return 0.0
            return dot_product / (norm_v1 * norm_v2)
    
    def __len__(self) -> int:
        """返回存储的向量数量"""
        return len(self.vector_store)
    
    def clear(self) -> None:
        """清空向量存储"""
        self.vector_store.clear()


def example(): 
    store = VectorStore()
    
    # 添加向量项
    store.add_item({
        'embedding': [0.1, 0.2, 0.3, 0.4],
        'document': '文档A：关于机器学习的介绍'
    })
    
    store.add_item({
        'embedding': [0.2, 0.3, 0.4, 0.5],
        'document': '文档B：深度学习基础'
    })
    
    store.add_item({
        'embedding': [0.9, 0.8, 0.7, 0.6],
        'document': '文档C：Python编程指南'
    })
    
    # 搜索相似文档
    query_vec = [0.15, 0.25, 0.35, 0.45]
    results = store.search(query_vec, top_k=2)
    print("异步搜索结果:", results)

if __name__ == "__main__":
    example()