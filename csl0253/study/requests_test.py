import requests

url = 'https://www.baidu.com'
response = requests.get(url)
response.encoding = 'utf-8'
print(response.status_code)
print(response.text)