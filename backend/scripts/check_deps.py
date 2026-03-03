"""
依赖检查脚本 - 检查 requirements.txt 里所有包是否已安装
"""

import sys
from pathlib import Path


def parse_requirements(req_file):
    """解析 requirements.txt，返回包名列表"""
    packages = []
    req_path = Path(req_file)

    if not req_path.exists():
        return None

    with open(req_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            # 跳过空行和注释
            if not line or line.startswith("#"):
                continue

            # 提取包名（去掉版本号）
            # 例如: fastapi==0.109.0 -> fastapi
            #       uvicorn[standard]==0.27.0 -> uvicorn
            pkg_name = line.split("==")[0].split(">=")[0].split("<=")[0].split("~=")[0]
            pkg_name = pkg_name.split("[")[0].strip()  # 去掉 extras，如 [standard]
            packages.append(pkg_name)

    return packages


def check_package_installed(pkg_name):
    """检查单个包是否已安装"""
    try:
        # 特殊处理一些包名映射（pip install 的名字和 import 的名字可能不同）
        import_mapping = {
            "python-multipart": "multipart",
            "python-dotenv": "dotenv",
            "pytest-cov": "pytest_cov",
            "playwright": "playwright",
            "APScheduler": "apscheduler",
            "boto3": "boto3",
            "paramiko": "paramiko",
            "DataRecorder": "DataRecorder",
            "DownloadKit": "DownloadKit",
            "websockets": "websockets",
            "aiofiles": "aiofiles",
        }

        import_name = import_mapping.get(pkg_name, pkg_name)

        __import__(import_name)
        return True
    except (ImportError, ModuleNotFoundError):
        return False


def main():
    # 艹，这个SB脚本找 requirements.txt 的时候路径不对！
    # __file__ 是 backend/scripts/check_deps.py
    # 所以需要往上两级才能找到 backend/requirements.txt
    req_file = Path(__file__).parent.parent / "requirements.txt"

    if not req_file.exists():
        print(f"[ERROR] requirements.txt not found: {req_file}")
        sys.exit(1)

    packages = parse_requirements(req_file)

    if not packages:
        print("[ERROR] No packages found in requirements.txt")
        sys.exit(1)

    # 检查每个包
    missing = []
    for pkg in packages:
        if not check_package_installed(pkg):
            missing.append(pkg)

    if missing:
        print(f"[MISSING] {len(missing)} package(s) not installed:")
        for pkg in missing:
            print(f"  - {pkg}")
        sys.exit(1)
    else:
        print(f"[OK] All {len(packages)} dependencies installed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
