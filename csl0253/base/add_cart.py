import requests
import time



cookies = {
    'dwanonymous_3facd8f6b3e5fa2a260a68a5693dcb4d': 'bc5aS1Qt330T6gnY2ahnRjar8A',
    '_gcl_au': '1.1.1092952078.1775602619',
    '_ga': 'GA1.1.1865141494.1775602620',
    'utag_main_v_id': '019d6a29da8a001b1f0e0be21b7d05075003106d00942',
    '__cq_uuid': 'bc5aS1Qt330T6gnY2ahnRjar8A',
    '__cq_bc': '%7B%22bjqd-hkt-hk%22%3A%5B%7B%22id%22%3A%22IP17scol%22%7D%5D%7D',
    '__cq_seg': '0~0.31!1~-0.22!2~-0.48!3~-0.26!4~0.34!5~0.14!6~-0.47!7~-0.17!8~0.36!9~0.18',
    'cookiesLifeTime': 'hide',
    'cqcid': 'bc5aS1Qt330T6gnY2ahnRjar8A',
    '__cq_dnt': '0',
    'dw_dnt': '0',
    '_cfuvid': 'IRF3a8wMeFw.mghYa28byXbMcZzLULfNYzQjZfyT96E-1776410328718-0.0.1.1-604800000',
    'utag_main__sn': '5',
    'utag_main_ses_id': '1776422877930%3Bexp-session',
    'utag_main_dc_visit': '4',
    'utag_main__ss': '0%3Bexp-session',
    'utag_main_dc_region': 'ap-northeast-1%3Bexp-session',
    'dwsid': '3hJdxPQkvZXuZBE11bxZ0zMsEJ-qxLhSbo_uONIom2-ZwWz58Z35A9-Ob8DY4Cn9uBCyOvjgXOeZOIQ5Ws4DMw==',
    'dwac_6e56e6f0e1d4cdea57f56efc1e': 'RsYRIHYO9QCCorGeoTm3Rq-JLI7Fj4JQx50%3D|dw-only|00276533||HKD|false|Asia%2FHong%5FKong|true',
    'cquid': 'm2XU6tZZCPsY8XB5sBqhzC+VwTboZ8O1xENL0BEAp7w=|7ccf6886898aa6bb3fd354f16cc2d6601a5d56a8b040f2a5d0c92b20e5721a8c|9ff28d4a63d56deee70a1f94b3ceb779add47b5cf0ee39ed07a99ad8c22a983f',
    'sid': 'ATPSqOFnKXJUCRzxUM0W2-wNn_O_hyy11OI',
    'popupBannerHome': 'hide',
    'utag_main__pn': '5%3Bexp-session',
    '_ga_TCDEZL15X6': 'GS2.1.s1776422877$o5$g1$t1776424484$j9$l0$h0',
    'utag_main__st': '1776426284884%3Bexp-session',
    'utag_main__se': '34%3Bexp-session',
    'utag_main_dc_event': '13%3Bexp-session',
}

headers = {
    'accept': '*/*',
    'accept-language': 'zh-CN,zh;q=0.9',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'origin': 'https://eshop.hkcsl.com',
    'priority': 'u=1, i',
    'referer': 'https://eshop.hkcsl.com/zh_HK/apple/IP17scol.html',
    'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
    'x-requested-with': 'XMLHttpRequest',
}

data = {
    'pid': '4030131scol',
    'quantity': '2',
    'options': '[]',
}

def get_pid(goods_choice, color, storage):
    """
    根据用户选择的商品、颜色和存储容量返回对应的pid
    """
    pid = ''
    if goods_choice == "3":
        if color == "25":
            if storage == "1025":
                pid = '4030131scol'
            elif storage == "1026":
                pid = '4030181scol'
        elif color == "962":
            if storage == "1025":
                pid = '4030141scol'
            elif storage == "1026":
                pid = '4030191scol'
        elif color == "16827":
            if storage == "1025":
                pid = '4030151scol'
            elif storage == "1026":
                pid = '4030201scol'
        elif color == "15121":
            if storage == "1025":
                pid = '4030161scol'
            elif storage == "1026":
                pid = '4030211scol'
        elif color == "31032":
            if storage == "1025":
                pid = '4030171scol'
            elif storage == "1026":
                pid = '4030221scol'
    elif goods_choice == "2":
        if color == "927":
            if storage == "1025":
                pid = '4030351scol'
            elif storage == "1026":
                pid = '4030381scol'
            elif storage == "1027":
                pid = '4030411scol'
        elif color == "31033":
            if storage == "1025":
                pid = '4030361scol'
            elif storage == "1026":
                pid = '4030391scol'
            elif storage == "1027":
                pid = '4030421scol'
        elif color == "31034":
            if storage == "1025":
                pid = '4030371scol'
            elif storage == "1026":
                pid = '4030401scol'
            elif storage == "1027":
                pid = '4030431scol'
    elif goods_choice == "1":
        if color == "927":
            if storage == "1025":
                pid = '4030011scol'
            elif storage == "1026":
                pid = '4030041scol'
            elif storage == "1027":
                pid = '4030071scol'
            elif storage == "4697":
                pid = '4030101scol'
        elif color == "31033":
            if storage == "1025":
                pid = '4030021scol'
            elif storage == "1026":
                pid = '4030051scol'
            elif storage == "1027":
                pid = '4030081scol'
            elif storage == "4697":
                pid = '4030111scol'
        elif color == "31034":
            if storage == "1025":
                pid = '4030031scol'
            elif storage == "1026":
                pid = '4030061scol'
            elif storage == "1027":
                pid = '4030091scol'
            elif storage == "4697":
                pid = '4030121scol'
    if pid == '':
        print("未找到对应的pid")
        input("请检查输入的参数是否正确")
    return pid

def base_add_cart(tab, goods_choice, color, storage):
    """
    使用 DrissionPage Tab 获取 cookies 并添加购物车
    
    Args:
        tab: DrissionPage Tab 实例
        goods_choice: 用户选择的商品的标号
        color: 颜色值
        storage: 存储容量值
    
    Returns:
        int: HTTP 状态码
    """
    cookies_dict = tab.cookies()
    cookies = {cookie['name']: cookie['value'] for cookie in cookies_dict}
    
    pid = get_pid(goods_choice, color, storage)
    
    data['pid'] = pid
    response = requests.post(
        'https://eshop.hkcsl.com/on/demandware.store/Sites-hkt-hk-Site/zh_HK/Cart-AddProduct',
        cookies=cookies,
        headers=headers,
        data=data,
    )
    print(f"加购物车ztm: {response.status_code}")
    return response.status_code
