from DrissionPage import Chromium, ChromiumOptions


co = ChromiumOptions()
# 'normal'：阻塞进程，等待所有资源下载完成（默认）
# 'eager'：DOM 就绪即停止加载
# 'none'：网页连接成功即停止加载
co.set_load_mode('none')
co.incognito(True)
co.no_imgs(False)
co.headless(False)


browser = Chromium(co)
tab = browser.latest_tab
tab.get("https://www.baidu.com")
print(tab.title)
browser.new_tab("https://www.taobao.com")
print(browser.latest_tab.title)
