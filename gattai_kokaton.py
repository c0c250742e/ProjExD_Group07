"""
スイカゲーム（背景のみ）
=======================================
・ウィンドウ表示と背景描画だけを行うベース部分
・フルーツや物理演算、スコアなどはまだ実装していない
"""
import os
import sys
import math
import random  # ランダム選択のために追加
import time
import pygame as pg
os.chdir(os.path.dirname(os.path.abspath(__file__)))

WIDTH, HEIGHT = 600, 800
FLOOR_Y = HEIGHT - 60
WALL_MARGIN = 40
GAME_OVER_LINE_Y = 120  # このラインを超えて積み上がったらゲームオーバー（予定）
GRAVITY = 0.5
RESTITUTION = 0.3  # 反発係数（0〜1）
FPS = 60
BALL_RADIUS = 12
# 複数のこうかとん画像に対応するためリストに格納
BALL_IMAGE_PATHS = [
    "fig/0.png", "fig/1.png", "fig/2.png", "fig/3.png", "fig/4.png",
    "fig/5.png", "fig/6.png", "fig/7.png", "fig/8.png", "fig/9.png"
]

BALL_IMAGE_PATH0 = pg.image.load("fig/0.png")
BALL_IMAGE_PATH1 = pg.image.load("fig/1.png")
BALL_IMAGE_PATH2 = pg.image.load("fig/2.png")
BALL_IMAGE_PATH3 = pg.image.load("fig/3.png")
BALL_IMAGE_PATH4 = pg.image.load("fig/4.png")
BALL_IMAGE_PATH5 = pg.image.load("fig/5.png")
BALL_IMAGE_PATH6 = pg.image.load("fig/6.png")
BALL_IMAGE_PATH7 = pg.image.load("fig/7.png")
BALL_IMAGE_PATH8 = pg.image.load("fig/8.png")
BALL_IMAGE_PATH9 = pg.image.load("fig/9.png")

BALL_IMAGE = [BALL_IMAGE_PATH0,BALL_IMAGE_PATH1,BALL_IMAGE_PATH2,BALL_IMAGE_PATH3,BALL_IMAGE_PATH4,BALL_IMAGE_PATH5,BALL_IMAGE_PATH6,BALL_IMAGE_PATH7,BALL_IMAGE_PATH8,BALL_IMAGE_PATH9]

class Score:  # 実装Score
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.value = 0
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-750

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)
class Ball:
    """落ちてくる小さい球（画像で表示）"""
    delta = {
        pg.K_a:(-7,0),
        pg.K_d:(+7,0),
    }
    def __init__(self, x: float, y: float, num: int, image: pg.Surface, ball_type: int = 0):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.falling = False  # Enterキーが押されるまでは静止
        self.num = num # 追加：番号を保存
        
        # 追加：番号(0~9)に応じて半径を大きくする（例として1段階ごとに+6ピクセル）
        self.radius = 15 + (num * 15) 
        
        size = self.radius * 2 # 自分のradiusを基準にする
        self.image = pg.transform.smoothscale(image, (size, size))

    
    def update_physics(self):
        if not self.falling:
            return
        self.vy += GRAVITY
        self.x += self.vx
        self.y += self.vy
        # 壁との衝突
        if self.x - self.radius < WALL_MARGIN:
            self.x = (WALL_MARGIN+ self.radius)
            self.vx *= -RESTITUTION
        if self.x + self.radius > WIDTH - WALL_MARGIN:
            self.x = (WIDTH- WALL_MARGIN- self.radius)
            self.vx *= -RESTITUTION

        # 床との衝突（BALL_RADIUS だった場所を self.radius に変更）
        if self.y + self.radius > FLOOR_Y:
            self.y = FLOOR_Y - self.radius
            self.vy *= -RESTITUTION
            if abs(self.vy) < 1.0:
                self.vy = 0.0

    def draw(self, key_lst: list[bool],screen: pg.Surface):
        #初期位置移動
        sum_mv = [0, 0]
        if not self.falling:
            for key in self.delta:
                if key_lst[key]:
                    sum_mv[0] += self.delta[key][0]
                    sum_mv[1] += self.delta[key][1]
                # 壁との衝突（初期位置の移動が壁を越えないように制限）
                if self.x - BALL_RADIUS < WALL_MARGIN:
                    self.x = WALL_MARGIN + BALL_RADIUS
                if self.x + BALL_RADIUS > WIDTH - WALL_MARGIN:
                    self.x = WIDTH - WALL_MARGIN - BALL_RADIUS
        self.x += sum_mv[0]
        self.y += sum_mv[1]
        
        rect = self.image.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(self.image, rect)

