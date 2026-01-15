import uiautomator2 as u2
import pdfplumber
import time
import os
import re


def run_task():
    # --- 配置区 ---
    PDF_FILE = "./pdfspre/abc_part2.pdf"

    # 1. 连接模拟器
    try:
        print("--- 步骤1: 连接模拟器 ---")
        d = u2.connect()
        print(f"✅ 连接成功: {d.serial}")
        d.set_input_ime(True)  # 开启快速输入模式
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return

    # 2. 检查 PDF 文件 (保持不变)
    if not os.path.exists(PDF_FILE):
        print(f"❌ 错误：找不到文件 '{PDF_FILE}'")
        return

    # 3. 解析 PDF (保持不变)
    print("\n--- 步骤2: 正在精准过滤条码 ---")
    barcode_list = []
    try:
        with pdfplumber.open(PDF_FILE) as pdf:
            for i, page in enumerate(pdf.pages):
                raw_text = page.extract_text()
                if raw_text:
                    words = raw_text.split()
                    current_page_barcodes = [
                        w.strip() for w in words
                        if len(w.strip()) >= 10
                           and w.strip() != 'YWORD01'
                           and not any('\u4e00' <= char <= '\u9fff' for char in w)
                           and re.match(r'^[A-Z0-9\-]+$', w.strip())
                    ]
                    if current_page_barcodes:
                        target = max(current_page_barcodes, key=len)
                        barcode_list.append(target)
    except Exception as e:
        print(f"❌ 解析 PDF 出错: {e}")
        return

    if not barcode_list:
        print("\n❌ 未能捕获有效条码")
        return

    print(f"\n--- 步骤3: 准备录入 (共 {len(barcode_list)} 个) ---")
    time.sleep(3)

    # 5. 自动循环录入 (核心修改区)
    for index, val in enumerate(barcode_list):
        print(f"🚀 [{index + 1}/{len(barcode_list)}] 录入: {val}")
        try:
            # --- 【关键：多重清空保障】 ---

            # 1. 强制点击输入框获取焦点 (防止 100 条后焦点丢失)
            # 如果你知道输入框的坐标，建议用 d.click(x, y) 更准
            d(focused=True).click()

            # 2. 调用 u2 自带的清空方法
            d(focused=True).clear_text()

            # 3. 物理保险：全选并删除 (防止有些输入框 clear_text 删不干净)
            # 模拟按键：Ctrl+A (全选) 然后按 Del (删除)
            d.press(29, meta=114)  # 部分模拟器支持通过 keyevent 清除，这里作为补充
            d.press("delete")

            # --- 【录入与提交】 ---

            # 输入内容
            d.send_keys(str(val))
            time.sleep(0.2)  # 给 0.2 秒缓冲

            # 模拟按下回车
            d.press("enter")

            # --- 【异常弹窗处理】 ---
            # 针对你说的有弹窗，自动尝试关闭弹窗
            if d(textMatches="确定|确认|我知道了|OK").exists(timeout=0.5):
                d(textMatches="确定|确认|我知道了|OK").click()
                print("💡 已自动点击弹窗确定按钮")

            # 处理 100 条后的卡顿，适当拉长等待时间
            time.sleep(1.5)

        except Exception as e:
            print(f"⚠️ 第 {index + 1} 个录入失败: {e}")
            continue

    d.set_input_ime(False)
    print("\n✨ 任务全部完成！")


if __name__ == "__main__":
    run_task()