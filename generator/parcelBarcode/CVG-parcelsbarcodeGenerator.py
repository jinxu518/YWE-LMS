import configparser

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode import code128
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import time

# -----------------------------
# 配置账号和网站（保持不改）
# -----------------------------
CONFIG_FILE = "config.ini"
config = configparser.ConfigParser()
config.read(CONFIG_FILE, encoding="utf-8")
USERNAME = config.get("credentials", "username")
PASSWORD = config.get("credentials", "password")
LOGIN_URL = "https://lms.yweinternal.com/login"

TASK_CODE = "TSK000000003533"  # 任务编号-每次替换

# -----------------------------
# PDF生成函数（只显示分箱号，支持中文字体）
# -----------------------------
def generate_barcodes_pdf(barcode_data, filename="barcodes.pdf"):
    pdfmetrics.registerFont(TTFont('SimSun', 'simsun.ttc'))  # 注册中文字体

    c = canvas.Canvas(filename, pagesize=A4)
    page_width, page_height = A4

    cols, rows = 3, 6
    x_margin, y_margin = 10 * mm, 10 * mm
    x_spacing, y_spacing = 60 * mm, 40 * mm
    x0, y0 = x_margin, page_height - y_margin
    col, row = 0, 0

    for package_number, cage_number in barcode_data:
        if row == 0 and col == 0:
            c.setFont("SimSun", 14)
            c.drawString(x0, page_height - 15*mm, "分箱包裹号")

        barcode = code128.Code128(str(package_number), barHeight=12*mm, barWidth=0.6, humanReadable=False)
        x = x0 + col * x_spacing
        y = y0 - row * y_spacing - 20*mm
        barcode.drawOn(c, x, y)

        c.setFont("SimSun", 10)
        text = f"分箱号: {cage_number}"
        text_width = c.stringWidth(text, "SimSun", 10)
        c.drawString(x + (barcode.width - text_width)/2, y - 12, text)

        col += 1
        if col >= cols:
            col = 0
            row += 1
        if row >= rows:
            row = 0
            c.showPage()

    c.save()
    print(f"✅ 条码 PDF 已生成: {filename}")

# -----------------------------
# 主流程
# -----------------------------
def main():
    driver = webdriver.Chrome()
    driver.get(LOGIN_URL)

    # 登录
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "form_item_username"))
    ).send_keys(USERNAME)
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "form_item_password"))
    ).send_keys(PASSWORD)
    WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, ".ant-btn.ant-btn-primary.ant-btn-lg.ant-btn-block"))
    ).click()
    time.sleep(5)

    # 点击分箱管理
    menu_titles = WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".ant-menu-title-content"))
    )
    for menu in menu_titles:
        if "分箱管理" in menu.text:
            driver.execute_script("arguments[0].scrollIntoView(true);", menu)
            menu.click()
            break
    time.sleep(1)

    # 点击分箱列表
    box_list = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-menu-id="/block/list"]'))
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", box_list)
    time.sleep(0.5)
    box_list.click()
    time.sleep(3)

    print("✅ 分箱列表已打开")

    # -----------------------------
    # 尝试关闭 Dashboard 标签
    # -----------------------------
    try:
        dashboard_close_btn = driver.find_element(
            By.CSS_SELECTOR,
            ".ant-dropdown-trigger .ant-tabs-tab-remove"
        )
        driver.execute_script("arguments[0].click();", dashboard_close_btn)
        print("✅ Dashboard 标签已关闭")
    except Exception as e:
        print("⚠ Dashboard 标签未找到或已关闭:", e)

    all_barcodes = []

    # 分箱号列表：301-335
    cage_numbers = list(range(301, 336))

    # 循环分箱号
    for cage_number in cage_numbers:
        try:
            # 输入任务编号
            task_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "searchForm_taskCode"))
            )
            task_input.clear()
            task_input.send_keys(TASK_CODE)

            # 输入分箱号
            cage_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "searchForm_cageNumber"))
            )
            cage_input.clear()
            cage_input.send_keys(str(cage_number))

            # 点击查询
            search_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".css-12q8zf4.ant-btn.ant-btn-primary"))
            )
            search_button.click()
            time.sleep(2)

            print(f"✅ 查询任务号 {TASK_CODE}, 分箱号 {cage_number}")

            # 取第一行第4列进入详情
            rows = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".ant-table-row.ant-table-row-level-0"))
            )
            if rows:
                first_row = rows[0]
                cells = first_row.find_elements(By.CSS_SELECTOR, ".ant-table-cell")
                if len(cells) >= 4:
                    driver.execute_script("arguments[0].scrollIntoView(true);", cells[3])
                    cells[3].click()
                    time.sleep(1)

                    # 在详情页抓第一行第一列包裹号
                    detail_rows = WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".ant-table-row.ant-table-row-level-0"))
                    )
                    if detail_rows:
                        detail_first_row = detail_rows[0]
                        detail_cells = detail_first_row.find_elements(By.CSS_SELECTOR, ".ant-table-cell")
                        if detail_cells:
                            package_number = detail_cells[0].text.strip()
                            if package_number:
                                all_barcodes.append((package_number, cage_number))

                    # 返回分箱列表
                    driver.back()
                    time.sleep(1)

        except Exception as e:
            print(f"⚠ 查询分箱号 {cage_number} 时失败: {e}")
            continue

    driver.quit()

    # 生成 PDF
    generate_barcodes_pdf(all_barcodes, filename="./CVG分箱包裹号.pdf")

if __name__ == "__main__":
    main()
