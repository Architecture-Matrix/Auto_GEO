#!/bin/bash
# ========================================
# AutoGeo Project Launcher (Linux/macOS)
# Maintainer: 老王
# Version: v3.1.0
# Updated: 2026-02-24
# ========================================
#
# 老王备注：
# 这是Linux/macOS版本的启动脚本
# 功能和Windows版本完全一致
#

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

# 清屏
clear

echo -e "${BLUE}"
echo "========================================"
echo "   AutoGeo Launcher v3.1.0"
echo "========================================"
echo -e "${NC}"

# 菜单循环
while true; do
    echo ""
    echo "Please select an option:"
    echo ""
    echo "  [1] Start Backend Service"
    echo "  [2] Start Frontend Electron App"
    echo "  [3] Restart Backend Service"
    echo "  [4] Restart Frontend Service"
    echo "  [5] Cleanup Project"
    echo "  [6] Reset Database (DANGER!)"
    echo "  [7] Exit (Close All Services)"
    echo ""
    echo "========================================"
    echo ""
    read -p "Enter option (1-7): " choice

    case $choice in
        1) start_backend ;;
        2) start_frontend ;;
        3) restart_backend ;;
        4) restart_frontend ;;
        5) cleanup_menu ;;
        6) reset_database ;;
        7) exit_all ;;
        *)
            echo -e "${RED}[ERROR] Invalid option, please try again!${NC}"
            sleep 2
            clear
            ;;
    esac
done

# ========================================
# Start Backend Service
# ========================================
start_backend() {
    echo ""
    echo "========================================"
    echo "   Starting Backend Service"
    echo "========================================"
    echo ""

    # Check if backend is already running
    if lsof -Pi :8001 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}[WARNING] Backend is already running!${NC}"
        echo ""
        read -p "Restart anyway? (Y/N): " override
        if [[ ! "$override" =~ ^[Yy]$ ]]; then
            return
        fi
        echo ""
        echo "Stopping existing backend service..."
        lsof -ti:8001 | xargs kill -9 2>/dev/null || true
        sleep 2
    fi

    # Check backend dependencies
    echo "Checking backend dependencies..."
    if [ ! -f "backend/requirements.txt" ]; then
        echo -e "${RED}[ERROR] backend/requirements.txt not found!${NC}"
        read -p "Press Enter to continue..."
        return
    fi

    # Set PYTHONPATH
    export PYTHONPATH=.

    # Check Python dependencies
    echo "Checking Python dependencies..."
    if ! python -c "import fastapi" 2>/dev/null; then
        echo ""
        echo -e "${YELLOW}[WARNING] Some dependencies are missing!${NC}"
        echo ""
        echo "Installing backend dependencies..."
        echo "This may take a few minutes, please wait..."
        echo ""
        pip install -r backend/requirements.txt
        if [ $? -ne 0 ]; then
            echo ""
            echo -e "${RED}[ERROR] Failed to install dependencies!${NC}"
            echo "Please check your internet connection and try again."
            echo ""
            read -p "Press Enter to continue..."
            return
        fi
        echo ""
        echo -e "${GREEN}[OK] Dependencies installed successfully!${NC}"
        echo ""
    fi

    echo ""
    echo "Starting backend service..."
    echo ""
    echo "  - Backend: http://127.0.0.1:8001"
    echo "  - API Docs: http://127.0.0.1:8001/docs"
    echo ""

    # 在新终端窗口启动（根据系统不同）
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        osascript -e "tell application \"Terminal\" to do script \"cd '$PWD' && PYTHONPATH=. python -m backend.main\"" 2>/dev/null
    else
        # Linux
        if command -v gnome-terminal &> /dev/null; then
            gnome-terminal -- bash -c "cd '$PWD' && PYTHONPATH=. python -m backend.main; exec bash" &
        elif command -v xterm &> /dev/null; then
            xterm -e "cd '$PWD' && PYTHONPATH=. python -m backend.main" &
        else
            # 没有GUI终端，后台运行
            PYTHONPATH=. python -m backend.main &
            echo -e "${GREEN}[OK] Backend started in background (PID: $!)${NC}"
        fi
    fi

    echo ""
    echo -e "${GREEN}[OK] Backend service started!${NC}"
    echo ""
    sleep 2
    clear
}

