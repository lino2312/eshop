import requests

url = "https://fanyi.baidu.com/sug"
data = {
    "kw": input("请输入一个单词：")
}
response = requests.post(url, data= data)
response.encoding = 'utf-8'
print(response.status_code)
print(response.json())