import random
import cv2
import math
from cvzone.HandTrackingModule import HandDetector

# OpenCV BGR颜色对照表
colors = {'黑色': (0, 0, 0), '红色': (0, 0, 255), '绿色': (0, 255, 0), '蓝色': (255, 0, 0), '紫色': (128, 0, 128),
          '白色': (255, 255, 255), '深红色': (255, 0, 255), '青色': (255, 255, 0), '黄色': (0, 255, 255)}

cap = cv2.VideoCapture(0)  # 使用默认摄像头
width, height = 1280, 720
cap.set(3, width)  # 设置宽度
cap.set(4, height)  # 设置高度
detector = HandDetector(detectionCon=1)  # 设置手部检测的置信度

# 游戏状态
game_started = False  # 游戏是否已开始
score = 0  # 得分
combo = 0  # 连击次数
max_combo = 10  # 连击上限
speed_increase_threshold = 3  # 每达到此连击数，增加速度
circle_radius = 200  # 增大的圆圈半径（适合手掌）

# 弹幕类，表示从圆心发射的弹幕
class Bullet:
    def __init__(self, angle, speed):
        self.angle = angle  # 弹幕的发射角度
        self.speed = speed  # 弹幕的速度
        self.x = width // 2  # 起始位置：圆心x坐标
        self.y = height // 2  # 起始位置：圆心y坐标
        self.radius = 10  # 弹幕半径

    def move(self):
        # 弹幕的 x, y 坐标根据速度和角度更新
        self.x += self.speed * math.cos(self.angle)
        self.y += self.speed * math.sin(self.angle)

    def draw(self, img):
        # 绘制弹幕
        cv2.circle(img, (int(self.x), int(self.y)), self.radius, colors['红色'], -1)

# 获取手掌心位置
def get_palm_center(landmarks):
    # 获取手掌的关键点：手腕到中指顶端的中点作为掌心位置
    wrist = landmarks[0]
    middle_finger = landmarks[12]
    palm_center_x = (wrist[0] + middle_finger[0]) // 2
    palm_center_y = (wrist[1] + middle_finger[1]) // 2
    return palm_center_x, palm_center_y

# 检查手掌心是否在圆圈边缘上
def check_hand_on_edge(palm_center):
    x, y = palm_center
    # 计算手掌心到圆心的距离
    distance = math.sqrt((x - width // 2) ** 2 + (y - height // 2) ** 2)
    # 判断是否在圆圈边缘，允许一定的误差（比如5像素内）
    if abs(distance - circle_radius) <= 5:
        return True
    return False

# 检查弹幕是否到达圆圈边缘
def check_bullet_in_circle(bullet):
    if (bullet.x - width // 2) ** 2 + (bullet.y - height // 2) ** 2 >= (circle_radius - bullet.radius) ** 2:
        return True
    return False

# 开始游戏
def start_game(landmarks):
    global game_started
    x, y = landmarks[8][0], landmarks[8][1]  # 食指尖
    start_button_x1, start_button_y1 = width // 3, height // 3
    start_button_x2, start_button_y2 = 2 * width // 3, height // 2

    if start_button_x1 < x < start_button_x2 and start_button_y1 < y < start_button_y2:
        game_started = True

# 初始化弹幕
bullets = []
bullet_speed = 4  # 初始速度
generate_bullet_time = 60  # 每60帧生成一个新的弹幕
frame_count = 0

while True:
    success, img = cap.read()
    
    if not success:
        print("无法读取摄像头图像，退出程序")
        break
    
    img = cv2.flip(img, 1)  # 水平翻转图像，使其符合人体感官

    img = detector.findHands(img)
    landmarks, _ = detector.findPosition(img)

    if game_started:  # 游戏开始后
        frame_count += 1

        # 随机生成弹幕
        if frame_count % generate_bullet_time == 0:
            angle = random.uniform(0, 2 * math.pi)  # 随机角度
            bullet = Bullet(angle, bullet_speed)
            bullets.append(bullet)

        # 绘制和移动所有弹幕
        for bullet in bullets:
            bullet.move()
            bullet.draw(img)

        # 获取手掌心的位置
        left_hand_palm_center = None
        right_hand_palm_center = None

        if landmarks:
            if landmarks[0][0] < width // 2:
                # 左手
                left_hand_palm_center = get_palm_center(landmarks)
            else:
                # 右手
                right_hand_palm_center = get_palm_center(landmarks)

        # 检查是否击中弹幕
        for bullet in bullets[:]:
            if check_bullet_in_circle(bullet):
                # 检查左右手掌心是否与弹幕所在圆圈重合
                if left_hand_palm_center and check_hand_on_edge(left_hand_palm_center):
                    score += combo + 1
                    combo += 1
                    bullets.remove(bullet)
                elif right_hand_palm_center and check_hand_on_edge(right_hand_palm_center):
                    score += combo + 1
                    combo += 1
                    bullets.remove(bullet)

        # 增加连击和速度
        if combo >= speed_increase_threshold:
            bullet_speed += 0.5  # 每达到阈值，增加弹幕的速度
            speed_increase_threshold += 3  # 每次阈值加3

        # 显示得分和连击
        cv2.putText(img, f'Score: {score}', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, colors['白色'], 3)
        cv2.putText(img, f'Combo: {combo}', (50, 120), cv2.FONT_HERSHEY_SIMPLEX, 2, colors['白色'], 3)

    else:  # 游戏未开始
        # 绘制开始按钮区域
        cv2.rectangle(img, (width // 3, height // 3), (2 * width // 3, height // 2), colors['绿色'], cv2.FILLED)
        cv2.putText(img, "Click to Start Game", (width // 3 + 55, height // 2 - 45), cv2.FONT_HERSHEY_SIMPLEX, 1, colors['黑色'], 3)

        # 检查是否点击了开始按钮
        if landmarks:
            start_game(landmarks)

    # 绘制检测点圆圈
    cv2.circle(img, (width // 2, height // 2), circle_radius, colors['白色'], 2)

    # 处理手部标识
    if len(landmarks) > 0:
        if len(landmarks) >= 21:
            # 判断左右手
            palm_center = get_palm_center(landmarks)
            if palm_center[0] < width // 2:
                # 左手
                cv2.rectangle(img, (landmarks[0][0] - 20, landmarks[0][1] - 20), (landmarks[9][0] + 20, landmarks[9][1] + 20), colors['绿色'], 3)
            else:
                # 右手
                cv2.rectangle(img, (landmarks[0][0] - 20, landmarks[0][1] - 20), (landmarks[9][0] + 20, landmarks[9][1] + 20), colors['红色'], 3)

    # 显示图像
    cv2.imshow("Hand Gesture Game", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
