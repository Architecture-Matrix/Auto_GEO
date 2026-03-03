#!/usr/bin/env node
/**
 * ========================================
 * AutoGeo Project Launcher (Cross-Platform)
 * Version: v3.1.0
 * Updated: 2026-02-24
 * ========================================
 *
 * 备注：
 * 这是跨平台Node.js版本，支持Windows/Linux/macOS
 * 可以打包成exe运行
 */

const { spawn, execSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

// 获取项目根目录
const PROJECT_ROOT = path.resolve(__dirname, "../..");

// 颜色输出（Windows可能不支持，所以用简单的文本）
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m'
};

// 检测平台
const platform = os.platform();
const isWindows = platform === 'win32';
const isMac = platform === 'darwin';
const isLinux = platform === 'linux';

// 清屏
console.clear();
console.log('');
console.log('========================================');
console.log('   AutoGeo Launcher v3.1.0');
console.log('========================================');
console.log('');

// 主菜单
showMainMenu();

function showMainMenu() {
  const readline = require('readline');
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });

  console.log('');
  console.log('Please select an option:');
  console.log('');
  console.log('  [1] Start Backend Service');
  console.log('  [2] Start Frontend Electron App');
  console.log('  [3] Restart Backend Service');
  console.log('  [4] Restart Frontend Service');
  console.log('  [5] Cleanup Project');
  console.log('  [6] Reset Database (DANGER!)');
  console.log('  [7] Exit (Close All Services)');
  console.log('');
  console.log('========================================');
  console.log('');

  rl.question('Enter option (1-7): ', (answer) => {
    rl.close();
    handleChoice(answer.trim());
  });
}

function handleChoice(choice) {
  switch (choice) {
    case '1':
      startBackend().then(() => showMainMenu());
      break;
    case '2':
      startFrontend().then(() => showMainMenu());
      break;
    case '3':
      restartBackend().then(() => showMainMenu());
      break;
    case '4':
      restartFrontend().then(() => showMainMenu());
      break;
    case '5':
      showCleanupMenu();
      break;
    case '6':
      resetDatabase().then(() => showMainMenu());
      break;
    case '7':
      exitAll();
      break;
    default:
      console.log(colors.red + '[ERROR] Invalid option, please try again!' + colors.reset);
      setTimeout(() => {
        console.clear();
        showMainMenu();
      }, 2000);
  }
}

// 检查端口是否被占用
function isPortInUse(port) {
  return new Promise((resolve) => {
    const command = isWindows
      ? `netstat -ano | findstr ":${port}" | findstr "LISTENING"`
      : isMac
      ? `lsof -Pi :${port} -sTCP:LISTEN -t`
      : `lsof -Pi :${port} -sTCP:LISTEN -t`;

    try {
      const result = execSync(command, { encoding: 'utf8' });
      resolve(result.trim().length > 0);
    } catch (error) {
      resolve(false);
    }
  });
}

// 杀掉占用端口的进程
function killPort(port) {
  return new Promise((resolve) => {
    if (isWindows) {
      execSync(`for /f "tokens=5" %a in ('netstat -ano ^| findstr ":${port}" ^| findstr "LISTENING"') do taskkill /F /PID %a`, { stdio: 'ignore' });
    } else {
      try {
        const pids = execSync(`lsof -ti:${port}`, { encoding: 'utf8' }).trim();
        if (pids) {
          pids.split('\n').forEach(pid => {
            execSync(`kill -9 ${pid}`, { stdio: 'ignore' });
          });
        }
      } catch (error) {
        // 端口没有被占用，忽略错误
      }
    }
    resolve();
  });
}

