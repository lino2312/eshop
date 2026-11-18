from DrissionPage import Chromium, ChromiumOptions
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(threadName)s] - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rush_buy.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
co = ChromiumOptions()

browser = Chromium(co)
tab = browser.latest_tab

logging.info("开始访问目标URL")

tab.get("https://eshop.hkcsl.com/zh_HK/apple/IP17scol.html")
tab.wait.ele_displayed("xpath=//*[@id='pdpContainer']/div[10]/div[1]/div/div/div[1]/div[1]")
logging.info("程序运行结束")
