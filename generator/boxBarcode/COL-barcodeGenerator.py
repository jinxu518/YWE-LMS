from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.graphics.barcode import code128
from reportlab.lib.units import mm

def generate_barcodes(prefix, box_numbers):
    start_box = box_numbers[0]
    end_box = box_numbers[-1]
    filename = f"{prefix}_{start_box}-{end_box}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    page_width, page_height = A4

    # 每页排版参数
    cols, rows = 3, 7   # 每行 3 个
    x_margin, y_margin = 20 * mm, 20 * mm
    x_spacing, y_spacing = 65 * mm, 40 * mm

    x0, y0 = x_margin, page_height - y_margin
    col, row = 0, 0

    for box_number in box_numbers:
        barcode_value = f"{prefix}{box_number}1"

        # Code128 条码（扁长、矮）
        barcode = code128.Code128(
            barcode_value,
            barHeight=12*mm,   # 高度矮
            barWidth=0.6,      # 拉长条码
            humanReadable=False
        )

        x = x0 + col * x_spacing
        y = y0 - row * y_spacing

        # 绘制条码
        barcode.drawOn(c, x, y)

        # 条码下方文字备注
        c.setFont("Helvetica", 9)
        text = f"{barcode_value} {box_number}"
        text_width = c.stringWidth(text, "Helvetica", 9)
        c.drawString(x + (barcode.width - text_width)/2, y - 12, text)

        # 更新列、行
        col += 1
        if col >= cols:
            col = 0
            row += 1
        if row >= rows:
            row = 0
            c.showPage()  # 换页

    c.save()
    print(f"✅ 批量条码已生成: {filename}")


if __name__ == "__main__":
    prefix = input("请输入前缀: ")  # 比如 TSK000000003548
    # 连续分箱号 601, 615
    box_numbers = list(range(601, 616))
    generate_barcodes(prefix, box_numbers)
