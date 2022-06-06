import pygame
import time
import math
from utils import scale_image, blit_rotate_center, blit_text_center
from mip_distance_object import solve

pygame.font.init()

GRASS = scale_image(pygame.image.load("imgs/grass.jpg"), 2.5)
TRACK = scale_image(pygame.image.load("imgs/11_highway.jpg"), 1.5)

#TRACK_BORDER = scale_image(pygame.image.load("imgs/track-border.png"), 0.9)
#TRACK_BORDER_MASK = pygame.mask.from_surface(TRACK_BORDER)

FINISH = pygame.image.load("imgs/finish.png")
FINISH_MASK = pygame.mask.from_surface(FINISH)
FINISH_POSITION = (1500, 60)

RED_CAR = scale_image(pygame.image.load("imgs/red-car.png"), 0.30)
RED_CAR_MASK=pygame.mask.from_surface(RED_CAR)
GREEN_CAR = scale_image(pygame.image.load("imgs/green-car.png"), 0.30)
GREEN_CAR_MASK=pygame.mask.from_surface(GREEN_CAR)

WIDTH, HEIGHT = TRACK.get_width(), TRACK.get_height()
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("MPC")

MAIN_FONT = pygame.font.SysFont("comicsans", 25)
right_lane_y = 100
right_lane_y_2 = 80
FPS = 60


SKY=70
BASEY=130
secondLaneBorder=95

x_start = 200
for x in range(x_start,2000,50):
    PATH = [ (x, right_lane_y), (x, right_lane_y), (x, right_lane_y), (x, right_lane_y), (x, right_lane_y), (x, right_lane_y), (x, right_lane_y), (x, right_lane_y), (x, right_lane_y), (x, right_lane_y),
        (x, right_lane_y), (x, right_lane_y), (x, right_lane_y), (x, right_lane_y), (x, right_lane_y), (x, right_lane_y), (x, right_lane_y), (x, right_lane_y), (x, right_lane_y), (x, right_lane_y), (x, right_lane_y)]
PATH2 = [ (20, right_lane_y_2), (30, right_lane_y_2), (40, right_lane_y_2), (50, right_lane_y_2), (60, right_lane_y_2), (70, right_lane_y_2), (80, right_lane_y_2), (90, right_lane_y_2), (100, right_lane_y_2), (150, right_lane_y_2),
        (200, right_lane_y_2), (250, right_lane_y_2), (300, right_lane_y_2), (350, right_lane_y_2), (400, right_lane_y_2), (450, right_lane_y_2), (500, right_lane_y_2), (550, right_lane_y_2), (600, right_lane_y_2), (650, right_lane_y_2), (2000, right_lane_y_2)]


class GameInfo:
    LEVELS = 10

    def __init__(self, level=1):
        self.level = level
        self.started = False
        self.level_start_time = 0

    def next_level(self):
        self.level += 1
        self.started = False

    def reset(self):
        self.level = 1
        self.started = False
        self.level_start_time = 0

    def game_finished(self):
        return self.level > self.LEVELS

    def start_level(self):
        self.started = True
        self.level_start_time = time.time()

    def get_level_time(self):
        if not self.started:
            return 0
        return round(time.time() - self.level_start_time)


class AbstractCar:
    def __init__(self, max_vel, rotation_vel):
        self.img = self.IMG
        self.max_vel = max_vel
        self.vel = 0
        self.rotation_vel = rotation_vel
        self.angle = 270
        self.x, self.y = self.START_POS
        self.acceleration = 0.1

    def rotate(self, left=False, right=False):
        if left:
            self.angle += self.rotation_vel
        elif right:
            self.angle -= self.rotation_vel

    def draw(self, win):
        blit_rotate_center(win, self.img, (self.x, self.y), self.angle)

    def move_forward(self):
        self.vel = min(self.vel + self.acceleration, self.max_vel)
        self.move()

    def move_backward(self):
        self.vel = max(self.vel - self.acceleration, -self.max_vel/2)
        self.move()

    def move(self):
        radians = math.radians(self.angle)
        vertical = math.cos(radians) * self.vel
        horizontal = math.sin(radians) * self.vel

        self.y -= vertical
        self.x -= horizontal

    def collide(self, mask, x=0, y=0):
        car_mask = pygame.mask.from_surface(self.img)
        offset = (int(self.x - x), int(self.y - y))
        poi = mask.overlap(car_mask, offset)
        # print('Collide')
        return poi

    def reset(self):
        self.x, self.y = self.START_POS
        self.angle = 270
        self.vel = 0


class PlayerCar(AbstractCar):
    IMG = RED_CAR
    START_POS = (100, 100)

    def reduce_speed(self):
        self.vel = max(self.vel - self.acceleration / 2, 0)
        self.move()

    def bounce(self):
        self.vel = -self.vel
        self.move()