def set_ball_image(ball: Ball, num: int):
    """
    合体後の画像番号、半径、画像サイズを変更する
    """

    # 新しい画像番号
    ball.num = num

    # 画像番号が大きくなるほど半径を大きくする
    ball.radius = 15 + (num * 15)

    # 画像サイズは直径
    size = ball.radius * 2

    # 次の画像に変更し、新しい半径に合わせて拡大する
    ball.image = pg.transform.smoothscale(
        BALL_IMAGE[num].convert_alpha(),
        (size, size)
    )

def merge(a: Ball, b: Ball, score: Score, hit_sound: pg.mixer.Sound, sound_type8: pg.mixer.Sound)->bool:
    """こうかとんの画像が同じならばaとbを合体する"""

    dx = b.x - a.x
    dy = b.y - a.y
    dist = math.hypot(dx, dy)
    min_dist = a.radius + b.radius

    # ぶつかっていないなら合体しない
    if dist == 0 or dist >= min_dist:
        return False

    # 同じ画像番号でなければ合体しない
    if a.num != b.num:
        return False

    # 最後の画像なら、それ以上進化しない
    if a.num >= len(BALL_IMAGE) - 1:
        return False

    # === 【修正点】合体が成功したタイミングでスコア加算とSE再生を行う ===
    ball_type = a.num  # a.num（0〜9の数値）を使用
    hit_sound.play()   # 通常の合体音を鳴らす
    
    if ball_type == 0:
        score.value += 1   # 種類0なら1点
    elif ball_type == 1:
        score.value += 5   # 種類1なら5点
    elif ball_type == 2:
        score.value += 10  # 種類2なら10点
    elif ball_type == 3:
        score.value += 20  # 種類3なら20点
    elif ball_type == 4:
        score.value += 30  # 種類4なら30点
    elif ball_type == 5:
        score.value += 40  # 種類5なら40点
    elif ball_type == 6:
        score.value += 50  # 種類6なら50点
    elif ball_type == 7:
        score.value += 60  # 種類7なら60点
    elif ball_type == 8:
        score.value += 100 # 種類8なら100点
        sound_type8.play() # 種類8同士の専用サウンド
    # =================================================================

    set_ball_image(a, a.num + 1)
    return True

def resolve_ball_collision(a: Ball, b: Ball):
    """2つの球が重なっていたら押し戻し、簡易的に弾き合う"""
    dx = b.x - a.x
    dy = b.y - a.y
    dist = math.hypot(dx, dy)
    min_dist = a.radius + b.radius # 2つの球の半径の和

    if dist == 0 or dist >= min_dist:
        return
        
    overlap = min_dist - dist
    nx, ny = dx / dist, dy / dist
    # 重なりを均等に押し戻す
    a.x -= nx * overlap / 2
    a.y -= ny * overlap / 2
    b.x += nx * overlap / 2
    b.y += ny * overlap / 2
    # 簡易的な反発（速度を軽く交換して弾く）
    a.vy -= ny * 1.5
    b.vy += ny * 1.5


