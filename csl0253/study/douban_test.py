import requests

url = "https://m.douban.com/rexxar/api/v2/subject/recent_hot/movie"

data = {
    "start":"0",
    "limit":"20"
}
headers = {
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
}

response = requests.get(url, params=data, headers=headers)

print(response.status_code)
print(response.json())
