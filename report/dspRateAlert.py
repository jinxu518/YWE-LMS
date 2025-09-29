import configparser
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains

# 配置
CONFIG_FILE = "config.ini"
config = configparser.ConfigParser()
config.read(CONFIG_FILE, encoding="utf-8")

USERNAME = config.get("credentials", "username")
PASSWORD = config.get("credentials", "password")
LOGIN_URL = "https://console.yanwentech.com/p/login/ywwl"
QBI_URL = "https://qbi.yanwentech.com/product/view.htm?module=dashboard&productId=54adbfd1-f4c8-4ce6-9763-4a9002668862&menuId=f1282448-cf30-4d34-98d9-af96f3a90a03"
IFRAME_SRC = "/dashboard/view/pc.htm?pageId=a1c6ed06-1cfc-4fd8-be08-25eed64a40dd&menuId=f1282448-cf30-4d34-98d9-af96f3a90a03&dd_orientation=auto&productView="

# 初始化浏览器
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
driver = webdriver.Chrome(options=options)
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
wait = WebDriverWait(driver, 20)
actions = ActionChains(driver)


def login():
    """登录函数"""
    for attempt in range(1, 4):
        try:
            driver.get(LOGIN_URL)
            print(f"打开登录页面: {LOGIN_URL} (第 {attempt} 次尝试)")

            username_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#login input[type='text']")))
            username_input.clear()
            username_input.send_keys(USERNAME)

            password_input = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#login input[type='password']")))
            password_input.clear()
            password_input.send_keys(PASSWORD)

            login_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#login button")))
            login_button.click()

            time.sleep(5)
            if driver.current_url != LOGIN_URL:
                print("✓ 登录成功")
                return True
            else:
                print(f"登录失败或跳回登录页 (第 {attempt} 次)")
        except Exception as e:
            print(f"登录异常: {e}")
        time.sleep(2)
    return False


def click_other_login():
    """点击 other-login-wrapper"""
    try:
        elem = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".other-login-wrapper")))
        driver.execute_script("arguments[0].scrollIntoView(true);", elem)
        time.sleep(1)
        elem.click()
        print("✓ 成功点击 other-login-wrapper")
        time.sleep(2)
        return True
    except Exception as e:
        print(f"点击 other-login-wrapper 失败: {e}")
        return False


def switch_to_iframe():
    """切入 iframe"""
    try:
        iframe = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f"iframe[src*='{IFRAME_SRC}']")))
        driver.switch_to.frame(iframe)
        print("✓ 成功切入指定 iframe")

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".story-builder-tabs")))
        time.sleep(3)
        return True
    except Exception as e:
        print(f"❌ 切入 iframe 失败: {e}")
        return False


def click_third_tab():
    """点击第三个 tab"""
    try:
        tabs = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".story-builder-tabs li.story-builder-tab")))

        if len(tabs) >= 3:
            third_tab = tabs[2]
            print(f"找到 {len(tabs)} 个tabs")

            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", third_tab)
            time.sleep(1)

            try:
                third_tab.click()
                print("✓ 点击第3个tab (普通点击)")
            except:
                driver.execute_script("arguments[0].click();", third_tab)
                print("✓ 点击第3个tab (JavaScript点击)")

            time.sleep(3)
            return True
        else:
            print("❌ 没找到足够的 tabs")
            return False
    except Exception as e:
        print(f"❌ 点击 tabs 出错: {e}")
        return False