class Game:
    """ゲーム全体の進行を管理するクラス"""
    def __init__(self):
        pg.init()
        pg.mixer.init()  # 実装Sound
        pg.mixer.music.load("ゆったりお散歩2.mp3")  
        pg.mixer.music.set_volume(0.5)
        pg.mixer.music.play(-1)
        self.hit_sound = pg.mixer.Sound("決定ボタンを押す52.wav")  # 実装Sound
        self.sound_type8 = pg.mixer.Sound("金額表示.wav")  # 実装Sound
        self.over_start = None #ゲームオーバー判定が始まった時刻を記録
        self.start = True
        self.game_over = False
        pg.display.set_caption("スイカゲーム（背景のみ）")
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        self.clock = pg.time.Clock()
        # ボール画像をロードしてリストに格納(選択される画像の追加に伴い、繰り返しに変更)
        self.ball_images = [
            pg.image.load(path).convert_alpha() for path in BALL_IMAGE_PATHS
        ]
        self.balls: list[Ball] = []
        #  次に作成するボールの種類を管理する変数（最初は種類 0）
        self.next_ball_type = 0
        # 画像(第3引数)と種類ID(第4引数)を連動させる
        rand_num = random.randint(0, 4) # 先に0~4の番号をランダム決定
        self.current_ball = Ball(WIDTH // 2, GAME_OVER_LINE_Y, rand_num, self.ball_images[self.next_ball_type], self.next_ball_type)
        self.score = Score()

    def handle_events(self):
        for event in pg.event.get():
            if self.start:
                if event.type == pg.MOUSEBUTTONDOWN:
                    self.start = False
            if not self.game_over:
                if event.type == pg.KEYDOWN and event.key == pg.K_RETURN:
                    self._drop_ball()

    def _drop_ball(self):
        self.current_ball.falling = True
        self.balls.append(self.current_ball)
        next_x = self.current_ball.x
        rand_num = random.randint(0, 4) # 次のボールも0~4からランダム決定
        self.current_ball = Ball(next_x, GAME_OVER_LINE_Y, rand_num, self.ball_images[rand_num])

    def update(self):
        if self.start or self.game_over:
            return
        for ball in self.balls:
            ball.update_physics()
        if self.balls:
            top = min(ball.y - BALL_RADIUS for ball in self.balls)
            if top <= GAME_OVER_LINE_Y:
                if self.over_start is None:
                    self.over_start = time.time()
                elif time.time() - self.over_start >= 1.5:
                    self.game_over = True
            else:
                self.over_start = None
            if self.game_over==True:
                        self.screen.fill((0, 0, 0))
                        fonto = pg.font.Font(None, 80)
                        txt = fonto.render("Game Over", True, (255, 0, 0))
                        self.screen.blit(txt, [WIDTH//2-150, HEIGHT//2])
                        pg.display.flip() 
                        time.sleep(2)
                        pg.quit()
                        sys.exit()

        i = 0
        while i < len(self.balls):  
            j = i + 1
            while j < len(self.balls):
                # 【変更】引数にスコアと効果音のオブジェクトを追加
                if merge(self.balls[i], self.balls[j], self.score, self.hit_sound, self.sound_type8): 
                    del self.balls[j]
                    continue 
                # 【変更】位置の押し戻しだけを行うシンプルな呼び出しに変更
                resolve_ball_collision(self.balls[i], self.balls[j]) 
                j += 1
            i += 1

    def draw(self):
        self.screen.fill((250, 240, 210))
        if self.start:
            title = pg.font.Font(None, 80)
            text = title.render("Gattai_kokaton", True, (255, 100, 0))
            self.screen.blit(text, (110, 250))
            font = pg.font.Font(None, 40)
            text2 = font.render("Press click to Start", True, (0, 0, 0))
            self.screen.blit(text2, (140, 400))
            pg.display.flip()
            return
        # ゲームオーバーライン
        pg.draw.line(self.screen, (255, 0, 0), (WALL_MARGIN, GAME_OVER_LINE_Y),(WIDTH - WALL_MARGIN, GAME_OVER_LINE_Y), 2)

        # 壁と床
        pg.draw.line(self.screen, (100, 60, 30), (WALL_MARGIN, 0), (WALL_MARGIN, FLOOR_Y), 4)
        pg.draw.line(self.screen, (100, 60, 30), (WIDTH - WALL_MARGIN, 0), (WIDTH - WALL_MARGIN, FLOOR_Y), 4)
        pg.draw.line(self.screen, (100, 60, 30), (WALL_MARGIN, FLOOR_Y), (WIDTH - WALL_MARGIN, FLOOR_Y), 4)
        for ball in self.balls:
            ball.draw(pg.key.get_pressed(), self.screen)
        self.current_ball.draw(pg.key.get_pressed(),self.screen)
        self.score.update(self.screen)
        pg.display.flip()

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
            
if __name__ == "__main__":
    Game().run()