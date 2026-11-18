"""
测试使用 Selenium cookies 检查库存（改进版）
增加 Cloudflare 验证等待逻辑
"""
import sys
import os
import time

try:
    import undetected_chromedriver as uc
    USE_UC = True
    print("✓ 使用 undetected_chromedriver")
except ImportError:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.common.by import By
    USE_UC = False
    print("✗ 使用标准 Selenium")

from csl_test.check_stock import get_check_stock

def wait_for_cloudflare(driver, timeout=60):
    """等待 Cloudflare 验证完成"""
    print("⏳ 等待 Cloudflare 验证...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        page_title = driver.title.lower()
        page_source = driver.page_source.lower()
        
        if 'cloudflare' not in page_source and '请稍候' not in page_title and 'just a moment' not in page_source:
            print(f"✅ Cloudflare 验证完成！（耗时 {int(time.time() - start_time)} 秒）")
            return True
        
        elapsed = int(time.time() - start_time)
        if elapsed % 3 == 0:
            print(f"等待中... 已等待 {elapsed} 秒")
        
        time.sleep(2)
    
    print("⚠️ Cloudflare 验证超时")
    return False

def test_with_selenium_cookies():
    """使用 Selenium cookies 测试库存检查"""
    
    print("\n" + "="*60)
    print("测试：使用 Selenium Cookies 检查库存（改进版）")
    print("="*60)
    
    if USE_UC:
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        try:
            driver = uc.Chrome(options=options, version_main=146)
            print("✅ undetected_chromedriver 初始化成功")
        except Exception as e:
            print(f"❌ undetected_chromedriver 失败: {e}")
            return
    else:
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
        print("\n📡 访问商品页面...")
        url = "https://eshop.hkcsl.com/zh_HK/apple/IP17scol.html"
        driver.get(url)
        
        # 等待 Cloudflare 验证完成
        if not wait_for_cloudflare(driver):
            print("❌ Cloudflare 验证失败，无法继续测试")
            return
        
        print(f"\n✅ 当前 URL: {driver.current_url}")
        print(f"✅ 页面标题: {driver.title}")
        
        print("\n🍪 获取浏览器 cookies...")
        selenium_cookies = driver.get_cookies()
        cookies_dict = {cookie['name']: cookie['value'] for cookie in selenium_cookies}
        print(f"✅ 获取到 {len(cookies_dict)} 个 cookies")
        
        # 打印 cookies 名称
        print(f"Cookies 名称: {list(cookies_dict.keys())}")
        
        print("\n🔍 检查库存（使用 cookies）...")
        goods = {
            "name": "iphone_17",
            "color": "15121",  # 薰衣草紫色
            "rom": "1026"      # 512GB
        }
        
        result = get_check_stock(goods, cookies=cookies_dict)
        print(f"\n{'✅' if result else '❌'} 库存检查结果: {result}")
        
        print("\n" + "="*60)
        print("测试完成！")
        print("="*60)
        
        print("\n浏览器将保持打开状态，按 Enter 键关闭...")
        input()
        
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n浏览器将保持打开状态以便调试，按 Enter 键关闭...")
        input()
    
    finally:
        print("\n关闭浏览器...")
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    test_with_selenium_cookies()
