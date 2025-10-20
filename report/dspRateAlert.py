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


def click_fourth_tab():
    """点击第四个 tab"""
    try:
        tabs = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".story-builder-tabs li.story-builder-tab")))

        if len(tabs) >= 4:
            fourth_tab = tabs[3]
            print(f"找到 {len(tabs)} 个tabs")

            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", fourth_tab)
            time.sleep(1)

            try:
                fourth_tab.click()
                print("✓ 点击第4个tab (普通点击)")
            except:
                driver.execute_script("arguments[0].click();", fourth_tab)
                print("✓ 点击第4个tab (JavaScript点击)")

            time.sleep(3)
            return True
        else:
            print("❌ 没找到足够的 tabs")
            return False
    except Exception as e:
        print(f"❌ 点击 tabs 出错: {e}")
        return False


def set_dates_via_calendar():
    """通过点击日历设置日期 - 昨天到今天"""
    today = datetime.today()
    yesterday = today - timedelta(days=1)
    start_str = yesterday.strftime("%Y-%m-%d")
    end_str = today.strftime("%Y-%m-%d")
    start_day = yesterday.strftime("%d").lstrip('0')
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
    """设置提货仓选择 - 添加了COL"""
    target_warehouses = ["ORD01", "IND01", "CVG01", "CVG02", "STL01", "COL01"]  # 添加了COL01

    try:
        print(f"\n{'=' * 60}")
        print(f"开始设置提货仓: {', '.join(target_warehouses)}")
        print(f"{'=' * 60}")

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

        print(f"\n[步骤3] 开始搜索并添加仓库...")
        selected_count = 0

        for idx, warehouse in enumerate(target_warehouses, 1):
            print(f"\n  [{idx}/{len(target_warehouses)}] 处理仓库: {warehouse}")

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

            if warehouse in ["STL01", "COL01"]:
                print(f"    → {warehouse}特殊处理：滚动选项列表")
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

            driver.execute_script("""
                var searchInput = document.querySelector('.advance-select-search input');
                if (searchInput) {
                    searchInput.style.border = '';
                }
            """)

            time.sleep(1.5)

        print(f"\n  完成: {selected_count}/{len(target_warehouses)} 个仓库已选择")

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


