import math
import pygame
import random
from enum import Enum
from config import FPS

from threading import Timer


class GameStates(Enum):
    RUNNING = 0
    GAME_OVER = 1
    QUIT = 2


class BalloonsGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((640, 480))
        self.clock = pygame.time.Clock()
        self.state = GameStates.RUNNING

        self.Balloons = []
        self.generator = Balloon.getNextPos(
            self.screen.get_height(), self.screen.get_width(), 50)
        self._generateBalloons()

        self.debugInfo = {}
        self.score = 0

        # Таймер игры
        self.timer = 120

        # Отслеживает прошедшую секунду для работы с таймером
        self.timerEvent = pygame.USEREVENT + 0
        pygame.time.set_timer(self.timerEvent, 1000)

        # Событие генерации шариков
        self.generationEvent = pygame.USEREVENT + 1
        pygame.time.set_timer(self.generationEvent, 3000)

    def run(self):
        for event in pygame.event.get():
            if event.type == self.timerEvent and self.timer > 0:
                self.timer -= 1
                if self.timer <= 0:
                    self.state = GameStates.GAME_OVER
                    self.scoreToFile()
            if event.type == self.generationEvent:
                self._generateBalloons(1)

            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if self.state == GameStates.RUNNING:
                    self.popBalloon(pos)
            if event.type == pygame.QUIT:
                self.state = GameStates.QUIT

        if self.state == GameStates.RUNNING:
            self.screen.fill((255, 255, 255))
            self._updateBalloons()
            self._drawBalloons()
            pygame.draw.rect(self.screen, (255, 255, 255),
                             pygame.Rect(0, 0, 640, 70))
            self._writeTime()
            self._writeScore()
        elif self.state == GameStates.GAME_OVER:
            self.screen.fill((255, 255, 255))
            # self._drawBalloons()
            # self._writeTime()
            self._writeScore()
            self._writeGameOver()

        # Uncomment for running in pygame window
        # pygame.display.flip()

        self.clock.tick(FPS)

    def _generateBalloons(self, num=1):
        for i in range(num):
            b = Balloon.generate(self.generator)
            self.Balloons.append(b)

    def _drawBalloons(self):
        for b in self.Balloons:
            b.draw(self.screen)

    def _updateBalloons(self):
        for b in self.Balloons:
            b.update(self.clock.get_time())
            if b.pos.y < -b.size * 2:
                self.Balloons.remove(b)

        # self.clock.tick(FPS)

    def popBalloon(self, pos):
        for b in self.Balloons:
            if math.sqrt((pos[0] - b.pos.x) ** 2 + (pos[1] - b.pos.y) ** 2) < b.size:
                # self.Balloons.remove(b)
                b.pop(pos)
                Timer(3, self.removeBalloon, [b]).start()
                self.score = self.score + 1

    def removeBalloon(self, item):
        self.Balloons.remove(item)

    def _writeScore(self):
        # myfont = pygame.font.SysFont("monospace", 30)
        myfont = pygame.font.Font('./assets/Minecraft Seven.ttf', 30)
        label = myfont.render("Score: " + str(self.score), 1, (0, 0, 0))
        self.screen.blit(label, (20, 10))

    def _writeTime(self):
        # myfont = pygame.font.SysFont("monospace", 30)
        myfont = pygame.font.Font('./assets/Minecraft Seven.ttf', 30)

        label = myfont.render("Time left: " + str(self.timer), 1, (0, 0, 0))
        self.screen.blit(label, (self.screen.get_width() -
                         300, 10))

    def _writeGameOver(self):
        # myfont = pygame.font.SysFont("monospace", 50)
        myfont = pygame.font.Font('./assets/Minecraft Seven.ttf', 50)

        label = myfont.render("GAME OVER", 1, (0, 0, 0))
        label_rect = label.get_rect(
            center=(self.screen.get_width()/2, self.screen.get_height()/2))
        self.screen.blit(label, label_rect)

    def _writeDebug(self):
        myfont = pygame.font.SysFont("monospace", 15)
        offset = 10
        for i, (k, v) in enumerate(self.debugInfo.items()):
            if isinstance(v, list):
                label = myfont.render(k, 1, (0, 0, 0))
            else:
                label = myfont.render(k + str(v), 1, (0, 0, 0))
            offset = offset + 10
            self.screen.blit(label, (300, offset))
            if isinstance(v, list):
                for idx, line in enumerate(v):
                    textLine = ' '.join(['{:.2f}'.format(x)
                                         for x in line])
                    label = myfont.render(textLine, 1, (0, 0, 0))
                    offset = offset + 10
                    self.screen.blit(label, (300, offset))

    def updateDebug(self, key, value):
        self.debugInfo[key] = value

    def checkIfBallonOnScreen(self, b):
        return b.pos.y < self.screen.get_height() - b.size and b.pos.y > b.size

    def countBalloonsOffScreen(self):
        cnt = 0
        for b in self.Balloons:
            if not (b.pos.y < self.screen.get_height() - b.size and b.pos.y > b.size):
                cnt = cnt + 1
        return cnt

    def scoreToFile(self):
        with open('leaderboard.txt', 'r') as f:
            lines = f.readlines()
        out = lines.copy()
        for i, line in enumerate(lines):
            if int(line) < self.score:
                out.insert(i, str(self.score) + '\n')
                break
        with open('leaderboard.txt', 'w') as f:
            f.write(''.join(out[:10]))


