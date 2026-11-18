import requests
import re
from datetime import datetime

session = requests.Session()

login_page_url = "https://eshop.hkcsl.com/on/demandware.store/Sites-hkt-hk-Site/zh_HK/Login-Show"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
}

login_page = session.get(login_page_url, headers=headers)
csrf_token_match = re.search(r'name="csrf_token"\s+value="([^"]+)"', login_page.text)
if csrf_token_match:
    csrf_token = csrf_token_match.group(1)
    print(f"获取到 CSRF Token: {csrf_token[:50]}...")
else:
    print("未能获取 CSRF Token")
    exit(1)

login_url = "https://eshop.hkcsl.com/on/demandware.store/Sites-hkt-hk-Site/zh_HK/Login-Submit"

data = {
    "dwfrm_cim_emailLogin_email": "leontang2010+97@gmail.com",
    "dwfrm_cim_emailLogin_password": "Freedom1140",
    "csrf_token": csrf_token,
    "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
    "Host": "eshop.hkcsl.com",
    "origin": "https://eshop.hkcsl.com",
    "referer": login_page_url,
    "sec-fetch-mode": "cors",
    "content-type": "application/x-www-form-urlencoded"
}

response = session.post(login_url, data=data, headers=headers)
print(f"状态码: {response.status_code}")
print(response.text)
if response.status_code == 200 and response.json()["csrf"]["token"]:
    print("登录成功")
else:
    print("登录失败")
# 将商品添加到购物车
add_cart_url = "https://eshop.hkcsl.com/on/demandware.store/Sites-hkt-hk-Site/zh_HK/Cart-AddProduct"

add_cart_data = {
    "pid":"4030181scol",
    "quantity":2,
    "options":[]
}

addcart_response = session.post(add_cart_url, headers=headers, data=add_cart_data)
print(f"状态码: {addcart_response.status_code}")
print(addcart_response.text)
if addcart_response.status_code == 200 and addcart_response.json()["quantityTotal"] != 0:
    print("添加成功")
else:
    print("添加失败")
print(addcart_response.cookies)
print(addcart_response.request.cookies)
