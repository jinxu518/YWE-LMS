import configparser
import time
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# -----------------------------
# 配置账号和网站
# -----------------------------
CONFIG_FILE = "config.ini"
config = configparser.ConfigParser()
config.read(CONFIG_FILE, encoding="utf-8")

# 企业后台账号
USERNAME = config.get("credentials", "username")
PASSWORD = config.get("credentials", "password")
LOGIN_URL = "https://console.yanwentech.com/p/login/ywwl"

# 邮件配置（可选）
EMAIL_HOST = config.get("email", "smtp_host")
EMAIL_PORT = config.getint("email", "smtp_port")
EMAIL_USER = config.get("email", "username")
EMAIL_PASS = config.get("email", "password")
EMAIL_TO = [x.strip() for x in config.get("email", "to").split(",")]
SEND_EMAIL = config.getboolean("email", "send", fallback=False)

# -----------------------------
# 邮件发送函数
# -----------------------------
def send_email(subject, body):
    message = MIMEText(body, 'plain', 'utf-8')
    message['From'] = Header(EMAIL_USER)
    message['To'] = Header(", ".join(EMAIL_TO))
    message['Subject'] = Header(subject, 'utf-8')

    with smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT) as server:
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, EMAIL_TO, message.as_string())
    print("✅ 邮件发送完成")

# -----------------------------
# 点击后台菜单 div.list-item-title-wrapper（跳转 QBI）
# -----------------------------
def click_list_item_title(driver, wait):
    try:
        divs = wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "div.list-item-title-wrapper")
        ))
    except Exception as e:
        print(f"❌ 没找到 div.list-item-title-wrapper：{e}")
        return False

    for idx, div in enumerate(divs):
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", div)
            time.sleep(0.3)

            if not div.is_displayed():
                print(f"跳过第 {idx+1} 个 div.list-item-title-wrapper（不可见）")
                continue

            driver.execute_script("arguments[0].click();", div)
            print(f"✅ 成功点击第 {idx+1} 个 div.list-item-title-wrapper")

            # 等待跳转到 QBI 页面
            WebDriverWait(driver, 15).until(
                lambda d: "qbi" in d.current_url.lower()
            )
            print(f"➡️ 已跳转到 QBI 页面: {driver.current_url}")
            return True
        except Exception as e:
            print(f"点击第 {idx+1} 个 div.list-item-title-wrapper 失败：{e}")
            continue

    print("❌ 没有可点击的 div.list-item-title-wrapper")
    return False

# -----------------------------
# 点击 QBI 页面元素（比如 span.multi-line.single-line）
# -----------------------------
def click_qbi_element(driver, wait):
    try:
        element = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "span.multi-line.single-line")  # 可以替换成你需要点击的 QBI 元素
        ))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.3)
        driver.execute_script("arguments[0].click();", element)
        print("✅ 成功点击 QBI 页面元素")
        return True
    except Exception as e:
        print(f"❌ 点击 QBI 页面元素失败: {e}")
        return False

# -----------------------------
# 主流程
# -----------------------------
def main():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)

    try:
        # 打开企业后台登录页
        driver.get(LOGIN_URL)

        # 登录
        username_input = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "#login .ant-form-item.login-formItem:nth-of-type(1) input")
        ))
        username_input.clear()
        username_input.send_keys(USERNAME)

        password_input = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "#login .ant-form-item.login-formItem:nth-of-type(2) input")
        ))
        password_input.clear()
        password_input.send_keys(PASSWORD)

        login_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#login button")))
        login_btn.click()
        print("✅ 登录成功")

        # 等待后台加载
        time.sleep(3)

        # 点击后台菜单 → 跳转 QBI
        success1 = click_list_item_title(driver, wait)

        # 如果成功进入 QBI，再点击指定 QBI 元素
        if success1:
            success2 = click_qbi_element(driver, wait)
        else:
            success2 = False

        # 邮件通知
        subject = "后台自动化完成"
        body = f"✅ 登录后台并点击后台菜单: {success1}\n✅ QBI 页面点击结果: {success2}\n当前URL: {driver.current_url}"
        if SEND_EMAIL:
            try:
                send_email(subject, body)
            except Exception as e:
                print(f"⚠️ 邮件发送失败: {e}")
        else:
            print("📧 邮件发送被禁用（config.ini send=false）")

    finally:
        time.sleep(1)
        driver.quit()

if __name__ == "__main__":
    main()
