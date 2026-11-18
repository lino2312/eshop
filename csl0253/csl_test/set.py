class goods_color:
    # 初始化的时候，需要指定颜色名字， id
    def __init__(self, name, id_str):
        self.name = name
        self.id_str = id_str

class goods_rom:
    def __init__(self, name, id_str):
        self.name = name
        self.id_str = id_str

class iphone_17:
    name = "iphone_17"
    url = "https://eshop.hkcsl.com/zh_HK/apple/IP17scol.html"
    黑色 = goods_color("黑色", "25")
    白色 = goods_color("白色", "962")
    藍色   = goods_color("藍色", "16827")
    薰衣草紫色 = goods_color("薰衣草紫色", "15121")
    鼠尾草綠色 = goods_color("鼠尾草綠色", "31032")
    rom256 = goods_rom("256GB", "1025")
    rom512 = goods_rom("512GB", "1026")

class iphone_17_pro:
    name = "iphone_17_pro"
    url = "https://eshop.hkcsl.com/zh_HK/apple/iPhone/IP17_proscol.html"
    銀色 = goods_color("銀色", "927")
    宇宙橙色 = goods_color("宇宙橙色", "31033")
    深墨藍色 = goods_color("深墨藍色", "31034")
    rom256 = goods_rom("256GB", "1025")
    rom512 = goods_rom("512GB", "1026")
    rom1tb = goods_rom("1TB", "1027")

class iphone_17_pro_max:
    name = "iphone_17_pro_max"
    url = "https://eshop.hkcsl.com/zh_HK/apple/iPhone/IP17_promaxscol.html"
    銀色 = goods_color("銀色", "927")
    宇宙橙色 = goods_color("宇宙橙色", "31033")
    深墨藍色 = goods_color("深墨藍色", "31034")
    rom256 = goods_rom("256GB", "1025")
    rom512 = goods_rom("512GB", "1026")
    rom1tb = goods_rom("1TB", "1027")
    rom2tb = goods_rom("2TB", "4697")



ACCOUNTS = {
        # "email": "leontang2010+97@gmail.com",
        "email": "leontang2010+97@gmail.com",
        "password": "Freedom1140",
    }
# GOODS = {"name": iphone_17.name, "color": iphone_17.白色, "rom": iphone_17.rom256}
GOODS = {"name": iphone_17_pro_max.name, "color": iphone_17_pro_max.銀色, "rom": iphone_17_pro_max.rom256}

LOGIN_URL = "https://eshop.hkcsl.com/on/demandware.store/Sites-hkt-hk-Site/zh_HK/Login-Show"

CHECK_INTERVAL = 0.1

PORT = 9223