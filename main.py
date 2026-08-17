"""
Easy-Web - 数据驱动的Web自动化测试框架 (Master 企业版)

作者：孙文龙 | 许可证：MIT

使用方式:
    python main.py                          # 运行所有测试
    python main.py -t search                # 只运行搜索测试
    python main.py -e playwright            # 使用 Playwright 引擎
    python main.py --headless               # 无头模式
    python main.py --no-website             # 不启动测试网站
"""
import argparse
import sys
import os
import subprocess
import time
import signal
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.config_loader import ConfigLoader
from utils.logger import get_logger


# 全局变量，用于存储网站进程
_website_process = None


def start_website(config: dict) -> bool:
    """
    启动测试网站

    Returns:
        bool: 是否成功启动
    """
    global _website_process

    if not config.get('auto_start_website', False):
        return True

    website_path = config.get('website_path', 'pkg/UITestWebsite/UITestWebsite.exe')
    website_port = config.get('website_port', 5000)

    # 转换为绝对路径
    if not os.path.isabs(website_path):
        website_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), website_path)

    if not os.path.exists(website_path):
        print(f"测试网站不存在: {website_path}")
        print("  请设置 auto_start_website: false 或提供正确的 website_path")
        return False

    print(f"\n启动测试网站: {website_path}")
    print(f"   端口: {website_port}")

    try:
        # 启动网站进程
        _website_process = subprocess.Popen(
            [website_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )

        # 等待网站启动
        print("   等待网站启动...")
        time.sleep(3)

        # 检查进程是否还在运行
        if _website_process.poll() is not None:
            print(f"网站启动失败，退出码: {_website_process.returncode}")
            return False

        print(f"测试网站已启动 (PID: {_website_process.pid})")
        print(f"   访问: http://localhost:{website_port}\n")

        return True

    except Exception as e:
        print(f"启动网站失败: {e}")
        return False


def stop_website():
    """停止测试网站"""
    global _website_process

    if _website_process:
        print("\n停止测试网站...")
        try:
            if os.name == 'nt':
                # Windows 系统
                subprocess.run(
                    ['taskkill', '/F', '/T', '/PID', str(_website_process.pid)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:
                # Linux/Mac 系统
                os.killpg(os.getpgid(_website_process.pid), signal.SIGTERM)

            _website_process.wait(timeout=5)
            print("测试网站已停止")
        except Exception as e:
            print(f"停止网站时出错: {e}")
        finally:
            _website_process = None


def get_allure_cmd(config: dict) -> str:
    """
    获取 Allure 命令行工具路径
    
    优先级:
    1. 配置文件中指定的 allure_path
    2. pkg 内置的 allure
    3. 系统 PATH 中的 allure
    
    Args:
        config: 配置字典
        
    Returns:
        Allure 命令路径
    """
    # 1. 检查配置文件
    allure_path = config.get('allure_path')
    if allure_path:
        allure_path = str(allure_path).strip()
        if allure_path:
            # Windows 下自动添加 .bat 扩展名
            if os.name == 'nt' and not allure_path.lower().endswith('.bat'):
                allure_path_with_ext = allure_path + '.bat'
                if os.path.exists(allure_path_with_ext):
                    print(f"   使用配置的 Allure: {allure_path_with_ext}")
                    return allure_path_with_ext
            
            # 尝试原始路径
            if os.path.exists(allure_path):
                print(f"   使用配置的 Allure: {allure_path}")
                return allure_path
    
    # 2. 检查 pkg 内置版本
    if os.name == 'nt':
        builtin_allure = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pkg/allurec/bin/allure.bat')
    else:
        builtin_allure = 'pkg/allurec/bin/allure'
    
    if os.path.exists(builtin_allure):
        print(f"   使用内置 Allure: {builtin_allure}")
        return builtin_allure
    
    # 3. Fallback 到系统 PATH
    system_allure = 'allure.bat' if os.name == 'nt' else 'allure'
    try:
        result = subprocess.run(
            ['where', system_allure] if os.name == 'nt' else ['which', system_allure],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            path = result.stdout.strip().split('\n')[0]
            print(f"   使用系统 Allure: {path}")
            return system_allure
    except:
        pass
    
    # 4. 都找不到，返回内置路径（会报错但给出明确提示）
    print(f"   未找到 Allure 工具，将尝试使用内置版本")
    return builtin_allure


def generate_allure_report(keep_history: bool = False, config: dict = None):
    """生成 Allure 报告
    
    Args:
        keep_history: 是否保留历史数据（用于趋势分析）
        config: 配置字典
    """
    allure_results_dir = 'allure-results'
    allure_report_dir = 'allure-report'
    allure_history_dir = os.path.join(allure_report_dir, 'history')

    # 获取 Allure 命令
    allure_cmd = get_allure_cmd(config or {})

    if not os.path.exists(allure_results_dir):
        print("未找到测试结果数据")
        return False

    print(f"\n生成 Allure 报告...")

    try:
        # 清理旧报告
        if os.path.exists(allure_report_dir):
            import shutil
            if keep_history and os.path.exists(allure_history_dir):
                # 保留历史数据：先备份 history 目录
                print("   保留历史趋势数据...")
                temp_history = os.path.join(allure_report_dir, '_temp_history')
                if os.path.exists(temp_history):
                    shutil.rmtree(temp_history)
                shutil.copytree(allure_history_dir, temp_history)
                shutil.rmtree(allure_report_dir)
                os.makedirs(allure_report_dir)
                shutil.move(temp_history, allure_history_dir)
            else:
                # 完全清理
                print("   清理历史报告数据...")
                shutil.rmtree(allure_report_dir)

        # 生成报告
        cmd = [
            allure_cmd,
            'generate',
            allure_results_dir,
            '-o', allure_report_dir,
            '--clean'  # 清理输出目录
        ]

        # Windows 下执行 .bat 文件需要 shell=True
        use_shell = os.name == 'nt' and allure_cmd.lower().endswith('.bat')
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            encoding='utf-8', 
            errors='ignore',
            shell=use_shell
        )

        if result.returncode == 0:
            print(f"Allure 报告已生成: {allure_report_dir}/index.html")
            if keep_history:
                print("   ℹ️  提示: 使用 --keep-history 保留了历史数据，可用于趋势分析")
            return True
        else:
            print(f"生成报告失败: {result.stderr}")
            return False

    except Exception as e:
        print(f"生成报告异常: {e}")
        return False


def kill_process_on_port(port: int):
    """
    杀死占用指定端口的进程
    
    Args:
        port: 端口号
    """
    try:
        if os.name == 'nt':
            # Windows: 使用 netstat 查找占用端口的 PID
            result = subprocess.run(
                ['netstat', '-ano'],
                capture_output=True,
                text=True,
                encoding='gbk'  # Windows 中文系统使用 gbk 编码
            )
            
            for line in result.stdout.split('\n'):
                if f':{port}' in line and 'LISTENING' in line:
                    # 提取 PID（最后一列）
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        try:
                            pid = int(pid)
                            print(f"   发现占用端口 {port} 的进程 (PID: {pid})，正在终止...")
                            subprocess.run(
                                ['taskkill', '/F', '/PID', str(pid)],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL
                            )
                            print(f"   已终止进程 {pid}")
                            time.sleep(1)  # 等待端口释放
                            return True
                        except ValueError:
                            continue
        else:
            # Linux/Mac: 使用 lsof 查找占用端口的 PID
            result = subprocess.run(
                ['lsof', '-ti', f':{port}'],
                capture_output=True,
                text=True
            )
            
            if result.stdout.strip():
                pid = result.stdout.strip()
                print(f"   发现占用端口 {port} 的进程 (PID: {pid})，正在终止...")
                subprocess.run(['kill', '-9', pid])
                print(f"   已终止进程 {pid}")
                time.sleep(1)
                return True
        
        return False
    except Exception as e:
        print(f"   清理端口 {port} 时出错: {e}")
        return False


def open_allure_report(config: dict = None):
    """打开 Allure 报告
    
    Args:
        config: 配置字典
    """
    allure_report_dir = 'allure-report'
    allure_port = 5252

    if not os.path.exists(allure_report_dir):
        return

    print(f"\n打开 Allure 报告...")

    try:
        # 获取 Allure 命令
        allure_cmd = get_allure_cmd(config or {})
        
        # 检查端口是否被占用，如果是则先清理
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', allure_port))
        sock.close()
        
        if result == 0:  # 端口被占用
            print(f"   端口 {allure_port} 已被占用，正在清理...")
            kill_process_on_port(allure_port)

        cmd = [
            allure_cmd,
            'open',
            allure_report_dir,
            '-p', str(allure_port)  # 指定端口
        ]

        # Windows 下执行 .bat 文件需要 shell=True
        use_shell = os.name == 'nt' and allure_cmd.lower().endswith('.bat')
        
        # 后台运行
        subprocess.Popen(
            cmd, 
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0,
            shell=use_shell
        )
        print(f"报告已在浏览器中打开 (http://localhost:{allure_port})")

    except Exception as e:
        print(f"打开报告失败: {e}")


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='Easy-Web自动化测试框架 (Master 企业版)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py                              # 运行所有测试
  python main.py -t search                    # 只运行搜索测试
  python main.py -e playwright                # 使用 Playwright 引擎
  python main.py -b chromium                  # 指定浏览器类型
  python main.py --headless                   # 无头模式
  python main.py --no-website                 # 不启动测试网站
  python main.py --no-report                  # 不生成 Allure 报告
  python main.py -d data/test_data.json       # 指定测试数据文件
  python main.py -c config/settings.yaml      # 指定配置文件
        """
    )
    parser.add_argument('--config', '-c', default='config/settings.yaml',
                        help='配置文件路径')
    parser.add_argument('--test', '-t',
                        choices=['search', 'login', 'nav', 'locator', 'workflow', 'all'],
                        default='all',
                        help='测试类型 (按 type 字段过滤)')
    parser.add_argument('--engine', '-e', choices=['selenium', 'playwright'],
                        help='指定自动化引擎 (覆盖配置文件)')
    parser.add_argument('--browser', '-b',
                        help='指定浏览器类型 (覆盖配置文件)')
    parser.add_argument('--headless', action='store_true',
                        help='无头模式运行浏览器')
    parser.add_argument('--no-website', action='store_true',
                        help='不自动启动测试网站')
    parser.add_argument('--no-report', action='store_true',
                        help='不生成 Allure 报告')
    parser.add_argument('--open-report', action='store_true', default=True,
                        help='测试完成后打开报告 (默认开启)')
    parser.add_argument('--keep-history', action='store_true',
                        help='保留历史测试数据（用于趋势分析）')
    parser.add_argument('--data-file', '-d',
                        help='指定测试数据文件路径 (支持 .json / .xlsx)')
    parser.add_argument('--cookie', '-C', action='append',
                        help='注入Cookie (格式: name=value 或 name=value;domain=xxx), 可多次使用')
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    logger = get_logger('Main')

    print("="*60)
    print("  Easy-Web 数据驱动Web自动化测试框架 (Master 企业版)")
    print("  Powered by Pytest + Allure")
    print("="*60)

    # 加载配置
    config = ConfigLoader(args.config).config

    # 命令行参数覆盖配置
    if args.engine:
        config['engine'] = args.engine
    if args.browser:
        config['browser'] = args.browser
    if args.headless:
        config['headless'] = True
    if args.no_website:
        config['auto_start_website'] = False
    
    # 解析 CLI cookie 参数
    cli_cookies = []
    if args.cookie:
        for cookie_str in args.cookie:
            parts = cookie_str.split(';')
            cookie = {}
            for part in parts:
                if '=' in part:
                    key, value = part.split('=', 1)
                    cookie[key.strip()] = value.strip()
            if 'name' in cookie and 'value' in cookie:
                cli_cookies.append(cookie)
        if cli_cookies:
            config['cli_cookies'] = cli_cookies
            print(f"CLI Cookie 注入: {len(cli_cookies)} 个")
            for c in cli_cookies:
                print(f"   {c['name']}={c['value'][:20]}...")

    # 显示配置信息
    print(f"\n配置信息:")
    print(f"   引擎: {config['engine']}")
    print(f"   浏览器: {config['browser']}")
    if config.get('browser_path'):
        print(f"   浏览器路径: {config['browser_path']}")
    if config.get('driver_path'):
        print(f"   驱动路径: {config['driver_path']}")
    print(f"   基础URL: {config.get('base_url', 'N/A')}")
    print()

    # 处理 -t 参数：按 type 过滤数据
    temp_data_file = 'data/_temp.json'
    original_data_file = 'data/test_data.json'
    data_file_to_use = original_data_file

    # 优先使用 -d 指定的数据文件
    if args.data_file:
        data_file_to_use = args.data_file
        if not os.path.isabs(data_file_to_use):
            data_file_to_use = os.path.join(os.path.dirname(os.path.abspath(__file__)), data_file_to_use)
        if os.path.exists(data_file_to_use):
            print(f"使用指定数据文件: {args.data_file}")
        else:
            print(f"数据文件不存在: {args.data_file}，将使用默认文件")
            data_file_to_use = original_data_file
    elif args.test != 'all' and os.path.exists(original_data_file):
        with open(original_data_file, 'r', encoding='utf-8') as f:
            all_data = json.load(f)
        filtered_data = [d for d in all_data if d.get('type') == args.test]
        if filtered_data:
            with open(temp_data_file, 'w', encoding='utf-8') as f:
                json.dump(filtered_data, f, ensure_ascii=False, indent=4)
            data_file_to_use = temp_data_file
            print(f"按类型 '{args.test}' 过滤: {len(filtered_data)}/{len(all_data)} 条用例")
        else:
            print(f"未找到类型为 '{args.test}' 的用例，将运行全部用例")

    # 启动测试网站
    if config.get('auto_start_website', False):
        if not start_website(config):
            print("\n网站启动失败，但将继续尝试运行测试...")
            print("  (可能无法访问测试页面)\n")
            time.sleep(2)

    try:
        # 构建 pytest 参数，传入数据文件路径
        pytest_args = [
            'tests/',
            f'--alluredir=allure-results',
            '-v',
            '-s',
            f'--data-file={data_file_to_use}'  # 自定义 pytest 参数
        ]

        # 运行 pytest
        print("开始执行测试...\n")
        exit_code = __import__('pytest').main(pytest_args)

        # 生成报告
        if not args.no_report:
            generate_allure_report(keep_history=args.keep_history, config=config)

            # 打开报告
            if args.open_report:
                open_allure_report(config=config)

        # 返回状态码
        sys.exit(exit_code)

    finally:
        # 清理临时文件
        if os.path.exists(temp_data_file):
            os.remove(temp_data_file)
        
        # 确保网站被停止
        if config.get('auto_start_website', False):
            stop_website()


if __name__ == '__main__':
    main()
