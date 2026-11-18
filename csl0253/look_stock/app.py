from flask import Flask, render_template, jsonify, request
import pymysql
from datetime import datetime, timedelta
import threading
import requests

app = Flask(__name__)

# MySQL 数据库配置
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "123qwe",
    "database": "look_stock"
}
color_map = {
    "25": "黑色",
    "962": "白色",
    "16827": "藍色",
    "15121": "薰衣草紫色",
    "31032": "鼠尾草綠色",
    "927": "銀色",
    "31033": "宇宙橙色",
    "31034": "深墨藍色",
}
rom_map = {
    "1025": "256GB",
    "1026": "512GB",
    "1027": "1TB",
    "4697": "2TB",
}


# 商品列表
GOODS_LIST = [
    {"name": "iphone_17", "color": "25", "rom": ["1025", "1026"]},
    {"name": "iphone_17", "color": "962", "rom": ["1025", "1026"]},
    {"name": "iphone_17", "color": "16827", "rom": ["1025", "1026"]},
    {"name": "iphone_17", "color": "15121", "rom": ["1025", "1026"]},
    {"name": "iphone_17", "color": "31032", "rom": ["1025", "1026"]},
    {"name": "iphone_17_pro", "color": "927", "rom": ["1025", "1026", "1027"]},
    {"name": "iphone_17_pro", "color": "31033", "rom": ["1025", "1026", "1027"]},
    {"name": "iphone_17_pro", "color": "31034", "rom": ["1025", "1026", "1027"]},
    {"name": "iphone_17_pro_max", "color": "927", "rom": ["1025", "1026", "1027", "4697"]},
    {"name": "iphone_17_pro_max", "color": "31033", "rom": ["1025", "1026", "1027", "4697"]},
    {"name": "iphone_17_pro_max", "color": "31034", "rom": ["1025", "1026", "1027", "4697"]},
]

# 监控线程控制
monitoring = True

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

    # 创建错误日志表
    create_error_table_sql = """
    CREATE TABLE IF NOT EXISTS error_log (
        id INT AUTO_INCREMENT PRIMARY KEY,
        product_name VARCHAR(50) NOT NULL,
        color_id VARCHAR(20) NOT NULL,
        url VARCHAR(500),
        error_type VARCHAR(50) NOT NULL,
        error_message TEXT NOT NULL,
        status_code INT,
        response_text TEXT,
        error_time DATETIME NOT NULL,
        INDEX idx_error_time (error_time),
        INDEX idx_product_name (product_name),
        INDEX idx_error_type (error_type)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """
    cursor.execute(create_error_table_sql)

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

