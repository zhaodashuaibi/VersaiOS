# gui/calibration_module.py
"""
模块一：准备阶段
- 模型提供方、API Key、模型名称等 LLM 配置
- 串口号与 HID 步数校准
"""
import threading
import time
import serial
import customtkinter as ctk

from .utils import load_existing_config, save_config_values
from config import (
    DEFAULT_HID_MAX_X,
    DEFAULT_HID_MAX_Y,
    is_hid_calibrated,
    reload_config,
)


class CalibrationModule(ctk.CTkFrame):
    """阶段一：模型配置 + HID 步数校准。"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._serial = None
        self._serial_lock = threading.Lock()
        self._acc_x = 0
        self._acc_y = 0

        self._build_ui()
        self._load_config()
        self._refresh_connection_state()

    # ========================== UI 构建 ==========================
    def _build_ui(self):
        # 标题
        ctk.CTkLabel(
            self, text="阶段一：准备（模型配置 + HID 校准）",
            font=("Arial", 18, "bold")
        ).pack(pady=(20, 10))

        # ---------------- 模型配置 ----------------
        model_frame = ctk.CTkFrame(self)
        model_frame.pack(padx=20, pady=10, fill="x")
        ctk.CTkLabel(model_frame, text="模型配置", font=("Arial", 14, "bold")).pack(pady=(10, 5))

        self.provider_var = ctk.StringVar(value="gemini")
        ctk.CTkLabel(model_frame, text="模型厂商").pack()
        ctk.CTkComboBox(
            model_frame,
            values=["gemini", "openai_compatible"],
            variable=self.provider_var,
            width=350
        ).pack(pady=5)

        ctk.CTkLabel(model_frame, text="API Key").pack()
        self.api_key_entry = ctk.CTkEntry(model_frame, show="*", width=350)
        self.api_key_entry.pack(pady=5)

        ctk.CTkLabel(model_frame, text="Base URL（仅 openai_compatible 需要）").pack()
        self.base_url_entry = ctk.CTkEntry(model_frame, width=350)
        self.base_url_entry.pack(pady=5)

        ctk.CTkLabel(model_frame, text="模型名称").pack()
        self.model_entry = ctk.CTkEntry(model_frame, width=350)
        self.model_entry.pack(pady=5)

        # ---------------- 连接配置 ----------------
        conn_frame = ctk.CTkFrame(self)
        conn_frame.pack(padx=20, pady=10, fill="x")
        ctk.CTkLabel(conn_frame, text="连接配置", font=("Arial", 14, "bold")).pack(pady=(10, 5))

        ctk.CTkLabel(conn_frame, text="串口号（如 COM3）").pack()
        self.com_port_entry = ctk.CTkEntry(conn_frame, width=120)
        self.com_port_entry.pack(pady=5)

        ctk.CTkLabel(conn_frame, text="投屏窗口名").pack()
        self.window_title_entry = ctk.CTkEntry(conn_frame, width=200)
        self.window_title_entry.pack(pady=5)

        self.connect_btn = ctk.CTkButton(
            conn_frame, text="连接 ESP32", command=self._connect_serial,
            fg_color="#2ecc71", hover_color="#27ae60"
        )
        self.connect_btn.pack(pady=5)

        self.disconnect_btn = ctk.CTkButton(
            conn_frame, text="断开连接", command=self._disconnect_serial,
            fg_color="#e74c3c", hover_color="#c0392b"
        )
        self.disconnect_btn.pack(pady=5)

        self.test_hw_btn = ctk.CTkButton(
            conn_frame, text="测试硬件点击", command=self._test_hardware_click,
            fg_color="#f39c12", hover_color="#d35400"
        )
        self.test_hw_btn.pack(pady=5)

        # ---------------- HID 校准 ----------------
        calib_frame = ctk.CTkFrame(self)
        calib_frame.pack(padx=20, pady=10, fill="x")
        ctk.CTkLabel(calib_frame, text="HID 步数校准", font=("Arial", 14, "bold")).pack(pady=(10, 5))

        hint = (
            "1. 连接 ESP32 后，使用 W/A/S/D 将光标推到屏幕边缘。\n"
            "2. 点击『归零』，再向反方向移动，记录累计步数。\n"
            "3. 将最终 X/Y 步数填入下方，点击『保存全部配置』。"
        )
        ctk.CTkLabel(calib_frame, text=hint, justify="left").pack(pady=5)

        self.acc_label = ctk.CTkLabel(calib_frame, text="当前累计: X=0, Y=0", font=("Arial", 14, "bold"))
        self.acc_label.pack(pady=5)

        ctk.CTkLabel(calib_frame, text="单次步长").pack()
        self.step_entry = ctk.CTkEntry(calib_frame, width=120)
        self.step_entry.insert(0, "50")
        self.step_entry.pack(pady=5)

        # 方向键区域
        dpad = ctk.CTkFrame(calib_frame, fg_color="transparent")
        dpad.pack(pady=10)
        ctk.CTkButton(dpad, text="W", width=60, command=lambda: self._on_direction(0, -1)).grid(row=0, column=1, padx=5, pady=5)
        ctk.CTkButton(dpad, text="A", width=60, command=lambda: self._on_direction(-1, 0)).grid(row=1, column=0, padx=5, pady=5)
        ctk.CTkButton(dpad, text="S", width=60, command=lambda: self._on_direction(0, 1)).grid(row=1, column=1, padx=5, pady=5)
        ctk.CTkButton(dpad, text="D", width=60, command=lambda: self._on_direction(1, 0)).grid(row=1, column=2, padx=5, pady=5)
        ctk.CTkButton(dpad, text="归零", width=60, command=self._reset_accumulator).grid(row=2, column=1, padx=5, pady=5)

        # 最终校准值
        value_frame = ctk.CTkFrame(calib_frame, fg_color="transparent")
        value_frame.pack(pady=10)
        ctk.CTkLabel(value_frame, text="hid_max_x").grid(row=0, column=0, padx=5)
        self.hid_max_x_entry = ctk.CTkEntry(value_frame, width=120)
        self.hid_max_x_entry.grid(row=0, column=1, padx=5)
        ctk.CTkLabel(value_frame, text="hid_max_y").grid(row=1, column=0, padx=5, pady=5)
        self.hid_max_y_entry = ctk.CTkEntry(value_frame, width=120)
        self.hid_max_y_entry.grid(row=1, column=1, padx=5, pady=5)

        # 未校准风险提示
        self.calib_warning_label = ctk.CTkLabel(
            calib_frame,
            text="",
            font=("Arial", 12, "bold"),
            text_color="orange",
            wraplength=500,
        )
        self.calib_warning_label.pack(pady=(5, 0))

        # 保存按钮
        ctk.CTkButton(
            self, text="保存全部配置", command=self._save_all_config,
            fg_color="#3498db", hover_color="#2980b9"
        ).pack(pady=15)

        self.status_label = ctk.CTkLabel(self, text="就绪")
        self.status_label.pack(pady=5)

    # ========================== 数据加载 ==========================
    def _load_config(self):
        try:
            cfg = load_existing_config()
        except Exception as e:
            self._set_status(f"加载配置失败: {e}", "red")
            return

        self.provider_var.set(cfg.get("llm_provider", "gemini"))
        self.api_key_entry.insert(0, cfg.get("llm_api_key", ""))
        self.base_url_entry.insert(0, cfg.get("llm_base_url", ""))
        self.model_entry.insert(0, cfg.get("llm_model", "gemini-3-flash-preview"))
        self.com_port_entry.insert(0, cfg.get("com_port", "COM3"))
        self.window_title_entry.insert(0, cfg.get("window_title", "VersaiOS_Screen"))
        self.hid_max_x_entry.insert(0, cfg.get("hid_max_x", str(DEFAULT_HID_MAX_X)))
        self.hid_max_y_entry.insert(0, cfg.get("hid_max_y", str(DEFAULT_HID_MAX_Y)))
        self._refresh_calibration_warning()

    # ========================== 串口连接 ==========================
    def _connect_serial(self):
        com_port = self.com_port_entry.get().strip() or "COM3"
        if self._serial is not None and self._serial.is_open:
            self._set_status(f"已连接 {com_port}", "green")
            return

        self._set_status(f"正在连接 {com_port}...", "orange")

        def _open():
            try:
                ser = serial.Serial(com_port, 115200, timeout=1)
                time.sleep(2)  # 等待 ESP32 重启
                with self._serial_lock:
                    self._serial = ser
                self.after(0, self._refresh_connection_state)
                self.after(0, lambda: self._set_status(f"已连接 {com_port}", "green"))
            except Exception as e:
                self.after(0, lambda: self._set_status(f"连接失败: {e}", "red"))

        threading.Thread(target=_open, daemon=True).start()

    def _disconnect_serial(self):
        with self._serial_lock:
            ser = self._serial
            self._serial = None
        if ser and ser.is_open:
            try:
                ser.close()
            except Exception as e:
                self._set_status(f"断开连接异常: {e}", "red")
                return
        self._refresh_connection_state()
        self._set_status("已断开 ESP32", "gray")

    def _refresh_connection_state(self):
        connected = self._serial is not None and self._serial.is_open
        self.connect_btn.configure(state="disabled" if connected else "normal")
        self.disconnect_btn.configure(state="normal" if connected else "disabled")
        self.test_hw_btn.configure(state="normal" if connected else "disabled")

    def _test_hardware_click(self):
        """发送一次测试点击，验证 ESP32 与串口链路。"""
        if self._serial is None or not self._serial.is_open:
            self._set_status("请先连接 ESP32", "red")
            return

        self._set_status("正在发送测试点击...", "orange")

        def _send():
            try:
                with self._serial_lock:
                    if self._serial is None or not self._serial.is_open:
                        return
                    # 发送点击屏幕中心附近的测试指令
                    self._serial.write("CLICK:50,50\n".encode("utf-8"))
                self.after(0, lambda: self._set_status("测试点击已发送，请观察 iPhone 是否响应", "green"))
            except Exception as e:
                self.after(0, lambda: self._set_status(f"测试点击失败: {e}", "red"))

        threading.Thread(target=_send, daemon=True).start()

    # ========================== 校准操作 ==========================
    def _get_step(self) -> int:
        try:
            return int(self.step_entry.get().strip())
        except ValueError:
            return 0

    def _on_direction(self, sign_x: int, sign_y: int):
        step = self._get_step()
        if step <= 0:
            self._set_status("请输入有效的正整数步长", "red")
            return

        dx = sign_x * step
        dy = sign_y * step

        if self._serial is None or not self._serial.is_open:
            self._set_status("请先连接 ESP32", "red")
            return

        def _send():
            try:
                with self._serial_lock:
                    if self._serial is None or not self._serial.is_open:
                        return
                    self._serial.write(f"REL:{dx},{dy}\n".encode("utf-8"))
                self._acc_x += dx
                self._acc_y += dy
                self.after(0, self._update_acc_label)
                self.after(0, lambda: self._set_status(f"已发送 REL:{dx},{dy}", "green"))
            except Exception as e:
                self.after(0, lambda: self._set_status(f"发送失败: {e}", "red"))

        threading.Thread(target=_send, daemon=True).start()

    def _reset_accumulator(self):
        self._acc_x = 0
        self._acc_y = 0
        self._update_acc_label()
        self._set_status("累计步数已归零", "gray")

    def _update_acc_label(self):
        self.acc_label.configure(text=f"当前累计: X={self._acc_x}, Y={self._acc_y}")

    # ========================== 配置保存 ==========================
    def _save_all_config(self):
        try:
            updates = {
                "llm_provider": self.provider_var.get().strip(),
                "llm_api_key": self.api_key_entry.get().strip(),
                "llm_base_url": self.base_url_entry.get().strip(),
                "llm_model": self.model_entry.get().strip(),
                "com_port": self.com_port_entry.get().strip() or "COM3",
                "window_title": self.window_title_entry.get().strip() or "VersaiOS_Screen",
                "hid_max_x": self.hid_max_x_entry.get().strip() or str(DEFAULT_HID_MAX_X),
                "hid_max_y": self.hid_max_y_entry.get().strip() or str(DEFAULT_HID_MAX_Y),
            }
            save_config_values(updates)
            reload_config()
            self._refresh_calibration_warning()
            self._set_status("配置已保存", "green")
        except Exception as e:
            self._set_status(f"保存失败: {e}", "red")

    def _refresh_calibration_warning(self):
        """根据 config 是否已显式配置 HID 步数更新风险提示。"""
        if is_hid_calibrated():
            self.calib_warning_label.configure(text="")
        else:
            self.calib_warning_label.configure(
                text=(
                    f"⚠️ HID 步数尚未显式配置（当前为默认值 "
                    f"{DEFAULT_HID_MAX_X}/{DEFAULT_HID_MAX_Y}）。"
                    "请点击坐标可能不准确，请先完成校准再保存。"
                )
            )

    # ========================== 状态提示 ==========================
    def _set_status(self, text: str, color: str = "gray"):
        self.status_label.configure(text=text, text_color=color)
