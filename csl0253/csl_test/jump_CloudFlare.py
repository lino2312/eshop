#!/usr/bin/env python
# -*- coding:utf-8 -*-
# 导入
from DrissionPage import Chromium, ChromiumOptions
import time
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)
# 创建配置对象
co = ChromiumOptions()
co.incognito(True)
# 创建浏览器对象
browser = Chromium(co)
tab = browser.latest_tab
# 访问网页
for i in range(100):
    logger.info(f"第{i}次访问")
    tab.get("https://eshop.hkcsl.com/on/demandware.store/Sites-hkt-hk-Site/zh_HK/Login-Show")
    logger.info(tab.title)
    logger.info(tab.url)
    for j in range(5):
        if "请稍候" in tab.title:
            logger.info("Cloudflareare")
            time.sleep(5)
        else:
            break
    logger.info("开始等待5秒")
    time.sleep(5)
