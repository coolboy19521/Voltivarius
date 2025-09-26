import cv2
import math
import time
import numpy
import robot_car
import rclpy.node
import sensor_msgs.msg

START = 0
KUBIK_UC = 1
KUBIK_TC = 2
BASE_WALL = 3
FOR_WALL = 4
NARROW = 5
FINAL = 6

GREEN = 0
RED = 1

class miav(rclpy.node.Node):
    def __init__(self):
        super().__init__('miav')
        self.create_subscription(sensor_msgs.msg.LaserScan, '/scan', self.scan_callback, 1)
        self.create_subscription(sensor_msgs.msg.CompressedImage, '/camera/image_raw/compressed', self.camera_callback, 1)
        self.create_timer(1.0 / 15.0, self.miav_callback)

        """
        Direction variables:
        """
        self.dir = None
        self.f_dir = False

        """
        Find kubix variables:
        """
        self.off_x = 35

        """
        Color detection variables:
        """
        self.color = None
        self.colors = {
            'green': [((70, 128, 75), (86, 255, 170)), ((67, 106, 22), (78, 188, 182)), ((69, 51, 33), (95, 193, 154))],
            'red': [((0, 154, 160), (179, 206, 235)), ((0, 113, 0), (8, 255, 255))],
        }

        """
        Exec variables:
        """
        self.kubik = None
        self.turned = False
        self.narrow = False
        self.wall_dis = None
        self.kubik_pos = None
        self.swing_ang = None
        self.start_pos = None
        self.skew_done = False
        self.manoeuvre = False
        self.color_val = False
        self.target_dis = None
        self.gone_back = False
        self.get_close = False
        self.face_kubik = False
        self.last_back_dis = None

        self.exec = START
        """
        Surpass variables:
        """
        self.time = None

        """
        Idle variables (set in scan, unset in miav):
        """
        self.idle = False
        self.idle_speed = None

        robot_car.read_encoder()

        self.kubiks = []
        self.kubik_ix = -1
        self.last_kubik = None
        self.last_dis = None
        self.last_side = None
        self.last_ok = False
        self.on_this_side = 0
        self.seen_start = False
        self.lap_cnt = 0

        self.start_time = None
        self.wall_tilt = None

        self.seen_on_for = False

        self.count = 0

    def find_katets(self, point):
        deg, hyp = point
        beta = math.radians(deg)
        adj = math.cos(beta) * hyp
        opp = math.sin(beta) * hyp
        return adj, opp

    def find_angle(self, a, b):
        (y1, x1), (y2, x2) = a, b
        dx, dy = abs(x2 - x1), abs(y2 - y1)
        return math.degrees(math.atan2(dy, dx))

    def find_wall_tilt(self, data):
        closest, furthest = None, None
        for point in data:
            y_dis, x_dis = self.find_katets(point)
            var = (self.dir == 90 and x_dis < 0) or \
                    (self.dir == -90 and x_dis > 0)
            if y_dis <= 15 and var:
                if furthest is None or y_dis >= furthest[0]:
                    furthest = (y_dis, x_dis)
                if closest is None or y_dis <= closest[0]:
                    closest = (y_dis, x_dis)
        if closest is None or furthest is None:
            return None
        else:
            angle = 90 - self.find_angle(closest, furthest)
            if closest[1] < furthest[1]:
                angle = -angle
            return angle

    def find_kubik(self, data, wall_dis):
        if wall_dis is None:
            return None

        left_lim = self.off_x - wall_dis
        right_lim = 100 - self.off_x - wall_dis

        if self.dir == -90:
            left_lim, right_lim = -right_lim, -left_lim

        closest, furthest = None, None

        for point in data:
            y_dis, x_dis = self.find_katets(point)
            if left_lim <= x_dis <= right_lim:
                if closest is None or closest[0] > y_dis:
                    closest = (y_dis, x_dis)
                if furthest is None or furthest[0] < y_dis:
                    furthest = (y_dis, x_dis)

        if closest is None or furthest is None or \
                furthest[0] - closest[0] <= 60 or \
                closest[0] >= 110 or closest[0] <= 5:
            return None

        if self.dir == 90:
            from_wall_dis = wall_dis + closest[1]
        elif self.dir == -90:
            from_wall_dis = wall_dis - closest[1]

        if (self.dir == 90 and from_wall_dis <= 50) or (self.dir == -90 and from_wall_dis <= 44):
            return 40, closest[0]
        else:
            return 60, closest[0]

    def scan_callback(self, msg):
        gyro_angle = robot_car.read_gyro()
        scan, rad = [], msg.angle_min
        for dis in msg.ranges:
            deg = gyro_angle - math.degrees(rad)
            if -90 <= deg <= 90 and math.isfinite(dis):
                scan.append((deg, dis * 100))
            rad += msg.angle_increment

        self.wall_tilt = self.find_wall_tilt(scan)

        if not self.f_dir:
            left = robot_car.find(max, scan, -90, -10)
            right = robot_car.find(max, scan, 10, 90)
            if left > right:
                self.dir = -90
            else:
                self.dir = 90
            self.f_dir = True
            print('dir found', self.dir)

        if self.dir == 90:
            r_wall_dis = robot_car.find(min, scan, -90, -85)
        else:
            r_wall_dis = robot_car.find(min, scan, 85, 90)

        for_dis = robot_car.find(min, scan, -30, 30)

        self.wall_dis = r_wall_dis

        if self.dir == 90:
            self.side_dis = robot_car.find(min, scan, 85, 90)
        elif self.dir == -90:
            self.side_dis = robot_car.find(min, scan, -90, -85)
        
        self.for_dis = for_dis

        if self.exec is not None:
            return

        kubik = self.find_kubik(scan, r_wall_dis)

        if kubik is not None and self.on_this_side < 2:
            if self.count == 4:
                print(r_wall_dis)
            if self.count == 0:
                self.seen_start = True
            self.time = None
            self.kubik = kubik
            if self.count < 5:
                print('KUBIK_UC prog')
                self.exec = KUBIK_UC
                self.on_this_side += 1
            else:
                side, y_dis = self.kubik
                if self.last_dis is None or (y_dis > self.last_dis and not abs(y_dis - self.last_dis) < 2) or self.last_side is None or side != self.last_side:
                    self.kubik_ix = (self.kubik_ix + 1) % len(self.kubiks)
                    if self.seen_start and self.kubik_ix == len(self.kubiks) - 2:
                        self.lap_cnt += 1
                    elif not self.seen_start and self.kubik_ix == len(self.kubiks) - 1:
                        self.lap_cnt += 1
                    self.last_side = side
                    self.exec = KUBIK_TC
                    print('KUBIK_TC prog', self.last_dis)
                    self.on_this_side += 1
                else:
                    self.idle_speed = 30
                    self.idle = True
                self.last_dis = y_dis
                print('LAST_DIS', self.last_dis)
            print(kubik)
        else:
            for_dis = robot_car.find(max, scan, -5, 5)
            if for_dis is not None and for_dis <= 30:
                print('FOR_WALL prog')
                robot_car.shift_angle -= self.dir
                self.exec = FOR_WALL
                self.last_dis = None
                self.count += 1
            else:
                if for_dis is not None and for_dis <= 85:
                    print(for_dis, r_wall_dis)
                if for_dis is not None and for_dis <= 85 and self.narrow and self.wall_dis is not None:
                    self.narrow = False
                    print('nar', self.wall_dis)
                    if (self.dir == 90 and self.wall_dis < 40) or (self.dir == -90 and self.wall_dis < 52):
                        if self.dir == 90:
                            swing_dis = 50 - self.wall_dis
                        elif self.dir == -90:
                            swing_dis = self.wall_dis - 62
                        self.swing_ang = robot_car.dis_to_ang(swing_dis)
                        self.exec = NARROW
                    elif self.wall_dis > 70:
                        if self.dir == 90:
                            swing_dis = 70 - self.wall_dis
                        elif self.dir == -90:
                            swing_dis = self.wall_dis - 70
                        self.swing_ang = robot_car.dis_to_ang(swing_dis)
                        self.exec = NARROW
                    print('NARROW prog')
                else:
                    if for_dis is not None:
                        self.idle_speed = robot_car.calc_ccel(18, 30, for_dis, 120)
                    else:
                        self.idle_speed = 17.5
                    self.idle = True

    def reset_vars(self):
        self.kubik = None
        self.swing_ang = None
        self.idle_set = False
        self.skew_done = False
        self.manoeuvre = False
        self.color_val = False
        self.start_time = None
        self.gone_back = False
        self.last_ok = False
        self.get_close = False
        self.start_time = None
        self.face_kubik = False
        self.last_back_dis = None

        self.exec = None

    def miav_callback(self):
        if robot_car.height_rot() < -10:
            robot_car.move(0,0)
            robot_car.ser.close()
            raise Exception

        if self.exec is not None:
            self.idle = False
        if not self.f_dir:
            return
        if self.idle:
            gyro_angle = robot_car.read_gyro()
            gyro_error = -gyro_angle
            robot_car.move(head = gyro_error * 2, speed = self.idle_speed)
        if self.exec is None:
            return
        if self.exec == KUBIK_UC:
            if not self.get_close:
                _, y_dis = self.kubik
                go_for = max(y_dis - 95, 0)
                if robot_car.pos is None:
                    self.start_pos = 0
                elif self.start_pos is None:
                    self.start_pos = robot_car.pos
                if go_for != 0 and (robot_car.pos is None or robot_car.rot_to_cm(robot_car.pos - self.start_pos) < go_for):
                    gyro_angle = robot_car.read_gyro()
                    gyro_error = -gyro_angle
                    if robot_car.pos is not None:
                        speed = robot_car.calc_ccel(20, 40, go_for - robot_car.rot_to_cm(robot_car.pos - self.start_pos), go_for)
                    else:
                        speed = 20
                    robot_car.move(head = gyro_error * 2, speed = speed)
                else:
                    self.start_pos = None
                    self.get_close = True
                    robot_car.move(0, 101)
            if self.get_close:
                robot_car.move(0, 101)
                if not self.face_kubik:
                    if self.swing_ang is None:
                        k_pos, _ = self.kubik
                        if self.dir == 90:
                            dis = k_pos - self.wall_dis
                        elif self.dir == -90:
                            dis = self.wall_dis - k_pos
                        self.swing_ang = robot_car.dis_to_ang(dis * .85)
                        if self.count == 1:
                            print(k_pos, self.wall_dis, dis, self.swing_ang)
                        if (dis >= 0) != (self.swing_ang >= 0):
                            self.swing_ang = 0
                        if self.count == 4:
                            print(dis, self.swing_ang)
                    if not self.skew_done:
                        gyro_angle = robot_car.read_gyro()
                        var = self.swing_ang >= 0 and gyro_angle < self.swing_ang or \
                                self.swing_ang < 0 and gyro_angle > self.swing_ang
                        if var:
                            if self.swing_ang >= 0:
                                robot_car.move(head = 50, speed = 40)
                            else:
                                robot_car.move(head = -50, speed = 40)
                        else:
                            self.skew_done = True
                            robot_car.move(0, 101)
                    if self.skew_done:
                        gyro_angle = robot_car.read_gyro()
                        gyro_error = -gyro_angle
                        if self.for_dis is not None:
                            speed = robot_car.calc_ccel(15, 27, self.for_dis, 80)
                        if self.for_dis is not None and self.for_dis >= 30:
                            gyro_angle = robot_car.read_gyro()
                            gyro_error = -gyro_angle
                            robot_car.move(head = gyro_error * 2, speed = speed)
                        else:
                            self.face_kubik = True
                            self.skew_done = False
                            robot_car.move(0, 101)
                if self.face_kubik:
                    if not self.gone_back:
                        if robot_car.pos is None:
                            self.start_pos = 0
                        elif self.start_pos is None:
                            self.start_pos = robot_car.pos
                        if robot_car.pos is None or robot_car.rot_to_cm(robot_car.pos - self.start_pos) < 10:
                            gyro_angle = robot_car.read_gyro()
                            if robot_car.pos is not None:
                                gone = robot_car.rot_to_cm(robot_car.pos - self.start_pos)
                                speed = -robot_car.calc_ccel(20, 30, max(20 - gone, 0), 40)
                            else:
                                speed = -20
                            robot_car.move(head = gyro_angle * 2, speed = speed)
                        else:
                            self.start_pos = None
                            self.gone_back = True
                    if self.gone_back:
                        if not self.color_val:
                            if self.color is None:
                                gyro_angle = robot_car.read_gyro()
                                gyro_error = -gyro_angle
                                robot_car.move(head = gyro_error * 2, speed = 20)
                            else:
                                k_pos, _ = self.kubik
                                if self.color == GREEN:
                                    if self.dir == 90:
                                        if self.count % 4 != 0:
                                            swing_dis = k_pos / 2 - self.wall_dis
                                        else:
                                            swing_dis = k_pos / 2 - self.wall_dis + 13
                                    elif self.dir == -90:
                                        swing_dis = self.wall_dis - (100 + k_pos) / 2
                                    self.swing_ang = robot_car.dis_to_ang(swing_dis * .87)
                                    print('GREEN', self.swing_ang)
                                elif self.color == RED:
                                    if self.dir == 90:
                                        swing_dis = (100 + k_pos) / 2 - self.wall_dis
                                    elif self.dir == -90:
                                        if self.count % 4 != 0:
                                            swing_dis = self.wall_dis - k_pos / 2
                                        else:
                                            swing_dis = self.wall_dis - k_pos / 2 - 15
                                    print(swing_dis)
                                    self.swing_ang = robot_car.dis_to_ang(swing_dis * .87)
                                    print('RED', self.swing_ang)
                                self.narrow = True
                                if self.color == GREEN:
                                    robot_car.green_led.on()
                                elif self.color == RED:
                                    robot_car.red_led.on()
                                if self.count > 0:
                                    self.kubiks.append(self.color)
                                    print('ADDED', self.color)
                                self.color_val = True
                                robot_car.move(0, 101)
                        if self.color_val:
                            if not self.skew_done:
                                gyro_angle = robot_car.read_gyro()
                                var = self.swing_ang >= 0 and gyro_angle < self.swing_ang or \
                                        self.swing_ang < 0 and gyro_angle > self.swing_ang
                                if var:
                                    if self.swing_ang >= 0:
                                        robot_car.move(head = 50, speed = 40)
                                    else:
                                        robot_car.move(head = -50, speed = 40)
                                else:
                                    self.skew_done = True
                                    robot_car.move(0, 101)
                            if self.skew_done:
                                gyro_angle = robot_car.read_gyro()
                                gyro_error = -gyro_angle
                                if not -4 <= gyro_error <= 4:
                                    gyro_angle = robot_car.read_gyro()
                                    gyro_error = -gyro_angle
                                    robot_car.move(head = gyro_error * 2, speed = 30)
                                else:
                                    print('KUBIK DONE')
                                    robot_car.green_led.off()
                                    robot_car.red_led.off()
                                    self.reset_vars()
                                    robot_car.move(0, 101)
        elif self.exec == KUBIK_TC:
            color = self.kubiks[self.kubik_ix]
            self.narrow = True
            if not self.skew_done:
                if self.swing_ang is None:
                    k_pos, _ = self.kubik
                    if color == GREEN:
                        if self.dir == 90:
                            if self.count % 4 != 0:
                                swing_dis = k_pos / 2 - self.wall_dis
                            else:
                                swing_dis = k_pos / 2 - self.wall_dis + 11
                        elif self.dir == -90:
                            swing_dis = self.wall_dis - (100 + k_pos) / 2
                        print('GREEN')
                        if self.count != 5:
                            self.swing_ang = robot_car.dis_to_ang(swing_dis * .73)
                        else:
                            self.swing_ang = robot_car.dis_to_ang(swing_dis * .75)
                        print('SWING_ANG', self.swing_ang)
                    elif color == RED:
                        if self.dir == 90:
                            swing_dis = (100 + k_pos) / 2 - self.wall_dis
                        elif self.dir == -90:
                            if self.count % 4 != 0:
                                swing_dis = self.wall_dis - k_pos / 2
                            else:
                                swing_dis = self.wall_dis - k_pos / 2 - 11
                        print('RED')
                        if self.count != 5:
                            self.swing_ang = robot_car.dis_to_ang(swing_dis * .73)
                        else:
                            self.swing_ang = robot_car.dis_to_ang(swing_dis * .75)
                        print('SWING_ANG', self.swing_ang)
                gyro_angle = robot_car.read_gyro()
                var = self.swing_ang >= 0 and gyro_angle < self.swing_ang or \
                        self.swing_ang < 0 and gyro_angle > self.swing_ang
                if var:
                    if self.swing_ang >= 0:
                        robot_car.move(head = 50, speed = 45)
                    else:
                        robot_car.move(head = -50, speed = 45)
                else:
                    self.skew_done = True
                    robot_car.move(0, 101)
                print('KUBIK done')
            if self.skew_done:
                gyro_angle = robot_car.read_gyro()
                gyro_error = -gyro_angle
                if not -3 <= gyro_error <= 3:
                    gyro_angle = robot_car.read_gyro()
                    gyro_error = -gyro_angle
                    if self.count > 4:
                        print(gyro_error)
                    if self.count != 5:
                        robot_car.move(head = gyro_error, speed = 45)
                    else:
                        robot_car.move(head = gyro_error, speed = 35)
                else:
                    self.exec = None
                    self.reset_vars()
                    if self.lap_cnt == 2:
                        print('HI')
                    if self.lap_cnt == 2 and self.count % 4 == 0:
                        robot_car.move(0, 0)
                        self.exec = FINAL
        elif self.exec == FOR_WALL:
            gyro_angle = robot_car.read_gyro()
            gyro_error = -gyro_angle
            back_dis = robot_car.ultra.distance * 100
            if (not self.last_ok or back_dis != 100) and back_dis >= 25:
                if back_dis < 50:
                    self.last_ok = True
                gyro_angle = robot_car.read_gyro()
                speed = robot_car.calc_ccel(22, 25, back_dis, 60)
                robot_car.move(head = gyro_angle, speed = -speed)
            else:
                now = time.monotonic()
                if self.start_time is None or now - self.start_time < .6:
                    if self.start_time is None:
                        robot_car.move(0, 101)
                        self.start_time = time.monotonic()
                    now = time.monotonic()
                else:
                    print('FOR_WALL done')
                    gyro_angle = robot_car.read_gyro()
                    if self.dir == 90:
                        robot_car.shift_angle += (self.wall_tilt - gyro_angle) * .85
                        print('SHIFTED BY', (self.wall_tilt - gyro_angle) * .85)
                    elif self.dir == -90:
                        robot_car.shift_angle += (self.wall_tilt - gyro_angle) * .65
                        print('SHIFTED BY', (self.wall_tilt - gyro_angle) * .65)
                    if self.lap_cnt >= 2:
                        print('DO', self.count % 4)
                    self.turned = True
                    self.on_this_side = 0
                    self.reset_vars()
                    if self.lap_cnt >= 2 and self.count % 4 == 0:
                        robot_car.move(0, 0)
                        self.seen_on_for = True
                        self.exec = FINAL
        elif self.exec == START:
            if self.dir == 90:
                if not self.skew_done:
                    gyro_angle = robot_car.read_gyro()
                    if gyro_angle < 60:
                        robot_car.move(head = 1000, speed = 24)
                    else:
                        robot_car.move(0, 0)
                        self.skew_done = True
                if self.skew_done:
                    if not self.manoeuvre:
                        gyro_angle = robot_car.read_gyro()
                        gyro_error = -gyro_angle
                        if not -5 <= gyro_error <= 5:
                            robot_car.move(head = gyro_error * 1.2, speed = 25)
                        else:
                            self.manoeuvre = True
                    if self.manoeuvre:
                        if robot_car.pos is None:
                            self.start_pos = 0
                        elif self.start_pos is None:
                            self.start_pos = robot_car.pos
                        if robot_car.pos is None or robot_car.rot_to_cm(robot_car.pos - self.start_pos) < 45:
                            gyro_angle = robot_car.read_gyro()
                            if robot_car.pos is not None:
                                gone = robot_car.rot_to_cm(robot_car.pos - self.start_pos)
                                speed = -robot_car.calc_ccel(25, 30, max(50 - gone, 0), 45)
                            else:
                                speed = -15
                            robot_car.move(head = gyro_angle * 2, speed = speed)
                        else:
                            robot_car.move(0, 0)
                            self.start_pos = None
                            self.manouevre = True
                            self.reset_vars()
            elif self.dir == -90:
                if not self.skew_done:
                    gyro_angle = robot_car.read_gyro()
                    if gyro_angle > -120:
                        robot_car.move(head = -1000, speed = 20)
                    else:
                        robot_car.move(0, 101)
                        self.skew_done = True
                if self.skew_done:
                    if not self.manoeuvre:
                        gyro_angle = robot_car.read_gyro()
                        gyro_error = -90 - gyro_angle
                        if self.side_dis >= 20:
                            robot_car.move(head = gyro_error * 1.2, speed = 20)
                        else:
                            self.manoeuvre = True
                            robot_car.move(0, 101)
                    if self.manoeuvre:
                        if not self.face_kubik:
                            gyro_angle = robot_car.read_gyro()
                            if not -3 <= gyro_angle <= 3:
                                gyro_angle = robot_car.read_gyro()
                                robot_car.move(head = -1000, speed = -23)
                            else:
                                self.face_kubik = True
                        if self.face_kubik:
                            if robot_car.pos is None:
                                self.start_pos = 0
                            elif self.start_pos is None:
                                self.start_pos = robot_car.pos
                            if robot_car.pos is None or robot_car.rot_to_cm(robot_car.pos - self.start_pos) < 25:
                                gyro_angle = robot_car.read_gyro()
                                if robot_car.pos is not None:
                                    gone = robot_car.rot_to_cm(robot_car.pos - self.start_pos)
                                    speed = -robot_car.calc_ccel(18, 26, max(25 - gone, 0), 25)
                                else:
                                    speed = -15
                                robot_car.move(head = gyro_angle * 2, speed = speed)
                            else:
                                robot_car.move(0, 101)
                                self.start_pos = None
                                self.reset_vars()
        elif self.exec == NARROW:
            gyro_angle = robot_car.read_gyro()
            var = self.swing_ang >= 0 and gyro_angle < self.swing_ang or \
                self.swing_ang < 0 and gyro_angle > self.swing_ang
            if var:
                if self.swing_ang >= 0:
                    robot_car.move(head = 50, speed = 30)
                else:
                    robot_car.move(head = -50, speed = 30)
            else:
                print('NARROW done')
                self.narrow = False
                self.exec = None
                self.reset_vars()
        elif self.exec == FINAL:
            if not self.gone_back:
                if not self.get_close:
                    robot_car.move(0, 0)
                    self.get_close = True
                back_dis = robot_car.ultra.distance * 100
                if back_dis > 45:
                    gyro_angle = robot_car.read_gyro()
                    robot_car.move(head = gyro_angle, speed = -22)
                else:
                    self.gone_back = True
                    robot_car.move(0, 0)
            if self.gone_back:
                if not self.manoeuvre:
                    if robot_car.pos is None:
                        self.start_pos = 0
                    elif self.start_pos is None:
                        self.start_pos = robot_car.pos
                    if self.dir == 90:
                        go_for = 125
                    elif self.dir == -90:
                        go_for = 182
                    if self.seen_on_for:
                        go_for += 20
                    if robot_car.pos is None or robot_car.rot_to_cm(robot_car.pos - self.start_pos) < go_for:
                        gyro_angle = robot_car.read_gyro()
                        gyro_error = -gyro_angle
                        if robot_car.pos is not None:
                            speed = robot_car.calc_ccel(25, 45, go_for - robot_car.rot_to_cm(robot_car.pos - self.start_pos), go_for)
                        else:
                            speed = 25
                        robot_car.move(head = gyro_error * 2, speed = speed)
                    else:
                        robot_car.move(0, 0)
                        self.manoeuvre = True
                if self.manoeuvre:
                    gyro_angle = robot_car.read_gyro()
                    if self.dir == 90:
                        gyro_error = 90 - gyro_angle
                    elif self.dir == -90:
                        gyro_error = -90 - gyro_angle
                    if not -3 <= gyro_error <= 3:
                        gyro_angle = robot_car.read_gyro()
                        if self.dir == 90:
                            gyro_error = 90 - gyro_angle
                        elif self.dir == -90:
                            gyro_error = -90 - gyro_angle
                        robot_car.move(head = -gyro_error, speed = -25)
                    else:
                        back_dis = robot_car.ultra.distance * 100
                        if (not self.last_ok or back_dis != 100) and back_dis >= 22:
                            if back_dis < 50:
                                self.last_ok = True
                            gyro_angle = robot_car.read_gyro()
                            if self.dir == 90:
                                gyro_error = 90 - gyro_angle
                            elif self.dir == -90:
                                gyro_error = -90 - gyro_angle
                            robot_car.move(head = gyro_error, speed = -24)
                        else:
                            robot_car.move(0, 101)
                            raise Exception

    def find_colors(self, hsv, colors):
        area = dict()
        for color, codes in self.colors.items():
            if color in colors:
                area[color], mask = 0, None
                for code in codes:
                    color_low = numpy.array(code[0])
                    color_high = numpy.array(code[1])
                    m = cv2.inRange(hsv, color_low, color_high)
                    mask = m if mask is None else cv2.bitwise_or(mask, m)
                if mask is not None:
                    coords = cv2.findNonZero(mask)
                    if coords is not None:
                        area[color] = len(coords)
        return area

    def camera_callback(self, msg):
        np_arr = numpy.frombuffer(msg.data, numpy.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        height, width, _ = frame.shape
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        k_hsv = hsv[height*4//10:,:]
        k_area = self.find_colors(k_hsv, ('green', 'red'))
        if k_area['green'] > k_area['red']: self.color = GREEN
        elif k_area['red'] > k_area['green']: self.color = RED
        else: self.color = None
