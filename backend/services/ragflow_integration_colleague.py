"""
RAGFlow与geo项目集成模块（同事提供版本）
提供与RAGFlow知识库交互的功能
"""
import requests
from typing import Dict, List
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGFlowClient:
    """
    RAGFlow客户端，用于与RAGFlow知识库进行交互
    """
    
    def __init__(self, base_url: str, api_key: str):
        """
        初始化RAGFlow客户端
        
        Args:
            base_url: RAGFlow服务的基础URL (如: http://localhost:9380)
            api_key: RAGFlow API密钥
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def list_datasets(self) -> List[Dict]:
        """
        获取所有知识库列表
        
        Returns:
            知识库列表
        """
        url = f"{self.base_url}/api/v1/datasets"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json().get('data', [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to list datasets: {e}")
            raise
    
    def search_in_dataset(self, dataset_id: str, query: str, top_k: int = 5, 
                         similarity_threshold: float = 0.3) -> Dict:
        """
        在指定知识库中搜索
        
        Args:
            dataset_id: 知识库ID
            query: 搜索查询
            top_k: 返回最相似的前k个结果
            similarity_threshold: 相似度阈值
        
        Returns:
            搜索结果
        """
        url = f"{self.base_url}/api/v1/datasets/{dataset_id}/search"
        payload = {
            "query": query,
            "top_k": top_k,
            "similarity_threshold": similarity_threshold
        }
        
        try:
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Search failed: {e}")
            raise
    
    def get_dataset_info(self, dataset_id: str) -> Dict:
        """
        获取知识库信息
        
        Args:
            dataset_id: 知识库ID
        
        Returns:
            知识库信息
        """
        url = f"{self.base_url}/api/v1/datasets/{dataset_id}"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get dataset info: {e}")
            raise
    
    def upload_document(self, dataset_id: str, file_path: str) -> Dict:
        """
        上传文档到知识库
        
        Args:
            dataset_id: 知识库ID
            file_path: 文档文件路径
        
        Returns:
            上传结果
        """
        url = f"{self.base_url}/api/v1/datasets/{dataset_id}/documents"
        try:
            with open(file_path, 'rb') as file:
                files = {'file': file}
                # 注意：上传文件时不需要 Content-Type: application/json
                headers = {'Authorization': f'Bearer {self.api_key}'}
                response = requests.post(url, files=files, headers=headers)
                response.raise_for_status()
                return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to upload document: {e}")
            raise

    def run_document_analysis(self, doc_ids: List[str]) -> Dict:
        """
        启动文档解析
        
        Args:
            doc_ids: 文档ID列表
            
        Returns:
            接口响应结果
        """
        # 注意：云端 API 路径可能与本地版本略有差异
        # 根据 RAGFlow 标准 API 文档，解析接口通常是 /api/v1/datasets/{dataset_id}/chunks
        # 但用户指定了 /api/v1/document/run，我们尝试另一种可能的标准路径
        url = f"{self.base_url}/api/v1/document/run"
        payload = {"doc_ids": doc_ids}
        try:
            response = requests.post(url, json=payload, headers=self.headers)
            # 如果 404，尝试备选路径
            if response.status_code == 404:
                logger.warning(f"Analysis URL {url} returned 404, please verify if the cloud API path is correct.")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to start document analysis: {e}")
            raise


class GeoRAGFlowIntegration:
    """
    geo项目与RAGFlow集成类
    提供地理空间知识查询等功能
    """
    
    def __init__(self, ragflow_config: Dict):
        """
        初始化集成类
        
        Args:
            ragflow_config: RAGFlow配置信息
                {
                    'base_url': 'RAGFlow服务地址',
                    'api_key': 'API密钥',
                    'dataset_id': '知识库ID'
                }
        """
        self.ragflow_client = RAGFlowClient(
            base_url=ragflow_config['base_url'],
            api_key=ragflow_config['api_key']
        )
        self.dataset_id = ragflow_config['dataset_id']
    
    def query_geospatial_knowledge(self, query: str) -> Dict:
        """
        查询地理空间相关知识
        
        Args:
            query: 查询内容
        
        Returns:
            查询结果
        """
        try:
            # 在RAGFlow知识库中搜索相关信息
            search_results = self.ragflow_client.search_in_dataset(
                dataset_id=self.dataset_id,
                query=query,
                top_k=5,
                similarity_threshold=0.3
            )
            
            # 处理搜索结果
            processed_results = self._process_search_results(search_results)
            
            return {
                'query': query,
                'results': processed_results,
                'success': True
            }
        except Exception as e:
            logger.error(f"Geo knowledge query failed: {e}")
            return {
                'query': query,
                'error': str(e),
                'success': False
            }
    
    def _process_search_results(self, search_results: Dict) -> List[Dict]:
        """
        处理搜索结果
        
        Args:
            search_results: 原始搜索结果
        
        Returns:
            处理后的结果列表
        """
        processed = []
        
        # 根据RAGFlow API返回格式调整
        # 搜索结果通常包含 chunks 或 documents 字段
        chunks = search_results.get('chunks', [])
        if not chunks:
            chunks = search_results.get('data', [])
        
        for chunk in chunks:
            processed_item = {
                'content': chunk.get('content', chunk.get('text', '')),
                'score': chunk.get('score', chunk.get('similarity', 0)),
                'source': chunk.get('doc_id', chunk.get('source', 'unknown')),
                'metadata': chunk.get('metadata', {})
            }
            processed.append(processed_item)
        
        return processed
    
    def get_knowledge_base_info(self) -> Dict:
        """
        获取当前知识库信息
        
        Returns:
            知识库信息
        """
        try:
            info = self.ragflow_client.get_dataset_info(self.dataset_id)
            return {
                'dataset_info': info,
                'success': True
            }
        except Exception as e:
            logger.error(f"Failed to get knowledge base info: {e}")
            return {
                'error': str(e),
                'success': False
            }
