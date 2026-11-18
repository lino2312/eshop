import requests

content = input('请输入搜索内容：')



url = f"https://www.sogou.com/web?query={content}&_asf=www.sogou.com&_ast=&w=01019900&p=40040100&ie=utf8&from=index-nologin&s_from=index&sourceid=9_01_03&sessiontime=1774660771231"
headers = {
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
}
response = requests.get(url,headers=headers)
response.encoding = 'utf-8'
# print(response.status_code)
# print(response.text)
print(response.request.headers)
