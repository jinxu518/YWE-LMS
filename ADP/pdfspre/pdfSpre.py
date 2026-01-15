import os
from PyPDF2 import PdfReader, PdfWriter


def split_pdf(filename, step=300):
    # 这里的路径处理是为了确保能找到 abc.pdf
    # 如果 abc.pdf 在 ADP 文件夹下，脚本在 pdfspre 下，可能需要调整路径
    if not os.path.exists(filename):
        print(f"❌ 错误：在当前目录下找不到文件 {filename}")
        print(f"当前运行路径是: {os.getcwd()}")
        return

    # 读取 PDF
    print(f"📂 正在读取 {filename}，请稍候...")
    reader = PdfReader(filename)

    # --- 修复位置：新版 PyPDF2 使用 len(reader.pages) ---
    total_pages = len(reader.pages)
    print(f"📊 总页数: {total_pages}")

    # 计算需要分几个文件
    for i in range(0, total_pages, step):
        writer = PdfWriter()
        # 确定当前分段的结束页
        end_page = min(i + step, total_pages)

        # 添加页面
        for page_num in range(i, end_page):
            writer.add_page(reader.pages[page_num])

        # 生成新文件名
        part_num = (i // step) + 1
        output_filename = f"abc_part{part_num}.pdf"

        # 保存文件
        with open(output_filename, "wb") as output_file:
            writer.write(output_file)

        print(f"✅ 已生成: {output_filename} (包含第 {i + 1} 到 {end_page} 页)")

    print("\n✨ 全部拆分完成！")


if __name__ == "__main__":
    # 如果 abc.pdf 在上一级目录，可以尝试用 "../abc.pdf"
    # 这里我们默认它就在同一个目录下
    split_pdf("abc.pdf", 300)