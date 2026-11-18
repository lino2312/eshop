"""
测试 Cloudflare 验证处理
用于验证 undetected_chromedriver 和 Cloudflare 验证是否正常工作
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import undetected_chromedriver as uc
    USE_UC = True
    print("✓ 检测到 undetected_chromedriver")
except ImportError:
    USE_UC = False
    print("✗ 未检测到 undetected_chromedriver，将使用标准 Selenium")

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def test_cloudflare_bypass():
    """测试 Cloudflare 验证绕过"""
    
    print("\n" + "="*60)
    print("Cloudflare 验证测试")
    print("="*60)
    
    if USE_UC:
        print("\n🚀 使用 undetected_chromedriver（推荐）")
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        try:
            driver = uc.Chrome(options=options, version_main=None)
            print("✅ undetected_chromedriver 初始化成功")
        except Exception as e:
            print(f"❌ undetected_chromedriver 初始化失败: {e}")
            print("回退到标准 Selenium...")
            USE_UC_FALLBACK = True
    else:
        print("\n🔧 使用标准 Selenium")
        options = Options()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
            """
        })
        print("✅ 标准 Selenium 初始化成功")
    
    try:
        print("\n📡 访问登录页面...")
        login_url = "https://eshop.hkcsl.com/on/demandware.store/Sites-hkt-hk-Site/zh_HK/Login-Show"
        driver.get(login_url)
        
        print("⏳ 等待页面加载...")
        time.sleep(3)
        
        page_source = driver.page_source.lower()
        page_title = driver.title.lower()
        
        if 'cloudflare' in page_source or '请稍候' in page_source or 'just a moment' in page_source:
            print("\n⚠️  检测到 Cloudflare 验证")
            print("等待验证通过...")
            
            max_wait = 60
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                time.sleep(2)
                page_source = driver.page_source.lower()
                
                if 'cloudflare' not in page_source and '请稍候' not in page_source and 'just a moment' not in page_source:
                    elapsed = int(time.time() - start_time)
                    print(f"\n✅ Cloudflare 验证已通过！（耗时 {elapsed} 秒）")
                    break
                
                elapsed = int(time.time() - start_time)
                if elapsed % 5 == 0:
                    print(f"等待中... 已等待 {elapsed} 秒")
            else:
                print("\n⚠️  等待超时，可能需要手动完成验证")
        else:
            print("\n✅ 未检测到 Cloudflare 验证，页面加载成功")
        
        print(f"\n📍 当前 URL: {driver.current_url}")
        print(f"📄 页面标题: {driver.title}")
        
        print("\n" + "="*60)
        print("✅ 测试完成！")
        print("="*60)
        print("\n浏览器将保持打开状态，你可以手动检查页面...")
        print("按 Enter 键关闭浏览器...")
        input()
        
    except Exception as e:
        print(f"\n❌ 测试过程出错: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n浏览器将保持打开状态以便调试...")
        print("按 Enter 键关闭浏览器...")
        input()
    
    finally:
        print("\n关闭浏览器...")
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    test_cloudflare_bypass()
