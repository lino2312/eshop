import requests

cookies = {
    'dwanonymous_3facd8f6b3e5fa2a260a68a5693dcb4d': 'bc5aS1Qt330T6gnY2ahnRjar8A',
    '_gcl_au': '1.1.1092952078.1775602619',
    '_ga': 'GA1.1.1865141494.1775602620',
    'utag_main_v_id': '019d6a29da8a001b1f0e0be21b7d05075003106d00942',
    '__cq_uuid': 'bc5aS1Qt330T6gnY2ahnRjar8A',
    '__cq_bc': '%7B%22bjqd-hkt-hk%22%3A%5B%7B%22id%22%3A%22IP17scol%22%7D%5D%7D',
    'cookiesLifeTime': 'hide',
    'cqcid': 'bc5aS1Qt330T6gnY2ahnRjar8A',
    '__cq_dnt': '0',
    'dw_dnt': '0',
    '_cfuvid': 'IJpNQKrtPwH0F6edLipSUY97MSBQWqskWs.0Xb2C_LI-1776473021874-0.0.1.1-604800000',
    '__cq_seg': '0~0.32!1~-0.45!2~-0.12!3~-0.65!4~0.02!5~-0.02!6~0.08!7~-0.02!8~0.05!9~-0.50',
    'dwsid': '1Ru0N5nVBvOLmf6D8EXFnWVdslvLg0QjI0XE7EKRmX3AhCHhZdpDKf9B9lUEbQ1MOR-gPppqwK75iAkwDL7phQ==',
    'dwac_6e56e6f0e1d4cdea57f56efc1e': 'fdNK8X7YZhl4J9hTt7BEZrCDmg9t6OuEkK8%3D|dw-only|00276533||HKD|false|Asia%2FHong%5FKong|true',
    'cquid': 'm2XU6tZZCPsY8XB5sBqhzC+VwTboZ8O1xENL0BEAp7w=|7ccf6886898aa6bb3fd354f16cc2d6601a5d56a8b040f2a5d0c92b20e5721a8c|9ff28d4a63d56deee70a1f94b3ceb779add47b5cf0ee39ed07a99ad8c22a983f',
    'sid': 'tmHwz0A8wytVw2rY883i8gYn9qMSaoH7_R8',
    'popupBannerHome': 'hide',
    'utag_main__sn': '10',
    'utag_main_ses_id': '1776507872128%3Bexp-session',
    'utag_main_dc_visit': '8',
    'utag_main__ss': '0%3Bexp-session',
    'utag_main_dc_region': 'ap-northeast-1%3Bexp-session',
    'utag_main__pn': '7%3Bexp-session',
    'utag_main_dc_event': '17%3Bexp-session',
    'utag_main__se': '47%3Bexp-session',
    'utag_main__st': '1776509805235%3Bexp-session',
    '_ga_TCDEZL15X6': 'GS2.1.s1776507870$o11$g1$t1776508954$j60$l0$h0',
}

headers = {
    'accept': '*/*',
    'accept-language': 'zh-CN,zh;q=0.9',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'origin': 'https://eshop.hkcsl.com',
    'priority': 'u=1, i',
    'referer': 'https://eshop.hkcsl.com/on/demandware.store/Sites-hkt-hk-Site/zh_HK/Checkout-Begin?stage=payment',
    'sec-ch-ua': '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36',
    'x-requested-with': 'XMLHttpRequest',
    # 'cookie': 'dwanonymous_3facd8f6b3e5fa2a260a68a5693dcb4d=bc5aS1Qt330T6gnY2ahnRjar8A; _gcl_au=1.1.1092952078.1775602619; _ga=GA1.1.1865141494.1775602620; utag_main_v_id=019d6a29da8a001b1f0e0be21b7d05075003106d00942; __cq_uuid=bc5aS1Qt330T6gnY2ahnRjar8A; __cq_bc=%7B%22bjqd-hkt-hk%22%3A%5B%7B%22id%22%3A%22IP17scol%22%7D%5D%7D; cookiesLifeTime=hide; cqcid=bc5aS1Qt330T6gnY2ahnRjar8A; __cq_dnt=0; dw_dnt=0; _cfuvid=IJpNQKrtPwH0F6edLipSUY97MSBQWqskWs.0Xb2C_LI-1776473021874-0.0.1.1-604800000; __cq_seg=0~0.32!1~-0.45!2~-0.12!3~-0.65!4~0.02!5~-0.02!6~0.08!7~-0.02!8~0.05!9~-0.50; dwsid=1Ru0N5nVBvOLmf6D8EXFnWVdslvLg0QjI0XE7EKRmX3AhCHhZdpDKf9B9lUEbQ1MOR-gPppqwK75iAkwDL7phQ==; dwac_6e56e6f0e1d4cdea57f56efc1e=fdNK8X7YZhl4J9hTt7BEZrCDmg9t6OuEkK8%3D|dw-only|00276533||HKD|false|Asia%2FHong%5FKong|true; cquid=m2XU6tZZCPsY8XB5sBqhzC+VwTboZ8O1xENL0BEAp7w=|7ccf6886898aa6bb3fd354f16cc2d6601a5d56a8b040f2a5d0c92b20e5721a8c|9ff28d4a63d56deee70a1f94b3ceb779add47b5cf0ee39ed07a99ad8c22a983f; sid=tmHwz0A8wytVw2rY883i8gYn9qMSaoH7_R8; popupBannerHome=hide; utag_main__sn=10; utag_main_ses_id=1776507872128%3Bexp-session; utag_main_dc_visit=8; utag_main__ss=0%3Bexp-session; utag_main_dc_region=ap-northeast-1%3Bexp-session; utag_main__pn=7%3Bexp-session; utag_main_dc_event=17%3Bexp-session; utag_main__se=47%3Bexp-session; utag_main__st=1776509805235%3Bexp-session; _ga_TCDEZL15X6=GS2.1.s1776507870$o11$g1$t1776508954$j60$l0$h0',
}

data = {
    'paymentMethod': 'CARD',
}

response = requests.post(
    'https://eshop.hkcsl.com/on/demandware.store/Sites-hkt-hk-Site/zh_HK/Checkout-SetPaymentInstrument',
    cookies=cookies,
    headers=headers,
    data=data,
)