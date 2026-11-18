import requests

def get_ip():
    url = "https://white.1024proxy.com/white/api?region=Rand&num=1&time=10&format=1&type=json"
    response = requests.get(url)
    data = response.json()
    print("代理 API 返回:", data)
    
    ip = data[0]["host"]
    port = data[0]["port"]
    user = "vdcy18009"
    pwd = "wereftdu"
    proxies = {
        "http":  f"http://{user}:{pwd}@{ip}:{port}",
        "https": f"http://{user}:{pwd}@{ip}:{port}",
    }
    
    try:
        response = requests.get("https://www.baidu.com", proxies=proxies, timeout=10)
        print("代理 IP:", response.text)
    except Exception as e:
        print(f"代理连接失败: {e}")
        print("\n请检查:")
        print("1. 是否已在代理服务商后台添加当前 IP 到白名单")
        print("2. 代理服务是否有效/未过期")
        print("3. 当前公网 IP:", requests.get("https://httpbin.org/ip", timeout=5).json())

get_ip()