// 启动后端服务
async function startBackend() {
  console.log('');
  console.log('========================================');
  console.log('   Starting Backend Service');
  console.log('========================================');
  console.log('');

  // 检查后端是否已经在运行
  const backendRunning = await isPortInUse(8001);
  if (backendRunning) {
    console.log(colors.yellow + '[WARNING] Backend is already running!' + colors.reset);
    await askQuestion('Restart anyway? (Y/N): ').then(answer => {
      if (answer.toUpperCase() !== 'Y') {
        return Promise.resolve();
      }
      console.log('');
      console.log('Stopping existing backend service...');
      return killPort(8001).then(() => new Promise(resolve => setTimeout(resolve, 2000)));
    });
  }

  // 检查依赖
  console.log('Checking backend dependencies...');
  if (!fs.existsSync(path.join(PROJECT_ROOT, 'backend/requirements.txt'))) {
    console.log(colors.red + '[ERROR] backend/requirements.txt not found!' + colors.reset);
    return Promise.resolve();
  }

  // 设置PYTHONPATH
  process.env.PYTHONPATH = PROJECT_ROOT;

  // 检查Python依赖
  console.log('Checking Python dependencies...');
  try {
    execSync('python -c "import fastapi"', { stdio: 'ignore' });
  } catch (error) {
    console.log('');
    console.log(colors.yellow + '[WARNING] Some dependencies are missing!' + colors.reset);
    console.log('');
    console.log('Installing backend dependencies...');
    console.log('This may take a few minutes, please wait...');
    console.log('');
    execSync('pip install -r backend/requirements.txt', { stdio: 'inherit', cwd: PROJECT_ROOT });
    console.log('');
    console.log(colors.green + '[OK] Dependencies installed successfully!' + colors.reset);
    console.log('');
  }

  console.log('');
  console.log('Starting backend service...');
  console.log('');
  console.log('  - Backend: http://127.0.0.1:8001');
  console.log('  - API Docs: http://127.0.0.1:8001/docs');
  console.log('');

  // 在新窗口启动
  startProcessInNewWindow(
    'AutoGeo-Backend',
    'python',
    ['-m', 'backend.main'],
    { PYTHONPATH: PROJECT_ROOT }
  );

  console.log('');
  console.log(colors.green + '[OK] Backend service started!' + colors.reset);
  console.log('');
  await sleep(3000);
  console.clear();
  return Promise.resolve();
}