def set_delivery_completion_rate():
    """设置分箱配送完成率为0.8"""
    try:
        print(f"\n{'=' * 60}")
        print("设置分箱配送完成率为 0.8")
        print(f"{'=' * 60}")

        input_info = driver.execute_script("""
            var allInputs = document.querySelectorAll('input.ant-input-number-input');
            var targetInput = null;

            for (var i = 0; i < allInputs.length; i++) {
                var input = allInputs[i];
                var rect = input.getBoundingClientRect();
                var isVisible = rect.width > 0 && rect.height > 0 && input.offsetParent !== null;
                var value = input.value;

                if (isVisible && (value === '0.9' || value === '0.90')) {
                    targetInput = {
                        element: input,
                        x: Math.round(rect.x),
                        y: Math.round(rect.y),
                        currentValue: value
                    };
                    break;
                }
            }

            return targetInput;
        """)

        if not input_info:
            print("❌ 未找到值为0.9的配送完成率输入框")
            return False

        print(f"✓ 找到输入框，当前值: {input_info['currentValue']}, 位置: ({input_info['x']}, {input_info['y']})")

        driver.execute_script(
            "arguments[0].style.border='3px solid blue';"
            "arguments[0].style.backgroundColor='lightyellow';",
            input_info['element']
        )
        time.sleep(1)

        try:
            input_info['element'].click()
            time.sleep(0.5)
            input_info['element'].send_keys(Keys.CONTROL + "a")
            time.sleep(0.3)
            input_info['element'].send_keys(Keys.BACKSPACE)
            time.sleep(0.5)
            print("  → 已清空输入框")
        except Exception as e:
            print(f"  ⚠ Selenium清空失败: {e}")

        driver.execute_script("""
            var input = arguments[0];
            input.value = '';
            input.dispatchEvent(new Event('input', {bubbles: true}));
        """, input_info['element'])
        time.sleep(0.5)

        try:
            input_info['element'].send_keys("0.8")
            time.sleep(0.5)
            print("  → 已输入 0.8 (Selenium)")
        except Exception as e:
            print(f"  ⚠ Selenium输入失败: {e}")
            driver.execute_script("""
                arguments[0].value = '0.8';
            """, input_info['element'])
            print("  → 已输入 0.8 (JavaScript)")

        time.sleep(0.5)

        driver.execute_script("""
            var input = arguments[0];
            input.dispatchEvent(new Event('input', {bubbles: true, cancelable: true}));
            input.dispatchEvent(new Event('change', {bubbles: true, cancelable: true}));
            input.dispatchEvent(new KeyboardEvent('keydown', {bubbles: true, cancelable: true}));
            input.dispatchEvent(new KeyboardEvent('keyup', {bubbles: true, cancelable: true}));
            input.dispatchEvent(new FocusEvent('blur', {bubbles: true, cancelable: true}));
        """, input_info['element'])

        time.sleep(1)

        final_value = driver.execute_script("return arguments[0].value;", input_info['element'])
        print(f"  → 最终值: {final_value}")

        if final_value == "0.8":
            print(f"✓ 成功设置配送完成率为: {final_value}")
        else:
            print(f"⚠ 值可能未正确设置，当前显示: {final_value}")
            driver.execute_script("""
                var input = arguments[0];
                var nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
                nativeInputValueSetter.call(input, '0.8');
                input.dispatchEvent(new Event('input', {bubbles: true}));
                input.dispatchEvent(new Event('change', {bubbles: true}));
            """, input_info['element'])
            time.sleep(1)
            final_value = driver.execute_script("return arguments[0].value;", input_info['element'])
            print(f"  → 最后尝试后的值: {final_value}")

        driver.execute_script("arguments[0].style.border=''; arguments[0].style.backgroundColor='';",
                              input_info['element'])

        time.sleep(2)

        print(f"{'=' * 60}")
        print("✓ 配送完成率设置完成")
        print(f"{'=' * 60}")

        return True

    except Exception as e:
        print(f"❌ 设置配送完成率异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def select_delivery_rate_fields():
    """在已选字段中选择1天、2天、3天妥投率 - 修复版"""
    try:
        print(f"\n{'=' * 60}")
        print("设置已选字段：选择妥投率")
        print(f"{'=' * 60}")

        print("\n[步骤1] 查找并点击'已选字段'下拉触发器...")

        field_button_info = driver.execute_script("""
            var dropdown = document.querySelector('.ant-dropdown-trigger.indicator-filter-dropdown');

            if (dropdown) {
                var rect = dropdown.getBoundingClientRect();
                var isVisible = rect.width > 0 && rect.height > 0 && dropdown.offsetParent !== null;

                if (isVisible) {
                    var titleSpan = dropdown.querySelector('.indicator-filter-title');
                    var text = titleSpan ? (titleSpan.textContent || titleSpan.innerText || '') : '';

                    return {
                        element: dropdown,
                        text: text.trim(),
                        x: Math.round(rect.x),
                        y: Math.round(rect.y),
                        className: dropdown.className,
                        method: 'exact'
                    };
                }
            }

            return null;
        """)

        if not field_button_info:
            print("❌ 未找到'已选字段'下拉触发器")
            return False

        print(f"✓ 找到'已选字段'下拉触发器")
        print(f"  文本: {field_button_info['text']}")
        print(f"  位置: ({field_button_info['x']}, {field_button_info['y']})")

        driver.execute_script(
            "arguments[0].style.border='3px solid blue';"
            "arguments[0].style.boxShadow='0 0 10px blue';"
            "arguments[0].style.backgroundColor='lightyellow';",
            field_button_info['element']
        )
        time.sleep(1.5)

        try:
            field_button_info['element'].click()
            print("✓ 已点击'已选字段'（普通点击）")
        except:
            driver.execute_script("arguments[0].click();", field_button_info['element'])
            print("✓ 已点击'已选字段'（JavaScript点击）")

        time.sleep(4)

        driver.execute_script(
            "arguments[0].style.border='';"
            "arguments[0].style.boxShadow='';"
            "arguments[0].style.backgroundColor='';",
            field_button_info['element']
        )

        print("\n[步骤2] 列出所有可选字段...")

        all_available_fields = driver.execute_script("""
            var allFields = [];
            var items = document.querySelectorAll(
                '.filter-indicator-container .menu-item-type-field, ' +
                '.filter-indicator-container .ant-tree-treenode'
            );

            for (var i = 0; i < items.length; i++) {
                var item = items[i];
                var rect = item.getBoundingClientRect();
                var isVisible = rect.width > 0 && rect.height > 0 && item.offsetParent !== null;

                if (isVisible) {
                    var textSpan = item.querySelector('.menu-item-name-text');
                    if (textSpan) {
                        var text = (textSpan.textContent || textSpan.innerText || '').trim();

                        if (text && text.length > 0 && text.length < 100) {
                            var checkbox = item.querySelector('input[type="checkbox"]');
                            var isChecked = checkbox ? checkbox.checked : null;

                            allFields.push({
                                text: text,
                                checked: isChecked,
                                hasCheckbox: checkbox !== null,
                                disabled: checkbox ? checkbox.disabled : false
                            });
                        }
                    }
                }
            }

            return allFields;
        """)

        print(f"\n找到 {len(all_available_fields)} 个可选字段：")
        print("=" * 80)
        for idx, field in enumerate(all_available_fields, 1):
            if field.get('disabled'):
                checked_status = "🔒 禁用"
            elif field.get('checked'):
                checked_status = "✓ 已选"
            elif field.get('hasCheckbox'):
                checked_status = "☐ 未选"
            else:
                checked_status = "  无框"
            print(f"{idx:3d}. [{checked_status}] {field['text']}")
        print("=" * 80)

        target_fields = ["1天妥投率", "2天妥投率", "3天妥投率"]
        print(f"\n[步骤3] 开始选择字段: {', '.join(target_fields)}")
        print("  → 每个字段将尝试最多3次，确保勾选成功")

        selected_count = 0

        for idx, field_name in enumerate(target_fields, 1):
            print(f"\n  [{idx}/{len(target_fields)}] 处理字段: {field_name}")

            # 每个字段最多尝试3次
            field_checked = False

            for try_num in range(1, 4):
                if try_num > 1:
                    print(f"    → 第{try_num}次尝试...")
                    time.sleep(1)

                field_result = driver.execute_script(f"""
                    var fieldName = '{field_name}';
                    var allItems = document.querySelectorAll('.filter-indicator-container .menu-item-type-field');

                    for (var i = 0; i < allItems.length; i++) {{
                        var item = allItems[i];
                        var textSpan = item.querySelector('.menu-item-name-text');

                        if (textSpan) {{
                            var text = (textSpan.textContent || textSpan.innerText || '').trim();

                            if (text === fieldName) {{
                                var rect = item.getBoundingClientRect();
                                var isVisible = rect.width > 0 && rect.height > 0 && item.offsetParent !== null;

                                if (isVisible) {{
                                    var checkbox = item.querySelector('input[type="checkbox"]');

                                    // 滚动到可见区域
                                    item.scrollIntoView({{block: 'center', behavior: 'smooth'}});

                                    return {{
                                        element: item,
                                        checkbox: checkbox,
                                        text: text,
                                        x: Math.round(rect.x),
                                        y: Math.round(rect.y),
                                        isChecked: checkbox ? checkbox.checked : false,
                                        isDisabled: checkbox ? checkbox.disabled : false
                                    }};
                                }}
                            }}
                        }}
                    }}

                    return null;
                """)

                if not field_result:
                    print(f"    ❌ 未找到字段: {field_name}")
                    if try_num < 3:
                        continue
                    else:
                        break

                print(f"    ✓ 找到字段: {field_result['text']}")
                print(f"      位置: ({field_result['x']}, {field_result['y']})")
                print(f"      状态: {'已勾选' if field_result.get('isChecked') else '未勾选'}")

                if field_result.get('isChecked'):
                    print(f"    → 字段已勾选")
                    selected_count += 1
                    field_checked = True
                    break

                if field_result.get('isDisabled'):
                    print(f"    → 字段已禁用，跳过")
                    break

                # 高亮
                driver.execute_script(
                    "arguments[0].style.border='2px solid green';"
                    "arguments[0].style.backgroundColor='lightgreen';",
                    field_result['element']
                )
                time.sleep(0.5)

                if field_result.get('checkbox'):
                    try:
                        checkbox_elem = driver.execute_script("return arguments[0];", field_result['checkbox'])

                        # 尝试多种点击方式
                        click_success = False

                        # 方式1: JavaScript点击checkbox
                        try:
                            driver.execute_script("arguments[0].click();", checkbox_elem)
                            time.sleep(0.3)
                            click_success = True
                            print(f"    ✓ 已点击checkbox（JavaScript）")
                        except:
                            pass

                        # 方式2: 如果失败，点击父元素
                        if not click_success:
                            try:
                                field_result['element'].click()
                                time.sleep(0.3)
                                click_success = True
                                print(f"    ✓ 已点击字段元素")
                            except:
                                pass

                        # 方式3: Selenium直接点击
                        if not click_success:
                            try:
                                checkbox_elem.click()
                                time.sleep(0.3)
                                click_success = True
                                print(f"    ✓ 已点击checkbox（Selenium）")
                            except:
                                pass

                        if click_success:
                            time.sleep(0.5)

                            # 验证是否勾选成功
                            is_checked_now = driver.execute_script("return arguments[0].checked;", checkbox_elem)
                            if is_checked_now:
                                print(f"    ✓ 验证：checkbox已成功勾选")
                                selected_count += 1
                                field_checked = True
                                break
                            else:
                                print(f"    ⚠ checkbox可能未成功勾选，将重试")
                        else:
                            print(f"    ⚠ 所有点击方式都失败")

                    except Exception as e:
                        print(f"    ❌ checkbox操作失败: {e}")

                # 移除高亮
                driver.execute_script(
                    "arguments[0].style.border='';"
                    "arguments[0].style.backgroundColor='';",
                    field_result['element']
                )

                time.sleep(0.8)

            if not field_checked:
                print(f"    ❌ 字段 '{field_name}' 最终未能成功勾选")

        print(f"\n  ✓ 完成: {selected_count}/{len(target_fields)} 个字段已选择")

        print("\n[步骤4] 查找并点击确定按钮...")
        time.sleep(2)

        # 多种方式查找确定按钮
        confirm_button_clicked = False

        # 方式1: 在弹出菜单中查找蓝色的确定按钮
        for attempt in range(3):
            print(f"  → 第{attempt + 1}次尝试查找确定按钮...")

            confirm_result = driver.execute_script("""
                var confirmButton = null;
                var allButtons = document.querySelectorAll('button');

                // 查找所有可能的确定按钮
                for (var i = 0; i < allButtons.length; i++) {
                    var btn = allButtons[i];
                    var text = (btn.textContent || btn.innerText || '').trim();
                    var rect = btn.getBoundingClientRect();
                    var isVisible = rect.width > 0 && rect.height > 0 && 
                                  btn.offsetParent !== null && !btn.disabled;

                    // 检查是否是确定按钮（文本匹配或者是蓝色按钮）
                    var isPrimaryButton = btn.classList.contains('ant-btn-primary') || 
                                         btn.classList.contains('primary-button') ||
                                         btn.style.backgroundColor.includes('blue') ||
                                         btn.style.backgroundColor.includes('rgb');

                    if (isVisible && (text === '确定' || text === '确 定' || 
                                     (isPrimaryButton && (text === '确定' || text === 'OK' || text === '完成')))) {
                        confirmButton = {
                            element: btn,
                            text: text,
                            x: Math.round(rect.x),
                            y: Math.round(rect.y),
                            className: btn.className
                        };
                        break;
                    }
                }

                if (confirmButton) {
                    confirmButton.element.style.border = '3px solid orange';
                    confirmButton.element.style.boxShadow = '0 0 10px orange';
                    return confirmButton;
                }

                return null;
            """)

            if confirm_result:
                print(f"    ✓ 找到确定按钮: '{confirm_result['text']}'")
                print(f"      位置: ({confirm_result.get('x', 0)}, {confirm_result.get('y', 0)})")
                print(f"      类名: {confirm_result.get('className', 'N/A')}")

                # 尝试点击
                try:
                    # 方式1: 直接点击
                    confirm_elem = driver.execute_script("return arguments[0];", confirm_result['element'])
                    confirm_elem.click()
                    print(f"    ✓ 成功点击确定按钮（普通点击）")
                    confirm_button_clicked = True
                    break
                except:
                    try:
                        # 方式2: JavaScript点击
                        driver.execute_script("arguments[0].click();", confirm_result['element'])
                        print(f"    ✓ 成功点击确定按钮（JavaScript点击）")
                        confirm_button_clicked = True
                        break
                    except Exception as e:
                        print(f"    ⚠ 点击失败: {e}")
                        if attempt < 2:
                            time.sleep(1)
            else:
                print(f"    ⚠ 未找到确定按钮")
                if attempt < 2:
                    time.sleep(1)

        # 方式2: 如果上面的方法都失败，尝试通过坐标点击右下角
        if not confirm_button_clicked:
            print("\n  → 尝试通过坐标点击右下角的确定按钮...")
            try:
                # 获取字段选择器的位置
                menu_info = driver.execute_script("""
                    var menu = document.querySelector('.filter-indicator-container');
                    if (menu) {
                        var rect = menu.getBoundingClientRect();
                        return {
                            x: Math.round(rect.x),
                            y: Math.round(rect.y),
                            width: Math.round(rect.width),
                            height: Math.round(rect.height)
                        };
                    }
                    return null;
                """)

                if menu_info:
                    # 计算右下角确定按钮的大致位置
                    button_x = menu_info['x'] + menu_info['width'] - 60
                    button_y = menu_info['y'] + menu_info['height'] - 30

                    # 使用ActionChains点击
                    actions.move_by_offset(button_x, button_y).click().perform()
                    actions.move_by_offset(-button_x, -button_y).perform()  # 重置鼠标位置
                    print(f"    ✓ 已通过坐标点击确定按钮")
                    confirm_button_clicked = True
            except Exception as e:
                print(f"    ⚠ 坐标点击失败: {e}")

        # 方式3: 如果还是失败，按ESC或点击已选字段来关闭
        if not confirm_button_clicked:
            print("\n  → 所有点击方式都失败，尝试按ESC关闭...")
            try:
                actions.send_keys(Keys.ESCAPE).perform()
                print(f"    ✓ 已按ESC键关闭")
                time.sleep(1)
            except:
                pass

        time.sleep(3)

        print(f"\n{'=' * 60}")
        print(f"✓ 已选字段设置完成（成功选择: {selected_count}/{len(target_fields)}）")
        print(f"{'=' * 60}")

        return selected_count > 0

    except Exception as e:
        print(f"\n❌ 设置已选字段异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def find_and_click_query_button():
    """查找并点击查询按钮"""
    try:
        print("\n" + "=" * 60)
        print("查找并点击查询按钮（完成率右侧最近的）")
        print("=" * 60)

        rate_input_pos = driver.execute_script("""
            var inputs = document.querySelectorAll('input.ant-input-number-input');
            for (var i = 0; i < inputs.length; i++) {
                var input = inputs[i];
                var rect = input.getBoundingClientRect();
                var value = input.value;
                if (rect.width > 0 && rect.height > 0 && (value === '0.8' || value === '0.9')) {
                    return {
                        x: rect.x + rect.width,
                        y: rect.y + rect.height / 2,
                        width: rect.width,
                        height: rect.height
                    };
                }
            }
            return null;
        """)

        if rate_input_pos:
            print(f"✓ 找到完成率输入框位置: ({rate_input_pos['x']}, {rate_input_pos['y']})")
        else:
            print("⚠ 未找到完成率输入框，使用默认查找方式")

        button_info = driver.execute_script("""
            var ratePos = arguments[0];
            var buttons = document.querySelectorAll('button.query-area-button, button.query-button, button.ant-btn-primary, button');
            var candidates = [];

            for (var i = 0; i < buttons.length; i++) {
                var btn = buttons[i];
                var text = btn.textContent || btn.innerText || '';
                var rect = btn.getBoundingClientRect();
                var isVisible = rect.width > 0 && rect.height > 0 && btn.offsetParent !== null;

                if (isVisible && !btn.disabled && (text.includes('查询') || text.includes('查 询'))) {
                    var btnCenterX = rect.x + rect.width / 2;
                    var btnCenterY = rect.y + rect.height / 2;

                    var distance = 999999;
                    var isRight = false;

                    if (ratePos) {
                        var dx = btnCenterX - ratePos.x;
                        var dy = btnCenterY - ratePos.y;
                        distance = Math.sqrt(dx * dx + dy * dy);
                        isRight = btnCenterX > ratePos.x;

                        if (isRight) {
                            distance = distance * 0.5;
                        }
                    }

                    candidates.push({
                        element: btn,
                        text: text.trim(),
                        x: Math.round(rect.x),
                        y: Math.round(rect.y),
                        className: btn.className,
                        distance: distance,
                        isRight: isRight
                    });
                }
            }

            candidates.sort(function(a, b) { 
                return a.distance - b.distance; 
            });

            return candidates.length > 0 ? candidates[0] : null;
        """, rate_input_pos)

        if not button_info:
            print("❌ 未找到查询按钮")
            return False

        position_info = "右侧" if button_info.get('isRight') else "左侧"
        print(f"✓ 找到最近的查询按钮 [{position_info}]")
        print(f"  文本: '{button_info['text']}'")
        print(f"  位置: ({button_info['x']}, {button_info['y']})")

        driver.execute_script(
            "arguments[0].style.border='3px solid red';"
            "arguments[0].style.boxShadow='0 0 10px red';",
            button_info['element']
        )
        time.sleep(1.5)

        try:
            button_info['element'].click()
            print("✓ 成功点击查询按钮（普通点击）")
        except:
            driver.execute_script("arguments[0].click();", button_info['element'])
            print("✓ 成功点击查询按钮（JavaScript点击）")

        time.sleep(0.5)

        driver.execute_script(
            "arguments[0].style.border='';"
            "arguments[0].style.boxShadow='';",
            button_info['element']
        )

        time.sleep(5)

        print("=" * 60)
        return True

    except Exception as e:
        print(f"❌ 查找查询按钮异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主流程"""
    try:
        print("\n" + "=" * 60)
        print("开始执行自动化流程")
        print("=" * 60)

        print("\n[1/9] 执行登录...")
        if not login():
            print("❌ 登录失败，退出")
            return

        print("\n[2/9] 打开QBI页面...")
        driver.get(QBI_URL)
        time.sleep(5)
        print("✓ QBI页面已打开")

        print("\n[3/9] 点击other-login...")
        if not click_other_login():
            print("⚠ 点击other-login失败，尝试继续")
            time.sleep(2)

        time.sleep(5)

        print("\n[4/9] 切换到iframe...")
        if not switch_to_iframe():
            print("❌ 切换iframe失败，退出")
            return

        print("\n[5/9] 点击第四个tab...")
        if not click_fourth_tab():
            print("⚠ 点击第四个tab可能失败，但继续执行")

        time.sleep(3)

        print("\n[6/9] 设置日期（昨天到今天）...")
        date_success = set_dates_via_calendar()
        if date_success:
            print("✓ 日期设置完成")
        else:
            print("⚠ 日期设置可能失败")

        print("\n[7/9] 设置提货仓（包含COL）...")
        warehouse_success = set_warehouse_selection()
        if warehouse_success:
            print("✓ 提货仓设置完成")
        else:
            print("⚠ 提货仓设置可能失败")

        print("\n[8/9] 设置配送完成率...")
        rate_success = set_delivery_completion_rate()
        if rate_success:
            print("✓ 配送完成率设置完成")
        else:
            print("⚠ 配送完成率设置可能失败")

        print("\n[9/9] 设置已选字段（妥投率）...")
        field_success = select_delivery_rate_fields()
        if field_success:
            print("✓ 已选字段设置完成")
        else:
            print("⚠ 已选字段设置可能失败")

        print("\n等待5秒确保设置生效...")
        time.sleep(5)

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

        print("\n等待查询结果加载...")
        time.sleep(5)

        print("\n" + "=" * 60)
        print("✓ 流程执行完毕")
        print("=" * 60)
        print("\n浏览器保持打开状态，请检查结果")
        print("请查看已选字段是否显示为 '已选字段(16)' 或更多")

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