class ComputerCar(AbstractCar):
    IMG = GREEN_CAR
    START_POS = (200, right_lane_y)

    def __init__(self, max_vel, rotation_vel, path=[]):
        super().__init__(max_vel, rotation_vel)
        self.path = path
        self.current_point = 0
        self.vel = max_vel

    def draw_points(self, win):
        for point in self.path:
            pygame.draw.circle(win, (255, 0, 0), point, 5)

    def draw(self, win):
        super().draw(win)
        # self.draw_points(win)

    def calculate_angle(self):
        target_x, target_y = self.path[self.current_point]
        x_diff = target_x - self.x
        y_diff = target_y - self.y

        if y_diff == 0:
            desired_radian_angle = math.pi / 2
        else:
            desired_radian_angle = math.atan(x_diff / y_diff)

        if target_y > self.y:
            desired_radian_angle += math.pi

        difference_in_angle = self.angle - math.degrees(desired_radian_angle)
        if difference_in_angle >= 180:
            difference_in_angle -= 360

        if difference_in_angle > 0:
            self.angle -= min(self.rotation_vel, abs(difference_in_angle))
        else:
            self.angle += min(self.rotation_vel, abs(difference_in_angle))

    def update_path_point(self):
        target = self.path[self.current_point]
        rect = pygame.Rect(
            self.x, self.y, self.img.get_width(), self.img.get_height())
        if rect.collidepoint(*target):
            self.current_point += 1

    def move(self):
        if self.current_point >= len(self.path):
            return

        self.calculate_angle()
        self.update_path_point()
        super().move()

    def next_level(self, level):
        self.reset()
        self.vel = self.max_vel + (level - 1) * 0.2
        self.current_point = 0

class ComputerCar2(AbstractCar):
    IMG = GREEN_CAR
    START_POS = (400, right_lane_y_2)

    def __init__(self, max_vel, rotation_vel, path=[]):
        super().__init__(max_vel, rotation_vel)
        self.path = path
        self.current_point = 0
        self.vel = max_vel

    def draw_points(self, win):
        for point in self.path:
            pygame.draw.circle(win, (255, 0, 0), point, 5)

    def draw(self, win):
        super().draw(win)
        # self.draw_points(win)

    def calculate_angle(self):
        target_x, target_y = self.path[self.current_point]
        x_diff = target_x - self.x
        y_diff = target_y - self.y

        if y_diff == 0:
            desired_radian_angle = math.pi / 2
        else:
            desired_radian_angle = math.atan(x_diff / y_diff)

        if target_y > self.y:
            desired_radian_angle += math.pi

        difference_in_angle = self.angle - math.degrees(desired_radian_angle)
        if difference_in_angle >= 180:
            difference_in_angle -= 360

        if difference_in_angle > 0:
            self.angle -= min(self.rotation_vel, abs(difference_in_angle))
        else:
            self.angle += min(self.rotation_vel, abs(difference_in_angle))

    def update_path_point(self):
        target = self.path[self.current_point]
        rect = pygame.Rect(
            self.x, self.y, self.img.get_width(), self.img.get_height())
        if rect.collidepoint(*target):
            self.current_point += 1

    def move(self):
        if self.current_point >= len(self.path):
            return

        self.calculate_angle()
        self.update_path_point()
        super().move()

    def next_level(self, level):
        self.reset()
        self.vel = self.max_vel + (level - 1) * 0.2
        self.current_point = 0


def draw(win, images, player_car, computer_car,computer_car_2,traj, game_info):
    for img, pos in images:
        win.blit(img, pos)

    """level_text = MAIN_FONT.render(
        f"Level {game_info.level}", 1, (255, 255, 255))
    win.blit(level_text, (10, HEIGHT - level_text.get_height() - 70))"""

    time_text = MAIN_FONT.render(
        f"Time: {game_info.get_level_time()}s", 1, (255, 255, 255))
    win.blit(time_text, (10, HEIGHT - time_text.get_height() - 100))

    vel_text = MAIN_FONT.render(
        f"Vel: {round(player_car.vel, 1)}px/s", 1, (255, 255, 255))
    win.blit(vel_text, (10, HEIGHT - vel_text.get_height() - 80))
    #print('trajjj',traj)
    pygame.draw.lines(WIN, (255,0,0), False, [(32+x,10+y) for (x,y) in traj], 3)
    #time.sleep(5)
    pygame.draw.line(WIN,(255,0,0),(0,BASEY),(WIDTH-1,BASEY))
    pygame.draw.line(WIN,(255,0,0),(0,SKY),(WIDTH-1,SKY))
    pygame.draw.line(WIN,(255,0,0),(0,secondLaneBorder),(WIDTH-1,secondLaneBorder))
    player_car.draw(win)
    computer_car.draw(win)
    computer_car_2.draw(win)
    pygame.display.update()

