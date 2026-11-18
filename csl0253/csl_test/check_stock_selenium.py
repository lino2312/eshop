# 检查是否有库存（使用 DrissionPage）
import time
from DrissionPage import Chromium, ChromiumOptions

# 监控时捕获到的最后一次 Product-Variation 请求完整 URL（含真实 dwvar_ 参数名），
# 供 API 加购快速通道构造带内存参数的查询 URL 使用
LAST_VARIATION_URL = None

def check_stock_with_selenium(tab, goods_item: dict):
    """
    使用 DrissionPage 直接在页面上检查库存
    
    Args:
        tab: DrissionPage Tab 实例
        goods_item: 商品信息字典，包含 name, color, rom
    
    Returns:
        bool: 是否有库存
    """
    
    name = goods_item["name"]
    color_id_str = goods_item["color"]
    rom_id_str = goods_item["rom"]
    
    try:
        print(f"🔍 开始检查库存: {name}, 颜色: {color_id_str}, 内存: {rom_id_str}")
        
        time.sleep(2)
        
        try:
            storage_select = tab.ele("tag:select@@class=select-storage@@data-attr=select-storage@@class=select-internal_storage_rom", timeout=5)
            
            if storage_select:
                options = storage_select.eles("tag:option")
                
                for option in options:
                    data_id = option.attr("data-id") or ""
                    data_attr_value = option.attr("data-attr-value") or ""
                    option_text = option.text.strip()
                    
                    if data_id == rom_id_str or data_attr_value == rom_id_str:
                        is_disabled = option.attr("disabled")
                        is_selectable = "售罄" not in option_text and "無貨" not in option_text and is_disabled is None
                        
                        print(f"✅ 找到目标内存: {option_text}, 可选: {is_selectable}")
                        return is_selectable
                
                print(f"❌ 未找到目标内存 ID: {rom_id_str}")
                return False
            
        except Exception as e:
            print(f"⚠️ 使用 select 方式查找失败: {e}")
        
        try:
            select_items = tab.eles(".select-items")
            if len(select_items) >= 2:
                memory_items = select_items[1]
                memory_options = memory_items.eles("tag:div")[1:]
                
                for option_div in memory_options:
                    value_span = option_div.ele(".value", timeout=1)
                    if value_span:
                        option_text = value_span.text.strip()
                        data_attr_value = value_span.attr("data-attr-value")
                        
                        if data_attr_value == rom_id_str:
                            is_selectable = "售罄" not in option_text and "無貨" not in option_text
                            print(f"✅ 找到目标内存: {option_text}, 可选: {is_selectable}")
                            return is_selectable
                
                print(f"❌ 未找到目标内存 ID: {rom_id_str}")
                return False
                
        except Exception as e:
            print(f"⚠️ 使用自定义下拉方式查找失败: {e}")
        
        print("❌ 无法找到内存选项元素")
        return False
        
    except Exception as e:
        print(f"❌ 检查库存时出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_stock_with_selenium2(tab, goods_item: dict):
    """
    使用 DrissionPage 直接在页面上检查库存
    Args:
        tab: DrissionPage Tab 实例
        goods_item: 商品信息字典，包含 name, color, rom
    Returns:
        bool: 是否有库存
    """
    global LAST_VARIATION_URL
    body = None
    name = goods_item["name"]
    color_id_str = goods_item["color"]
    rom_id_str = goods_item["rom"]
    
    try:
        # time.sleep(2)
        color_option = tab.ele(f"tag:option@@data-id={color_id_str}")
        # color_option2 = tab.ele(f"tag:span@@data-attr-value={color_id_str}")
        if color_option:
            tab.listen.start('on/demandware.store/Sites-hkt-hk-Site/zh_HK/Product-Variation')  # 开始监听，指定获取包含该文本的数据包
            # print("点击颜色选项")
            js_code = f'''
            (function() {{
                var select = document.querySelector('select.select-color, select[data-attr="select-color"]');
                if (select) {{
                    var options = select.querySelectorAll('option');
                    for (var i = 0; i < options.length; i++) {{
                        var opt = options[i];
                        if (opt.getAttribute('data-id') === '{color_id_str}' || opt.getAttribute('data-attr-value') === '{color_id_str}') {{
                            opt.selected = true;
                            var event = new Event('change', {{ bubbles: true }});
                            select.dispatchEvent(event);
                            return true;
                        }}
                    }}
                }}
                return false;
            }})();
            '''
            result = tab.run_js(js_code)
            # print(f"JS点击结果: {result}")
            # print("等待数据包")
            for packet in tab.listen.steps():
                body = packet.response.body
                # 记录真实的 variation 请求 URL（含 dwvar_ 参数名），供 API 加购使用
                try:
                    if packet.url and "Product-Variation" in packet.url:
                        LAST_VARIATION_URL = packet.url
                except Exception:
                    pass
                if "Just a moment" in body:
                    tab.refresh()
                    return False
                # print(body)
                # print("-----------------")
                rom_list = body["product"]["variationAttributes"][1]["values"]
                for rom in rom_list:
                    if rom["id"] == rom_id_str:
                        # print(f"✅ 找到目标内存: {rom['id']}")
                        # print(f"✅ 是否可选: {rom['selectable']}")
                        return rom['selectable']
                        # break
                break
        else:
            print(f"❌ 未找到目标颜色 ID: {color_id_str},请确认颜色是否正确")
            return False
        # rom_option = tab.ele(f"tag:span@@class=value@@data-attr-value={rom_id_str}")
        # if rom_option:
        #     rom_text = rom_option.text.strip()
        #     # print(f"✅ 找到目标内存: {rom_text}")
        #     if "售罄" in rom_text:
        #         return False
        #     else:
        #         return True
    #     else:
    #         print(f"❌ 未找到目标内存 ID: {rom_id_str}")
    #         return False
    except Exception as e:
        print(f"❌ 检查库存时出错: {e}")
        # print(body)
        tab.refresh()
        return False

if __name__ == "__main__":
    co = ChromiumOptions()
    # co.add_argument("--headless")
    browser = Chromium(co)
    tab = browser.latest_tab
    print("开始打开商品页面")
    tab.get("https://eshop.hkcsl.com/zh_HK/apple/IP17scol.html", timeout=20)
    goods = {
        "name": "iphone_17",
        "color": "15121",
        "rom": "1026"
    }
    for i in range(1000):
        print(f"第{i}次检查库存")
        check_stock_with_selenium2(tab, goods)
        time.sleep(1)
