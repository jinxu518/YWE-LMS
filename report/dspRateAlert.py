import configparser
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# -----------------------------
# 配置
# -----------------------------
CONFIG_FILE = "config.ini"
config = configparser.ConfigParser()
config.read(CONFIG_FILE, encoding="utf-8")

USERNAME = config.get("credentials", "username")
PASSWORD = config.get("credentials", "password")
LOGIN_URL = "https://console.yanwentech.com/p/login/ywwl"
QBI_URL = "https://qbi.yanwentech.com/product/view.htm?module=dashboard&productId=54adbfd1-f4c8-4ce6-9763-4a9002668862&menuId=f1282448-cf30-4d34-98d9-af96f3a90a03"
IFRAME_SRC = "/dashboard/view/pc.htm?pageId=a1c6ed06-1cfc-4fd8-be08-25eed64a40dd&menuId=f1282448-cf30-4d34-98d9-af96f3a90a03&dd_orientation=auto&productView="

# -----------------------------
# 初始化浏览器
# -----------------------------
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 20)

# -----------------------------
# 登录函数
# -----------------------------
def login():
    for attempt in range(1, 4):
        try:
            driver.get(LOGIN_URL)
            print(f"⏳ 打开登录页面: {LOGIN_URL} (第 {attempt} 次尝试)")
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#login input[type='text']"))).send_keys(USERNAME)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#login input[type='password']"))).send_keys(PASSWORD)
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#login button"))).click()
            time.sleep(5)
            if driver.current_url != LOGIN_URL:
                print("✅ 登录成功")
                return True
            else:
                print(f"❌ 登录失败或跳回登录页 (第 {attempt} 次)")
        except Exception as e:
            print(f"❌ 登录异常: {e}")
        time.sleep(2)
    return False

# -----------------------------
# 点击 other-login-wrapper
# -----------------------------
def click_other_login():
    try:
        elem = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".other-login-wrapper")))
        elem.click()
        print("✅ 成功点击 other-login-wrapper")
        time.sleep(2)
        return True
    except:
        print("❌ 点击 other-login-wrapper 失败")
        return False

# -----------------------------
# 切入 iframe
# -----------------------------
def switch_to_iframe():
    try:
        iframe = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, f"iframe[src*='{IFRAME_SRC}']"))
        )
        driver.switch_to.frame(iframe)
        print("✅ 成功切入指定 iframe")
        return True
    except:
        print("❌ 切入 iframe 失败")
        return False

# -----------------------------
# 点击第三个 tab
# -----------------------------
def click_third_tab():
    try:
        tabs = driver.find_elements(By.CSS_SELECTOR, ".story-builder-tabs li.story-builder-tab")
        if len(tabs) >= 3:
            driver.execute_script("arguments[0].scrollIntoView(true);", tabs[2])
            tabs[2].click()
            print("✅ 点击第 3 个 tab")
            return True
        else:
            print("❌ 没找到足够的 tabs")
            return False
    except Exception as e:
        print(f"❌ 点击 tabs 出错: {e}")
        return False

# -----------------------------
# 修改日期
# -----------------------------
def set_range_date():
    today = datetime.today()
    four_days_ago = today - timedelta(days=4)
    start_str = four_days_ago.strftime("%Y-%m-%d")
    end_str = today.strftime("%Y-%m-%d")

    try:
        # 等待第三 tab 的日期控件渲染完成
        wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//span[text()='计划提货日期']/../../..//div[@class='range-date-time']")
        ))

        # 开始日期
        start_input = driver.find_element(By.XPATH, "//span[text()='计划提货日期']/../../..//div[@class='range-date-time']//input[1]")
        start_input.click()
        td_start = wait.until(EC.element_to_be_clickable((By.XPATH, f"//td[@title='{start_str}']")))
        td_start.click()

        # 结束日期
        end_input = driver.find_element(By.XPATH, "//span[text()='计划提货日期']/../../..//div[@class='range-date-time']//input[2]")
        end_input.click()
        td_end = wait.until(EC.element_to_be_clickable((By.XPATH, f"//td[@title='{end_str}']")))
        td_end.click()

        print(f"✅ 日期修改完成: {start_str} - {end_str}")
        return True
    except Exception as e:
        print(f"❌ 修改日期失败: {e}")
        return False

# -----------------------------
# 点击查询按钮
# -----------------------------
def click_query_button():
    try:
        btn = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, ".query-button-areas.horizontal.horizontal-label .query-button")
        ))
        btn.click()
        print("✅ 点击查询按钮成功")
        return True
    except Exception as e:
        print(f"❌ 点击查询按钮失败: {e}")
        return False

# -----------------------------
# 主流程
# -----------------------------
def main():
    if not login():
        print("❌ 登录失败，退出")
        return

    driver.get(QBI_URL)
    time.sleep(5)
    print(f"✅ 打开 QBI 页面: {QBI_URL}")

    click_other_login()
    time.sleep(5)

    if not switch_to_iframe():
        print("❌ 切 iframe 失败，退出")
        return

    time.sleep(5)

    if click_third_tab():
        # 等 tab 渲染完成
        time.sleep(3)
        set_range_date()
        click_query_button()

    print("⏳ 浏览器保持打开状态，请手动操作和关闭...")

if __name__ == "__main__":
    main()