def draw2(win, images, player_car, computer_car, game_info):
    for img, pos in images:
        win.blit(img, pos)

    """level_text = MAIN_FONT.render(
        f"Level {game_info.level}", 1, (255, 255, 255))
    win.blit(level_text, (10, HEIGHT - level_text.get_height() - 70))"""

    time_text = MAIN_FONT.render(
        f"Time: {game_info.get_level_time()}s", 1, (255, 255, 255))
    win.blit(time_text, (10, HEIGHT - time_text.get_height() - 100))

    vel_text = MAIN_FONT.render(
        f"Vel: {round(player_car.vel, 1)}px/s", 1, (255, 255, 255))
    win.blit(vel_text, (10, HEIGHT - vel_text.get_height() - 80))

    computer_car.draw(win)
    #computer_car_2.draw(win)
    pygame.display.update()



def move_player(player_car):
    keys = pygame.key.get_pressed()
    moved = False

    if keys[pygame.K_a]:
        player_car.rotate(left=True)
    if keys[pygame.K_d]:
        player_car.rotate(right=True)
    if keys[pygame.K_w]:
        moved = True
        player_car.move_forward()
    if keys[pygame.K_s]:
        moved = True
        player_car.move_backward()

    if not moved:
        player_car.reduce_speed()


def handle_collision(player_car, computer_car,computer_car_2, game_info):
    #if player_car.collide(TRACK_BORDER_MASK) != None:
    #    player_car.bounce()

    computer_finish_poi_collide = computer_car.collide(FINISH_MASK, *FINISH_POSITION)
    computer_finish_poi_collide2 = computer_car_2.collide(FINISH_MASK, *FINISH_POSITION)

    if computer_finish_poi_collide != None:
        blit_text_center(WIN, MAIN_FONT, "Trajectory could not be completed!")
        pygame.display.update()
        pygame.time.wait(5000)
        game_info.reset()
        player_car.reset()
        computer_car.reset()
        computer_car_2.reset()

    player_finish_poi_collide = player_car.collide(FINISH_MASK, *FINISH_POSITION)
    collision_of_cars=player_car.collide(GREEN_CAR_MASK)
    if collision_of_cars!=None:
        print('Araclar carpisti')
    if player_finish_poi_collide != None:
        if player_finish_poi_collide[1] == 0:
            player_car.bounce()
        else:
            game_info.next_level()
            player_car.reset()
            computer_car.next_level(game_info.level)
            computer_car_2.next_level(game_info.level)



run = True
clock = pygame.time.Clock()
images = [(GRASS, (0, 0)), (TRACK, (0, 0)),
          (FINISH, FINISH_POSITION) ]#(TRACK_BORDER, (0, 0))
player_car = PlayerCar(4, 1)
computer_car = ComputerCar(1, 1, PATH)
computer_car_2 = ComputerCar2(1, 1, PATH)
#computer_car_2 = ComputerCar(2, 1, PATH2)
game_info = GameInfo()


def DetectCollision(computer_car, player_car):
    diff_x = computer_car.x - player_car.x
    diff_y = computer_car.y - player_car.y

    line1 = math.sin(diff_x/RED_CAR.get_height())
    line2 = math.sin(diff_y / RED_CAR.get_width())

    diff1 = ((computer_car.x - player_car.x) ** 2) ** 0.5
    diff2 = ((computer_car.y - player_car.y) ** 2) ** 0.5
    return ((diff1 <= RED_CAR.get_height()) and (diff2 <= RED_CAR.get_width()))


while run:
    clock.tick(FPS)

    #draw(WIN, images, player_car, computer_car , computer_car_2, game_info)
    # draw2(WIN, images, player_car, computer_car_2, game_info)

    while not game_info.started:
        #blit_text_center(
            #WIN, MAIN_FONT, f"Press any key to start level {game_info.level}!")
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                break

            if event.type == pygame.KEYDOWN:
                game_info.start_level()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
            break

    print('velocity',player_car.vel)
    print(player_car.acceleration)
    print('playercar x',player_car.x)
    print('playercar yyy',player_car.y)

    Acc, traj,left_angle,right_angle = solve(player_car.x, player_car.y, player_car.vel,player_car.angle,computer_car.x,computer_car.y)
    #print('Acc',Acc)
    if Acc:
        #print('traj',traj)
        moved = True
        player_car.move_forward()

    if left_angle:
        player_car.rotate(left=True)

    if right_angle:
        player_car.rotate(right=True)

    # if angle_:
    #     print("rotate")
    #     player_car.rotate(left=True)
    #     player_car.move_forward()



    move_player(player_car)
    computer_car.move()
    computer_car_2.move()
    handle_collision(player_car, computer_car,computer_car_2, game_info)
    draw(WIN, images, player_car, computer_car , computer_car_2, traj,game_info)
    if(DetectCollision(computer_car,player_car) or DetectCollision(computer_car_2,player_car)):
        print("Collision")
        player_car.reset()
        computer_car.next_level(game_info.level)
        computer_car_2.next_level(game_info.level)

    if game_info.game_finished():
        blit_text_center(WIN, MAIN_FONT, "Trajectory completed!")
        pygame.time.wait(5000)
        game_info.reset()
        player_car.reset()
        computer_car.reset()
        computer_car_2.reset()

pygame.quit()