// 启动前端服务
async function startFrontend() {
  console.log('');
  console.log('========================================');
  console.log('   Starting Frontend App');
  console.log('========================================');
  console.log('');

  // 检查前端是否已经在运行
  const frontendRunning = await isPortInUse(5173);
  if (frontendRunning) {
    console.log(colors.yellow + '[WARNING] Frontend is already running!' + colors.reset);
    const answer = await askQuestion('Restart anyway? (Y/N): ');
    if (answer.toUpperCase() !== 'Y') {
      return Promise.resolve();
    }
    console.log('');
    console.log('Stopping existing frontend service...');
    await killPort(5173);
    await new Promise(resolve => setTimeout(resolve, 2000));
  }

  // 检查依赖
  console.log('Checking frontend dependencies...');
  if (!fs.existsSync(path.join(PROJECT_ROOT, 'frontend/package.json'))) {
    console.log(colors.red + '[ERROR] frontend/package.json not found!' + colors.reset);
    return Promise.resolve();
  }

  // 增强的依赖检查
  let needInstall = false;

  // Check 1: node_modules
  if (!fs.existsSync(path.join(PROJECT_ROOT, 'frontend/node_modules'))) {
    console.log(colors.yellow + '[WARNING] node_modules not found!' + colors.reset);
    needInstall = true;
  }

  // Check 2: package-lock.json
  if (!fs.existsSync(path.join(PROJECT_ROOT, 'frontend/package-lock.json'))) {
    console.log(colors.yellow + '[WARNING] package-lock.json not found!' + colors.reset);
    needInstall = true;
  }

  // Check 3: Electron executable
  const electronPath = path.join(PROJECT_ROOT, 'frontend/node_modules/electron');
  if (fs.existsSync(electronPath)) {
    const electronExe = isWindows
      ? path.join(electronPath, 'dist/electron.exe')
      : isMac
      ? path.join(electronPath, 'dist/Electron.app')
      : path.join(electronPath, 'dist/electron');

    if (!fs.existsSync(electronExe)) {
      console.log(colors.yellow + '[WARNING] Electron executable is missing!' + colors.reset);
      needInstall = true;
    }
  }

  // Check 4: path.txt
  if (fs.existsSync(electronPath)) {
    if (!fs.existsSync(path.join(electronPath, 'path.txt'))) {
      console.log(colors.yellow + '[WARNING] Electron path.txt is missing!' + colors.reset);
    }
  }

  if (needInstall) {
    console.log('');
    console.log('========================================');
    console.log('Installing Frontend Dependencies');
    console.log('========================================');
    console.log('');
    console.log('This may take a few minutes, please wait...');
    console.log('');

    const frontendDir = path.join(PROJECT_ROOT, 'frontend');

    // Clean install
    if (fs.existsSync(path.join(frontendDir, 'node_modules'))) {
      console.log('[INFO] Cleaning existing node_modules...');
      fs.rmSync(path.join(frontendDir, 'node_modules'), { recursive: true, force: true });
    }

    console.log('[1/2] Running npm install...');
    try {
      execSync('npm install', { stdio: 'inherit', cwd: frontendDir });
    } catch (error) {
      console.log('');
      console.log(colors.red + '[ERROR] npm install failed!' + colors.reset);
      console.log('Please check your internet connection and try again.');
      return Promise.resolve();
    }

    console.log('[2/2] Fixing Electron installation...');
    try {
      if (isWindows) {
        execSync('scripts\\fix-electron.bat', { stdio: 'inherit', cwd: PROJECT_ROOT });
      } else {
        execSync('./scripts/fix-electron.sh', { stdio: 'inherit', cwd: PROJECT_ROOT });
      }
    } catch (error) {
      console.log('');
      console.log(colors.yellow + '[WARNING] Electron fix had issues, but continuing...' + colors.reset);
      console.log('');
    }

    console.log('');
    console.log(colors.green + '[OK] Dependencies installed and fixed successfully!' + colors.reset);
    console.log('');
  }

  // Auto-fix Electron
  console.log('Checking Electron installation...');
  const electronExe = isWindows
    ? path.join(PROJECT_ROOT, 'frontend/node_modules/electron/dist/electron.exe')
    : isMac
    ? path.join(PROJECT_ROOT, 'frontend/node_modules/electron/dist/Electron.app')
    : path.join(PROJECT_ROOT, 'frontend/node_modules/electron/dist/electron');

  if (fs.existsSync(electronExe)) {
    const pathTxt = path.join(PROJECT_ROOT, 'frontend/node_modules/electron/path.txt');
    if (!fs.existsSync(pathTxt)) {
      console.log('');
      console.log(colors.yellow + '[WARNING] Electron path.txt is missing!' + colors.reset);
      console.log('');
      console.log('Auto-fixing Electron installation...');
      try {
        if (isWindows) {
          execSync('scripts\\fix-electron.bat', { stdio: 'inherit', cwd: PROJECT_ROOT });
        } else {
          execSync('./scripts/fix-electron.sh', { stdio: 'inherit', cwd: PROJECT_ROOT });
        }
        console.log('');
        console.log(colors.green + '[OK] Electron fixed successfully!' + colors.reset);
        console.log('');
      } catch (error) {
        console.log('');
        console.log(colors.red + '[ERROR] Failed to fix Electron installation!' + colors.reset);
        return Promise.resolve();
      }
    }
  } else {
    console.log('[INFO] Electron not found, skipping fix...');
  }

  console.log('');
  console.log('Starting frontend Electron app...');
  console.log('');
  console.log('  - Frontend: http://127.0.0.1:5173');
  console.log('');

  startProcessInNewWindow(
    'AutoGeo-Frontend',
    'npm',
    ['run', 'dev'],
    null,
    path.join(PROJECT_ROOT, 'frontend')
  );

  console.log('');
  console.log(colors.green + '[OK] Frontend app started!' + colors.reset);
  console.log('');
  await sleep(3000);
  console.clear();
  return Promise.resolve();
}

// 重启后端
async function restartBackend() {
  console.log('');
  console.log('========================================');
  console.log('   Restarting Backend Service');
  console.log('========================================');
  console.log('');

  console.log('Stopping backend service...');
  await killPort(8001);
  console.log(colors.green + '[OK] Backend service stopped' + colors.reset);

  await sleep(2000);
  console.log('');
  console.log('Starting backend service...');
  console.log('');

  await startBackend();
}

// 重启前端
async function restartFrontend() {
  console.log('');
  console.log('========================================');
  console.log('   Restarting Frontend Service');
  console.log('========================================');
  console.log('');

  console.log('Stopping frontend service...');
  await killPort(5173);
  console.log(colors.green + '[OK] Frontend service stopped' + colors.reset);

  await sleep(2000);
  console.log('');
  console.log('Starting frontend service...');
  console.log('');

  await startFrontend();
}

