import crawl
import time

members={
    "向晚":672346917,
    "乃琳":672342685,
    "嘉然":672328094,
    "贝拉":672353429
}

for name, mid in members.items():
    try:
        crawl.crawl(mid, name)
        print(f"--- [{name}] 爬取结束，休息 10 秒 ---")
        time.sleep(10)
    except Exception as e:
        print(f"爬取 {name} 时发生错误: {e}")