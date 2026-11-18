import requests

cookies = {
    '_gcl_au': '1.1.1933889722.1774744926',
    'utag_main_v_id': '019d370a78ae000f15f7385d57180506f004e06700bd8',
    '_ga': 'GA1.1.885329121.1774744926',
    '_fbp': 'fb.1.1774744943742.668855317130348453',
    '__cq_uuid': 'abpLb44SdA9iwhFI61G766NNGk',
    'cookiesLifeTime': 'hide',
    'dwanonymous_3facd8f6b3e5fa2a260a68a5693dcb4d': 'dg2oYqmov8pibB1a2cSHdU9elA',
    '__cq_bc': '%7B%22bjqd-hkt-hk%22%3A%5B%7B%22id%22%3A%22IP17scol%22%7D%2C%7B%22id%22%3A%22IP17_proscol%22%7D%2C%7B%22id%22%3A%22IP17_promaxscol%22%7D%5D%7D',
    'cqcid': 'dg2oYqmov8pibB1a2cSHdU9elA',
    '__cq_dnt': '0',
    'dw_dnt': '0',
    '_cfuvid': 'UjIqXb2dpE1C7FIJ4ut4OytzRx1rFgVIH_3q.sBy8fc-1776640361424-0.0.1.1-604800000',
    'utag_main__sn': '36',
    'utag_main_ses_id': '1776640366893%3Bexp-session',
    'utag_main_dc_visit': '32',
    'utag_main__ss': '0%3Bexp-session',
    'utag_main_dc_region': 'ap-northeast-1%3Bexp-session',
    'dwsid': 'vcJaj4jVkGKbMjXmTUFRaVvLLk_E3VVCpqXrj9XaRn_oaBm5gmr3OZep2SthkosHxAfuYHnaIl0i-x72Mi5POQ==',
    'dwac_6e56e6f0e1d4cdea57f56efc1e': 'xmuwrSumti5ibY37XhKbDcdBTHC3u0vf1zA%3D|dw-only|00276533||HKD|false|Asia%2FHong%5FKong|true',
    'cquid': 'm2XU6tZZCPsY8XB5sBqhzC+VwTboZ8O1xENL0BEAp7w=|7ccf6886898aa6bb3fd354f16cc2d6601a5d56a8b040f2a5d0c92b20e5721a8c|9ff28d4a63d56deee70a1f94b3ceb779add47b5cf0ee39ed07a99ad8c22a983f',
    'sid': 'Hj9oJ5WjgpdllRi470xFOPg2HOfZq0e3WAI',
    'popupBannerHome': 'hide',
    'utag_main__pn': '7%3Bexp-session',
    'utag_main_dc_event': '17%3Bexp-session',
    '__cq_seg': '0~0.11!1~-0.29!2~-0.40!3~0.56!4~0.21!5~-0.31!6~0.24!7~-0.40!8~-0.18!9~-0.21!f0~3~1!n0~2',
    'utag_main__se': '51%3Bexp-session',
    'utag_main__st': '1776643121136%3Bexp-session',
    '_ga_TCDEZL15X6': 'GS2.1.s1776640366$o44$g1$t1776641343$j60$l0$h0',
}

headers = {
    'accept': '*/*',
    'accept-language': 'zh-CN,zh;q=0.9',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'origin': 'https://eshop.hkcsl.com',
    'priority': 'u=1, i',
    'referer': 'https://eshop.hkcsl.com/on/demandware.store/Sites-hkt-hk-Site/zh_HK/Checkout-Begin?stage=payment',
    'sec-ch-ua': '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
    'x-requested-with': 'XMLHttpRequest',
    # 'cookie': '_gcl_au=1.1.1933889722.1774744926; utag_main_v_id=019d370a78ae000f15f7385d57180506f004e06700bd8; _ga=GA1.1.885329121.1774744926; _fbp=fb.1.1774744943742.668855317130348453; __cq_uuid=abpLb44SdA9iwhFI61G766NNGk; cookiesLifeTime=hide; dwanonymous_3facd8f6b3e5fa2a260a68a5693dcb4d=dg2oYqmov8pibB1a2cSHdU9elA; __cq_bc=%7B%22bjqd-hkt-hk%22%3A%5B%7B%22id%22%3A%22IP17scol%22%7D%2C%7B%22id%22%3A%22IP17_proscol%22%7D%2C%7B%22id%22%3A%22IP17_promaxscol%22%7D%5D%7D; cqcid=dg2oYqmov8pibB1a2cSHdU9elA; __cq_dnt=0; dw_dnt=0; _cfuvid=UjIqXb2dpE1C7FIJ4ut4OytzRx1rFgVIH_3q.sBy8fc-1776640361424-0.0.1.1-604800000; utag_main__sn=36; utag_main_ses_id=1776640366893%3Bexp-session; utag_main_dc_visit=32; utag_main__ss=0%3Bexp-session; utag_main_dc_region=ap-northeast-1%3Bexp-session; dwsid=vcJaj4jVkGKbMjXmTUFRaVvLLk_E3VVCpqXrj9XaRn_oaBm5gmr3OZep2SthkosHxAfuYHnaIl0i-x72Mi5POQ==; dwac_6e56e6f0e1d4cdea57f56efc1e=xmuwrSumti5ibY37XhKbDcdBTHC3u0vf1zA%3D|dw-only|00276533||HKD|false|Asia%2FHong%5FKong|true; cquid=m2XU6tZZCPsY8XB5sBqhzC+VwTboZ8O1xENL0BEAp7w=|7ccf6886898aa6bb3fd354f16cc2d6601a5d56a8b040f2a5d0c92b20e5721a8c|9ff28d4a63d56deee70a1f94b3ceb779add47b5cf0ee39ed07a99ad8c22a983f; sid=Hj9oJ5WjgpdllRi470xFOPg2HOfZq0e3WAI; popupBannerHome=hide; utag_main__pn=7%3Bexp-session; utag_main_dc_event=17%3Bexp-session; __cq_seg=0~0.11!1~-0.29!2~-0.40!3~0.56!4~0.21!5~-0.31!6~0.24!7~-0.40!8~-0.18!9~-0.21!f0~3~1!n0~2; utag_main__se=51%3Bexp-session; utag_main__st=1776643121136%3Bexp-session; _ga_TCDEZL15X6=GS2.1.s1776640366$o44$g1$t1776641343$j60$l0$h0',
}

data = {
    'paymentmethod': 'CARD',
    'agreeterms': 'on',
    'dwfrm_address_regionpicker_region': '',
    'isPickup': 'false',
}

response = requests.post(
    'https://eshop.hkcsl.com/on/demandware.store/Sites-hkt-hk-Site/zh_HK/CheckoutServices-PlaceOrder',
    cookies=cookies,
    headers=headers,
    data=data,
)