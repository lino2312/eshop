"""
清理 Chrome 和 ChromeDriver 残留进程
用于解决浏览器初始化失败的问题
"""
import subprocess
import platform
import time
import os
import shutil

def cleanup_chrome():
    """清理所有 Chrome 和 ChromeDriver 进程"""
    print("="*60)
    print("清理 Chrome 和 ChromeDriver 残留进程")
    print("="*60)
    
    system = platform.system()
    
    if system == "Windows":
        print("\n🔍 Windows 系统 - 清理进程...")
        
        # 清理 Chrome 进程
        try:
            result = subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe', '/T'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("✅ 已终止所有 Chrome 进程")
            else:
                print("ℹ️  没有找到 Chrome 进程（可能已经关闭）")
        except Exception as e:
            print(f"⚠️  清理 Chrome 进程时出错: {e}")
        
        # 清理 ChromeDriver 进程
        try:
            result = subprocess.run(['taskkill', '/F', '/IM', 'chromedriver.exe', '/T'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("✅ 已终止所有 ChromeDriver 进程")
            else:
                print("ℹ️  没有找到 ChromeDriver 进程（可能已经关闭）")
        except Exception as e:
            print(f"⚠️  清理 ChromeDriver 进程时出错: {e}")
            
    elif system == "Darwin":
        print("\n🔍 macOS 系统 - 清理进程...")
        
        try:
            subprocess.run(['pkill', '-9', 'Google Chrome'], timeout=10)
            print("✅ 已终止所有 Chrome 进程")
        except:
            print("ℹ️  没有找到 Chrome 进程")
        
        try:
            subprocess.run(['pkill', '-9', 'chromedriver'], timeout=10)
            print("✅ 已终止所有 ChromeDriver 进程")
        except:
            print("ℹ️  没有找到 ChromeDriver 进程")
            
    elif system == "Linux":
        print("\n🔍 Linux 系统 - 清理进程...")
        
        try:
            subprocess.run(['pkill', '-9', 'chrome'], timeout=10)
            print("✅ 已终止所有 Chrome 进程")
        except:
            print("ℹ️  没有找到 Chrome 进程")
        
        try:
            subprocess.run(['pkill', '-9', 'chromedriver'], timeout=10)
            print("✅ 已终止所有 ChromeDriver 进程")
        except:
            print("ℹ️  没有找到 ChromeDriver 进程")
    
    # 清理临时文件
    print("\n🗑️  清理临时文件...")
    
    temp_dirs = []
    
    if system == "Windows":
        temp_dirs = [
            os.path.join(os.environ.get('TEMP', ''), 'scoped_dir*'),
            os.path.join(os.environ.get('TEMP', ''), 'chrome_*'),
        ]
    elif system == "Darwin":
        temp_dirs = [
            '/tmp/.com.google.Chrome.*',
            '/tmp/scoped_dir*',
        ]
    elif system == "Linux":
        temp_dirs = [
            '/tmp/.com.google.Chrome.*',
            '/tmp/scoped_dir*',
        ]
    
    for temp_dir in temp_dirs:
        try:
            import glob
            for dir_path in glob.glob(temp_dir):
                if os.path.exists(dir_path):
                    shutil.rmtree(dir_path, ignore_errors=True)
                    print(f"✅ 已删除: {dir_path}")
        except Exception as e:
            print(f"⚠️  清理临时文件时出错: {e}")
    
    print("\n" + "="*60)
    print("✅ 清理完成！")
    print("="*60)
    print("\n现在可以重新运行程序了：")
    print("  python rush_buy.py")

if __name__ == "__main__":
    cleanup_chrome()
