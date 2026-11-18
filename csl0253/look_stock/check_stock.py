# 检查是否有库存 - 持续监控并保存到MySQL数据库

import requests
import time
import pymysql
from datetime import datetime

# MySQL 数据库配置
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "123qwe",
    "database": "look_stock"
}

# 全局变量
proxies = None
interval_seconds = 30  # 查询间隔时间（秒）

# 初始化数据库
def init_database():
    """创建数据库和表"""
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # 创建库存历史记录表
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS stock_history (
        id INT AUTO_INCREMENT PRIMARY KEY,
        product_name VARCHAR(50) NOT NULL,
        color_id VARCHAR(20) NOT NULL,
        rom_id VARCHAR(20) NOT NULL,
        in_stock TINYINT(1) NOT NULL,
        check_time DATETIME NOT NULL,
        INDEX idx_product_color_rom (product_name, color_id, rom_id),
        INDEX idx_check_time (check_time)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """
    cursor.execute(create_table_sql)
    conn.commit()
    cursor.close()
    conn.close()
    print("数据库初始化完成")

def save_to_db(product_name, color_id, rom_id, in_stock, check_time):
    """保存库存记录到数据库"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()

        insert_sql = """
        INSERT INTO stock_history (product_name, color_id, rom_id, in_stock, check_time)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(insert_sql, (product_name, color_id, rom_id, in_stock, check_time))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"保存到数据库时出错: {e}")

def get_check_stock(goods_item: dict):
    """检查指定商品的库存情况"""
    global proxies
    name = goods_item["name"]
    color_id_str = goods_item["color"]
    rom_id_str_list = goods_item["rom"]
    res = []

    if name == "iphone_17":
        url = f"https://eshop.hkcsl.com/on/demandware.store/Sites-hkt-hk-Site/zh_HK/Product-Variation?dwvar_IP17scol_color={color_id_str}&pid=IP17scol&quantity=1&source=ajax&offerPriceId=hkd-m-Inbase-prices"
    elif name == "iphone_17_pro":
        url = f"https://eshop.hkcsl.com/on/demandware.store/Sites-hkt-hk-Site/zh_HK/Product-Variation?dwvar_IP17__proscol_color={color_id_str}&pid=IP17_proscol&quantity=1&source=ajax&offerPriceId=undefined"
    elif name == "iphone_17_pro_max":
        url = f"https://eshop.hkcsl.com/on/demandware.store/Sites-hkt-hk-Site/zh_HK/Product-Variation?dwvar_IP17__promaxscol_color={color_id_str}&pid=IP17_promaxscol&quantity=1&source=ajax&offerPriceId=undefined"
    else:
        print(f"不支持的产品名称: {name}")
        return res

    try:
        response = requests.get(url)
        rom_base = response.json()["product"]["variationAttributes"][1]['values']
        for rom_base_item in rom_base:
            if rom_base_item['id'] in rom_id_str_list:
                res.append({
                    "rom_id": rom_base_item['id'],
                    "in_stock": rom_base_item['selectable']
                })
    except Exception as e:
        print(f"检查库存时出错: {e}")
        res = []

    return res

def monitor_stock():
    """持续监控库存"""
    goods_list = [
        {
            "name": "iphone_17",
            "color": "25",
            "rom": ["1025", "1026"],
        },
        {
            "name": "iphone_17",
            "color": "962",
            "rom": ["1025", "1026"],
        },
        {
            "name": "iphone_17",
            "color": "16827",
            "rom": ["1025", "1026"],
        },
        {
            "name": "iphone_17",
            "color": "15121",
            "rom": ["1025", "1026"],
        },
        {
            "name": "iphone_17",
            "color": "31032",
            "rom": ["1025", "1026"],
        },
    ]

    print(f"开始监控库存，每 {interval_seconds} 秒检查一次...")
    print("按 Ctrl+C 停止程序")

    check_count = 0
    start_time = datetime.now()

    try:
        while True:
            check_count += 1
            check_time = datetime.now()
            print(f"\n[{check_time.strftime('%Y-%m-%d %H:%M:%S')}] 第 {check_count} 次检查")

            for goods_item in goods_list:
                name = goods_item["name"]
                color_id = goods_item["color"]

                res = get_check_stock(goods_item)

                if res:
                    for item in res:
                        rom_id = item["rom_id"]
                        in_stock = item["in_stock"]

                        # 保存到数据库
                        save_to_db(name, color_id, rom_id, in_stock, check_time)

                        # 打印结果
                        stock_status = "有库存" if in_stock else "无库存"
                        print(f"  {name} | 颜色ID: {color_id} | ROM: {rom_id} | {stock_status}")
                else:
                    print(f"  {name} | 颜色ID: {color_id} | 检查失败")

            print(f"等待 {interval_seconds} 秒后进行下一次检查...")
            time.sleep(interval_seconds)

    except KeyboardInterrupt:
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        print(f"\n\n监控已停止")
        print(f"总共运行时间: {total_time:.2f} 秒")
        print(f"总共检查次数: {check_count} 次")

if __name__ == "__main__":
    # 初始化数据库
    init_database()

    # 开始监控
    monitor_stock()
