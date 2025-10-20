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

# 配置
CONFIG_FILE = "config.ini"
config = configparser.ConfigParser()
config.read(CONFIG_FILE, encoding="utf-8")
USERNAME = config.get("credentials", "username")
PASSWORD = config.get("credentials", "password")
LOGIN_URL = "https://lms.yweinternal.com/login"
TASK_CODE = "TSK000000003978"
MAX_RETRIES = 3  # 重试次数


# PDF生成
def generate_barcodes_pdf(barcode_data, filename="barcodes.pdf"):
    pdfmetrics.registerFont(TTFont('SimSun', 'simsun.ttc'))
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
            c.drawString(x0, page_height - 15 * mm, "分箱包裹号")

        barcode = code128.Code128(str(package_number), barHeight=12 * mm, barWidth=0.6, humanReadable=False)
        x = x0 + col * x_spacing
        y = y0 - row * y_spacing - 20 * mm
        barcode.drawOn(c, x, y)

        c.setFont("SimSun", 10)
        text = f"分箱号: {cage_number}"
        text_width = c.stringWidth(text, "SimSun", 10)
        c.drawString(x + (barcode.width - text_width) / 2, y - 12, text)

        col += 1
        if col >= cols:
            col = 0
            row += 1
        if row >= rows:
            row = 0
            c.showPage()

    c.save()
    print(f"✅ PDF已生成: {filename}")


# 查询单个分箱（带重试）
def query_cage(driver, cage_number):
    for attempt in range(MAX_RETRIES):
        try:
            # 输入搜索条件
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "searchForm_taskCode"))
            ).clear()
            driver.find_element(By.ID, "searchForm_taskCode").send_keys(TASK_CODE)

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "searchForm_cageNumber"))
            ).clear()
            driver.find_element(By.ID, "searchForm_cageNumber").send_keys(str(cage_number))

            # 点击查询
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".css-12q8zf4.ant-btn.ant-btn-primary"))
            ).click()
            time.sleep(2)

            # 点击第一行第4列进详情
            rows = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".ant-table-row.ant-table-row-level-0"))
            )
            if rows:
                cells = rows[0].find_elements(By.CSS_SELECTOR, ".ant-table-cell")
                if len(cells) >= 4:
                    cells[3].click()
                    time.sleep(2)

                    # 获取包裹号
                    detail_rows = WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".ant-table-row.ant-table-row-level-0"))
                    )
                    if detail_rows:
                        package_number = detail_rows[0].find_elements(By.CSS_SELECTOR, ".ant-table-cell")[
                            0].text.strip()
                        driver.back()
                        time.sleep(1)
                        if package_number:
                            print(f"✅ 分箱{cage_number}: {package_number}")
                            return package_number

            driver.back()
            return None

        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                print(f"⚠ 重试 {cage_number} ({attempt + 1}/{MAX_RETRIES})")
                driver.refresh()
                time.sleep(2)
            else:
                print(f"❌ 失败: {cage_number}")
                return None


def main():
    driver = webdriver.Chrome()
    driver.maximize_window()

    try:
        # 登录
        driver.get(LOGIN_URL)
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

        # 导航到分箱列表
        menu_titles = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".ant-menu-title-content"))
        )
        for menu in menu_titles:
            if "分箱管理" in menu.text:
                menu.click()
                break
        time.sleep(2)

        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-menu-id="/block/list"]'))
        ).click()
        time.sleep(3)

        # 关闭Dashboard
        try:
            driver.find_element(By.CSS_SELECTOR, ".ant-dropdown-trigger .ant-tabs-tab-remove").click()
            time.sleep(1)
        except:
            pass

        # 查询所有分箱
        all_barcodes = []
        for cage_number in range(301, 336):
            package_number = query_cage(driver, cage_number)
            if package_number:
                all_barcodes.append((package_number, cage_number))

        print(f"\n成功: {len(all_barcodes)}/35")

        if all_barcodes:
            generate_barcodes_pdf(all_barcodes, filename="CVG分箱包裹号.pdf")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()