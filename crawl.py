import requests
import time
import random
import database
import os



# 创建全局会话对象
session = requests.session()
session.trust_env = False

URL = "https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/space"


def crawl(mid, name):
    cookie_str = os.environ.get("BI_COOKIE") 
    # 动态生成 Headers，确保 Referer 随用户 UID 改变
    current_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": f"https://space.bilibili.com/{mid}/dynamic",
        "Origin": "https://space.bilibili.com",
        "Host": "api.bilibili.com",
        "Cookie": cookie_str
    }

    offset = ""
    print(f"\n>>> 正在抓取 [{name}] (UID: {mid})")

    while True:
        params = {
            "host_mid": mid,
            "offset": offset,
            "timezone_offset": -480
        }

        try:
            # 使用刚才生成的 current_headers
            r = session.get(URL, params=params, headers=current_headers, timeout=10)

            # 如果依然报 -352，打印出完整信息以便排查
            data = r.json()
            if data.get("code") == -352:
                print(f"!!! 触发风控 (-352)。建议更换 Cookie 或稍后再试。")
                break

            if data.get("code") != 0:
                print(f"API 报错: {data.get('message')} (Code: {data.get('code')})")
                break

            items = data.get("data", {}).get("items", [])
            if not items:
                print("该页面没有动态内容。")
                break

            for item in items:
                dynamic_id = item["id_str"]
                dynamic_type = item["type"]

                # 提取时间
                pub_ts = item.get("modules", {}).get("module_author", {}).get("pub_ts", 0)

                text = ""
                img_urls = ""

                try:
                    # 统一处理文字内容 (module_dynamic 是大部分类型的通用容器)
                    module_dyn = item.get("modules", {}).get("module_dynamic", {})

                    if dynamic_type in ["DYNAMIC_TYPE_WORD", "DYNAMIC_TYPE_DRAW"]:
                        if module_dyn.get("desc"):
                            text = module_dyn["desc"]["text"]

                        if dynamic_type == "DYNAMIC_TYPE_DRAW":
                            draw_items = module_dyn.get("major", {}).get("draw", {}).get("items", [])
                            img_urls = ",".join([img["src"] for img in draw_items])

                    elif dynamic_type == "DYNAMIC_TYPE_FORWARD":
                        fwd_text = module_dyn.get("desc", {}).get("text", "")
                        text = f"[转发动态] {fwd_text}"

                    elif dynamic_type == "DYNAMIC_TYPE_AV":
                        archive = module_dyn.get("major", {}).get("archive", {})
                        text = f"[视频投稿] {archive.get('title')}"

                    else:
                        continue

                except Exception:
                    continue

                # 插入数据库
                database.insert_dynamic(dynamic_id, name, pub_ts, text, img_urls)
                print(f"已存: {text[:15]}...")

            # 翻页逻辑
            if not data["data"].get("has_more"):
                break

            offset = data["data"].get("offset")

            # 随机等待 2-4 秒，模仿人类行为
            wait_time = random.uniform(2, 4)
            time.sleep(wait_time)

        except Exception as e:
            print(f"请求发生异常: {e}")
            break
