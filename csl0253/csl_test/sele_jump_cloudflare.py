#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
使用 Selenium 绕过 Cloudflare 验证
仿照 jump_CloudFlare.py 的功能
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s', 
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def create_browser():
    """创建 Chrome 浏览器实例"""
    logger.info("创建浏览器实例...")
    
    # 配置 Chrome 选项
    chrome_options = Options()
    
    # 无痕模式
    chrome_options.add_argument('--incognito')
    
    # 禁用一些可能被检测的功能
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # 设置 User-Agent
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # 其他选项
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    # 创建浏览器实例
    driver = webdriver.Chrome(options=chrome_options)
    
    # 执行 CDP 命令，隐藏 webdriver 属性
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        '''
    })
    
    logger.info("✅ 浏览器创建成功")
    return driver

def check_cloudflare(driver, max_wait=20):
    """
    检查并等待 Cloudflare 验证完成
    
    Args:
        driver: Selenium WebDriver 实例
        max_wait: 最大等待次数（每次 5 秒）
    
    Returns:
        bool: 是否通过验证
    """
    for j in range(max_wait):
        title = driver.title
        if "请稍候" in title or "Just a moment" in title:
            logger.info(f"Cloudflare 验证中 {j}/{max_wait}")
            time.sleep(5)
        else:
            logger.info(f"✅ Cloudflare 验证通过")
            return True
    
    logger.warning(f"⚠️ Cloudflare 验证超时")
    return False

def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("启动 Cloudflare 绕过脚本（Selenium 版本）")
    logger.info("=" * 60)
    
    # 创建浏览器
    driver = create_browser()
    
    try:
        # 访问网页（循环 100 次）
        for i in range(100):
            logger.info(f"第 {i+1} 次访问")
            
            # 访问目标网站
            url = "https://eshop.hkcsl.com/on/demandware.store/Sites-hkt-hk-Site/zh_HK/Login-Show"
            driver.get(url)
            
            # 等待页面加载
            time.sleep(2)
            
            # 打印当前页面信息
            logger.info(f"页面标题: {driver.title}")
            logger.info(f"页面 URL: {driver.current_url}")
            
            # 检查 Cloudflare 验证
            check_cloudflare(driver, max_wait=20)
            
            # 打印验证后的标题
            logger.info(f"验证后标题: {driver.title}")
            
            # 等待 50 秒
            logger.info("开始等待 50 秒...")
            time.sleep(50)
            
    except KeyboardInterrupt:
        logger.info("\n用户中断程序")
    except Exception as e:
        logger.error(f"发生错误: {e}")
    finally:
        # 关闭浏览器
        logger.info("关闭浏览器...")
        driver.quit()
        logger.info("程序结束")

if __name__ == "__main__":
    main()