# ========================================
# Start Frontend Service
# ========================================
start_frontend() {
    echo ""
    echo "========================================"
    echo "   Starting Frontend App"
    echo "========================================"
    echo ""

    # Check if frontend is already running
    if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}[WARNING] Frontend is already running!${NC}"
        echo ""
        read -p "Restart anyway? (Y/N): " override
        if [[ ! "$override" =~ ^[Yy]$ ]]; then
            return
        fi
        echo ""
        echo "Stopping existing frontend service..."
        lsof -ti:5173 | xargs kill -9 2>/dev/null || true
        sleep 2
    fi

    # Check frontend dependencies
    echo "Checking frontend dependencies..."
    if [ ! -f "frontend/package.json" ]; then
        echo -e "${RED}[ERROR] frontend/package.json not found!${NC}"
        read -p "Press Enter to continue..."
        return
    fi

    # Enhanced dependency check
    NEED_INSTALL=0

    # Check 1: node_modules directory
    if [ ! -d "frontend/node_modules" ]; then
        echo -e "${YELLOW}[WARNING] node_modules not found!${NC}"
        NEED_INSTALL=1
    fi

    # Check 2: package-lock.json
    if [ ! -f "frontend/package-lock.json" ]; then
        echo -e "${YELLOW}[WARNING] package-lock.json not found!${NC}"
        NEED_INSTALL=1
    fi

    # Check 3: Electron executable
    if [ -d "frontend/node_modules/electron" ]; then
        if [ "$OSTYPE" == "darwin"* ]; then
            # macOS
            if [ ! -f "frontend/node_modules/electron/dist/Electron.app" ]; then
                echo -e "${YELLOW}[WARNING] Electron executable is missing!${NC}"
                NEED_INSTALL=1
            fi
        else
            # Linux
            if [ ! -f "frontend/node_modules/electron/dist/electron" ]; then
                echo -e "${YELLOW}[WARNING] Electron executable is missing!${NC}"
                NEED_INSTALL=1
            fi
        fi
    fi

    # Check 4: path.txt configuration
    if [ -d "frontend/node_modules/electron" ]; then
        if [ ! -f "frontend/node_modules/electron/path.txt" ]; then
            echo -e "${YELLOW}[WARNING] Electron path.txt is missing!${NC}"
        fi
    fi

    if [ $NEED_INSTALL -eq 1 ]; then
        echo ""
        echo "========================================"
        echo "Installing Frontend Dependencies"
        echo "========================================"
        echo ""
        echo "This may take a few minutes, please wait..."
        echo ""

        cd frontend

        # Clean install
        if [ -d "node_modules" ]; then
            echo "[INFO] Cleaning existing node_modules..."
            rm -rf node_modules
        fi

        echo "[1/2] Running npm install..."
        npm install
        if [ $? -ne 0 ]; then
            echo ""
            echo -e "${RED}[ERROR] npm install failed!${NC}"
            echo "Please check your internet connection and try again."
            echo ""
            cd ..
            read -p "Press Enter to continue..."
            return
        fi

        echo "[2/2] Fixing Electron installation..."
        cd ..
        chmod +x scripts/fix-electron.sh
        ./scripts/fix-electron.sh
        if [ $? -ne 0 ]; then
            echo ""
            echo -e "${YELLOW}[WARNING] Electron fix had issues, but continuing...${NC}"
            echo ""
        fi

        echo ""
        echo -e "${GREEN}[OK] Dependencies installed and fixed successfully!${NC}"
        echo ""
        cd ..
    fi

    # Auto-fix Electron installation
    echo "Checking Electron installation..."
    if [ "$OSTYPE" == "darwin"* ]; then
        # macOS
        if [ -f "frontend/node_modules/electron/dist/Electron.app" ]; then
            if [ ! -f "frontend/node_modules/electron/path.txt" ]; then
                echo ""
                echo -e "${YELLOW}[WARNING] Electron path.txt is missing!${NC}"
                echo ""
                echo "Auto-fixing Electron installation..."
                chmod +x scripts/fix-electron.sh
                ./scripts/fix-electron.sh
                if [ $? -ne 0 ]; then
                    echo ""
                    echo -e "${RED}[ERROR] Failed to fix Electron installation!${NC}"
                    echo ""
                    read -p "Press Enter to continue..."
                    return
                fi
                echo ""
                echo -e "${GREEN}[OK] Electron fixed successfully!${NC}"
                echo ""
            fi
        fi
    else
        # Linux
        if [ -f "frontend/node_modules/electron/dist/electron" ]; then
            if [ ! -f "frontend/node_modules/electron/path.txt" ]; then
                echo ""
                echo -e "${YELLOW}[WARNING] Electron path.txt is missing!${NC}"
                echo ""
                echo "Auto-fixing Electron installation..."
                chmod +x scripts/fix-electron.sh
                ./scripts/fix-electron.sh
                if [ $? -ne 0 ]; then
                    echo ""
                    echo -e "${RED}[ERROR] Failed to fix Electron installation!${NC}"
                    echo ""
                    read -p "Press Enter to continue..."
                    return
                fi
                echo ""
                echo -e "${GREEN}[OK] Electron fixed successfully!${NC}"
                echo ""
            fi
        fi
    fi

    echo ""
    echo "Starting frontend Electron app..."
    echo ""
    echo "  - Frontend: http://127.0.0.1:5173"
    echo ""

    cd frontend

    # 在新终端窗口启动
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        osascript -e "tell application \"Terminal\" to do script \"cd '$PWD' && npm run dev\"" 2>/dev/null
    else
        # Linux
        if command -v gnome-terminal &> /dev/null; then
            gnome-terminal -- bash -c "cd '$PWD' && npm run dev; exec bash" &
        elif command -v xterm &> /dev/null; then
            xterm -e "cd '$PWD' && npm run dev" &
        else
            # 没有GUI终端，后台运行
            npm run dev &
            echo -e "${GREEN}[OK] Frontend started in background (PID: $!)${NC}"
        fi
    fi

    cd ..

    echo ""
    echo -e "${GREEN}[OK] Frontend app started!${NC}"
    echo ""
    sleep 2
    clear
}

