# gui/control_module.py
"""
模块二：使用阶段
- 启动/停止 UxPlay 投屏接收端
- 启动/停止主控端（main_versaios.py）
- 输入自然语言指令并查看实时日志
- 测试视觉（截图 + AI 目标定位 + 红圈标记）
"""
import os
import subprocess
import sys
import threading
import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageDraw

from .utils import UXPLAY_MAIN_PATH, MAIN_VERSAIOS_PATH, SRC_PATH
from config import (
    get_window_title,
    get_llm_provider,
    get_llm_api_key,
    get_llm_model,
    get_llm_base_url,
    validate_llm_config,
)
from vision_engine import VersaiOSVision
from ai_brain import VersaiOSAgent


class ControlModule(ctk.CTkFrame):
    """阶段二：接收端启动 + 指令交互。"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.uxplay_process = None
        self.controller_process = None
        self._reader_thread = None
        self._stop_reading = threading.Event()
        self._build_ui()

    # ========================== UI 构建 ==========================
    def _build_ui(self):
        ctk.CTkLabel(
            self, text="阶段二：运行（接收端 + 主控端 + 指令）",
            font=("Arial", 18, "bold")
        ).pack(pady=(20, 10))

        # ---------------- 投屏接收端 ----------------
        ux_frame = ctk.CTkFrame(self)
        ux_frame.pack(padx=20, pady=10, fill="x")
        ctk.CTkLabel(ux_frame, text="投屏接收端 (UxPlay)", font=("Arial", 14, "bold")).pack(pady=(10, 5))

        ux_btn_frame = ctk.CTkFrame(ux_frame, fg_color="transparent")
        ux_btn_frame.pack(pady=5)
        ctk.CTkButton(
            ux_btn_frame, text="启动接收端", width=120,
            fg_color="#2ecc71", hover_color="#27ae60",
            command=self._start_uxplay
        ).grid(row=0, column=0, padx=10)
        ctk.CTkButton(
            ux_btn_frame, text="停止接收端", width=120,
            fg_color="#e74c3c", hover_color="#c0392b",
            command=self._stop_uxplay
        ).grid(row=0, column=1, padx=10)

        self.ux_status_label = ctk.CTkLabel(ux_frame, text="未启动")
        self.ux_status_label.pack(pady=5)

        ctk.CTkLabel(
            ux_frame,
            text="提示：启动后，请在 iPhone 上发起「屏幕镜像」到 VersaiOS_Screen。",
            font=("Arial", 11)
        ).pack(pady=5)

        # ---------------- 主控端 ----------------
        ctrl_frame = ctk.CTkFrame(self)
        ctrl_frame.pack(padx=20, pady=10, fill="x")
        ctk.CTkLabel(ctrl_frame, text="主控端", font=("Arial", 14, "bold")).pack(pady=(10, 5))

        ctrl_btn_frame = ctk.CTkFrame(ctrl_frame, fg_color="transparent")
        ctrl_btn_frame.pack(pady=5)
        self.start_controller_btn = ctk.CTkButton(
            ctrl_btn_frame, text="启动主控端", width=120,
            fg_color="#2ecc71", hover_color="#27ae60",
            command=self._start_controller
        )
        self.start_controller_btn.grid(row=0, column=0, padx=10)
        ctk.CTkButton(
            ctrl_btn_frame, text="停止主控端", width=120,
            fg_color="#e74c3c", hover_color="#c0392b",
            command=self._stop_controller
        ).grid(row=0, column=1, padx=10)

        self.ctrl_status_label = ctk.CTkLabel(ctrl_frame, text="未启动")
        self.ctrl_status_label.pack(pady=5)

        ctk.CTkButton(
            ctrl_frame, text="测试视觉（截图+标红目标）", command=self._test_vision,
            fg_color="#9b59b6", hover_color="#8e44ad"
        ).pack(pady=5)

        # ---------------- 指令输入 ----------------
        cmd_frame = ctk.CTkFrame(self)
        cmd_frame.pack(padx=20, pady=10, fill="x")
        ctk.CTkLabel(cmd_frame, text="自然语言指令", font=("Arial", 14, "bold")).pack(pady=(10, 5))

        self.instruction_entry = ctk.CTkEntry(cmd_frame, width=350, placeholder_text="例如：点击微信")
        self.instruction_entry.pack(pady=5)
        ctk.CTkButton(
            cmd_frame, text="发送指令", command=self._send_instruction
        ).pack(pady=5)

        self.instruction_entry.bind("<Return>", lambda event: self._send_instruction())

        # ---------------- 日志输出 ----------------
        log_frame = ctk.CTkFrame(self)
        log_frame.pack(padx=20, pady=10, fill="both", expand=True)
        ctk.CTkLabel(log_frame, text="运行日志", font=("Arial", 14, "bold")).pack(pady=(10, 5))

        self.log_text = ctk.CTkTextbox(log_frame, height=200, state="disabled")
        self.log_text.pack(padx=10, pady=5, fill="both", expand=True)

        ctk.CTkButton(
            log_frame, text="清空日志", command=self._clear_log
        ).pack(pady=5)

    # ========================== 投屏接收端 ==========================
    def _start_uxplay(self):
        if self.uxplay_process is not None and self.uxplay_process.poll() is None:
            self._log("接收端已在运行中", "orange")
            return
        if not os.path.exists(UXPLAY_MAIN_PATH):
            self._log(f"未找到投屏入口: {UXPLAY_MAIN_PATH}", "red")
            return

        try:
            # UxPlay/main.py 会启动 uxplay.exe 并阻塞等待；我们用子进程运行它
            self.uxplay_process = subprocess.Popen(
                [sys.executable, UXPLAY_MAIN_PATH],
                cwd=os.path.dirname(UXPLAY_MAIN_PATH)
            )
            self.ux_status_label.configure(text="接收端运行中", text_color="green")
            self._log("投屏接收端已启动", "green")
        except Exception as e:
            self.ux_status_label.configure(text="启动失败", text_color="red")
            self._log(f"启动接收端失败: {e}", "red")

    def _stop_uxplay(self):
        if self.uxplay_process is None or self.uxplay_process.poll() is not None:
            self.ux_status_label.configure(text="未启动", text_color="gray")
            self._log("接收端当前未在运行", "gray")
            return
        try:
            self.uxplay_process.terminate()
            self.uxplay_process.wait(timeout=3)
        except Exception as e:
            self._log(f"停止接收端时发生异常: {e}", "red")
        finally:
            self.uxplay_process = None
            self.ux_status_label.configure(text="已停止", text_color="red")
            self._log("投屏接收端已停止", "red")

    # ========================== 主控端 ==========================
    def _start_controller(self):
        if self.controller_process is not None and self.controller_process.poll() is None:
            self._log("主控端已在运行中", "orange")
            return
        if not os.path.exists(MAIN_VERSAIOS_PATH):
            self._log(f"未找到主控端入口: {MAIN_VERSAIOS_PATH}", "red")
            return

        try:
            # 主控端通过 input() 读取指令，因此需要 stdin=PIPE
            self.controller_process = subprocess.Popen(
                [sys.executable, MAIN_VERSAIOS_PATH],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=SRC_PATH
            )
            self._stop_reading.clear()
            self._reader_thread = threading.Thread(
                target=self._read_controller_output, daemon=True
            )
            self._reader_thread.start()

            self.ctrl_status_label.configure(text="主控端运行中", text_color="green")
            self.start_controller_btn.configure(state="disabled")
            self._log("主控端已启动，可以发送指令", "green")
        except Exception as e:
            self.ctrl_status_label.configure(text="启动失败", text_color="red")
            self._log(f"启动主控端失败: {e}", "red")

    def _stop_controller(self):
        if self.controller_process is None or self.controller_process.poll() is not None:
            self.ctrl_status_label.configure(text="未启动", text_color="gray")
            self.start_controller_btn.configure(state="normal")
            self._log("主控端当前未在运行", "gray")
            return

        self._stop_reading.set()
        try:
            self.controller_process.terminate()
            self.controller_process.wait(timeout=3)
        except Exception as e:
            self._log(f"停止主控端时发生异常: {e}", "red")
        finally:
            self.controller_process = None
            self._reader_thread = None
            self.ctrl_status_label.configure(text="已停止", text_color="red")
            self.start_controller_btn.configure(state="normal")
            self._log("主控端已停止", "red")

    def _read_controller_output(self):
        """在后台线程读取主控端 stdout 并写入日志区。"""
        if self.controller_process is None or self.controller_process.stdout is None:
            return
        for line in iter(self.controller_process.stdout.readline, ""):
            if self._stop_reading.is_set():
                break
            if line:
                self.after(0, lambda text=line.rstrip(): self._log(text))
        # 读取结束，说明进程已退出
        self.after(0, self._on_controller_exit)

    def _on_controller_exit(self):
        self.ctrl_status_label.configure(text="已停止", text_color="red")
        self.start_controller_btn.configure(state="normal")
        if self.controller_process is not None and self.controller_process.poll() is None:
            try:
                self.controller_process.terminate()
            except Exception:
                pass
        self.controller_process = None

    # ========================== 视觉测试 ==========================
    def _test_vision(self):
        """截图、调用 VLM 定位测试目标、绘制红圈并弹窗预览。"""
        self._log("正在进行视觉测试，请稍候...", "orange")

        def _run():
            try:
                config_err = validate_llm_config()
                if config_err:
                    self.after(0, lambda: self._log(f"视觉测试失败：LLM 配置无效 - {config_err}", "red"))
                    return

                window_title = get_window_title()
                vision = VersaiOSVision(window_title=window_title)
                frame = vision.grab_frame_for_ai()
                if frame is None:
                    self.after(0, lambda: self._log("视觉测试失败：未找到投屏窗口或窗口被最小化", "red"))
                    return

                self.after(0, lambda: self._log(f"已截取画面: {frame.size}", "green"))

                agent = VersaiOSAgent(
                    provider=get_llm_provider(),
                    api_key=get_llm_api_key(),
                    model_name=get_llm_model(),
                    base_url=get_llm_base_url(),
                )
                instruction = "请帮我点击屏幕中的 '微信' 图标。"
                plan = agent.analyze_ui_and_plan(frame, instruction)

                if plan and "x_ratio" in plan and "y_ratio" in plan:
                    target_x = int(frame.width * plan["x_ratio"])
                    target_y = int(frame.height * plan["y_ratio"])
                    draw = ImageDraw.Draw(frame)
                    r = 15
                    draw.ellipse(
                        (target_x - r, target_y - r, target_x + r, target_y + r),
                        outline="red", width=5
                    )

                    save_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "debug_target_result.png")
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    frame.save(save_path)

                    self.after(0, lambda: self._log(f"视觉测试成功，目标 ({target_x}, {target_y})，结果已保存到 {save_path}", "green"))
                    self.after(0, lambda path=save_path, img=frame.copy(): self._show_image_popup(path, img))
                else:
                    self.after(0, lambda: self._log(f"视觉测试失败：AI 未返回有效坐标。plan={plan}", "red"))
            except Exception as e:
                self.after(0, lambda: self._log(f"视觉测试异常: {e}", "red"))

        threading.Thread(target=_run, daemon=True).start()

    def _show_image_popup(self, image_path: str, pil_img: Image.Image):
        """弹出预览窗口显示带红圈的测试结果。"""
        popup = ctk.CTkToplevel(self)
        popup.title("视觉测试结果")
        popup.geometry("640x520")

        # 等比例缩放，宽度限制为 600
        max_width = 600
        ratio = min(max_width / pil_img.width, 1.0)
        display_size = (int(pil_img.width * ratio), int(pil_img.height * ratio))
        resized = pil_img.resize(display_size, Image.Resampling.LANCZOS)
        ctk_img = ctk.CTkImage(light_image=resized, dark_image=resized, size=display_size)

        ctk.CTkLabel(popup, text="红圈为 AI 预测目标位置", font=("Arial", 14, "bold")).pack(pady=10)
        ctk.CTkLabel(popup, image=ctk_img, text="").pack(pady=5)
        ctk.CTkLabel(popup, text=f"保存路径: {image_path}", font=("Arial", 11)).pack(pady=5)

        def _open_image():
            try:
                os.startfile(image_path)
            except Exception as e:
                self._log(f"打开图片失败: {e}", "red")

        ctk.CTkButton(popup, text="打开图片", command=_open_image).pack(pady=10)

    # ========================== 指令发送 ==========================
    def _send_instruction(self):
        instruction = self.instruction_entry.get().strip()
        if not instruction:
            return

        if self.controller_process is None or self.controller_process.poll() is not None:
            self._log("主控端未运行，请先启动主控端", "red")
            return

        try:
            self.controller_process.stdin.write(instruction + "\n")
            self.controller_process.stdin.flush()
            self._log(f"发送指令: {instruction}", "blue")
            self.instruction_entry.delete(0, "end")
        except Exception as e:
            self._log(f"发送指令失败: {e}", "red")

    # ========================== 日志工具 ==========================
    def _log(self, text: str, color: str = "gray"):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", text + "\n")
        self.log_text.configure(state="disabled")
        self.log_text.see("end")

    def _clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
