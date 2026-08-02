"""
VersaiOS 图形化控制台
"""
import customtkinter as ctk

from gui.calibration_module import CalibrationModule
from gui.control_module import ControlModule
from config import APP_VERSION


# CTk 全局样式
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


def main():
    app = ctk.CTk()
    app.title(f"VersaiOS 控制台 V{APP_VERSION}")
    app.geometry("700x880")

    # 顶部引导说明
    header = ctk.CTkFrame(app, fg_color="transparent")
    header.pack(padx=20, pady=(20, 0), fill="x")
    ctk.CTkLabel(
        header,
        text="VersaiOS 图形化控制台",
        font=("Arial", 22, "bold")
    ).pack()
    ctk.CTkLabel(
        header,
        text="请按顺序完成『准备』与『运行』两个阶段。",
        font=("Arial", 12)
    ).pack(pady=5)

    # 阶段化标签页
    tabview = ctk.CTkTabview(app)
    tabview.pack(padx=20, pady=20, fill="both", expand=True)

    tab_prepare = tabview.add("阶段一：准备")
    tab_run = tabview.add("阶段二：运行")

    CalibrationModule(tab_prepare).pack(fill="both", expand=True)
    ControlModule(tab_run).pack(fill="both", expand=True)

    app.mainloop()


if __name__ == "__main__":
    main()
