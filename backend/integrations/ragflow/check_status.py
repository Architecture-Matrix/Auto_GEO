"""
RAGFlow服务状态检查脚本
用于检查RAGFlow服务是否正在运行
"""
import requests
import json
import os
from ragflow_integration import RAGFlowClient

def check_ragflow_status(base_url):
    """检查RAGFlow服务状态"""
    print(f"检查RAGFlow服务状态: {base_url}")
    
    try:
        # 尝试访问RAGFlow的API端点
        response = requests.get(f"{base_url}/api/v1/health", timeout=10)
        if response.status_code == 200:
            print("✓ RAGFlow服务正在运行")
            return True
        else:
            print(f"✗ RAGFlow服务响应异常，状态码: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ 无法连接到RAGFlow服务，请确保服务正在运行")
        return False
    except requests.exceptions.Timeout:
        print("✗ 连接RAGFlow服务超时")
        return False
    except Exception as e:
        print(f"✗ 检查RAGFlow服务时出错: {e}")
        return False


def load_config():
    """加载配置文件"""
    config_path = 'config.json'
    if not os.path.exists(config_path):
        config_path = 'config_example.json'
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config['ragflow_config']
    except FileNotFoundError:
        print(f"配置文件 {config_path} 未找到")
        return None
    except json.JSONDecodeError:
        print("配置文件格式错误，请检查JSON格式")
        return None


def test_api_key_validity(config):
    """测试API密钥是否有效"""
    print("\n测试API密钥有效性...")
    
    try:
        client = RAGFlowClient(config['base_url'], config['api_key'])
        
        # 尝试列出数据集，验证API密钥
        datasets = client.list_datasets()
        print(f"✓ API密钥有效，找到 {len(datasets)} 个知识库")
        
        if datasets:
            print("  知识库列表:")
            for i, dataset in enumerate(datasets[:5], 1):
                print(f"  {i}. {dataset.get('name', 'Unknown')} (ID: {dataset.get('id', 'Unknown')})")
        
        return True, datasets
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("✗ API密钥无效或已过期")
        elif e.response.status_code == 403:
            print("✗ API密钥无权限访问")
        else:
            print(f"✗ API请求失败: {e}")
        return False, []
    except Exception as e:
        print(f"✗ 测试API密钥时出错: {e}")
        return False, []


def main():
    print("=" * 60)
    print("RAGFlow服务状态检查")
    print("=" * 60)
    
    # 加载配置
    config = load_config()
    if not config:
        print("无法加载配置，请确保config.json或config_example.json存在")
        return False
    
    print("使用配置:")
    print(f"  URL: {config['base_url']}")
    print(f"  API Key: {'*' * (len(config['api_key']) - 4) + config['api_key'][-4:]}")  # 隐藏API密钥
    print(f"  Dataset ID: {config['dataset_id']}")
    
    # 检查服务状态
    service_running = check_ragflow_status(config['base_url'])
    
    if not service_running:
        print("\n⚠️  RAGFlow服务未运行")
        print(f"请确保RAGFlow服务在 {config['base_url']} 上运行")
        print("如果您使用不同的端口或地址，请更新配置文件")
        return False
    
    # 测试API密钥
    api_valid, datasets = test_api_key_validity(config)
    
    if not api_valid:
        print("\n⚠️  API密钥无效")
        print("请检查:")
        print("  1. API密钥是否正确")
        print("  2. API密钥是否已过期")
        print("  3. API密钥是否有足够的权限")
        print("\n获取API密钥方法:")
        print("  1. 登录RAGFlow界面")
        print("  2. 点击右上角用户头像")
        print("  3. 选择'API' -> 'RAGFlow API'")
        print("  4. 复制API Key")
        return False
    
    print("\n✓ 所有检查通过!")
    print("✓ RAGFlow服务运行正常")
    print("✓ API密钥有效")
    print("✓ 可以进行连接测试")
    
    if datasets:
        print("\n下一步您可以:")
        print("  1. 运行连接测试: python test_connection.py")
        print("  2. 在您的geo项目中使用集成框架")
    else:
        print("\n注意: 没有找到知识库")
        print("请先在RAGFlow中创建知识库并添加文档")
    
    return True


if __name__ == "__main__":
    main()