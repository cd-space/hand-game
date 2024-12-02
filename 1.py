import random
import cv2
import math
from cvzone.HandTrackingModule import HandDetector

# OpenCV BGR颜色对照表
colors = {'黑色': (0, 0, 0), '红色': (0, 0, 255), '绿色': (0, 255, 0), '白色': (255, 255, 255)}

# 摄像头设置
cap = cv2.VideoCapture(0)
width, height = 1280, 720
cap.set(3, width)
cap.set(4, height)

detector = HandDetector(detectionCon=1)  # 设置手部检测的置信度

# 游戏状态
game_started = False
score = 0
combo = 0
max_combo = 10
circle_radius = 300  # 检测圆半径
bullet_radius = 20  # 弹幕圆半径

# 弹幕类，表示从圆心发射的弹幕
class Bullet:
    def __init__(self, angle, speed):
        self.angle = angle  # 弹幕的发射角度
        self.speed = speed  # 弹幕的速度
        self.x = width // 2  # 起始位置：圆心x坐标
        self.y = height // 2  # 起始位置：圆心y坐标

    def move(self):
        # 弹幕的 x, y 坐标根据速度和角度更新
        self.x += self.speed * math.cos(self.angle)
        self.y += self.speed * math.sin(self.angle)

    def draw(self, img):
        # 绘制弹幕
        cv2.circle(img, (int(self.x), int(self.y)), bullet_radius, colors['红色'], -1)

# 获取手掌心位置
def get_palm_center(landmarks):
    wrist = landmarks[0]
    middle_finger = landmarks[12]
    palm_center_x = (wrist[0] + middle_finger[0]) // 2
    palm_center_y = (wrist[1] + middle_finger[1]) // 2
    return palm_center_x, palm_center_y

# 检查手掌心是否在圆圈内
def check_hand_in_circle(palm_center):
    x, y = palm_center
    distance = math.sqrt((x - width // 2) ** 2 + (y - height // 2) ** 2)
    return distance <= circle_radius

# 检查弹幕是否到达圆圈边缘
def check_bullet_in_circle(bullet):
    return (bullet.x - width // 2) ** 2 + (bullet.y - height // 2) ** 2 >= (circle_radius - bullet_radius) ** 2

# 开始游戏
def start_game(landmarks):
    global game_started
    x, y = landmarks[8][0], landmarks[8][1]  # 食指尖
    start_button_x1, start_button_y1 = width // 3, height // 3
    start_button_x2, start_button_y2 = 2 * width // 3, height // 2
    if start_button_x1 < x < start_button_x2 and start_button_y1 < y < start_button_y2:
        game_started = True

# 游戏主循环
bullets = []
bullet_speed = 4  # 初始速度
frame_count = 0

while True:
    success, img = cap.read()
    if not success:
        print("无法读取摄像头图像，退出程序")
        break

    img = cv2.flip(img, 1)  # 水平翻转图像
    img = detector.findHands(img)
    landmarks, _ = detector.findPosition(img)

    # 初始化左右手掌心位置
    left_hand_palm_center = None
    right_hand_palm_center = None

    if game_started:
        frame_count += 1
        # 随机生成弹幕
        if frame_count % 60 == 0:  # 每60帧生成一个新的弹幕
            angle = random.uniform(0, 2 * math.pi)
            bullet = Bullet(angle, bullet_speed)
            bullets.append(bullet)

        # 绘制和移动所有弹幕
        for bullet in bullets:
            bullet.move()
            bullet.draw(img)

        # 检测左右手
        if landmarks:
            # 检测左手
            if landmarks[0][0] < width // 2:
                left_hand_palm_center = get_palm_center(landmarks)
            # 检测右手
            elif landmarks[0][0] > width // 2:
                right_hand_palm_center = get_palm_center(landmarks)

        # 检查弹幕
        for bullet in bullets[:]:
            if check_bullet_in_circle(bullet):
                # 检查是否在左手掌心内并击中
                if left_hand_palm_center and check_hand_in_circle(left_hand_palm_center):
                    score += combo + 1
                    combo += 1
                    bullets.remove(bullet)
                # 检查是否在右手掌心内并击中
                elif right_hand_palm_center and check_hand_in_circle(right_hand_palm_center):
                    score += combo + 1
                    combo += 1
                    bullets.remove(bullet)
                else:
                    combo = 0  # 如果没有在手掌心内击中，重置连击
                    bullets.remove(bullet)

        # 增加连击和速度
        if combo >= max_combo:
            bullet_speed += 0.5  # 每达到最大连击，增加弹幕的速度
            max_combo += 3  # 增加连击上限

        # 显示得分和连击
        cv2.putText(img, f'Score: {score}', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, colors['黑色'], 3)
        cv2.putText(img, f'Combo: {combo}', (50, 120), cv2.FONT_HERSHEY_SIMPLEX, 2, colors['黑色'], 3)

    else:
        # 游戏未开始，绘制开始按钮
        cv2.rectangle(img, (width // 3, height // 3), (2 * width // 3, height // 2), colors['绿色'], cv2.FILLED)
        cv2.putText(img, "Click to Start Game", (width // 3 + 55, height // 2 - 45), cv2.FONT_HERSHEY_SIMPLEX, 1, colors['黑色'], 3)

        if landmarks:
            start_game(landmarks)

    # 绘制检测圆和两只手的掌心标记
    cv2.circle(img, (width // 2, height // 2), circle_radius, colors['白色'], 2)

    # 如果有左手，绘制左手掌心
    if left_hand_palm_center:
        cv2.circle(img, left_hand_palm_center, 15, colors['红色'], -1)

    # 如果有右手，绘制右手掌心
    if right_hand_palm_center:
        cv2.circle(img, right_hand_palm_center, 15, colors['红色'], -1)

    # 显示图像
    cv2.imshow("Hand Gesture Game", img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
