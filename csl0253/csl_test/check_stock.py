# 检查是否有库存

import requests
import json

proxies = None
user_proxies = False

def get_proxy():
    url = "https://white.1024proxy.com/white/api?region=HK&num=1&format=1&type=json"
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
    return proxies

def get_check_stock(goods_item: dict, cookies=None):
    """
    检查商品库存
    
    Args:
        goods_item: 商品信息字典，包含 name, color, rom
        cookies: 可选的 cookies 字典
    
    Returns:
        bool: 是否有库存
    """
    global proxies, user_proxies
    name = goods_item["name"]
    color_id_str = goods_item["color"]
    rom_id_str = goods_item["rom"]
    res = False
    '''
    https://eshop.hkcsl.com/on/demandware.store/Sites-hkt-hk-Site/zh_HK/Product-Variation?dwvar_IP17scol_color=25&pid=IP17scol&quantity=1&source=ajax&offerPriceId=online-price
    '''
    if name == "iphone_17":
        url = f"https://eshop.hkcsl.com/on/demandware.store/Sites-hkt-hk-Site/zh_HK/Product-Variation?dwvar_IP17scol_color={color_id_str}&pid=IP17scol&quantity=1&source=ajax&offerPriceId=online-price"
    elif name == "iphone_17_pro":
        url = f"https://eshop.hkcsl.com/on/demandware.store/Sites-hkt-hk-Site/zh_HK/Product-Variation?dwvar_IP17__proscol_color={color_id_str}&pid=IP17_proscol&quantity=1&source=ajax&offerPriceId=undefined"
    elif name == "iphone_17_pro_max":
        url = f"https://eshop.hkcsl.com/on/demandware.store/Sites-hkt-hk-Site/zh_HK/Product-Variation?dwvar_IP17__promaxscol_color={color_id_str}&pid=IP17_promaxscol&quantity=1&source=ajax&offerPriceId=undefined"
    else:
        return res
    
    try:
        print(f"开始检查库存: {name}, 颜色: {color_id_str}, 内存: {rom_id_str}")
        
        headers = {
            'accept': '*/*',
            'accept-language': 'zh-CN,zh;q=0.9',
            'priority': 'u=1, i',
            'referer': 'https://eshop.hkcsl.com/zh_HK/apple/IP17scol.html',
            'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
            'sec-ch-ua-arch': '"x86"',
            'sec-ch-ua-bitness': '"64"',
            'sec-ch-ua-full-version': '"146.0.7680.80"',
            'sec-ch-ua-full-version-list': '"Chromium";v="146.0.7680.80", "Not-A.Brand";v="24.0.0.0", "Google Chrome";v="146.0.7680.80"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-model': '""',
            'sec-ch-ua-platform': '"Windows"',
            'sec-ch-ua-platform-version': '"10.0.0"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
        }
        
        if proxies is None and user_proxies:
            proxies = get_proxy()
        
        if user_proxies:
            response = requests.get(url, headers=headers, proxies=proxies, cookies=cookies, timeout=10)
        else:
            response = requests.get(url, headers=headers, cookies=cookies, timeout=10)
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容前100字符: {response.text[:100]}")
        
        if response.status_code != 200:
            print(f"请求失败，状态码: {response.status_code}")
            return False
        
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            print(f"JSON 解析失败: {e}")
            print(f"响应内容: {response.text[:500]}")
            return False
        
        if "product" not in data:
            print(f"响应中没有 product 字段: {data}")
            return False
        
        if "variationAttributes" not in data["product"]:
            print(f"响应中没有 variationAttributes 字段")
            return False
        
        rom_base = data["product"]["variationAttributes"][1]['values']
        
        for rom_base_item in rom_base:
            if rom_base_item['id'] == rom_id_str:
                res = rom_base_item.get('selectable', False)
                print(f"找到目标内存 {rom_id_str}, 可选状态: {res}")
                break
        
        if not any(rom_base_item['id'] == rom_id_str for rom_base_item in rom_base):
            print(f"未找到目标内存 ID: {rom_id_str}")
            print(f"可用的内存 ID: {[item['id'] for item in rom_base]}")
        
    except requests.exceptions.Timeout:
        print(f"检查库存超时")
        if user_proxies:
            proxies = get_proxy()
        res = False
    except requests.exceptions.RequestException as e:
        print(f"网络请求错误: {e}")
        if user_proxies:
            proxies = get_proxy()
        res = False
    except Exception as e:
        print(f"检查库存时出错: {e}")
        import traceback
        traceback.print_exc()
        if user_proxies:
            proxies = get_proxy()
        res = False
    
    return res


if __name__ == "__main__":
    goods = {
        "name": "iphone_17",
        "color": "15121",
        "rom": "1026"
    }
    result = get_check_stock(goods)
    print(f"库存检查结果: {result}")