def save_error_log(product_name, color_id, url, error_type, error_message, status_code=None, response_text=None, error_time=None):
    """保存错误日志到数据库"""
    if error_time is None:
        error_time = datetime.now()

    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        insert_sql = """
        INSERT INTO error_log (product_name, color_id, url, error_type, error_message, status_code, response_text, error_time)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_sql, (product_name, color_id, url, error_type, error_message, status_code, response_text, error_time))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"保存错误日志时出错: {e}")

def get_check_stock(goods_item: dict):
    """检查指定商品的库存情况"""
    name = goods_item["name"]
    color_id_str = goods_item["color"]
    rom_id_str_list = goods_item["rom"]
    res = []
    url = None

    if name == "iphone_17":
        url = f"https://eshop.hkcsl.com/on/demandware.store/Sites-hkt-hk-Site/zh_HK/Product-Variation?dwvar_IP17scol_color={color_id_str}&pid=IP17scol&quantity=1&source=ajax&offerPriceId=hkd-m-Inbase-prices"
    elif name == "iphone_17_pro":
        url = f"https://eshop.hkcsl.com/on/demandware.store/Sites-hkt-hk-Site/zh_HK/Product-Variation?dwvar_IP17__proscol_color={color_id_str}&pid=IP17_proscol&quantity=1&source=ajax&offerPriceId=undefined"
    elif name == "iphone_17_pro_max":
        url = f"https://eshop.hkcsl.com/on/demandware.store/Sites-hkt-hk-Site/zh_HK/Product-Variation?dwvar_IP17__promaxscol_color={color_id_str}&pid=IP17_promaxscol&quantity=1&source=ajax&offerPriceId=undefined"
    else:
        save_error_log(name, color_id_str, "", "UNSUPPORTED_PRODUCT", f"不支持的产品名称: {name}")
        return res

    try:
        response = requests.get(url, timeout=10)

        # 检查HTTP状态码
        if response.status_code != 200:
            error_type = "HTTP_ERROR"
            if response.status_code == 403:
                error_type = "IP_BLOCKED"
            elif response.status_code == 429:
                error_type = "RATE_LIMIT"
            elif response.status_code == 500:
                error_type = "SERVER_ERROR"
            elif response.status_code == 503:
                error_type = "SERVICE_UNAVAILABLE"

            save_error_log(
                name, color_id_str, url, error_type,
                f"HTTP状态码异常: {response.status_code}",
                status_code=response.status_code,
                response_text=response.text[:1000]  # 限制响应文本长度
            )
            return res

        # 尝试解析JSON
        try:
            data = response.json()
        except ValueError as e:
            save_error_log(
                name, color_id_str, url, "JSON_PARSE_ERROR",
                f"无法解析JSON响应: {str(e)}",
                status_code=response.status_code,
                response_text=response.text[:1000]
            )
            return res

        # 检查响应数据结构
        if "product" not in data:
            save_error_log(
                name, color_id_str, url, "INVALID_RESPONSE",
                "响应中缺少 'product' 字段",
                status_code=response.status_code,
                response_text=str(data)[:1000]
            )
            return res

        if "variationAttributes" not in data["product"] or len(data["product"]["variationAttributes"]) < 2:
            save_error_log(
                name, color_id_str, url, "INVALID_RESPONSE",
                "响应中缺少 'variationAttributes' 或结构异常",
                status_code=response.status_code,
                response_text=str(data)[:1000]
            )
            return res

        rom_base = data["product"]["variationAttributes"][1]['values']
        for rom_base_item in rom_base:
            if rom_base_item['id'] in rom_id_str_list:
                res.append({
                    "rom_id": rom_base_item['id'],
                    "in_stock": rom_base_item['selectable']
                })

    except requests.exceptions.Timeout as e:
        save_error_log(name, color_id_str, url, "TIMEOUT", f"请求超时: {str(e)}")
        res = []
    except requests.exceptions.ConnectionError as e:
        save_error_log(name, color_id_str, url, "CONNECTION_ERROR", f"网络连接错误: {str(e)}")
        res = []
    except requests.exceptions.RequestException as e:
        save_error_log(name, color_id_str, url, "REQUEST_ERROR", f"请求错误: {str(e)}")
        res = []
    except KeyError as e:
        save_error_log(name, color_id_str, url, "DATA_STRUCTURE_ERROR", f"响应数据结构错误，缺少字段: {str(e)}")
        res = []
    except Exception as e:
        save_error_log(name, color_id_str, url, "UNKNOWN_ERROR", f"未知错误: {str(e)}")
        res = []

    return res

def monitor_stock():
    """持续监控库存 - 无延迟循环"""
    check_count = 0
    start_time = datetime.now()

    while monitoring:
        check_count += 1
        check_time = datetime.now()

        for goods_item in GOODS_LIST:
            name = goods_item["name"]
            color_id = goods_item["color"]
            res = get_check_stock(goods_item)

            if res:
                for item in res:
                    rom_id = item["rom_id"]
                    in_stock = item["in_stock"]
                    save_to_db(name, color_id, rom_id, in_stock, check_time)
            else:
                print(f"检查失败: {name} | 颜色ID: {color_id}")

        if check_count % 10 == 0:
            print(f"已完成 {check_count} 次检查，当前时间: {check_time.strftime('%H:%M:%S')}")

# Web 路由
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stock')
def get_stock_data():
    """获取库存数据，支持筛选"""
    product = request.args.get('product', '')
    color_id = request.args.get('color_id', '')
    rom_id = request.args.get('rom_id', '')
    in_stock = request.args.get('in_stock', '')
    hours = request.args.get('hours', '24', type=int)
    limit = request.args.get('limit', '1000', type=int)

    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    time_threshold = datetime.now() - timedelta(hours=hours)

    sql = """
    SELECT * FROM stock_history
    WHERE check_time >= %s
    """
    params = [time_threshold]

    if product:
        sql += " AND product_name = %s"
        params.append(product)
    if color_id:
        sql += " AND color_id = %s"
        params.append(color_id)
    if rom_id:
        sql += " AND rom_id = %s"
        params.append(rom_id)
    if in_stock != '':
        sql += " AND in_stock = %s"
        params.append(int(in_stock))

    sql += " ORDER BY check_time DESC LIMIT %s"
    params.append(limit)

    cursor.execute(sql, params)
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(data)

@app.route('/api/stock/summary')
def get_stock_summary():
    """获取库存摘要（最新状态）"""
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    sql = """
    SELECT s.product_name, s.color_id, s.rom_id, s.in_stock, s.check_time as last_check
    FROM stock_history s
    INNER JOIN (
        SELECT product_name, color_id, rom_id, MAX(check_time) as max_time
        FROM stock_history
        WHERE check_time >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
        GROUP BY product_name, color_id, rom_id
    ) latest ON s.product_name = latest.product_name
            AND s.color_id = latest.color_id
            AND s.rom_id = latest.rom_id
            AND s.check_time = latest.max_time
    ORDER BY s.product_name, s.color_id, s.rom_id
    """

    cursor.execute(sql)
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(data)

@app.route('/api/stock/stats')
def get_stock_stats():
    """获取统计数据"""
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    sql = """
    SELECT
        COUNT(*) as total_checks,
        SUM(in_stock) as in_stock_count,
        COUNT(*) - SUM(in_stock) as out_of_stock_count,
        COUNT(DISTINCT product_name) as products,
        COUNT(DISTINCT CONCAT(product_name, '-', color_id, '-', rom_id)) as variants
    FROM stock_history
    WHERE check_time >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
    """

    cursor.execute(sql)
    stats = cursor.fetchone()
    cursor.close()
    conn.close()

    return jsonify(stats)

@app.route('/api/errors')
def get_error_logs():
    """获取错误日志"""
    product = request.args.get('product', '')
    error_type = request.args.get('error_type', '')
    hours = request.args.get('hours', '24', type=int)
    limit = request.args.get('limit', '100', type=int)

    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    time_threshold = datetime.now() - timedelta(hours=hours)

    sql = """
    SELECT * FROM error_log
    WHERE error_time >= %s
    """
    params = [time_threshold]

    if product:
        sql += " AND product_name = %s"
        params.append(product)
    if error_type:
        sql += " AND error_type = %s"
        params.append(error_type)

    sql += " ORDER BY error_time DESC LIMIT %s"
    params.append(limit)

    cursor.execute(sql, params)
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(data)

@app.route('/api/errors/summary')
def get_error_summary():
    """获取错误统计摘要"""
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    sql = """
    SELECT
        COUNT(*) as total_errors,
        error_type,
        COUNT(*) as error_count
    FROM error_log
    WHERE error_time >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
    GROUP BY error_type
    ORDER BY error_count DESC
    """

    cursor.execute(sql)
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(data)

if __name__ == '__main__':
    init_database()

    # 启动监控线程
    monitor_thread = threading.Thread(target=monitor_stock, daemon=True)
    monitor_thread.start()

    # 启动Flask应用
    app.run(debug=True, port=5000, use_reloader=False)
