from selenium.webdriver import Chrome
from selenium.webdriver.chrome.service import Service


# web = Chrome(service=Service(executable_path='./chromedriver.exe'))
web = Chrome()
web.get('https://www.baidu.com')
print(web.title)
