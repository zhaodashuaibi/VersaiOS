#include <BleMouse.h>

BleMouse bleMouse("VersaiOS Mouse", "Apple", 100);

// 改为动态变量，默认值给个大概即可，实际会由 Python 覆盖
long screen_max_x = 2000;
long screen_max_y = 4000;

void setup() {
    Serial.begin(115200);
    Serial.println(">>> [系统] 正在初始化 VersaiOS BLE 动态鼠标引擎...");
    bleMouse.begin();
}

void move_relative_safe(long dx, long dy) {
    while (dx != 0 || dy != 0) {
        int8_t step_x = 0;
        int8_t step_y = 0;

        if (dx > 100) step_x = 100;
        else if (dx < -100) step_x = -100;
        else step_x = dx;

        if (dy > 100) step_y = 100;
        else if (dy < -100) step_y = -100;
        else step_y = dy;

        bleMouse.move(step_x, step_y);
        dx -= step_x;
        dy -= step_y;

        delay(8); // 防止蓝牙拥堵
    }
}

// 使用动态变量进行中线十字校准
void perform_center_cross_calibration() {
    move_relative_safe(0, screen_max_y * 2);
    delay(50);
    move_relative_safe(0, -screen_max_y / 2);
    delay(50);
    move_relative_safe(-screen_max_x * 2, 0);
    delay(50);
    move_relative_safe(screen_max_x / 2, 0);
    delay(50);
}

void loop() {
    if (bleMouse.isConnected() && Serial.available() > 0) {
        String cmd = Serial.readStringUntil('\n');
        cmd.trim();

        int x, y;

        // 1. 动态配置指令
        if (sscanf(cmd.c_str(), "SET:%d,%d", &x, &y) == 2) {
            screen_max_x = x;
            screen_max_y = y;
            Serial.printf(">>> [配置] 收到 Python 下发参数: 最大步数 X=%ld, Y=%ld\n", screen_max_x, screen_max_y);
        }
        // 2. 交互测试指令（供 GUI 校准模块使用）
        else if (sscanf(cmd.c_str(), "REL:%d,%d", &x, &y) == 2) {
            move_relative_safe(x, y);
            Serial.printf(">>> [测试] 纯相对移动: dx=%d, dy=%d\n", x, y);
        }
        // 3. 核心击发指令（供主程序 main_versaios.py 使用）
        else if (sscanf(cmd.c_str(), "CLICK:%d,%d", &x, &y) == 2) {
            Serial.printf(">>> [指令] 收到点击任务: 目标 (%d, %d)\n", x, y);

            perform_center_cross_calibration(); // 根据 SET 收到的参数进行归零

            long center_x = screen_max_x / 2;
            long center_y = screen_max_y / 2;
            long move_dx = x - center_x;
            long move_dy = y - center_y;

            move_relative_safe(move_dx, move_dy);
            delay(50);
            bleMouse.click();
            Serial.println(">>> [执行] 点击完成！");
        }
    }
    delay(10);
}