# ========================================
# Restart Backend Service
# ========================================
restart_backend() {
    echo ""
    echo "========================================"
    echo "   Restarting Backend Service"
    echo "========================================"
    echo ""

    echo "Stopping backend service..."
    if lsof -ti:8001 >/dev/null 2>&1; then
        lsof -ti:8001 | xargs kill -9 2>/dev/null
        echo -e "${GREEN}[OK] Backend service stopped${NC}"
    else
        echo "[INFO] Backend service was not running"
    fi

    sleep 2
    echo ""
    echo "Starting backend service..."
    echo ""

    start_backend
}

# ========================================
# Restart Frontend Service
# ========================================
restart_frontend() {
    echo ""
    echo "========================================"
    echo "   Restarting Frontend Service"
    echo "========================================"
    echo ""

    echo "Stopping frontend service..."
    if lsof -ti:5173 >/dev/null 2>&1; then
        lsof -ti:5173 | xargs kill -9 2>/dev/null
        echo -e "${GREEN}[OK] Frontend service stopped${NC}"
    else
        echo "[INFO] Frontend service was not running"
    fi

    sleep 2
    echo ""
    echo "Starting frontend service..."
    echo ""

    start_frontend
}

# ========================================
# Cleanup Menu
# ========================================
cleanup_menu() {
    echo ""
    echo "========================================"
    echo "   Cleanup Options"
    echo "========================================"
    echo ""
    echo "  [1] Quick Cleanup (Safe)"
    echo "  [2] Full Cleanup (Aggressive)"
    echo "  [3] Back to Main Menu"
    echo ""
    read -p "Choose cleanup option (1-3): " cleanup_choice

    case $cleanup_choice in
        1) quick_cleanup ;;
        2) full_cleanup ;;
        3) clear; return ;;
        *)
            echo -e "${RED}[ERROR] Invalid option!${NC}"
            sleep 2
            clear
            ;;
    esac
}

