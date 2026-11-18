from check_stock import check_stock
from set import GOODS

# for goods_item in GOODS:

res = check_stock(GOODS)
print(f"{GOODS['name']} {GOODS['color'].name} {GOODS['rom'].name} {res}")

