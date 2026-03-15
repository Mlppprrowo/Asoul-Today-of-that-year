import sqlite3
import requests
import datetime
import os

# --- 1. 环境与路径配置 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "dynamic.db")

# 你的 Token 记得之后去钉钉重置一下，并在 GitHub Secrets 里设置 PUSH_URL 哦！
PUSH_URL = os.environ.get("PUSH_URL") or "你自己的钉钉（或其他）webhook地址"
def get_memories():
    """从数据库检索那年今日的内容"""
    if not os.path.exists(DB_PATH):
        print(f"找不到数据库文件: {DB_PATH}")
        return []

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 获取今天在本地时区的 月-日 (格式如 03-15)
    today_md = datetime.datetime.now().strftime('%m-%d')
    # 获取今年年份 (防止把刚才爬的今天动态又推给自己)
    this_year = datetime.datetime.now().strftime('%Y')

    # SQL 检索往年今日
    query = """
    SELECT user, content, pub_time FROM dynamic 
    WHERE strftime('%m-%d', pub_time, 'unixepoch', 'localtime') = ?
    AND strftime('%Y', pub_time, 'unixepoch', 'localtime') != ?
    ORDER BY pub_time DESC
    """

    cursor.execute(query, (today_md, this_year))
    rows = cursor.fetchall()
    conn.close()
    return rows


def push_to_dingtalk():
    """将回忆推送到钉钉"""
    memories = get_memories()

    if not memories:
        print("今天在asoul历史长河中很安静，没有找到那年今日的动态")
        return

    block_keywords = ["运营代转"]

    # 构建消息头部 —— “那年今日”是钉钉的关键词
    message = "【那年今日 · 时光机】\n"
    message += "--------------------------\n"

    found_count = 0
    for user, content, ts in memories:
        # --- 2. 过滤逻辑 ---
        # 屏蔽包含关键词的动态
        if any(kw in content for kw in block_keywords):
            continue

        dt = datetime.datetime.fromtimestamp(ts)
        year = dt.year
        # 格式化时间显示：例如 14:30
        time_str = dt.strftime('%H:%M')

        # --- 3. 内容处理 ---
        clean_content = content.strip()

        # 如果是视频投稿/切片（通常带 [视频投稿] 字样），保持截断
        if "[视频投稿]" in clean_content or "http" in clean_content:
            display_content = clean_content[:50] + "..."
        else:
            # 本人发的文字动态：不截断，完整展示
            display_content = clean_content

        message += f"{year}年 | {time_str} | {user}\n"
        message += f"{display_content}\n"
        message += "──────────────────\n"
        found_count += 1

    if found_count == 0:
        print("经过过滤后没有符合条件的动态。")
        return

    message += "顶碗人祝你今天也有好心情喵~"

    # --- 4. 发送逻辑 (保持 session 屏蔽代理) ---
    session = requests.Session()
    session.trust_env = False
    payload = {"msgtype": "text", "text": {"content": message}}

    try:
        r = session.post(PUSH_URL, json=payload, timeout=10)
        if r.status_code == 200:
            print("推送成功！")
    except Exception as e:
        print(f"推送出错: {e}")


if __name__ == "__main__":
    push_to_dingtalk()