def set_dates_via_calendar():
    """通过点击日历设置日期"""
    today = datetime.today()
    four_days_ago = today - timedelta(days=4)
    start_str = four_days_ago.strftime("%Y-%m-%d")
    end_str = today.strftime("%Y-%m-%d")
    start_day = four_days_ago.strftime("%d").lstrip('0')
    end_day = today.strftime("%d").lstrip('0')

    try:
        print(f"\n通过日历设置日期: {start_str}({start_day}日) 到 {end_str}({end_day}日)")

        pickers_info = driver.execute_script("""
            var allPickers = document.querySelectorAll('.ant-picker');
            var targetPickers = [];

            for (var i = 0; i < allPickers.length; i++) {
                var picker = allPickers[i];
                var rect = picker.getBoundingClientRect();
                var isVisible = rect.width > 0 && rect.height > 0 && picker.offsetParent !== null;

                if (isVisible && rect.x > 300) {
                    targetPickers.push({
                        index: i,
                        element: picker,
                        x: Math.round(rect.x),
                        y: Math.round(rect.y),
                        input: picker.querySelector('input')
                    });
                }
            }

            return targetPickers;
        """)

        if len(pickers_info) < 2:
            print(f"❌ 未找到足够的目标日期选择器: {len(pickers_info)}")
            return False

        print(f"找到 {len(pickers_info)} 个目标日期选择器")

        start_success = set_single_date_via_calendar(pickers_info[0], start_day, start_str, "开始")
        time.sleep(2)

        end_success = set_single_date_via_calendar(pickers_info[1], end_day, end_str, "结束")
        time.sleep(2)

        return start_success or end_success

    except Exception as e:
        print(f"❌ 通过日历设置日期异常: {e}")
        return False


def set_single_date_via_calendar(picker_info, target_day, target_date, date_type):
    """通过日历设置单个日期"""
    try:
        print(f"  设置{date_type}日期: {target_date} ({target_day}日)")

        driver.execute_script("arguments[0].style.border='3px solid blue';", picker_info['element'])
        time.sleep(0.5)

        try:
            picker_info['element'].click()
        except:
            driver.execute_script("arguments[0].click();", picker_info['element'])

        time.sleep(2)

        date_clicked = False
        date_selectors = [
            f"//td[contains(@class, 'ant-picker-cell') and not(contains(@class, 'ant-picker-cell-disabled')) and .//div[text()='{target_day}']]",
            f"//td[@title='{target_date}' and not(contains(@class, 'disabled'))]",
            f"//div[contains(@class, 'ant-picker-cell-inner') and text()='{target_day}']"
        ]

        for selector in date_selectors:
            try:
                short_wait = WebDriverWait(driver, 3)
                date_elements = short_wait.until(EC.presence_of_all_elements_located((By.XPATH, selector)))

                if date_elements:
                    for date_elem in date_elements:
                        try:
                            if date_elem.is_displayed() and date_elem.is_enabled():
                                driver.execute_script(
                                    "arguments[0].style.background='yellow'; arguments[0].style.border='2px solid red';",
                                    date_elem)
                                time.sleep(0.5)

                                try:
                                    date_elem.click()
                                except:
                                    driver.execute_script("arguments[0].click();", date_elem)

                                print(f"  ✓ 成功点击{date_type}日期: {target_day}")
                                date_clicked = True
                                time.sleep(1)
                                break
                        except:
                            continue

                if date_clicked:
                    break
            except TimeoutException:
                continue
            except Exception:
                continue

        try:
            actions.send_keys(Keys.ESCAPE).perform()
            time.sleep(0.5)
        except:
            pass

        try:
            driver.execute_script("arguments[0].style.border='';", picker_info['element'])
        except:
            pass

        return date_clicked

    except Exception as e:
        print(f"  ❌ 设置{date_type}日期异常: {e}")
        return False


