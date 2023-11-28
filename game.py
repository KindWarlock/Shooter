import math
import pygame
import random
from enum import Enum


class GameStates(Enum):
    RUNNING = 0
    GAME_OVER = 1
    QUIT = 2


class BaloonsGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((640, 480))
        self.clock = pygame.time.Clock()
        self.state = GameStates.RUNNING

        self.baloons = []
        self.baloonsCount = 6
        self.generator = Baloon.getNextPos(
            self.screen.get_height(), self.screen.get_width(), 50)
        self._generateBaloons()

        self.debugInfo = {}
        self.score = 0

        # Timer for a game
        self.timer = 40  # time in seconds
        self.timerEvent = pygame.USEREVENT + 0
        self.generationEvent = pygame.USEREVENT + 1
        pygame.time.set_timer(self.timerEvent, 1000)
        pygame.time.set_timer(self.generationEvent, 3000)

    def run(self):
        for event in pygame.event.get():
            if event.type == self.timerEvent and self.timer > 0:
                self.timer -= 1
                if self.timer <= 0:
                    self.state = GameStates.GAME_OVER
            if event.type == self.generationEvent:
                self._generateBaloons(1)

            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if self.state == GameStates.RUNNING:
                    self.popBaloon(pos)
            if event.type == pygame.QUIT:
                self.state = GameStates.QUIT

        if self.state == GameStates.RUNNING:
            self.screen.fill((255, 255, 255))
            self._updateBaloons()
            self._drawBaloons()
            self._writeTime()

            self._writeScore()
        elif self.state == GameStates.GAME_OVER:
            self.screen.fill((255, 255, 255))
            # self._drawBaloons()
            # self._writeTime()
            self._writeScore()
            self._writeGameOver()

        # Uncomment for running in pygame window
        pygame.display.flip()

        self.clock.tick(60)

    def _generateBaloons(self, num=1):
        for i in range(num):
            b = Baloon.generate(self.generator)
            self.baloons.append(b)

    def _drawBaloons(self):
        for b in self.baloons:
            b.draw(self.screen)

    def _updateBaloons(self):
        for b in self.baloons:
            b.update(self.clock.get_time())
            if b.pos.y < -b.size * 2:
                self.baloons.remove(b)

        self.clock.tick(60)

    def popBaloon(self, pos):
        for b in self.baloons:
            if math.sqrt((pos[0] - b.pos.x) ** 2 + (pos[1] - b.pos.y) ** 2) < b.size:
                self.baloons.remove(b)
                self.score = self.score + 1
                # b.changeColor((0, 225, 225))

    def _writeScore(self):
        myfont = pygame.font.SysFont("monospace", 30)
        label = myfont.render("Score: " + str(self.score), 1, (0, 0, 0))
        self.screen.blit(label, (20, 10))

    def _writeTime(self):
        myfont = pygame.font.SysFont("monospace", 30)
        label = myfont.render("Time left: " + str(self.timer), 1, (0, 0, 0))
        self.screen.blit(label, (self.screen.get_width() -
                         300, 10))

    def _writeGameOver(self):
        myfont = pygame.font.SysFont("monospace", 50)
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
                    # label = myfont.render(' '.join(line), 1, (0, 0, 0))
                    textLine = ' '.join(['{:.2f}'.format(x)
                                         for x in line])
                    label = myfont.render(textLine, 1, (0, 0, 0))
                    offset = offset + 10
                    self.screen.blit(label, (300, offset))

    def updateDebug(self, key, value):
        self.debugInfo[key] = value

    def checkIfBallonOnScreen(self, b):
        return b.pos.y < self.screen.get_height() - b.size and b.pos.y > b.size

    def countBaloonsOffScreen(self):
        cnt = 0
        for b in self.baloons:
            if not (b.pos.y < self.screen.get_height() - b.size and b.pos.y > b.size):
                cnt = cnt + 1
        return cnt


class Baloon(pygame.sprite.Sprite):
    def __init__(self, x, y, size):
        super(Baloon, self).__init__()
        self.surf = pygame.image.load('assets/balloon.png').convert_alpha()
        self.rect = self.surf.get_rect()
        self.pos = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(0, -2)
        self.acceleration = pygame.Vector2(0, 0)
        self.size = size
        self.timePassed = 0
        self.color = (0, 0, 255)

        self.surf = pygame.transform.scale(
            self.surf, (size * 2, size * 2 + 0.8 * size))
        self.rect.update(self.pos.x - self.size,
                         self.pos.y - self.size, self.size * 2, self.size * 2)

    def update(self, dt):
        self.timePassed = self.timePassed + dt * 100
        # self.acceleration.x = math.cos(self.timePassed)
        # self.velocity = self.velocity + self.acceleration
        # print(self.velocity)
        # print(self.acceleration, self.velocity)
        self.pos = self.pos + self.velocity

    def draw(self, surf):
        self.rect.move_ip(self.velocity.x, self.velocity.y)
        surf.blit(self.surf, self.rect, )
        # pygame.draw.circle(surf, self.color, self.pos, self.size, 2)

    def generate(gen):
        size = 50
        x, y = next(gen)
        return Baloon(x, y, size)

    def getNextPos(screenHeight, screenWidth, size):
        offset = 15
        rows = int(screenHeight / (size * 2 + offset))
        cols = int(screenWidth / (size * 2 + offset))
        randXs = Baloon._randomSequence(cols)
        randYs = Baloon._randomSequence(rows)
        fieldHeight = int(screenHeight / rows)
        fieldWidth = int(screenWidth / cols)
        while True:
            if len(randXs) == 0:
                randXs = Baloon._randomSequence(cols)
            if len(randYs) == 0:
                randYs = Baloon._randomSequence(rows)
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


game = BaloonsGame()
while True:
    game.run()
    if game.state == GameStates.QUIT:
        break