// 清理菜单
function showCleanupMenu() {
  const readline = require('readline');
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });

  console.log('');
  console.log('========================================');
  console.log('   Cleanup Options');
  console.log('========================================');
  console.log('');
  console.log('  [1] Quick Cleanup (Safe)');
  console.log('  [2] Full Cleanup (Aggressive)');
  console.log('  [3] Back to Main Menu');
  console.log('');

  rl.question('Choose cleanup option (1-3): ', (answer) => {
    rl.close();
    switch (answer.trim()) {
      case '1':
        quickCleanup().then(() => showMainMenu());
        break;
      case '2':
        fullCleanup().then(() => showMainMenu());
        break;
      case '3':
        console.clear();
        showMainMenu();
        break;
      default:
        console.log(colors.red + '[ERROR] Invalid option!' + colors.reset);
        setTimeout(() => {
          console.clear();
          showMainMenu();
        }, 2000);
    }
  });
}

// 快速清理
async function quickCleanup() {
  console.log('');
  console.log('Performing quick cleanup...');
  console.log('');

  console.log('Cleaning Python cache...');
  cleanupDirectory('backend', /__pycache__/);
  cleanupFiles('backend', /\.pyc$/);

  console.log('Cleaning Vite cache...');
  const viteCache = path.join(PROJECT_ROOT, 'frontend/.vite');
  if (fs.existsSync(viteCache)) {
    fs.rmSync(viteCache, { recursive: true, force: true });
  }

  console.log('Cleaning database temp files...');
  cleanupFiles('backend/database', /\.(wal|shm)$/);

  console.log('Cleaning log files...');
  cleanupFiles('.', /\.log$/);

  console.log('Cleaning system temp files...');
  cleanupFiles('.', /\.(DS_Store|Thumbs\.db)$/);

  console.log('');
  console.log(colors.green + '[OK] Quick cleanup completed!' + colors.reset);
  console.log('');
  await askQuestion('Press Enter to continue...');
  console.clear();
}

// 完全清理
async function fullCleanup() {
  console.log('');
  console.log('WARNING: This will delete node_modules and require reinstallation!');
  console.log('');
  const answer = await askQuestion('Are you sure? (Y/N): ');
  if (answer.toUpperCase() !== 'Y') {
    console.log('Cancelled.');
    await askQuestion('Press Enter to continue...');
    console.clear();
    return;
  }

  console.log('');
  console.log('Performing full cleanup...');
  console.log('');

  console.log('Cleaning Python cache...');
  cleanupDirectory('.', /__pycache__/);
  cleanupFiles('.', /\.pyc$/);

  console.log('Cleaning frontend...');
  const viteCache = path.join(PROJECT_ROOT, 'frontend/.vite');
  if (fs.existsSync(viteCache)) {
    fs.rmSync(viteCache, { recursive: true, force: true });
  }

  const nodeModules = path.join(PROJECT_ROOT, 'frontend/node_modules');
  if (fs.existsSync(nodeModules)) {
    console.log('Removing node_modules (this may take a moment)...');
    fs.rmSync(nodeModules, { recursive: true, force: true });
  }

  console.log('Cleaning database temp files...');
  cleanupFiles('backend/database', /\.(wal|shm)$/);

  console.log('Cleaning log files...');
  cleanupFiles('.', /\.log$/);

  console.log('Cleaning system temp files...');
  cleanupFiles('.', /\.(DS_Store|Thumbs\.db)$/);
  cleanupDirectory('.', /\.pytest_cache/);

  console.log('');
  console.log(colors.green + '[OK] Full cleanup completed!' + colors.reset);
  console.log('');
  console.log('[IMPORTANT] You need to reinstall dependencies:');
  console.log('  - Backend: pip install -r backend/requirements.txt');
  console.log('  - Frontend: cd frontend && npm install');
  console.log('');
  await askQuestion('Press Enter to continue...');
  console.clear();
}

