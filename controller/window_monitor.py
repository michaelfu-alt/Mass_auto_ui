"""
窗口监控和控制模块
用于监测和控制Recipe窗口和按钮
"""
import time
from PySide6.QtCore import Signal, QObject
from pywinauto import Desktop


class WindowMonitor(QObject):
    """监测和控制Recipe窗口和按钮"""
    window_status_changed = Signal(bool, str)  # (是否存在, 状态消息)
    
    def __init__(self):
        super().__init__()
        self.window_title = "Recipe: Setup Summary"  # 窗口名称关键字
        self.button_name = "Start Once"
        self.button_type = "Start Once"  # 按钮类型："Start Once" 或 "Start Continuous"
        self.window = None
        self.window_uia = None  # UIA后端的窗口
        self.button = None
        self.dropdown_button = None  # Start Continuous的下拉按钮
        self.backend = "win32"  # 默认使用win32查找窗口
        
    def check_window_exists(self):
        """检查窗口是否存在"""
        try:
            # 使用win32后端查找窗口
            print("\n使用 win32 后端查找窗口...")
            desktop = Desktop(backend="win32")
            windows = desktop.windows()
            
            for win in windows:
                try:
                    title = win.window_text()
                    if self.window_title in title:
                        self.window = win
                        print(f"\n=== 找到窗口 (win32): {title} ===")
                        self._print_window_controls()
                        
                        # 同时获取UIA后端的窗口对象
                        try:
                            print("\n尝试用 UIA 后端连接同一个窗口...")
                            desktop_uia = Desktop(backend="uia")
                            for win_uia in desktop_uia.windows():
                                if self.window_title in win_uia.window_text():
                                    self.window_uia = win_uia
                                    print(f"✅ 成功获取 UIA 窗口对象")
                                    break
                        except Exception as e:
                            print(f"⚠️ 获取UIA窗口失败: {e}")
                        
                        # 查找按钮
                        if self._check_button_exists():
                            self.window_status_changed.emit(True, f"✅ 找到窗口和按钮")
                            return True
                        else:
                            self.window_status_changed.emit(False, f"⚠️ 找到窗口但未找到按钮")
                            return False
                except Exception:
                    continue
                    
            self.window_status_changed.emit(False, "❌ 未找到Recipe窗口")
            return False
        except Exception as e:
            self.window_status_changed.emit(False, f"❌ 检查窗口失败: {e}")
            return False
    
    def _print_window_controls(self):
        """打印窗口的所有子控件信息（调试用）"""
        try:
            if not self.window:
                print("Window object is None")
                return
            
            print("\n" + "=" * 80)
            print(f"窗口标题: {self.window.window_text()}")
            print(f"窗口类名: {self.window.class_name()}")
            print("=" * 80)
            print("窗口的所有子控件:")
            print("-" * 80)
            
            children = self.window.children()
            print(f"总共找到 {len(children)} 个子控件\n")
            
            for idx, child in enumerate(children):
                try:
                    ctrl_type = child.friendly_class_name()
                    ctrl_title = child.window_text()
                    ctrl_id = child.control_id()
                    ctrl_class = child.class_name()
                    is_visible = child.is_visible()
                    is_enabled = child.is_enabled()
                    
                    print(f"控件 [{idx}]:")
                    print(f"  类型(Type):     {ctrl_type}")
                    print(f"  标题(Title):    '{ctrl_title}'")
                    print(f"  ID:             {ctrl_id}")
                    print(f"  类名(Class):    {ctrl_class}")
                    print(f"  可见(Visible):  {is_visible}")
                    print(f"  启用(Enabled):  {is_enabled}")
                    print("-" * 80)
                except Exception as e:
                    print(f"控件 [{idx}]: Error reading control - {e}")
                    print("-" * 80)
            
            print("=" * 80 + "\n")
        except Exception as e:
            print(f"Error printing controls: {e}")
    
    def get_controls_list(self):
        """获取窗口所有子控件信息列表"""
        controls_info = []
        try:
            if not self.window:
                return ["窗口不存在，请先检查窗口"]
            
            controls_info.append(f"窗口标题: {self.window.window_text()}")
            controls_info.append(f"窗口类名: {self.window.class_name()}\n")
            
            children = self.window.children()
            controls_info.append(f"找到 {len(children)} 个子控件:\n")
            controls_info.append("=" * 60 + "\n")
            
            for idx, child in enumerate(children):
                try:
                    ctrl_type = child.friendly_class_name()
                    ctrl_title = child.window_text()
                    ctrl_id = child.control_id()
                    ctrl_class = child.class_name()
                    is_visible = child.is_visible()
                    is_enabled = child.is_enabled()
                    
                    controls_info.append(f"控件 [{idx}]:")
                    controls_info.append(f"  类型(Type):     {ctrl_type}")
                    controls_info.append(f"  标题(Title):    '{ctrl_title}'")
                    controls_info.append(f"  ID:             {ctrl_id}")
                    controls_info.append(f"  类名(Class):    {ctrl_class}")
                    controls_info.append(f"  可见(Visible):  {is_visible}")
                    controls_info.append(f"  启用(Enabled):  {is_enabled}")
                    controls_info.append("-" * 60 + "\n")
                except Exception as e:
                    controls_info.append(f"[{idx}] Error: {e}\n")
            
            return controls_info
        except Exception as e:
            return [f"获取控件列表失败: {e}"]
    
    def _check_button_exists(self):
        """检查按钮是否存在"""
        try:
            print("\n" + "="*60)
            print(f"开始查找 '{self.button_type}' 按钮...")
            print("="*60)
            
            if self.button_type == "Start Once":
                return self._find_start_once_button()
            elif self.button_type == "Start Continuous":
                return self._find_start_continuous_button()
            else:
                print(f"❌ 未知的按钮类型: {self.button_type}")
                return False
            
        except Exception as e:
            print(f"❌ _check_button_exists 严重错误: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _find_start_once_button(self):
        """查找Start Once按钮"""
        # 方法1: 使用 UIA 后端查找按钮（推荐用于按钮操作）
        if self.window_uia:
            try:
                print("方法1: 使用 UIA 后端查找按钮...")
                self.button = self.window_uia.child_window(title="Start Once", control_type="Button")
                if self.button.exists():
                    print("✅ 找到按钮 - UIA后端成功!")
                    self.backend = "uia"
                    return True
            except Exception as e:
                print(f"⚠️ UIA方法1失败: {e}")
            
            # UIA方法2: 通过遍历查找
            try:
                print("方法2: UIA - 通过遍历...")
                buttons = self.window_uia.descendants(control_type="Button")
                print(f"  找到 {len(buttons)} 个Button控件")
                for btn in buttons:
                    try:
                        btn_name = btn.window_text()
                        if btn_name == "Start Once":
                            self.button = btn
                            print(f"✅ 找到按钮 - UIA遍历成功: '{btn_name}'")
                            self.backend = "uia"
                            return True
                    except:
                        continue
            except Exception as e:
                print(f"⚠️ UIA方法2失败: {e}")
        
        # 方法3: Win32后端 - 遍历所有子控件
        if self.window:
            try:
                print("\n方法3: Win32 - 遍历所有子控件...")
                children = self.window.children()
                print(f"  窗口共有 {len(children)} 个子控件")
                
                for idx, child in enumerate(children):
                    try:
                        child_title = child.window_text()
                        child_class = child.class_name()
                        child_id = child.control_id()
                        
                        if child_class == "Button":
                            print(f"  控件[{idx}] - Button: '{child_title}' (ID:{child_id})")
                        
                        if child_title == "Start Once" and child_class == "Button":
                            self.button = child
                            print(f"✅ 找到按钮 - Win32遍历成功! 控件[{idx}], ID={child_id}")
                            self.backend = "win32"
                            return True
                    except Exception as e:
                        continue
                
                print("⚠️ Win32遍历完成，未找到按钮")
            except Exception as e:
                print(f"❌ Win32方法失败: {e}")
        
        print("\n" + "="*60)
        print("❌ 所有方法都未能找到Start Once按钮")
        print("="*60 + "\n")
        return False
    
    def _find_start_continuous_button(self):
        """查找Start Continuous按钮，如果不存在则通过下拉菜单切换"""
        print("\n" + "="*60)
        print("开始查找 Start Continuous 按钮...")
        print("="*60)
        
        # 步骤1: 首先检查 "Start Continuous" 按钮是否已经存在
        if self._check_start_continuous_exists():
            print("✅ Start Continuous按钮已存在，直接使用")
            return True
        
        # 步骤2: 如果不存在，需要通过下拉菜单切换到Continuous模式
        print("\n⚠️ Start Continuous按钮不存在，需要通过下拉菜单切换...")
        print("步骤: 查找Start Once按钮 -> 点击下拉按钮 -> 选择Continuous Acquisition")
        
        # 2.1 查找Start Once按钮
        start_once_button = None
        if self.window_uia:
            try:
                start_once_button = self.window_uia.child_window(title="Start Once", control_type="Button")
                if not start_once_button.exists():
                    start_once_button = None
            except:
                pass
            
            if not start_once_button:
                buttons = self.window_uia.descendants(control_type="Button")
                for btn in buttons:
                    try:
                        if btn.window_text() == "Start Once":
                            start_once_button = btn
                            break
                    except:
                        continue
        
        if not start_once_button and self.window:
            children = self.window.children()
            for child in children:
                try:
                    if child.window_text() == "Start Once" and child.class_name() == "Button":
                        start_once_button = child
                        break
                except:
                    continue
        
        if not start_once_button:
            print("❌ 未找到Start Once按钮，无法切换模式")
            return False
        
        print("✅ 找到Start Once按钮")
        
        # 2.2 查找Start Once按钮右侧的下拉按钮
        dropdown_button = self._find_dropdown_button_for_start_once(start_once_button)
        if not dropdown_button:
            print("❌ 未找到Start Once按钮的下拉按钮")
            return False
        
        print("✅ 找到下拉按钮")
        
        # 2.3 点击下拉按钮，显示下拉菜单
        try:
            if self.backend == "uia":
                dropdown_button.click()
            else:
                dropdown_button.click()
            print("✅ 已点击下拉按钮，等待菜单显示...")
            time.sleep(0.3)  # 等待菜单显示
        except Exception as e:
            print(f"❌ 点击下拉按钮失败: {e}")
            return False
        
        # 2.4 查找并点击下拉菜单中的 "Continuous Acquisition" 选项
        if not self._click_menu_item("Continuous Acquisition"):
            print("❌ 未找到或无法点击 'Continuous Acquisition' 菜单项")
            return False
        
        print("✅ 已点击 'Continuous Acquisition' 菜单项")
        time.sleep(0.5)  # 等待菜单关闭和按钮切换
        
        # 2.5 再次查找 "Start Continuous" 按钮
        if self._check_start_continuous_exists():
            print("✅ 成功切换到Start Continuous模式")
            return True
        else:
            print("❌ 切换后仍未找到Start Continuous按钮")
            return False
    
    def _check_start_continuous_exists(self):
        """检查Start Continuous按钮是否存在"""
        # 方法1: 使用 UIA 后端查找
        if self.window_uia:
            try:
                self.button = self.window_uia.child_window(title="Start Continuous", control_type="Button")
                if self.button.exists():
                    print("✅ 找到Start Continuous按钮 - UIA后端")
                    self.backend = "uia"
                    return True
            except:
                pass
            
            # 通过遍历查找
            try:
                buttons = self.window_uia.descendants(control_type="Button")
                for btn in buttons:
                    try:
                        if btn.window_text() == "Start Continuous":
                            self.button = btn
                            print("✅ 找到Start Continuous按钮 - UIA遍历")
                            self.backend = "uia"
                            return True
                    except:
                        continue
            except:
                pass
        
        # 方法2: Win32后端
        if self.window:
            try:
                children = self.window.children()
                for child in children:
                    try:
                        if child.window_text() == "Start Continuous" and child.class_name() == "Button":
                            self.button = child
                            print("✅ 找到Start Continuous按钮 - Win32")
                            self.backend = "win32"
                            return True
                    except:
                        continue
            except:
                pass
        
        return False
    
    def _find_dropdown_button_for_start_once(self, start_once_button):
        """查找Start Once按钮右侧的下拉按钮"""
        try:
            # 获取Start Once按钮的位置
            main_rect = start_once_button.rectangle()
            print(f"Start Once按钮位置: {main_rect}")
            
            if self.window_uia:
                # 查找按钮右侧的按钮
                all_buttons = self.window_uia.descendants(control_type="Button")
                for btn in all_buttons:
                    try:
                        btn_rect = btn.rectangle()
                        btn_name = btn.window_text()
                        # 检查是否在Start Once按钮右侧
                        if (btn_rect.left() > main_rect.right() - 20 and 
                            btn_rect.left() < main_rect.right() + 30 and
                            btn_rect.top() >= main_rect.top() - 5 and
                            btn_rect.bottom() <= main_rect.bottom() + 5):
                            # 可能是下拉按钮（通常没有文本或文本很短）
                            if not btn_name or len(btn_name) <= 3:
                                print(f"✅ 找到下拉按钮: '{btn_name}', 位置: {btn_rect}")
                                return btn
                    except:
                        continue
            
            if self.window:
                children = self.window.children()
                for child in children:
                    try:
                        if child.class_name() == "Button":
                            child_rect = child.rectangle()
                            child_title = child.window_text()
                            if (child_rect.left() > main_rect.right() - 20 and 
                                child_rect.left() < main_rect.right() + 30 and
                                child_rect.top() >= main_rect.top() - 5 and
                                child_rect.bottom() <= main_rect.bottom() + 5):
                                if not child_title or len(child_title) <= 3:
                                    print(f"✅ 找到下拉按钮 - Win32: '{child_title}'")
                                    return child
                    except:
                        continue
        except Exception as e:
            print(f"⚠️ 查找下拉按钮失败: {e}")
        
        return None
    
    def _click_menu_item(self, item_text):
        """查找并点击下拉菜单中的菜单项"""
        try:
            print(f"\n查找菜单项: '{item_text}'...")
            
            # 方法1: 使用UIA后端查找菜单项
            if self.window_uia:
                try:
                    # 查找MenuItem控件
                    menu_items = self.window_uia.descendants(control_type="MenuItem")
                    print(f"  找到 {len(menu_items)} 个菜单项")
                    for item in menu_items:
                        try:
                            item_name = item.window_text()
                            print(f"    菜单项: '{item_name}'")
                            if item_text in item_name or item_name == item_text:
                                print(f"✅ 找到菜单项: '{item_name}'")
                                item.click()
                                return True
                        except:
                            continue
                except Exception as e:
                    print(f"⚠️ UIA查找菜单项失败: {e}")
                
                # 方法2: 查找所有控件，包括菜单
                try:
                    all_controls = self.window_uia.descendants()
                    for ctrl in all_controls:
                        try:
                            ctrl_name = ctrl.window_text()
                            ctrl_type = str(ctrl.element_info.control_type)
                            if (item_text in ctrl_name or ctrl_name == item_text) and "Menu" in ctrl_type:
                                print(f"✅ 找到菜单项: '{ctrl_name}' (类型: {ctrl_type})")
                                ctrl.click()
                                return True
                        except:
                            continue
                except Exception as e:
                    print(f"⚠️ UIA遍历所有控件失败: {e}")
            
            # 方法3: 使用Win32后端查找菜单
            if self.window:
                try:
                    # Win32中菜单通常是独立的窗口
                    desktop = Desktop(backend="win32")
                    windows = desktop.windows()
                    for win in windows:
                        try:
                            win_class = win.class_name()
                            if "Menu" in win_class:
                                # 查找菜单项
                                menu_items = win.children()
                                for menu_item in menu_items:
                                    try:
                                        item_text_win = menu_item.window_text()
                                        if item_text in item_text_win or item_text_win == item_text:
                                            print(f"✅ 找到菜单项 - Win32: '{item_text_win}'")
                                            menu_item.click()
                                            return True
                                    except:
                                        continue
                        except:
                            continue
                except Exception as e:
                    print(f"⚠️ Win32查找菜单失败: {e}")
            
            print(f"❌ 未找到菜单项: '{item_text}'")
            return False
            
        except Exception as e:
            print(f"❌ 点击菜单项失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def click_start_button(self):
        """点击按钮（根据button_type决定点击哪个按钮）"""
        try:
            print("\n" + "="*60)
            print(f"准备点击 {self.button_type} 按钮...")
            print(f"使用后端: {self.backend}")
            print("="*60)
            
            if not self.button:
                print("⚠️ 按钮对象不存在，尝试重新查找...")
                if not self.check_window_exists():
                    return False, "窗口或按钮不存在"
            
            # 无论是Start Once还是Start Continuous，都直接点击按钮本身
            # Start Continuous的下拉按钮只在切换模式时使用，触发时只点击主按钮
            return self._click_start_once_button()
            
        except Exception as e:
            error_msg = f"❌ 点击按钮失败: {e}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return False, error_msg
    
    def _click_start_once_button(self):
        """点击按钮（支持Start Once和Start Continuous）"""
        button_name = self.button_type
        # 使用UIA后端时的点击方法
        if self.backend == "uia":
            try:
                print("方法1: UIA - 使用click()...")
                self.button.click()
                print("✅ UIA click() 成功")
                return True, f"✅ 成功点击{button_name}按钮 (UIA)"
            except Exception as e:
                print(f"⚠️ UIA click()失败: {e}")
                try:
                    print("方法2: UIA - 使用invoke()...")
                    self.button.invoke()
                    print("✅ UIA invoke() 成功")
                    return True, f"✅ 成功点击{button_name}按钮 (UIA invoke)"
                except Exception as e2:
                    print(f"❌ UIA invoke()失败: {e2}")
        
        # 使用Win32后端时的点击方法
        else:
            try:
                # 确保窗口可见
                if self.window and not self.window.is_visible():
                    print("窗口不可见，尝试激活...")
                    self.window.set_focus()
                
                print("方法3: Win32 - 使用click()...")
                self.button.click()
                print("✅ Win32 click() 成功")
                return True, f"✅ 成功点击{button_name}按钮 (Win32)"
            except Exception as e:
                print(f"❌ Win32 click()失败: {e}")
        
        return False, f"❌ 所有点击方法都失败"
    
    def bring_window_to_top(self, window_title_keyword):
        """将指定窗口置顶"""
        try:
            print(f"\n尝试将包含 '{window_title_keyword}' 的窗口置顶...")
            
            # 先尝试UIA后端
            try:
                desktop_uia = Desktop(backend="uia")
                windows = desktop_uia.windows()
                for win in windows:
                    try:
                        title = win.window_text()
                        if window_title_keyword in title:
                            win.set_focus()
                            print(f"✅ UIA - 窗口已置顶: {title}")
                            return True, f"✅ 窗口已置顶: {title}"
                    except Exception:
                        continue
            except Exception as e:
                print(f"⚠️ UIA置顶失败: {e}")
            
            # 再尝试Win32后端
            try:
                desktop = Desktop(backend="win32")
                windows = desktop.windows()
                for win in windows:
                    try:
                        title = win.window_text()
                        if window_title_keyword in title:
                            win.set_focus()
                            print(f"✅ Win32 - 窗口已置顶: {title}")
                            return True, f"✅ 窗口已置顶: {title}"
                    except Exception:
                        continue
            except Exception as e:
                print(f"❌ Win32置顶失败: {e}")
            
            return False, f"❌ 未找到包含 '{window_title_keyword}' 的窗口"
        except Exception as e:
            return False, f"❌ 置顶窗口失败: {e}"

