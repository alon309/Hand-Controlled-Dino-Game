import pygame 
import os
import cv2
import pyautogui 
import mediapipe as mp 
import time
import threading
import random

pygame.init()

#globals
SCREEN_WIDTH = 1100
SCREEN_HEIGHT = 600
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

RUNNING = [pygame.image.load(os.path.join("Images","DinoRun1.png")),
           pygame.image.load(os.path.join("Images","DinoRun2.png"))]

JUMPING = pygame.image.load(os.path.join("Images","DinoJump.png"))

DUCKING = [pygame.image.load(os.path.join("Images","DinoDuck1.png")),
           pygame.image.load(os.path.join("Images","DinoDuck2.png"))]

SMALL_CACTUS_OG = [pygame.image.load(os.path.join("Images","SmallCactus1.png")),
           pygame.image.load(os.path.join("Images","SmallCactus2.png")),
           pygame.image.load(os.path.join("Images","SmallCactus3.png"))]

LARGE_CACTUS_OG = [pygame.image.load(os.path.join("Images","LargeCactus1.png")),
           pygame.image.load(os.path.join("Images","LargeCactus2.png")),
           pygame.image.load(os.path.join("Images","LargeCactus3.png"))]

BIRD = [pygame.image.load(os.path.join("Images","Bird1.png")),
           pygame.image.load(os.path.join("Images","Bird2.png"))]

CLOUD = pygame.image.load(os.path.join("Images","Cloud.png"))

BG = pygame.image.load(os.path.join("Images","Track.png"))

