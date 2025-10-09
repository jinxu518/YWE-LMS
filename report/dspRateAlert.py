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
            fourth_tab = tabs[3]  # 修改：索引改为3，即第4个tab
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
    """通过点击日历设置日期 - 修改为昨天到今天"""
    today = datetime.today()
    yesterday = today - timedelta(days=1)  # 修改：改为昨天
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


def set_delivery_completion_rate():
    """新增：设置分箱配送完成率为0.8"""
    try:
        print(f"\n{'=' * 60}")
        print("设置分箱配送完成率为 0.8")
        print(f"{'=' * 60}")

        # 直接查找 ant-input-number-input 类的输入框，值为0.9的
        input_info = driver.execute_script("""
            var allInputs = document.querySelectorAll('input.ant-input-number-input');
            var targetInput = null;

            for (var i = 0; i < allInputs.length; i++) {
                var input = allInputs[i];
                var rect = input.getBoundingClientRect();
                var isVisible = rect.width > 0 && rect.height > 0 && input.offsetParent !== null;
                var value = input.value;

                // 查找值为0.9的输入框
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
            # 尝试查找所有ant-input-number-input并打印
            all_inputs = driver.execute_script("""
                var inputs = document.querySelectorAll('input.ant-input-number-input');
                var result = [];
                for (var i = 0; i < inputs.length; i++) {
                    var rect = inputs[i].getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {
                        result.push({
                            value: inputs[i].value,
                            placeholder: inputs[i].placeholder
                        });
                    }
                }
                return result;
            """)
            print(f"找到的所有数字输入框: {all_inputs}")
            return False

        print(f"✓ 找到输入框，当前值: {input_info['currentValue']}, 位置: ({input_info['x']}, {input_info['y']})")

        # 高亮输入框
        driver.execute_script(
            "arguments[0].style.border='3px solid blue';"
            "arguments[0].style.backgroundColor='lightyellow';",
            input_info['element']
        )
        time.sleep(1)

        # 方法1: 先用Selenium点击并清空
        try:
            input_info['element'].click()
            time.sleep(0.5)

            # 全选
            input_info['element'].send_keys(Keys.CONTROL + "a")
            time.sleep(0.3)

            # 删除
            input_info['element'].send_keys(Keys.BACKSPACE)
            time.sleep(0.5)

            print("  → 已清空输入框")
        except Exception as e:
            print(f"  ⚠ Selenium清空失败: {e}")

        # 方法2: 使用JavaScript强制清空
        driver.execute_script("""
            var input = arguments[0];
            input.value = '';
            input.dispatchEvent(new Event('input', {bubbles: true}));
        """, input_info['element'])
        time.sleep(0.5)

        # 方法3: 使用Selenium输入新值
        try:
            input_info['element'].send_keys("0.8")
            time.sleep(0.5)
            print("  → 已输入 0.8 (Selenium)")
        except Exception as e:
            print(f"  ⚠ Selenium输入失败: {e}")
            # 备用：JavaScript输入
            driver.execute_script("""
                arguments[0].value = '0.8';
            """, input_info['element'])
            print("  → 已输入 0.8 (JavaScript)")

        time.sleep(0.5)

        # 方法4: 触发所有可能的事件
        driver.execute_script("""
            var input = arguments[0];

            // 触发输入事件
            input.dispatchEvent(new Event('input', {bubbles: true, cancelable: true}));

            // 触发change事件
            input.dispatchEvent(new Event('change', {bubbles: true, cancelable: true}));

            // 触发键盘事件
            input.dispatchEvent(new KeyboardEvent('keydown', {bubbles: true, cancelable: true}));
            input.dispatchEvent(new KeyboardEvent('keyup', {bubbles: true, cancelable: true}));

            // 触发焦点事件
            input.dispatchEvent(new FocusEvent('blur', {bubbles: true, cancelable: true}));
        """, input_info['element'])

        time.sleep(1)

        # 验证值是否改变
        final_value = driver.execute_script("return arguments[0].value;", input_info['element'])
        print(f"  → 最终值: {final_value}")

        if final_value == "0.8":
            print(f"✓ 成功设置配送完成率为: {final_value}")
        else:
            print(f"⚠ 值可能未正确设置，当前显示: {final_value}")
            # 最后一次尝试
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

        # 移除高亮
        driver.execute_script("arguments[0].style.border=''; arguments[0].style.backgroundColor='';",
                              input_info['element'])

        time.sleep(2)  # 增加等待时间，确保值生效

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
    """新增：在已选字段中选择1天、2天、3天妥投率"""
    try:
        print(f"\n{'=' * 60}")
        print("设置已选字段：选择妥投率")
        print(f"{'=' * 60}")

        # 步骤1: 查找并点击"已选字段"下拉触发器
        print("\n[步骤1] 查找并点击'已选字段'下拉触发器...")

        field_button_info = driver.execute_script("""
            // 方法1: 精确查找 ant-dropdown-trigger indicator-filter-dropdown
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

            // 方法2: 通过indicator-filter-title查找
            var titleSpans = document.querySelectorAll('.indicator-filter-title');
            for (var i = 0; i < titleSpans.length; i++) {
                var span = titleSpans[i];
                var text = span.textContent || span.innerText || '';

                if (text.includes('已选字段')) {
                    var parent = span.parentElement;
                    var rect = parent.getBoundingClientRect();

                    if (rect.width > 0 && rect.height > 0 && parent.offsetParent !== null) {
                        return {
                            element: parent,
                            text: text.trim(),
                            x: Math.round(rect.x),
                            y: Math.round(rect.y),
                            className: parent.className,
                            method: 'parent'
                        };
                    }
                }
            }

            return null;
        """)

        if not field_button_info:
            print("❌ 未找到'已选字段'下拉触发器")
            return False

        print(f"✓ 找到'已选字段'下拉触发器 (方法: {field_button_info.get('method', 'unknown')})")
        print(f"  文本: {field_button_info['text']}")
        print(f"  位置: ({field_button_info['x']}, {field_button_info['y']})")
        print(f"  类名: {field_button_info['className']}")

        # 高亮并点击
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

        time.sleep(3)

        # 移除高亮
        driver.execute_script(
            "arguments[0].style.border='';"
            "arguments[0].style.boxShadow='';"
            "arguments[0].style.backgroundColor='';",
            field_button_info['element']
        )

        # 步骤2: 列出所有可选字段（调试用）
        print("\n[步骤2] 列出所有可选字段...")

        all_available_fields = driver.execute_script("""
            var allFields = [];

            // 正确的容器：filter-indicator-container，不是ant-dropdown！
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

        # 步骤3: 让用户确认
        print("\n请查看上面列出的字段。")
        print("脚本将选择: 1天妥投率, 2天妥投率, 3天妥投率")
        print("\n继续等待3秒后选择...")
        time.sleep(3)

        # 步骤4: 选择字段
        target_fields = ["1天妥投率", "2天妥投率", "3天妥投率"]
        print(f"\n[步骤3] 开始选择字段: {', '.join(target_fields)}")

        selected_count = 0

        for idx, field_name in enumerate(target_fields, 1):
            print(f"\n  [{idx}/{len(target_fields)}] 查找字段: {field_name}")

            # 在正确的容器里查找字段
            field_result = driver.execute_script(f"""
                var fieldName = '{field_name}';

                // 在 filter-indicator-container 里查找
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
                continue

            print(f"    ✓ 找到字段: {field_result['text']}")
            print(f"      位置: ({field_result['x']}, {field_result['y']})")
            print(f"      状态: {'已勾选' if field_result.get('isChecked') else '未勾选'}")

            # 如果已经勾选，跳过
            if field_result.get('isChecked'):
                print(f"    → 字段已勾选，跳过")
                continue

            # 如果禁用，跳过
            if field_result.get('isDisabled'):
                print(f"    → 字段已禁用，跳过")
                continue

            # 高亮
            driver.execute_script(
                "arguments[0].style.border='2px solid green';"
                "arguments[0].style.backgroundColor='lightgreen';",
                field_result['element']
            )
            time.sleep(0.8)

            # 点击checkbox
            if field_result.get('checkbox'):
                try:
                    checkbox_elem = driver.execute_script("return arguments[0];", field_result['checkbox'])

                    # 使用JavaScript点击
                    driver.execute_script("arguments[0].click();", checkbox_elem)
                    print(f"    ✓ 已勾选checkbox")
                    selected_count += 1
                    time.sleep(0.5)

                    # 验证是否勾选成功
                    is_checked_now = driver.execute_script("return arguments[0].checked;", checkbox_elem)
                    if is_checked_now:
                        print(f"    ✓ 验证：checkbox已成功勾选")
                    else:
                        print(f"    ⚠ 警告：checkbox可能未成功勾选")

                except Exception as e:
                    print(f"    ❌ checkbox操作失败: {e}")

            # 移除高亮
            driver.execute_script(
                "arguments[0].style.border='';"
                "arguments[0].style.backgroundColor='';",
                field_result['element']
            )

            time.sleep(1)

        print(f"\n  完成: {selected_count}/{len(target_fields)} 个字段已选择")

        # 步骤5: 不需要点确定按钮，直接关闭选择器
        print("\n[步骤4] 关闭字段选择器...")
        time.sleep(1)

        # 再次点击"已选字段"来关闭
        try:
            field_button_info['element'].click()
            print("✓ 已关闭字段选择器（点击已选字段）")
        except:
            driver.execute_script("arguments[0].click();", field_button_info['element'])
            print("✓ 已关闭字段选择器（JavaScript点击）")

        time.sleep(2)

        print(f"\n{'=' * 60}")
        print(f"✓ 已选字段设置完成（成功选择: {selected_count}/{len(target_fields)}）")
        print(f"{'=' * 60}")

        return True

    except Exception as e:
        print(f"\n❌ 设置已选字段异常: {e}")
        import traceback
        traceback.print_exc()
        return False

        # 步骤2: 等待下拉菜单出现
        print("\n[步骤2] 等待下拉菜单出现...")
        time.sleep(3)

        # 检查下拉菜单是否出现
        dropdown_visible = driver.execute_script("""
            var dropdowns = document.querySelectorAll('.ant-dropdown, .dropdown-menu, [class*="dropdown"]');
            for (var i = 0; i < dropdowns.length; i++) {
                var dd = dropdowns[i];
                var rect = dd.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0 && dd.offsetParent !== null) {
                    return {
                        visible: true,
                        className: dd.className,
                        x: Math.round(rect.x),
                        y: Math.round(rect.y)
                    };
                }
            }
            return {visible: false};
        """)

        if dropdown_visible.get('visible'):
            print(f"✓ 下拉菜单已出现")
            print(f"  类名: {dropdown_visible.get('className', 'N/A')}")
            print(f"  位置: ({dropdown_visible.get('x', 0)}, {dropdown_visible.get('y', 0)})")
        else:
            print("⚠ 下拉菜单可能未出现，尝试继续")

        # 步骤3: 查找并选择三个妥投率字段
        target_fields = ["1天妥投率", "2天妥投率", "3天妥投率"]  # 修改为数字形式
        print(f"\n[步骤3] 开始选择字段: {', '.join(target_fields)}")

        selected_count = 0

        for idx, field_name in enumerate(target_fields, 1):
            print(f"\n  [{idx}/{len(target_fields)}] 查找字段: {field_name}")

            # 查找字段选项
            field_result = driver.execute_script(f"""
                var fieldName = '{field_name}';

                // 查找所有可能包含字段的元素
                var allElements = document.querySelectorAll(
                    '.ant-dropdown label, .ant-dropdown .ant-checkbox-wrapper, ' +
                    '.dropdown-menu label, .dropdown-menu .checkbox, ' +
                    'li, .menu-item, .ant-dropdown-menu-item, ' +
                    'div[class*="item"], div[class*="field"], ' +
                    'span, label'
                );

                var candidates = [];

                for (var i = 0; i < allElements.length; i++) {{
                    var elem = allElements[i];
                    var text = elem.textContent || elem.innerText || '';
                    var rect = elem.getBoundingClientRect();
                    var isVisible = rect.width > 0 && rect.height > 0 && elem.offsetParent !== null;

                    // 精确匹配字段名（去除空格后比较）
                    var cleanText = text.trim().replace(/\\s+/g, '');
                    var cleanFieldName = fieldName.replace(/\\s+/g, '');

                    if (isVisible && (cleanText === cleanFieldName || text.trim() === fieldName)) {{
                        // 查找关联的checkbox
                        var checkbox = elem.querySelector('input[type="checkbox"]');
                        if (!checkbox) {{
                            var parent = elem.closest('label, .checkbox, .ant-checkbox-wrapper, li, .menu-item');
                            if (parent) {{
                                checkbox = parent.querySelector('input[type="checkbox"]');
                            }}
                        }}

                        candidates.push({{
                            element: elem,
                            checkbox: checkbox,
                            text: text.trim(),
                            x: Math.round(rect.x),
                            y: Math.round(rect.y),
                            tag: elem.tagName,
                            class: elem.className
                        }});

                        // 精确匹配就用第一个
                        break;
                    }}
                }}

                // 如果精确匹配没找到，尝试模糊匹配
                if (candidates.length === 0) {{
                    for (var i = 0; i < allElements.length; i++) {{
                        var elem = allElements[i];
                        var text = elem.textContent || elem.innerText || '';
                        var rect = elem.getBoundingClientRect();
                        var isVisible = rect.width > 0 && rect.height > 0 && elem.offsetParent !== null;

                        if (isVisible && text.includes(fieldName)) {{
                            var checkbox = elem.querySelector('input[type="checkbox"]');
                            if (!checkbox) {{
                                var parent = elem.closest('label, .checkbox, .ant-checkbox-wrapper, li, .menu-item');
                                if (parent) {{
                                    checkbox = parent.querySelector('input[type="checkbox"]');
                                }}
                            }}

                            candidates.push({{
                                element: elem,
                                checkbox: checkbox,
                                text: text.trim(),
                                x: Math.round(rect.x),
                                y: Math.round(rect.y),
                                tag: elem.tagName,
                                class: elem.className
                            }});
                            break;
                        }}
                    }}
                }}

                return candidates.length > 0 ? candidates[0] : null;
            """)

            if not field_result:
                print(f"    ❌ 未找到字段: {field_name}")
                # 调试信息 - 显示所有包含"妥投率"的文本
                debug_fields = driver.execute_script("""
                    var items = document.querySelectorAll('.ant-dropdown *, .dropdown-menu *');
                    var texts = [];
                    for (var i = 0; i < items.length; i++) {
                        var rect = items[i].getBoundingClientRect();
                        if (rect.width > 0 && rect.height > 0) {
                            var text = (items[i].textContent || '').trim();
                            if (text && text.includes('妥投率') && text.length < 50) {
                                texts.push(text);
                            }
                        }
                    }
                    return [...new Set(texts)];
                """)
                print(f"    调试：找到的妥投率相关字段: {debug_fields}")
                continue

            print(f"    ✓ 找到字段: {field_result['text']}")
            print(f"      位置: ({field_result['x']}, {field_result['y']})")
            print(f"      标签: {field_result['tag']}, 类: {field_result.get('class', 'N/A')[:50]}")

            # 高亮
            driver.execute_script(
                "arguments[0].style.border='2px solid green';"
                "arguments[0].style.backgroundColor='lightgreen';",
                field_result['element']
            )
            time.sleep(0.8)

            # 点击选择
            clicked = False

            # 方法1: 如果有checkbox，先检查是否已勾选
            if field_result.get('checkbox'):
                try:
                    checkbox_elem = driver.execute_script("return arguments[0];", field_result['checkbox'])
                    is_checked = driver.execute_script("return arguments[0].checked;", checkbox_elem)

                    print(f"      Checkbox状态: {'已勾选' if is_checked else '未勾选'}")

                    if not is_checked:
                        # 尝试点击checkbox
                        try:
                            driver.execute_script("arguments[0].click();", checkbox_elem)
                            clicked = True
                            print(f"    ✓ 已勾选checkbox (JavaScript)")
                        except:
                            # 如果checkbox不能点击，点击父元素
                            try:
                                field_result['element'].click()
                                clicked = True
                                print(f"    ✓ 已点击字段元素")
                            except:
                                driver.execute_script("arguments[0].click();", field_result['element'])
                                clicked = True
                                print(f"    ✓ 已点击字段元素 (JavaScript)")
                    else:
                        print(f"    → 字段已勾选，跳过")
                        clicked = True
                except Exception as e:
                    print(f"    ⚠ checkbox操作失败: {e}")

            # 方法2: 点击元素本身
            if not clicked:
                try:
                    driver.execute_script("arguments[0].click();", field_result['element'])
                    clicked = True
                    print(f"    ✓ 已点击字段元素 (JavaScript)")
                except Exception as e:
                    print(f"    ❌ 点击失败: {e}")

            if clicked:
                selected_count += 1

            # 移除高亮
            driver.execute_script(
                "arguments[0].style.border='';"
                "arguments[0].style.backgroundColor='';",
                field_result['element']
            )

            time.sleep(1)

        print(f"\n  完成: {selected_count}/{len(target_fields)} 个字段已选择")

        # 步骤4: 查找并点击确定按钮
        print("\n[步骤4] 查找并点击确定按钮...")
        time.sleep(1.5)

        # 尝试多种方式查找确定按钮
        confirm_result = driver.execute_script("""
            // 方法1: 在下拉菜单内查找确定按钮
            var dropdowns = document.querySelectorAll('.ant-dropdown, .dropdown-menu');
            var confirmButton = null;

            for (var d = 0; d < dropdowns.length; d++) {
                var dropdown = dropdowns[d];
                var rect = dropdown.getBoundingClientRect();

                if (rect.width > 0 && rect.height > 0 && dropdown.offsetParent !== null) {
                    var buttons = dropdown.querySelectorAll('button');

                    for (var i = 0; i < buttons.length; i++) {
                        var btn = buttons[i];
                        var text = (btn.textContent || btn.innerText || '').trim();
                        var btnRect = btn.getBoundingClientRect();
                        var isVisible = btnRect.width > 0 && btnRect.height > 0 && 
                                      btn.offsetParent !== null && !btn.disabled;

                        if (isVisible && (text === '确 定' || text === '确定' || text === 'OK' || text === '应用' || text === '完成')) {
                            confirmButton = {
                                element: btn,
                                text: text,
                                x: Math.round(btnRect.x),
                                y: Math.round(btnRect.y),
                                location: 'dropdown'
                            };
                            break;
                        }
                    }

                    if (confirmButton) break;
                }
            }

            // 方法2: 如果下拉菜单里没找到，在整个页面查找
            if (!confirmButton) {
                var allButtons = document.querySelectorAll('button');

                for (var i = 0; i < allButtons.length; i++) {
                    var btn = allButtons[i];
                    var text = (btn.textContent || btn.innerText || '').trim();
                    var btnRect = btn.getBoundingClientRect();
                    var isVisible = btnRect.width > 0 && btnRect.height > 0 && 
                                  btn.offsetParent !== null && !btn.disabled;

                    if (isVisible && (text === '确 定' || text === '确定' || text === 'OK' || text === '应用' || text === '完成')) {
                        confirmButton = {
                            element: btn,
                            text: text,
                            x: Math.round(btnRect.x),
                            y: Math.round(btnRect.y),
                            location: 'page'
                        };
                        break;
                    }
                }
            }

            if (confirmButton) {
                confirmButton.element.style.border = '3px solid orange';
                confirmButton.element.style.boxShadow = '0 0 10px orange';

                try {
                    confirmButton.element.click();
                    return {
                        success: true, 
                        text: confirmButton.text,
                        x: confirmButton.x,
                        y: confirmButton.y,
                        location: confirmButton.location
                    };
                } catch(e) {
                    return {success: false, error: e.message};
                }
            }

            return {success: false, message: '未找到确定按钮'};
        """)

        if confirm_result.get('success'):
            print(f"  ✓ 已点击确定按钮: '{confirm_result['text']}'")
            print(f"    位置: ({confirm_result.get('x', 0)}, {confirm_result.get('y', 0)})")
            print(f"    来源: {confirm_result.get('location', 'unknown')}")
            time.sleep(2)
        else:
            print(f"  ⚠ {confirm_result.get('message', '确定按钮点击失败')}")
            # 列出所有可见按钮用于调试
            all_btns = driver.execute_script("""
                var buttons = document.querySelectorAll('button');
                var result = [];
                for (var i = 0; i < buttons.length; i++) {
                    var rect = buttons[i].getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {
                        result.push((buttons[i].textContent || '').trim());
                    }
                }
                return result.slice(0, 10);
            """)
            print(f"  调试：找到的前10个按钮: {all_btns}")

            # 尝试按ESC关闭
            try:
                actions.send_keys(Keys.ESCAPE).perform()
                print(f"  → 已按ESC键关闭")
                time.sleep(1)
            except:
                pass

        time.sleep(2)

        print(f"\n{'=' * 60}")
        print(f"✓ 已选字段设置完成 (成功选择: {selected_count}/{len(target_fields)})")
        print(f"{'=' * 60}")

        return selected_count > 0

    except Exception as e:
        print(f"\n❌ 设置已选字段异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def read_table_data():
    """新增：读取表格数据"""
    try:
        print(f"\n{'=' * 60}")
        print("开始读取表格数据")
        print(f"{'=' * 60}")

        time.sleep(3)  # 等待表格加载

        # 查找表格
        table_data = driver.execute_script("""
            var tables = document.querySelectorAll('table, .ant-table, .data-table, div[class*="table"]');
            var result = {
                found: false,
                tables: []
            };

            for (var i = 0; i < tables.length; i++) {
                var table = tables[i];
                var rect = table.getBoundingClientRect();
                var isVisible = rect.width > 0 && rect.height > 0 && table.offsetParent !== null;

                if (isVisible && rect.width > 200 && rect.height > 100) {
                    // 尝试读取表头
                    var headers = [];
                    var headerRows = table.querySelectorAll('thead tr, tr:first-child, div[class*="header"]');

                    if (headerRows.length > 0) {
                        var headerCells = headerRows[0].querySelectorAll('th, td, div[class*="cell"]');
                        for (var j = 0; j < headerCells.length; j++) {
                            var text = (headerCells[j].textContent || headerCells[j].innerText || '').trim();
                            if (text) headers.push(text);
                        }
                    }

                    // 尝试读取数据行
                    var rows = [];
                    var dataRows = table.querySelectorAll('tbody tr, tr:not(:first-child), div[class*="row"]:not([class*="header"])');

                    for (var k = 0; k < Math.min(dataRows.length, 20); k++) {
                        var row = dataRows[k];
                        var cells = row.querySelectorAll('td, div[class*="cell"]');
                        var rowData = [];

                        for (var m = 0; m < cells.length; m++) {
                            var cellText = (cells[m].textContent || cells[m].innerText || '').trim();
                            rowData.push(cellText);
                        }

                        if (rowData.length > 0) {
                            rows.push(rowData);
                        }
                    }

                    if (headers.length > 0 || rows.length > 0) {
                        result.tables.push({
                            index: i,
                            headers: headers,
                            rows: rows,
                            rowCount: dataRows.length,
                            x: Math.round(rect.x),
                            y: Math.round(rect.y)
                        });
                        result.found = true;
                    }
                }
            }

            return result;
        """)

        if not table_data['found'] or len(table_data['tables']) == 0:
            print("❌ 未找到可读取的表格")
            return False

        print(f"✓ 找到 {len(table_data['tables'])} 个表格")

        # 打印所有找到的表格数据
        for idx, table in enumerate(table_data['tables'], 1):
            print(f"\n{'─' * 60}")
            print(f"表格 #{idx} - 位置: ({table['x']}, {table['y']})")
            print(f"总行数: {table['rowCount']}")
            print(f"{'─' * 60}")

            # 打印表头
            if table['headers']:
                print("\n【表头】")
                print(" | ".join(table['headers']))
                print("─" * 60)

            # 打印数据行
            if table['rows']:
                print(f"\n【数据】(显示前{min(len(table['rows']), 10)}行)")
                for row_idx, row in enumerate(table['rows'][:10], 1):
                    print(f"{row_idx:3d}. {' | '.join(row)}")

                if len(table['rows']) > 10:
                    print(f"\n... 还有 {len(table['rows']) - 10} 行未显示")

        # 保存数据到文件
        try:
            import csv
            timestamp = int(time.time())

            for idx, table in enumerate(table_data['tables'], 1):
                filename = f"table_data_{timestamp}_table{idx}.csv"

                with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
                    writer = csv.writer(f)

                    # 写入表头
                    if table['headers']:
                        writer.writerow(table['headers'])

                    # 写入数据
                    for row in table['rows']:
                        writer.writerow(row)

                print(f"\n✓ 表格 #{idx} 已保存到: {filename}")

        except Exception as e:
            print(f"⚠ 保存CSV文件失败: {e}")

        print(f"\n{'=' * 60}")
        print("✓ 表格数据读取完成")
        print(f"{'=' * 60}")

        return True

    except Exception as e:
        print(f"❌ 读取表格数据异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def find_and_click_query_button():
    """查找并点击查询按钮 - 点击完成率输入框右侧最近的查询按钮"""
    try:
        print("\n" + "=" * 60)
        print("查找并点击查询按钮（完成率右侧最近的）")
        print("=" * 60)

        # 先找到完成率输入框的位置
        rate_input_pos = driver.execute_script("""
            var inputs = document.querySelectorAll('input.ant-input-number-input');
            for (var i = 0; i < inputs.length; i++) {
                var input = inputs[i];
                var rect = input.getBoundingClientRect();
                var value = input.value;
                if (rect.width > 0 && rect.height > 0 && (value === '0.8' || value === '0.9')) {
                    return {
                        x: rect.x + rect.width,  // 右边缘
                        y: rect.y + rect.height / 2,  // 中心点
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

        # 查找所有查询按钮，并计算与完成率输入框的距离
        button_info = driver.execute_script("""
            var ratePos = arguments[0];
            var buttons = document.querySelectorAll('button.query-area-button, button.query-button, button.ant-btn-primary, button');
            var candidates = [];

            for (var i = 0; i < buttons.length; i++) {
                var btn = buttons[i];
                var text = btn.textContent || btn.innerText || '';
                var rect = btn.getBoundingClientRect();
                var isVisible = rect.width > 0 && rect.height > 0 && btn.offsetParent !== null;

                // 查找包含"查询"或"查 询"的按钮
                if (isVisible && !btn.disabled && (text.includes('查询') || text.includes('查 询'))) {
                    var btnCenterX = rect.x + rect.width / 2;
                    var btnCenterY = rect.y + rect.height / 2;

                    var distance = 999999;
                    var isRight = false;

                    if (ratePos) {
                        // 计算距离（优先考虑右侧的按钮）
                        var dx = btnCenterX - ratePos.x;
                        var dy = btnCenterY - ratePos.y;
                        distance = Math.sqrt(dx * dx + dy * dy);
                        isRight = btnCenterX > ratePos.x;  // 是否在右侧

                        // 如果在右侧，距离权重降低（优先选择）
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

            // 按距离排序，选择最近的
            candidates.sort(function(a, b) { 
                return a.distance - b.distance; 
            });

            return candidates.length > 0 ? candidates[0] : null;
        """, rate_input_pos)

        if not button_info:
            print("❌ 未找到查询按钮")
            # 打印所有按钮用于调试
            all_buttons = driver.execute_script("""
                var buttons = document.querySelectorAll('button');
                var result = [];
                for (var i = 0; i < buttons.length; i++) {
                    var rect = buttons[i].getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {
                        result.push({
                            text: (buttons[i].textContent || buttons[i].innerText || '').trim(),
                            className: buttons[i].className,
                            x: Math.round(rect.x),
                            y: Math.round(rect.y)
                        });
                    }
                }
                return result.slice(0, 10);
            """)
            print(f"找到的前10个按钮: {all_buttons}")
            return False

        position_info = "右侧" if button_info.get('isRight') else "左侧"
        print(f"✓ 找到最近的查询按钮 [{position_info}]")
        print(f"  文本: '{button_info['text']}'")
        print(f"  位置: ({button_info['x']}, {button_info['y']})")
        print(f"  类名: {button_info['className']}")
        if rate_input_pos:
            print(f"  距离: {button_info.get('distance', 'N/A'):.1f}px")

        # 高亮按钮
        driver.execute_script(
            "arguments[0].style.border='3px solid red';"
            "arguments[0].style.boxShadow='0 0 10px red';",
            button_info['element']
        )
        time.sleep(1.5)

        # 点击按钮
        try:
            button_info['element'].click()
            print("✓ 成功点击查询按钮（普通点击）")
        except:
            driver.execute_script("arguments[0].click();", button_info['element'])
            print("✓ 成功点击查询按钮（JavaScript点击）")

        time.sleep(0.5)

        # 移除高亮
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

        # 登录
        print("\n[1/9] 执行登录...")
        if not login():
            print("❌ 登录失败，退出")
            return

        # 打开QBI页面
        print("\n[2/9] 打开QBI页面...")
        driver.get(QBI_URL)
        time.sleep(5)
        print("✓ QBI页面已打开")

        # 点击other-login
        print("\n[3/9] 点击other-login...")
        if not click_other_login():
            print("⚠ 点击other-login失败，尝试继续")
            time.sleep(2)

        time.sleep(5)

        # 切换iframe
        print("\n[4/9] 切换到iframe...")
        if not switch_to_iframe():
            print("❌ 切换iframe失败，退出")
            return

        # 点击第四个tab
        print("\n[5/9] 点击第四个tab...")
        if not click_fourth_tab():
            print("⚠ 点击第四个tab可能失败，但继续执行")

        time.sleep(3)

        # 通过日历设置日期（昨天到今天）
        print("\n[6/9] 设置日期（昨天到今天）...")
        date_success = set_dates_via_calendar()
        if date_success:
            print("✓ 日期设置完成")
        else:
            print("⚠ 日期设置可能失败")

        # 设置提货仓
        print("\n[7/9] 设置提货仓...")
        warehouse_success = set_warehouse_selection()
        if warehouse_success:
            print("✓ 提货仓设置完成")
        else:
            print("⚠ 提货仓设置可能失败")

        # 设置配送完成率为0.8
        print("\n[8/9] 设置配送完成率...")
        rate_success = set_delivery_completion_rate()
        if rate_success:
            print("✓ 配送完成率设置完成")
        else:
            print("⚠ 配送完成率设置可能失败")

        # 设置已选字段（妥投率）
        print("\n[9/9] 设置已选字段（妥投率）...")

        # 先截图看看当前状态
        try:
            screenshot_path = f"before_field_selection_{int(time.time())}.png"
            driver.save_screenshot(screenshot_path)
            print(f"  已保存设置前截图: {screenshot_path}")
        except:
            pass

        field_success = select_delivery_rate_fields()
        if field_success:
            print("✓ 已选字段设置完成")
        else:
            print("⚠ 已选字段设置可能失败")

        # 设置后再截图
        try:
            screenshot_path = f"after_field_selection_{int(time.time())}.png"
            driver.save_screenshot(screenshot_path)
            print(f"  已保存设置后截图: {screenshot_path}")
        except:
            pass

        # 等待一下确保设置生效
        print("\n等待5秒确保设置生效...")
        time.sleep(5)

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

        # 等待查询结果
        print("\n等待查询结果加载...")
        time.sleep(5)

        # 最终截图
        try:
            screenshot_path = f"final_result_{int(time.time())}.png"
            driver.save_screenshot(screenshot_path)
            print(f"✓ 已保存最终截图: {screenshot_path}")
        except:
            pass

        print("\n" + "=" * 60)
        print("✓ 流程执行完毕")
        print("=" * 60)
        print("\n浏览器保持打开状态，请检查结果")
        print("请查看已选字段是否显示为 '已选字段(13)'")

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