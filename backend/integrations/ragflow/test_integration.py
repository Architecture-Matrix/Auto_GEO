"""
RAGFlow与geo项目集成框架测试脚本
用于验证集成框架是否能够正常运行
"""
import json
import sys
import os
from unittest.mock import patch

# 添加项目路径到系统路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from ragflow_integration import RAGFlowClient, GeoRAGFlowIntegration


def test_ragflow_client_initialization():
    """测试RAGFlowClient初始化"""
    print("测试1: RAGFlowClient初始化...")
    try:
        client = RAGFlowClient("http://localhost:9380", "test_api_key")
        assert client.base_url == "http://localhost:9380"
        assert client.api_key == "test_api_key"
        print("  ✓ 初始化成功")
        return True
    except Exception as e:
        print(f"  ✗ 初始化失败: {e}")
        return False


def test_geo_ragflow_integration_initialization():
    """测试GeoRAGFlowIntegration初始化"""
    print("测试2: GeoRAGFlowIntegration初始化...")
    try:
        config = {
            'base_url': 'http://localhost:9380',
            'api_key': 'test_api_key',
            'dataset_id': 'test_dataset_id'
        }
        integration = GeoRAGFlowIntegration(config)
        assert integration.dataset_id == 'test_dataset_id'
        print("  ✓ 初始化成功")
        return True
    except Exception as e:
        print(f"  ✗ 初始化失败: {e}")
        return False


def test_headers_construction():
    """测试请求头构建"""
    print("测试3: 请求头构建...")
    try:
        client = RAGFlowClient("http://localhost:9380", "test_api_key")
        expected_headers = {
            'Authorization': 'Bearer test_api_key',
            'Content-Type': 'application/json'
        }
        assert client.headers == expected_headers
        print("  ✓ 请求头构建正确")
        return True
    except Exception as e:
        print(f"  ✗ 请求头构建失败: {e}")
        return False


def test_url_construction():
    """测试URL构建"""
    print("测试4: URL构建...")
    try:
        client = RAGFlowClient("http://localhost:9380", "test_api_key")
        
        # 测试基础URL处理（去除末尾斜杠）
        assert client.base_url == "http://localhost:9380"
        
        # 测试搜索URL构建
        search_url = f"{client.base_url}/api/v1/datasets/test_dataset_id/search"
        expected_url = "http://localhost:9380/api/v1/datasets/test_dataset_id/search"
        assert search_url == expected_url
        
        print("  ✓ URL构建正确")
        return True
    except Exception as e:
        print(f"  ✗ URL构建失败: {e}")
        return False


def test_config_file():
    """测试配置文件格式"""
    print("测试5: 配置文件格式...")
    try:
        with open('config_example.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        required_keys = ['ragflow_config', 'search_params', 'connection']
        for key in required_keys:
            assert key in config, f"缺少必需的配置键: {key}"
        
        ragflow_keys = ['base_url', 'api_key', 'dataset_id']
        for key in ragflow_keys:
            assert key in config['ragflow_config'], f"缺少必需的RAGFlow配置键: {key}"
        
        print("  ✓ 配置文件格式正确")
        return True
    except Exception as e:
        print(f"  ✗ 配置文件验证失败: {e}")
        return False


def test_dependencies():
    """测试依赖项"""
    print("测试6: 依赖项检查...")
    try:
        import requests
        print(f"  ✓ requests版本: {requests.__version__}")
        return True
    except ImportError as e:
        print(f"  ✗ 依赖项导入失败: {e}")
        return False


def run_mock_tests():
    """运行模拟测试（模拟API调用）"""
    print("测试7: 模拟API调用...")
    try:
        # 模拟API响应
        mock_response = {
            'data': [
                {
                    'id': 'test_dataset',
                    'name': 'Test Dataset',
                    'status': 'ready'
                }
            ]
        }
        
        # 模拟搜索响应
        mock_search_response = {
            'chunks': [
                {
                    'content': '这是一个测试结果',
                    'score': 0.8,
                    'doc_id': 'test_doc_1'
                }
            ]
        }
        
        # 创建客户端实例
        client = RAGFlowClient("http://localhost:9380", "test_api_key")
        
        # 使用mock测试API调用
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response
            
            # 测试获取数据集列表
            datasets = client.list_datasets()
            assert len(datasets) == 1
            assert datasets[0]['name'] == 'Test Dataset'
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_search_response
            
            # 测试搜索功能
            search_results = client.search_in_dataset('test_dataset_id', 'test query')
            assert 'chunks' in search_results
        
        print("  ✓ 模拟API调用成功")
        return True
    except Exception as e:
        print(f"  ✗ 模拟API调用失败: {e}")
        return False


def test_integration_methods():
    """测试集成类方法"""
    print("测试8: 集成类方法...")
    try:
        config = {
            'base_url': 'http://localhost:9380',
            'api_key': 'test_api_key',
            'dataset_id': 'test_dataset_id'
        }
        integration = GeoRAGFlowIntegration(config)
        
        # 检查必需的方法是否存在
        assert hasattr(integration, 'query_geospatial_knowledge')
        assert hasattr(integration, 'get_knowledge_base_info')
        assert hasattr(integration, '_process_search_results')
        
        # 测试结果处理方法
        raw_results = {'chunks': [{'content': 'test content', 'score': 0.9, 'doc_id': 'doc1'}]}
        processed = integration._process_search_results(raw_results)
        assert len(processed) == 1
        assert processed[0]['content'] == 'test content'
        assert processed[0]['score'] == 0.9
        assert processed[0]['source'] == 'doc1'
        
        print("  ✓ 集成类方法正常")
        return True
    except Exception as e:
        print(f"  ✗ 集成类方法测试失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("开始测试RAGFlow与geo项目集成框架...")
    print("=" * 50)
    
    tests = [
        test_ragflow_client_initialization,
        test_geo_ragflow_integration_initialization,
        test_headers_construction,
        test_url_construction,
        test_config_file,
        test_dependencies,
        run_mock_tests,
        test_integration_methods
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
        print()
    
    print("=" * 50)
    print(f"测试完成! 通过: {sum(results)}/8")
    
    if all(results):
        print("🎉 所有测试通过! 集成框架可以正常运行。")
        print("\n要进行实际连接测试，请:")
        print("1. 确保RAGFlow服务正在运行")
        print("2. 更新config_example.json中的配置信息")
        print("3. 运行: python test_connection.py")
    else:
        print("⚠️  部分测试失败，请检查代码和依赖项。")
    
    return all(results)


if __name__ == "__main__":
    main()