def set_warehouse_selection():
    """设置提货仓选择 - 完整优化版"""
    target_warehouses = ["ORD01", "IND01", "CVG01", "CVG02", "STL01"]

    try:
        print(f"\n{'=' * 60}")
        print(f"开始设置提货仓: {', '.join(target_warehouses)}")
        print(f"{'=' * 60}")

        # ========== 步骤1: 打开选择器并等待数据稳定 ==========
        print("\n[步骤1] 查找并打开提货仓选择器...")
        selector_info = driver.execute_script("""
            var allSelectors = document.querySelectorAll('.query-field-wrapper, .enum-select, .advance-select');
            var targetSelector = null;

            for (var i = 0; i < allSelectors.length; i++) {
                var selector = allSelectors[i];
                var text = selector.textContent || selector.innerText || '';
                var rect = selector.getBoundingClientRect();
                var isVisible = rect.width > 0 && rect.height > 0 && selector.offsetParent !== null;

                if (isVisible && rect.x > 300 && text.includes('提货仓')) {
                    var dropdown = selector.querySelector('.advance-select-input-selected-value, .enum-select, input');
                    if (!dropdown) {
                        dropdown = selector.closest('.query-field').querySelector('.advance-select-input-selected-value, .enum-select, input');
                    }

                    if (dropdown) {
                        targetSelector = {
                            element: dropdown,
                            x: Math.round(rect.x),
                            y: Math.round(rect.y)
                        };
                        break;
                    }
                }
            }

            return targetSelector;
        """)

        if not selector_info:
            print("❌ 未找到提货仓选择器")
            return False

        print(f"✓ 找到选择器，位置: ({selector_info['x']}, {selector_info['y']})")

        driver.execute_script(
            "arguments[0].style.border='3px solid blue';"
            "arguments[0].style.backgroundColor='lightyellow';",
            selector_info['element']
        )
        time.sleep(0.5)

        try:
            selector_info['element'].click()
        except:
            driver.execute_script("arguments[0].click();", selector_info['element'])

        print("✓ 选择器已打开")

        # 等待数据加载并稳定
        print("\n→ 监测选择器数据稳定性...")

        stable_required = 4
        stable_count = 0
        last_count = -1

        for check_num in range(1, 11):
            time.sleep(5)

            item_count = driver.execute_script("""
                var items = document.querySelectorAll('.advance-select-item');
                var visibleCount = 0;

                for (var i = 0; i < items.length; i++) {
                    var rect = items[i].getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0 && items[i].offsetParent !== null) {
                        visibleCount++;
                    }
                }

                return visibleCount;
            """)

            print(f"  第{check_num}次: {item_count}个选项", end="")

            if item_count == last_count and item_count > 0:
                stable_count += 1
                print(f" [稳定{stable_count}/{stable_required}]")

                if stable_count >= stable_required:
                    print(f"✓ 数据已完全稳定! (连续{stable_required}次={item_count}个)")
                    break
            else:
                if last_count != -1:
                    print(f" [变化: {last_count}→{item_count}，重置]")
                else:
                    print(f" [首次检测]")
                stable_count = 0

            last_count = item_count

        print("→ 最后等待5秒再执行清空...")
        time.sleep(5)

        # ========== 步骤2: 逐个删除已选项 ==========
        print(f"\n[步骤2] 逐个删除已选的默认选项...")
        time.sleep(2)

        deleted_count = 0
        for attempt in range(10):
            delete_result = driver.execute_script("""
                var deleteIcons = document.querySelectorAll(
                    '.advance-select-selected .advance-select-item .icon-delete, ' +
                    '.advance-select-selected .advance-select-item .icon-quick-bi-del, ' +
                    '.advance-select-selected .advance-select-item .advance-select-item-icon.icon-delete'
                );

                for (var i = 0; i < deleteIcons.length; i++) {
                    var icon = deleteIcons[i];
                    var rect = icon.getBoundingClientRect();
                    var isVisible = rect.width > 0 && rect.height > 0 && icon.offsetParent !== null;

                    if (isVisible) {
                        var item = icon.closest('.advance-select-item');
                        var text = '';
                        if (item) {
                            var textSpan = item.querySelector('.advance-select-item-text');
                            if (textSpan) {
                                text = textSpan.textContent || textSpan.innerText || '';
                            }
                        }

                        icon.style.border = '2px solid red';
                        icon.style.backgroundColor = 'yellow';

                        try {
                            icon.click();
                            return {success: true, text: text.trim()};
                        } catch(e) {
                            try {
                                icon.parentElement.click();
                                return {success: true, text: text.trim()};
                            } catch(e2) {
                                return {success: false, error: e2.message};
                            }
                        }
                    }
                }

                return {success: false, message: '没有更多删除图标'};
            """)

            if delete_result.get('success'):
                deleted_count += 1
                print(f"  第{deleted_count}次删除: {delete_result.get('text', '未知')}")
                time.sleep(0.8)
            else:
                if deleted_count > 0:
                    print(f"✓ 已删除完成，共删除 {deleted_count} 个")
                else:
                    print(f"✓ 没有默认选项需要删除")
                break

        time.sleep(2)

        # ========== 步骤3: 逐个搜索并选择 ==========
        print(f"\n[步骤3] 开始搜索并添加仓库...")
        selected_count = 0

        for idx, warehouse in enumerate(target_warehouses, 1):
            print(f"\n  [{idx}/{len(target_warehouses)}] 处理仓库: {warehouse}")

            # 统一使用JavaScript输入
            print(f"    → 输入: {warehouse}")
            input_result = driver.execute_script(f"""
                var searchInput = document.querySelector('.advance-select-search input, input[placeholder*="查询"]');

                if (searchInput && searchInput.offsetParent !== null) {{
                    searchInput.value = '';
                    searchInput.focus();
                    searchInput.value = '{warehouse}';
                    searchInput.dispatchEvent(new Event('input', {{bubbles: true}}));
                    searchInput.dispatchEvent(new Event('change', {{bubbles: true}}));
                    searchInput.style.border = '2px solid green';
                    return {{success: true, value: searchInput.value}};
                }}
                return {{success: false}};
            """)

            if not input_result.get('success'):
                print(f"    ❌ 输入失败")
                continue

            print(f"    ✓ 已输入: {input_result['value']}")

            try:
                search_input = driver.find_element(By.CSS_SELECTOR, '.advance-select-search input')
                search_input.send_keys(Keys.ENTER)
                print(f"    ✓ 已按回车键")
                time.sleep(0.5)
            except Exception as e:
                print(f"    ⚠ 按回车失败: {e}")

            # 统一等待5秒
            print(f"    → 等待搜索过滤... (5秒)")
            time.sleep(5)

            filtered_count = driver.execute_script("""
                var items = document.querySelectorAll('.advance-select-item');
                var visibleCount = 0;

                for (var i = 0; i < items.length; i++) {
                    var rect = items[i].getBoundingClientRect();
                    var style = window.getComputedStyle(items[i]);
                    if (rect.width > 0 && rect.height > 0 && 
                        items[i].offsetParent !== null &&
                        style.display !== 'none') {
                        visibleCount++;
                    }
                }

                return visibleCount;
            """)

            print(f"    → 过滤后: {filtered_count} 个选项")

            # STL01滚动处理
            if warehouse == "STL01":
                print(f"    → STL01特殊处理：滚动选项列表")
                try:
                    scroll_result = driver.execute_script("""
                        var containers = ['.advance-select-items', '.ReactVirtualized__Grid', '.ant-select-dropdown'];

                        for (var i = 0; i < containers.length; i++) {
                            var container = document.querySelector(containers[i]);
                            if (container) {
                                var rect = container.getBoundingClientRect();
                                if (rect.width > 0 && rect.height > 0) {
                                    container.scrollTop = container.scrollHeight;
                                    return {success: true, selector: containers[i], scrollHeight: container.scrollHeight};
                                }
                            }
                        }

                        return {success: false};
                    """)

                    if scroll_result.get('success'):
                        print(f"      ✓ 已滚动到底部: {scroll_result.get('selector', '')}")
                        time.sleep(1)

                        driver.execute_script("""
                            var container = document.querySelector('.advance-select-items, .ReactVirtualized__Grid');
                            if (container) {
                                container.scrollTop = 0;
                            }
                        """)
                        print(f"      ✓ 已滚动到顶部")
                        time.sleep(1)
                    else:
                        print(f"      ⚠ 未找到滚动容器")
                except Exception as e:
                    print(f"      ⚠ 滚动失败: {e}")

            # 统一尝试3次
            max_attempts = 3
            option_found = False

            for attempt in range(1, max_attempts + 1):
                print(f"    → 尝试{attempt}/{max_attempts}: 查找选项")

                option_result = driver.execute_script(f"""
                    var warehouse = '{warehouse}';
                    var items = document.querySelectorAll('.advance-select-item');
                    var allVisible = [];
                    var matched = [];

                    for (var i = 0; i < items.length; i++) {{
                        var item = items[i];
                        var rect = item.getBoundingClientRect();
                        var style = window.getComputedStyle(item);

                        var isVisible = rect.width > 0 && rect.height > 0 && 
                                      item.offsetParent !== null &&
                                      style.display !== 'none';

                        if (isVisible) {{
                            var text = (item.textContent || item.innerText || '').trim();
                            allVisible.push(text);

                            if (text.includes(warehouse)) {{
                                matched.push({{text: text, element: item}});
                            }}
                        }}
                    }}

                    if (matched.length > 0) {{
                        var target = matched[0].element;
                        target.style.backgroundColor = 'lightgreen';
                        target.style.border = '3px solid blue';
                        target.scrollIntoView({{block: 'center'}});

                        try {{
                            target.click();
                            return {{success: true, text: matched[0].text, total: allVisible.length}};
                        }} catch(e) {{
                            return {{success: false, error: e.message, total: allVisible.length}};
                        }}
                    }}

                    return {{success: false, message: '未找到', total: allVisible.length, allVisible: allVisible}};
                """)

                if option_result.get('success'):
                    selected_count += 1
                    print(f"    ✓ 成功选择: {option_result['text']}")
                    option_found = True
                    break
                else:
                    print(f"      未找到 (可见{option_result.get('total', 0)}个)")
                    if attempt < max_attempts:
                        time.sleep(2)

            if not option_found:
                print(f"    ❌ 选择失败: {warehouse}")
                if warehouse == "STL01":
                    try:
                        screenshot_path = f"stl01_debug_{int(time.time())}.png"
                        driver.save_screenshot(screenshot_path)
                        print(f"    已保存调试截图: {screenshot_path}")
                    except:
                        pass

            driver.execute_script("""
                var searchInput = document.querySelector('.advance-select-search input');
                if (searchInput) {
                    searchInput.style.border = '';
                }
            """)

            time.sleep(1.5)

        print(f"\n  完成: {selected_count}/{len(target_warehouses)} 个仓库已选择")

        # ========== 步骤4: 点击确定 ==========
        print("\n[步骤4] 点击确定按钮...")
        time.sleep(1)

        confirm_result = driver.execute_script("""
            var allButtons = document.querySelectorAll('button');
            for (var i = 0; i < allButtons.length; i++) {
                var btn = allButtons[i];
                var text = (btn.textContent || btn.innerText || '').trim();
                var rect = btn.getBoundingClientRect();
                var isVisible = rect.width > 0 && rect.height > 0 && 
                              btn.offsetParent !== null && !btn.disabled;

                if (isVisible && (text === '确 定' || text === '确定')) {
                    btn.style.border = '3px solid orange';
                    try {
                        btn.click();
                        return {success: true, text: text};
                    } catch(e) {
                        return {success: false, error: e.message};
                    }
                }
            }

            return {success: false};
        """)

        if confirm_result.get('success'):
            print(f"  ✓ 已点击确定按钮: '{confirm_result['text']}'")
        else:
            print(f"  ⚠ 未找到确定按钮")

        time.sleep(2)

        driver.execute_script("""
            document.querySelectorAll('*').forEach(function(elem) {
                elem.style.border = '';
                elem.style.backgroundColor = '';
            });
        """)

        print(f"\n{'=' * 60}")
        print(f"✓ 提货仓设置完成 (成功选择: {selected_count}/{len(target_warehouses)})")
        print(f"{'=' * 60}")

        return selected_count > 0

    except Exception as e:
        print(f"\n❌ 设置提货仓异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def find_and_click_query_button():
    """查找并点击查询按钮"""
    try:
        print("\n" + "=" * 60)
        print("查找并点击查询按钮")
        print("=" * 60)

        buttons_info = driver.execute_script("""
            var buttons = [];
            var allButtons = document.querySelectorAll('button, input[type="button"]');

            for (var i = 0; i < allButtons.length; i++) {
                var btn = allButtons[i];
                var text = btn.textContent || btn.value || '';
                var rect = btn.getBoundingClientRect();
                var isVisible = rect.width > 0 && rect.height > 0;

                if (isVisible && !btn.disabled && text.includes('查询')) {
                    buttons.push({
                        element: btn,
                        text: text.trim(),
                        x: Math.round(rect.x),
                        y: Math.round(rect.y)
                    });
                }
            }

            buttons.sort(function(a, b) { return b.x - a.x; });
            return buttons;
        """)

        print(f"找到 {len(buttons_info)} 个查询按钮")

        if buttons_info:
            target_btn = buttons_info[0]
            print(f"选择查询按钮: '{target_btn['text']}' at ({target_btn['x']}, {target_btn['y']})")

            driver.execute_script(
                "arguments[0].style.border='3px solid red';",
                target_btn['element'])
            time.sleep(1.5)

            try:
                target_btn['element'].click()
            except:
                driver.execute_script("arguments[0].click();", target_btn['element'])

            print(f"✓ 成功点击查询按钮")
            time.sleep(5)

            return True

        return False

    except Exception as e:
        print(f"❌ 查找查询按钮异常: {e}")
        return False


def main():
    """主流程"""
    try:
        print("\n" + "=" * 60)
        print("开始执行自动化流程")
        print("=" * 60)

        # 登录
        print("\n[1/7] 执行登录...")
        if not login():
            print("❌ 登录失败，退出")
            return

        # 打开QBI页面
        print("\n[2/7] 打开QBI页面...")
        driver.get(QBI_URL)
        time.sleep(5)
        print("✓ QBI页面已打开")

        # 点击other-login
        print("\n[3/7] 点击other-login...")
        if not click_other_login():
            print("⚠ 点击other-login失败，尝试继续")
            time.sleep(2)

        time.sleep(5)

        # 切换iframe
        print("\n[4/7] 切换到iframe...")
        if not switch_to_iframe():
            print("❌ 切换iframe失败，退出")
            return

        # 点击第三个tab
        print("\n[5/7] 点击第三个tab...")
        if not click_third_tab():
            print("⚠ 点击第三个tab可能失败，但继续执行")

        time.sleep(3)

        # 通过日历设置日期
        print("\n[6/7] 设置日期...")
        date_success = set_dates_via_calendar()
        if date_success:
            print("✓ 日期设置完成")
        else:
            print("⚠ 日期设置可能失败")

        # 设置提货仓
        print("\n[7/7] 设置提货仓...")
        warehouse_success = set_warehouse_selection()
        if warehouse_success:
            print("✓ 提货仓设置完成")
        else:
            print("⚠ 提货仓设置可能失败")

        # 截图保存结果
        try:
            screenshot_path = f"result_{int(time.time())}.png"
            driver.save_screenshot(screenshot_path)
            print(f"\n✓ 已保存截图: {screenshot_path}")
        except:
            pass

        # 查询 - 点击两次
        print("\n[查询] 第1次点击查询按钮...")
        if find_and_click_query_button():
            print("✓ 第1次查询执行成功")
        else:
            print("⚠ 第1次查询执行可能失败")

        time.sleep(3)

        print("\n[查询] 第2次点击查询按钮...")
        if find_and_click_query_button():
            print("✓ 第2次查询执行成功")
        else:
            print("⚠ 第2次查询执行可能失败")

        print("\n" + "=" * 60)
        print("✓ 流程执行完毕")
        print("=" * 60)
        print("\n浏览器保持打开状态，请检查结果")

    except Exception as e:
        print(f"\n❌ 主流程异常: {e}")
        import traceback
        traceback.print_exc()
        print("\n浏览器保持打开状态，请手动操作")
    finally:
        input("\n按回车键关闭浏览器...")
        try:
            driver.quit()
        except:
            pass


if __name__ == "__main__":
    main()