#resize the Cactuses
SMALL_CACTUS = [pygame.transform.scale(img, (img.get_width() // 2 + 30, img.get_height() // 2 + 30)) for img in SMALL_CACTUS_OG]
LARGE_CACTUS = [pygame.transform.scale(img, (img.get_width() // 2 + 30, img.get_height() // 2 + 30)) for img in LARGE_CACTUS_OG]


#for head detector
is_pointing_down = False
is_hand_closed = False

#for dino game
run_flag = False
game_speed = 10
bg_x = 0
bg_y = 380
score = 0
obstacles = []
death_cnt = 0


# Class representing the player character, the dinosaur
class Dinosaur:
    x_pos =80
    y_pos = 310
    y_pos_duck = 340
    jmp_vel = 8.5

    def __init__(dino):
        # Images for different states of the dinosaur
        dino.duckImg = DUCKING
        dino.runImg = RUNNING
        dino.jumpImg = JUMPING

         # Status flags
        dino.isDuck = False
        dino.isRun = True
        dino.isJump = False

        dino.step_index = 0
        dino.jmpVel = dino.jmp_vel
        dino.img = dino.runImg[0]
        dino.dino_rect = dino.img.get_rect()
        dino.dino_rect.x = dino.x_pos
        dino.dino_rect.y = dino.y_pos


    # Update the dinosaur's state based on hand gestures
    def update(dino, userInput):
        if dino.isDuck:
            dino.duck()
        if dino.isRun:
            dino.run()
        if dino.isJump:
            dino.jump()

        if dino.step_index > 9:
            dino.step_index=0
        
        # Detect hand gestures to control the dinosaur's actions
        if is_hand_closed and not dino.isJump:
            dino.isDuck = False
            dino.isRun = False
            dino.isJump = True

        elif is_pointing_down and not dino.isDuck:
            dino.isDuck = True
            dino.isRun = False
            dino.isJump = False


        elif not (userInput[pygame.K_DOWN] or is_pointing_down or dino.isJump):
            dino.isDuck = False
            dino.isRun = True
            dino.isJump = False

    # Handle ducking animation
    def duck(dino):
        dino.img = dino.duckImg[dino.step_index // 5]
        dino.dino_rect = dino.img.get_rect()
        dino.dino_rect.x = dino.x_pos
        dino.dino_rect.y = dino.y_pos_duck
        dino.step_index += 1

     # Handle jumping animation
    def jump(dino):
        dino.img = dino.jumpImg
        if dino.isJump:
            dino.dino_rect.y -= dino.jmpVel * 4
            dino.jmpVel -= 0.8
        if dino.jmpVel < -dino.jmp_vel:
            dino.isJump = False
            dino.jmpVel = dino.jmp_vel


    # Handle running animation
    def run(dino):
        dino.img = dino.runImg[dino.step_index // 5]
        dino.dino_rect = dino.img.get_rect()
        dino.dino_rect.x = dino.x_pos
        dino.dino_rect.y = dino.y_pos
        dino.step_index += 1


    # Draw the dinosaur on the screen
    def draw(dino, SCREEN):
        SCREEN.blit(dino.img, (dino.dino_rect.x, dino.dino_rect.y))


# Class representing clouds in the background
class Cloud:
    def __init__(self):
        self.x = SCREEN_WIDTH + random.randint(800,1000)
        self.y = random.randint(50,100)
        self.img = CLOUD
        self.width = self.img.get_width()

    # Update the cloud's position
    def update(self):
        self.x -= game_speed
        if self.x < -self.width:
            self.x = SCREEN_WIDTH + random.randint(2500,3000)
            self.y = random.randint(50,100)

    # Draw the cloud on the screen
    def draw(self,SCREEN):
        SCREEN.blit(self.img, (self.x, self.y))

# Class representing for game obstacles
class Obstacles:
    def __init__(self, img, type):
        self.img = img
        self.type = type
        self.rect = self.img[self.type].get_rect()
        self.rect.x = SCREEN_WIDTH

    # Update the obstacle's position
    def update(self):
        self.rect.x -= game_speed
        if self.rect.x < -self.rect.width:
            obstacles.pop()

    # Draw the obstacle on the screen
    def draw(self,SCREEN):
        SCREEN.blit(self.img[self.type], self.rect)

# Class for small cactus obstacles
class SmallCactus(Obstacles):
    def __init__(self, img):
        self.type = random.randint(0,2)
        super().__init__(img, self.type)
        self.rect.y = 325

# Class for large cacti obstacles
class LargeCactus(Obstacles):
    def __init__(self, img):
        self.type = random.randint(0,2)
        super().__init__(img, self.type)
        self.rect.y = 300

# Class for bird obstacles
class Bird(Obstacles):
    def __init__(self, img):
        self.type = 0
        super().__init__(img, self.type)
        self.rect.y = 250
        self.index = 0

    # Draw the bird animation
    def draw(self, SCREEN):
        if self.index >= 9:
            self.index = 0
        SCREEN.blit(self.img[self.index // 5], self.rect)
        self.index += 1


# Function for hand gesture detection using Mediapipe
def HandDetector():
    global  run_flag, is_hand_closed, is_pointing_down

    cap = cv2.VideoCapture(0)

    mpHands = mp.solutions.hands
    hands=mpHands.Hands(static_image_mode=False, max_num_hands=1,
                        min_detection_confidence=0.5, min_tracking_confidence=0.5)

    mpDrawing = mp.solutions.drawing_utils

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb_image)

        if result.multi_hand_landmarks:
            # Draw landmarks and detect hand gestures
            for cur_hand in result.multi_hand_landmarks:
                mpDrawing.draw_landmarks(frame, cur_hand,mpHands.HAND_CONNECTIONS)

                thumb = cur_hand.landmark[mpHands.HandLandmark.THUMB_TIP]
                index = cur_hand.landmark[mpHands.HandLandmark.INDEX_FINGER_TIP]
                middle = cur_hand.landmark[mpHands.HandLandmark.MIDDLE_FINGER_TIP]
                ring = cur_hand.landmark[mpHands.HandLandmark.RING_FINGER_TIP]
                pinky = cur_hand.landmark[mpHands.HandLandmark.PINKY_TIP]

                # Detect hand gestures based on finger positions
                is_hand_closed = (index.y > thumb.y and middle.y > thumb.y and ring.y > thumb.y and pinky.y > thumb.y)
                is_pointing_down = (index.y > thumb.y and index.y > middle.y and index.y > ring.y and index.y > pinky.y)
                
                
        else:
            is_hand_closed = False
            is_pointing_down = False

        cv2.imshow("HandGame", frame)

         # Exit the hand detection loop if the game is not running or 'q' is pressed
        if (cv2.waitKey(1) & 0xFF==ord('q')) or (not run_flag):
            run_flag = False
            break

    cap.release()
    cv2.destroyAllWindows()
        

# Main game loop
def main():
    global run_flag, game_speed, bg_x, bg_y, score, obstacles, death_cnt
    run_flag = True
    clock = pygame.time.Clock()
    player = Dinosaur()
    isOpen = False
    game_speed = 14
    font = pygame.font.Font('freesansbold.ttf', 20)

    cloud = Cloud()

    # Start a separate thread for hand gesture detection
    Detector_thread=threading.Thread(target=HandDetector)
    Detector_thread.start()

    # Function to display and manage the background scrolling
    def Background():
        global bg_x, bg_y, game_speed
        img_width = BG.get_width()
        SCREEN.blit(BG, (bg_x, bg_y))
        SCREEN.blit(BG, (img_width + bg_x, bg_y))

        if bg_x <= -img_width:
            SCREEN.blit(BG,(img_width + bg_x, bg_y))
            bg_x=0

        bg_x -= game_speed
    
    # Function to display the player's score on the screen
    def points():
        global game_speed, score
        score += 1
        if score % 100 == 0:
            game_speed += 1
        
        txt = font.render("Score: " + str(score), True, (0,0,0))
        txt_rect = txt.get_rect()
        txt_rect.center = (1000,40)
        SCREEN.blit(txt, txt_rect)


    pygame.time.delay(5000)

    while run_flag:
        # Exit the game if Exit button pressed 
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                run_flag = False

        SCREEN.fill((255, 255, 255))
        userInput = pygame.key.get_pressed()


        player.draw(SCREEN)
        player.update(userInput)

        # Add random obstacle to obstacle array
        if len(obstacles) == 0:
            if random.randint(0,2) == 0:
                obstacles.append(SmallCactus(SMALL_CACTUS))
            elif random.randint(0,2) == 1:
                obstacles.append(LargeCactus(LARGE_CACTUS))
            elif random.randint(0,2) == 2:
                obstacles.append(Bird(BIRD))

        # Draw obstacles
        for obstacle in obstacles:
            obstacle.draw(SCREEN)
            obstacle.update()

            # Check for collisions between the player and obstacles
            if player.dino_rect.colliderect(obstacle.rect):
                pygame.time.delay(2000)
                death_cnt += 1
                menu(death_cnt)

        # Draw clouds
        cloud.draw(SCREEN)
        cloud.update()

        Background()
        points()

        clock.tick(30)
        pygame.display.update()

    # For new game
    obstacles.clear()
    score = 0
    game_speed = 10
    bg_x = 0
    bg_y = 380
    death_cnt = 0


# Function to display the game menu
def menu(death_cnt):
    global score, game_speed, bg_x, bg_y, run_flag
    run_flag = True
    help_button_clicked = False

    while run_flag:
        font = pygame.font.Font('freesansbold.ttf', 30)
        SCREEN.fill((255, 255, 255))

        # User's entrance screen
        if death_cnt == 0:
            txt = font.render("Press any key to start", True, (0, 0, 0))

            # Menu screen
            if not help_button_clicked:
                help_button = pygame.draw.rect(SCREEN, (255, 0, 0), (50, 50, 100, 50))
                help_text = font.render("HELP", True, (255, 255, 255))  # Render text on the button
                help_text_rect = help_text.get_rect()
                help_text_rect.center = help_button.center  # Center the text on the button
                txt = font.render("Press any key to start", True, (0, 0, 0))
            # Help screen
            else:
                txt = font.render("", True, (0, 0, 0))

                instructions = [
                "Open your hand to run",
                "Close hand to jump",
                "Point your index finger down to duck"
            ]
                for i, instruction in enumerate(instructions):
                    instruction_text = font.render(instruction, True, (0, 0, 0))
                    instruction_rect = instruction_text.get_rect()
                    instruction_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50 * i)
                    SCREEN.blit(instruction_text, instruction_rect)

                back_button = pygame.draw.rect(SCREEN, (0, 0, 0), (50, 500, 100, 50))
                back_text = font.render("Back", True, (255, 255, 255))
                back_text_rect = back_text.get_rect()
                back_text_rect.center = back_button.center
                SCREEN.blit(back_text, back_text_rect)

        # Screen after user died
        elif death_cnt > 0:
            txt = font.render("Press any key to start", True, (0, 0, 0))
            result = font.render("Your score: " + str(score), True, (0, 0, 0))
            resultRect = result.get_rect()
            resultRect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50)
            SCREEN.blit(result, resultRect)

        txtRect = txt. get_rect()
        txtRect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        SCREEN.blit(txt, txtRect)
        SCREEN.blit(RUNNING[0], (SCREEN_WIDTH // 2 - 30, SCREEN_HEIGHT // 2 - 140))
        
        if not help_button_clicked and death_cnt == 0:
            pygame.draw.rect(SCREEN, (0, 0, 0), help_button)  # Draw the "Help" button
            SCREEN.blit(help_text, help_text_rect)

        pygame.display.update()

        for event in pygame.event.get():
            # If user press exit, the game will exit
            if event.type == pygame.QUIT:
                run_flag = False

            # If user press any key, the game will start
            if event.type == pygame.KEYDOWN:
                obstacles.clear()
                score = 0
                game_speed = 10
                bg_x = 0
                bg_y = 380
                death_cnt = 0
                main()
            
            # If user press HELP button, HELP screen will pop
            if event.type == pygame.MOUSEBUTTONDOWN:
                if not help_button_clicked and death_cnt == 0 and help_button.collidepoint(event.pos):
                    help_button_clicked = True
                elif help_button_clicked and back_button.collidepoint(event.pos):
                    help_button_clicked = False  # Go back to the previous screen



menu(death_cnt)