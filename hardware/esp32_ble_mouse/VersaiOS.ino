#include <BleMouse.h>

BleMouse bleMouse("VersaiOS_Hand", "Apple", 100);

void setup() {
  Serial.begin(115200);
  bleMouse.begin();
}

void loop() {
  if (bleMouse.isConnected() && Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    // 监听 Python 发来的带坐标的攻击指令，格式："CLICK:221,450"
    if (command.startsWith("CLICK:")) {
      String coords = command.substring(6);
      int commaIndex = coords.indexOf(',');
      
      if (commaIndex != -1) {
        int targetX = coords.substring(0, commaIndex).toInt();
        int targetY = coords.substring(commaIndex + 1).toInt();

        Serial.print(">>> [ESP32] 接收到 AI 坐标: X=");
        Serial.print(targetX);
        Serial.print(", Y=");
        Serial.println(targetY);

        // 1. 暴力归零：向屏幕左上角狂奔 40 次，绝对能顶到 (0,0) 点
        for(int i = 0; i < 40; i++) {
          bleMouse.move(-127, -127);
          delay(10);
        }

        // 2. 绕过加速度的匀速步进：把长距离拆分成 5 像素一次的小碎步
        int currentX = 0;
        while(currentX < targetX) {
          int step = (targetX - currentX > 5) ? 5 : (targetX - currentX);
          bleMouse.move(step, 0);
          currentX += step;
          delay(5);
        }

        int currentY = 0;
        while(currentY < targetY) {
          int step = (targetY - currentY > 5) ? 5 : (targetY - currentY);
          bleMouse.move(0, step);
          currentY += step;
          delay(5);
        }

        // 3. 到达指定坐标，执行开火！
        delay(100); // 停顿 0.1 秒让光标完全稳住
        
        // 💡 修复点：拆分按下和抬起动作，强制 iOS 识别
        bleMouse.press(MOUSE_LEFT);  // 按下左键
        delay(100);                  // 保持按压 0.1 秒
        bleMouse.release(MOUSE_LEFT);// 抬起左键
        
        Serial.println(">>> [ESP32] 目标已击毁！");
      }
    }
  }
  delay(10);
}