quick_cleanup() {
    echo ""
    echo "Performing quick cleanup..."
    echo ""

    echo "Cleaning Python cache..."
    find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
    find backend -name "*.pyc" -delete 2>/dev/null

    echo "Cleaning Vite cache..."
    rm -rf frontend/.vite 2>/dev/null

    echo "Cleaning database temp files..."
    find backend/database -name "*.wal" -delete 2>/dev/null
    find backend/database -name "*.shm" -delete 2>/dev/null

    echo "Cleaning log files..."
    find . -name "*.log" -delete 2>/dev/null

    echo "Cleaning system temp files..."
    find . -name ".DS_Store" -delete 2>/dev/null
    find . -name "Thumbs.db" -delete 2>/dev/null

    echo ""
    echo -e "${GREEN}[OK] Quick cleanup completed!${NC}"
    echo ""
    read -p "Press Enter to continue..."
    clear
}

full_cleanup() {
    echo ""
    echo "WARNING: This will delete node_modules and require reinstallation!"
    echo ""
    read -p "Are you sure? (Y/N): " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        read -p "Press Enter to continue..."
        clear
        return
    fi

    echo ""
    echo "Performing full cleanup..."
    echo ""

    echo "Cleaning Python cache..."
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
    find . -name "*.pyc" -delete 2>/dev/null

    echo "Cleaning frontend..."
    rm -rf frontend/.vite 2>/dev/null
    if [ -d "frontend/node_modules" ]; then
        echo "Removing node_modules (this may take a moment)..."
        rm -rf frontend/node_modules
    fi

    echo "Cleaning database temp files..."
    find backend/database -name "*.wal" -delete 2>/dev/null
    find backend/database -name "*.shm" -delete 2>/dev/null

    echo "Cleaning log files..."
    find . -name "*.log" -delete 2>/dev/null

    echo "Cleaning system temp files..."
    find . -name ".DS_Store" -delete 2>/dev/null
    find . -name "Thumbs.db" -delete 2>/dev/null
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null

    echo ""
    echo -e "${GREEN}[OK] Full cleanup completed!${NC}"
    echo ""
    echo "[IMPORTANT] You need to reinstall dependencies:"
    echo "  - Backend: pip install -r backend/requirements.txt"
    echo "  - Frontend: cd frontend && npm install"
    echo ""
    read -p "Press Enter to continue..."
    clear
}

# ========================================
# Reset Database
# ========================================
reset_database() {
    echo ""
    echo "========================================"
    echo "   Reset Database (DANGER!)"
    echo "========================================"
    echo ""
    echo "WARNING: This will delete all data!"
    echo ""
    read -p "Type 'RESET' to confirm: " confirm
    if [ "$confirm" != "RESET" ]; then
        echo "Cancelled."
        read -p "Press Enter to continue..."
        clear
        return
    fi

    echo ""
    echo "Stopping services..."
    lsof -ti:8001 | xargs kill -9 2>/dev/null || true
    lsof -ti:5173 | xargs kill -9 2>/dev/null || true

    sleep 2

    echo "Deleting database..."
    rm -f backend/database/auto_geo_v3.db
    rm -f backend/database/auto_geo_v3.db-shm
    rm -f backend/database/auto_geo_v3.db-wal

    echo ""
    echo -e "${GREEN}[OK] Database has been reset!${NC}"
    echo ""
    read -p "Press Enter to continue..."
    clear
}

# ========================================
# Exit All
# ========================================
exit_all() {
    echo ""
    echo "Stopping all services..."
    echo ""

    echo "Stopping backend..."
    lsof -ti:8001 | xargs kill -9 2>/dev/null || true

    echo "Stopping frontend..."
    lsof -ti:5173 | xargs kill -9 2>/dev/null || true

    sleep 2

    echo ""
    echo -e "${GREEN}[OK] All services stopped.${NC}"
    echo ""
    sleep 2
    exit 0
}