class Balloon(pygame.sprite.Sprite):
    def __init__(self, x, y, size):
        super(Balloon, self).__init__()

        self.surf = pygame.image.load('assets/balloon.png').convert_alpha()
        self.surf = pygame.transform.scale(
            self.surf, (size * 2, size * 2 + 0.8 * size))

        self.rect = self.surf.get_rect()
        self.velocity = pygame.Vector2(0, -0.1)

        self.pos = pygame.Vector2(x, y)
        self.size = size

        self.rect.update(self.pos.x - self.size,
                         self.pos.y - self.size, self.size * 2, self.size * 2)

    def update(self, dt):
        self.dpos = self.velocity * dt
        self.pos += self.dpos

    def draw(self, surf):
        self.rect.move_ip(self.dpos.x, self.dpos.y)
        surf.blit(self.surf, self.rect)

    def generate(gen):
        size = 50
        x, y = next(gen)
        return Balloon(x, y, size)

    def getNextPos(screenHeight, screenWidth, size):
        offset = 15
        rows = int(screenHeight / (size * 2 + offset))
        cols = int(screenWidth / (size * 2 + offset))
        randXs = Balloon._randomSequence(cols)
        randYs = Balloon._randomSequence(rows)
        fieldHeight = int(screenHeight / rows)
        fieldWidth = int(screenWidth / cols)
        while True:
            if len(randXs) == 0:
                randXs = Balloon._randomSequence(cols)
            if len(randYs) == 0:
                randYs = Balloon._randomSequence(rows)
            y = randYs.pop()
            x = randXs.pop()
            randFieldY = (fieldHeight * y + size,
                          fieldHeight * (y + 1) - size)
            randFieldX = (fieldWidth * x + size,
                          fieldWidth * (x + 1) - size)
            outX = random.randint(randFieldX[0], randFieldX[1])

            # outY = screenHeight + random.randint(randFieldY[0], randFieldY[1])
            outY = screenHeight + size * 2 + 30
            yield outX, outY

    def _randomSequence(maxNum):
        randList = [*range(maxNum)]
        random.shuffle(randList)
        return randList

    def changeColor(self, color):
        self.color = color

    def pop(self, pos):
        self.surf = pygame.image.load('assets/splash.png').convert_alpha()
        self.surf = pygame.transform.scale(
            self.surf, (self.size * 2, self.size * 2))

        self.rect = self.surf.get_rect()
        self.rect.update(pos[0] - self.size,
                         pos[1] - self.size, self.size * 2, self.size * 2)
        self.velocity *= 0


# game = BalloonsGame()
# while True:
    # game.run()
    # if game.state == GameStates.QUIT:
        # break