// 重置数据库
async function resetDatabase() {
  console.log('');
  console.log('========================================');
  console.log('   Reset Database (DANGER!)');
  console.log('========================================');
  console.log('');
  console.log('WARNING: This will delete all data!');
  console.log('');
  const answer = await askQuestion("Type 'RESET' to confirm: ");
  if (answer !== 'RESET') {
    console.log('Cancelled.');
    await askQuestion('Press Enter to continue...');
    console.clear();
    return;
  }

  console.log('');
  console.log('Stopping services...');
  await killPort(8001);
  await killPort(5173);

  await sleep(2000);

  console.log('Deleting database...');
  const dbDir = path.join(PROJECT_ROOT, 'backend/database');
  ['auto_geo_v3.db', 'auto_geo_v3.db-shm', 'auto_geo_v3.db-wal'].forEach(file => {
    const dbFile = path.join(dbDir, file);
    if (fs.existsSync(dbFile)) {
      fs.unlinkSync(dbFile);
    }
  });

  console.log('');
  console.log(colors.green + '[OK] Database has been reset!' + colors.reset);
  console.log('');
  await askQuestion('Press Enter to continue...');
  console.clear();
}

// 退出所有
async function exitAll() {
  console.log('');
  console.log('Stopping all services...');
  console.log('');

  console.log('Stopping backend...');
  await killPort(8001);

  console.log('Stopping frontend...');
  await killPort(5173);

  await sleep(2000);

  console.log('');
  console.log(colors.green + '[OK] All services stopped.' + colors.reset);
  console.log('');
  await sleep(2000);
  process.exit(0);
}

// ==================== 工具函数 ====================

function startProcessInNewWindow(title, command, args, env, cwd) {
  cwd = cwd || PROJECT_ROOT;
  env = env || {};

  if (isWindows) {
    // Windows: 在新cmd窗口启动
    // 备注：命令需要正确拼接，env变量+命令+参数
    const envVars = Object.entries(env)
      .map(([k, v]) => `set ${k}=${v}&& `)
      .join('');
    const fullCommand = `${envVars}${command} ${args.join(' ')}`;
    spawn('cmd', ['/k', `cd /d "${cwd}" && ${fullCommand}`], {
      shell: true,
      detached: true,
      stdio: 'ignore'
    });
  } else if (isMac) {
    // macOS: 使用osascript在新终端窗口启动
    const envStr = Object.entries(env)
      .map(([k, v]) => `${k}="${v}"`)
      .join(' ');
    const commandStr = `cd "${cwd}" && ${envStr} ${command} ${args.join(' ')}`;
    execSync(`osascript -e 'tell application "Terminal" to do script "${commandStr}"'`, {
      stdio: 'ignore'
    });
  } else {
    // Linux: 使用gnome-terminal或xterm
    const envStr = Object.entries(env)
      .map(([k, v]) => `${k}="${v}"`)
      .join(' ');
    const commandStr = `cd "${cwd}" && ${envStr} ${command} ${args.join(' ')}`;

    try {
      execSync(`gnome-terminal -- bash -c "${commandStr}; exec bash" &`, {
        stdio: 'ignore'
      });
    } catch (error) {
      try {
        execSync(`xterm -e "${commandStr}" &`, { stdio: 'ignore' });
      } catch (error2) {
        // 没有GUI终端，后台运行
        spawn(command, args, {
          cwd,
          env: { ...process.env, ...env },
          detached: true,
          stdio: 'ignore'
        }).unref();
      }
    }
  }
}

function askQuestion(question) {
  const readline = require('readline');
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });

  return new Promise(resolve => {
    rl.question(question, answer => {
      rl.close();
      resolve(answer);
    });
  });
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function cleanupDirectory(dir, pattern) {
  const fullPath = path.join(PROJECT_ROOT, dir);
  if (!fs.existsSync(fullPath)) return;

  const items = fs.readdirSync(fullPath);
  items.forEach(item => {
    const itemPath = path.join(fullPath, item);
    const stat = fs.statSync(itemPath);

    if (stat.isDirectory()) {
      if (pattern.test(item)) {
        fs.rmSync(itemPath, { recursive: true, force: true });
      } else {
        cleanupDirectory(path.join(dir, item), pattern);
      }
    }
  });
}

function cleanupFiles(dir, pattern) {
  const fullPath = path.join(PROJECT_ROOT, dir);
  if (!fs.existsSync(fullPath)) return;

  const items = fs.readdirSync(fullPath);
  items.forEach(item => {
    if (pattern.test(item)) {
      const itemPath = path.join(fullPath, item);
      if (fs.statSync(itemPath).isFile()) {
        fs.unlinkSync(itemPath);
      }
    }
  });
}
