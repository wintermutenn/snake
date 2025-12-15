"""Модуль игры 'Змейка' на Pygame."""
import json
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from random import choice, random, shuffle

import pygame as pg
import pygame_menu

# Размеры различных окон.
SCREEN_SIZE = (860, 500)
SCREEN_NAME_INPUT = (400, 200)
SCREEN_SHOW_SCORES = (600, 400)
SCREEN_MANUAL = (800, 600)
SCREEN_GAME_MENU = (250, 550)

GRID_SIZE = 20
AREA_SIZE = (660, 500)

BOARD_BACKGROUND_COLOR = '#d9e0c1'
SNAKE_COLOR = '#ffeb00'

# Константы для смены направления движения змейки.
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

# Угол поворота головы в зависимости от направления.
ANGLE = {
    UP: 180,
    DOWN: 0,
    LEFT: 270,
    RIGHT: 90
}

#
TURN_MAP = {
    (pg.K_UP, LEFT): UP,
    (pg.K_UP, RIGHT): UP,
    (pg.K_DOWN, RIGHT): DOWN,
    (pg.K_DOWN, LEFT): DOWN,
    (pg.K_LEFT, UP): LEFT,
    (pg.K_LEFT, DOWN): LEFT,
    (pg.K_RIGHT, UP): RIGHT,
    (pg.K_RIGHT, DOWN): RIGHT
}

WALL_POSITIONS = set()

# Позиции вертикальной стены.
for y in range(0, AREA_SIZE[1], GRID_SIZE):
    WALL_POSITIONS.add(((AREA_SIZE[0] // 2) - GRID_SIZE // 2, y))

# Позиции горизонтальной стены.
for x in range(0, AREA_SIZE[0], GRID_SIZE):
    WALL_POSITIONS.add((x, (AREA_SIZE[1] // 2) - GRID_SIZE // 2))

# Все доступные для игры ячейки.
GRID_POSITIONS = {(x, y) for x in range(0, AREA_SIZE[0], GRID_SIZE)
                  for y in range(0, AREA_SIZE[1], GRID_SIZE)}

# Исключает стены из списка доступных ячеек.
DRAW_POSITIONS = GRID_POSITIONS - WALL_POSITIONS

START_POSITION = [choice(tuple(DRAW_POSITIONS))]

# Константы фруктов.
FRUIT_APPLE = 'apple'
FRUIT_CHERRY = 'cherry'
FRUIT_PLUM = 'pulm'
FRUIT_ORANGE = 'orange'

# Инициализация Pygame
pg.init()

# Основное игровое окно.
screen = pg.display.set_mode(SCREEN_SIZE)

clock = pg.time.Clock()
pg.display.set_caption('Изгиб питона')

# Загрузка изображений(pg.transform.scale - изменяет размер изображения).
images = {
    'fon': pg.image.load('assets/images/fon.png'),
    'frame': pg.image.load('assets/images/frame.png'),
    'logo': pg.transform.scale(pg.image.load('assets/images/logo.png'),
                               (300, 225)),
    'logo_menu': pg.image.load('assets/images/logo.png'),
    'manual': pg.transform.scale(pg.image.load('assets/images/manual.png'),
                                 (800, 600)),
    'snake_head': pg.transform.scale(
        pg.image.load('assets/images/snake_head.png'),
        (GRID_SIZE, GRID_SIZE)
    ),
    'snake_body': pg.transform.scale(
        pg.image.load('assets/images/snake_body.png'),
        (GRID_SIZE, GRID_SIZE)
    ),
    'apple': pg.transform.scale(pg.image.load('assets/images/apple.png'),
                                (GRID_SIZE, GRID_SIZE)),
    'cherry': pg.transform.scale(pg.image.load('assets/images/cherry.png'),
                                 (GRID_SIZE, GRID_SIZE)),
    'pulm': pg.transform.scale(pg.image.load('assets/images/pulm.png'),
                               (GRID_SIZE, GRID_SIZE)),
    'orange': pg.transform.scale(pg.image.load('assets/images/orange.png'),
                                 (GRID_SIZE, GRID_SIZE)),
}

# Загрузка звуков.
sounds = {
    'background_music': pg.mixer.Sound("assets/sounds/background_music.mp3"),
    'ate': pg.mixer.Sound("assets/sounds/ate.wav"),
    'open_menu': pg.mixer.Sound("assets/sounds/open_menu.ogg"),
    'click_mouse': pg.mixer.Sound("assets/sounds/click_mouse.ogg"),
}


class GameObject(ABC):
    """Базовый класс для игровых объектов."""

    @abstractmethod
    def draw(self) -> None:
        """Отрисовка объекта на поверхности"""

    def draw_images(self, image: pg.Surface,
                    position: tuple[int, int]) -> None:
        """Отрисовка изображения объекта на заданной позиции."""
        screen.blit(image, position)


class Snake(GameObject):
    """
    Класс змейки.

    Attributes:
        direction (Tuple[int, int]): Текущее направление движения.
        positions (List[Tuple[int, int]]): Список позиций сегментов тела.
        length (int): Длина змейки.
        speed (float): Скорость змейки.
    """

    def __init__(self):
        super().__init__()
        self.direction = None
        self.reset()

    def reset(self) -> None:
        """
        Сброс состояния змейки в начальное положение.

        Args:
            direction: Направление движения змейки.
        """
        # Первое направление RIGHT. После reset случайное.
        self.direction = choice((RIGHT, LEFT, UP, DOWN))
        # Случайная позиция змейки.
        self.positions = [choice(tuple(DRAW_POSITIONS))]
        self.length = 1
        self.speed = 0.1

    def update_direction(self, new_dir: tuple[int, int]) -> None:
        """
        Обновление направления движения змейки.

        Args:
            new_dir: Новое направление движения (UP, DOWN, LEFT, RIGHT).
        """
        self.direction = new_dir

    def move(self) -> None:
        """Перемещение змейки в текущем направлении."""
        x_local, y_local = self.get_head_position()
        dx, dy = self.direction

        # Обновляет позиции с учётом границ игрового поля.
        self.positions.insert(0, (
            (x_local + dx * GRID_SIZE) % AREA_SIZE[0],
            (y_local + dy * GRID_SIZE) % AREA_SIZE[1])
        )
        if len(self.positions) > self.length:
            self.positions.pop()

    def draw(self) -> None:
        """Отрисовка змейки на экране."""
        # Рисует и поворачивает голову в зависимости от направления.
        rotated_head = pg.transform.rotate(images['snake_head'],
                                           ANGLE[self.direction])
        self.draw_images(rotated_head, self.get_head_position())

        # Рисует тело.
        for pos in self.positions[1:]:
            self.draw_images(images['snake_body'], pos)

    def get_head_position(self):
        """Возвращает позицию головы змейки."""
        return self.positions[0]


class Fruit(GameObject):
    """Базовый класс для фруктов"""

    def __init__(self, occupied: set[tuple[int, int]], image_name: str):
        """
        Инициализация фрукта.

        Args:
            occupied: Множество занятых позиций.
            image_name: Ключ изображения в словаре images.
        """
        super().__init__()
        self.image = images[image_name]
        self.randomize_position(occupied)

    def randomize_position(self, occupied: set[tuple[int, int]]) -> None:
        """
        Генерация случайной позиции для фрукта.

        Args:
            occupied: Множество занятых позиций.
        """
        self.position = choice(tuple(GRID_POSITIONS - set(occupied)))

    def draw(self) -> None:
        """Отрисовка фрукта, если он активен."""
        self.draw_images(self.image, self.position)


class Apple(Fruit):
    """Класс яблоко"""

    def __init__(self, snake_positions: list[tuple[int, int]]):
        super().__init__(set(snake_positions) | WALL_POSITIONS, FRUIT_APPLE)


class Bonus(Fruit):
    """
    Бонусный фрукт с временным эффектом.

    Attributes:
        spawn_time (datetime): Время появления бонуса.
        font (pg.font.Font): Шрифт для отображения таймера.
        fruit_name (str): Название фрукта (для определения эффекта).
        active_bonus (Optional[Bonus]): Активный бонусный фрукт.
    """

    spawn_time = datetime.now()
    font = pg.font.Font(None, 24)

    def __init__(self, fruit_name: str):
        super().__init__(set(), fruit_name)
        self.fruit_name = fruit_name
        self.active_bonus = None

    def activate(self, occupied: set[tuple[int, int]]) -> None:
        """
        Активация бонуса на игровом поле.

        Args:
            occupied: Множество занятых позиций.
        """
        self.randomize_position(occupied)
        Bonus.spawn_time = datetime.now()

    def draw(self) -> None:
        """Отрисовка бонуса с таймером обратного отсчёта."""
        # Отрисовывает базовое изображение фрукта.
        super().draw()

        # Рассчитывает оставшееся время.
        elapsed = (datetime.now() - Bonus.spawn_time).seconds
        remaining = max(0, 10 - elapsed)

        # Создаёт и позиционируем текст с таймером.
        text = Bonus.font.render(str(remaining), 1, (100, 0, 0))
        text_rect = text.get_rect(
            center=(
                self.position[0] + GRID_SIZE // 2,
                self.position[1] + GRID_SIZE // 2
            )
        )
        screen.blit(text, text_rect)


class GameState:
    """
    Класс для управления игровым состоянием.

    Attributes:
        screen (pg.Surface): Игровое окно.
        font (pg.font.Font): Шрифт для интерфейса.
        snake (Snake): Объект змейки.
        apple (Apple): Объект яблока.
        bonuses (List[Bonus]): Список бонусных фруктов.
        score (int): Текущий счет игрока.
        paused (bool): Флаг паузы игры.
        player_name (str): Имя текущего игрока.
        best_score (int): Лучший счет.
    """

    def __init__(self, player_name: str):
        """
        Инициализация игрового состояния.

        Args:
            player_name: Имя текущего игрока.
        """
        self.screen = pg.display.set_mode(SCREEN_SIZE)
        self.font = pg.font.SysFont('comicsans', 27)
        self.snake = Snake()
        self.apple = Apple(self.snake.positions)

        # Создаёт бонусные фрукты.
        self.bonuses = [
            Bonus(FRUIT_ORANGE),  # Уменьшение длины.
            Bonus(FRUIT_PLUM),  # Уменьшение скорости.
            Bonus(FRUIT_CHERRY),  # Бонус очков.
        ]

        self.score = 0
        self.paused = False
        self.player_name = player_name
        self.best_score = load_best_score()

    def bonus_spawn(self):
        """Проверка условий и активация бонусных фруктов."""
        # Спавн бонуса не чаще 15 секунд.
        if datetime.now() - Bonus.spawn_time < timedelta(seconds=15):
            return
        # Перемешивает список для последующей вставки в цикл.
        # Множество здесь не подходит потому что оно сохраняет
        # порядок вставки.
        shuffle(self.bonuses)
        # Проверяет условия для активации
        for bonus in self.bonuses:
            # Условия для активации разных типов бонусов.
            conditions = {
                FRUIT_ORANGE: self.snake.length > 5 and random() <= 0.01,
                # 1% шанс только если длина змейки > 5.
                FRUIT_PLUM: self.snake.speed > 1 and random() <= 0.01,
                # 1% шанс если скорости скорость змейки > 1.
                FRUIT_CHERRY: random() < 0.05  # 5% шанс всегда.
            }

            # Активирует подходящий бонус если он еще не активен.
            if conditions[bonus.fruit_name] and not bonus.active_bonus:
                # Занятые позиции.
                occupied = set(self.snake.positions) | WALL_POSITIONS
                bonus.activate(occupied)
                bonus.active_bonus = bonus
                break

    def handle_collision(self) -> None:
        """Обработка столкновений змейки."""
        # Проверка столкновения с яблоком.
        if self.snake.get_head_position() == self.apple.position:
            self.snake.length += 1
            self.score += 10
            self.snake.speed += 0.05
            self.apple.randomize_position(
                set(self.snake.positions) | WALL_POSITIONS)
            sounds['ate'].play()

        # Проверка столкновения с телом.
        if self.snake.get_head_position() in self.snake.positions[1:]:
            save_score(self.player_name, self.score)
            self.score = 0
            self.snake.reset()

        # Проверка столкновения со стенами.
        if self.snake.get_head_position() in WALL_POSITIONS:
            save_score(self.player_name, self.score)
            self.score = 0
            self.snake.reset()

        # Проверка столкновения с бонусами.
        for bonus in self.bonuses:
            if (bonus.active_bonus and bonus.position
               == self.snake.get_head_position()):
                # Обработка разных типов бонусов.
                if bonus.fruit_name == FRUIT_ORANGE:
                    # Уменьшает длину змейки (не менее 5 сегментов).
                    self.snake.length = max(5, self.snake.length - 1)
                    self.snake.positions \
                        = self.snake.positions[:self.snake.length]
                    self.score += 30

                elif bonus.fruit_name == FRUIT_PLUM:
                    # Уменьшает скорость на 0.5 (не менее 1).
                    self.snake.speed = max(1, self.snake.speed - 0.5)
                    self.score += 30

                elif bonus.fruit_name == FRUIT_CHERRY:
                    # Бонус очков в зависимости от времени активации.
                    time_active = (datetime.now() - bonus.spawn_time).seconds
                    points = 150 - 10 * time_active
                    self.score += points
                    self.snake.length += 1
                    self.snake.speed += 0.05

                # Деактивирует бонус и проигрывает звук.
                bonus.active_bonus = None
                sounds['ate'].play()

    def draw_all(self) -> None:
        """Отрисовка всех игровых объектов и статистики."""
        # Отрисовка изображений и фона.
        screen.fill(BOARD_BACKGROUND_COLOR)
        screen.blit(images['fon'], (0, 0))
        screen.blit(images['frame'], (660, 0))
        screen.blit(images['logo'], (610, 0))

        # Отрисовка бонусов
        for bonus in self.bonuses:
            if (bonus.active_bonus and datetime.now()
                    < Bonus.spawn_time + timedelta(seconds=10)):
                bonus.draw()

        # Отображение игровой статистики.
        interface_data = [
            f'Счёт: {self.score}',
            f'Рекорд: {self.best_score}',
            f'Скорость: {round(self.snake.speed, 1)}',
            f'Длина: {self.snake.length}',
            f'Игрок: {self.player_name}',
        ]
        # enumerate - формирует пару счётчик и элемент.
        for i, text in enumerate(interface_data):
            surf = self.font.render(text, 1, (0, 0, 0))
            screen.blit(surf, (675, 200 + i * 40))

        # Отрисовка яблока и змейки.
        self.apple.draw()
        self.snake.draw()

        pg.display.update()


def save_score(name: str, score: int) -> None:
    """
    Сохраняет результат игрока в файл рекордов.

    Args:
        name: Имя игрока.
        score: Достигнутый счет.
    """
    try:
        with open('scores.json', 'r', encoding='utf-8') as f:
            scores = json.load(f)
    except FileNotFoundError:
        scores = []

    scores.append({
        'name': name,
        'score': score,
        'date': datetime.now().strftime('%Y-%m-%d')
    })

    with open('scores.json', 'w', encoding='utf-8') as f:
        # Сохраняет только 5 лучших результатов.
        json.dump(sorted(scores,
                         key=lambda x: x['score'], reverse=True)[:5], f)


def load_scores() -> list[dict]:
    """
    Загружает таблицу рекордов из файла.

    Returns:
        Список словарей с результатами игроков.
    """
    try:
        with open('scores.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def load_best_score() -> int:
    """
    Загрузка лучшего счёта из таблицы рекордов.

    Returns:
        Лучший счёт или 0, если таблица пуста.
    """
    scores = load_scores()
    return max(scores, key=lambda x: x['score'])['score'] if scores else 0


def handle_keys(snake: Snake, game_state: GameState) -> bool:
    """
    Обрабатывает пользовательский ввод.

    Returns:
        Обновленное состояние паузы.
    """
    for event in pg.event.get():
        if event.type == pg.QUIT:
            pg.quit()
            raise SystemExit
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_p:
                return not game_state.paused  # Переключает паузу.
            elif event.key == pg.K_ESCAPE:
                pg.quit()
                raise SystemExit
            elif (not game_state.paused
                  and (event.key, snake.direction) in TURN_MAP):
                snake.update_direction(TURN_MAP.get(
                    (event.key, snake.direction))
                )
    return game_state.paused


def create_menu_theme(coord: tuple[int, int]) -> pygame_menu.themes.Theme:
    """
    Создаёт тему для меню.

    Args:
        coord: Координаты для позиционирования заголовка.

    Returns:
        Объект темы меню.
    """
    theme = pygame_menu.themes.Theme(title_offset=coord)
    theme.widget_font = pygame_menu.font.FONT_OPEN_SANS_BOLD
    theme.title_font = pygame_menu.font.FONT_OPEN_SANS_BOLD
    theme.title_bar_style = pygame_menu.widgets.MENUBAR_STYLE_UNDERLINE
    theme.background_color = (215, 215, 215, 0)
    theme.widget_font_color = (0, 0, 0)
    theme.title_font_color = (0, 0, 0)
    theme.title_font_size = 30
    return theme


def update(menu_surface: pg.Surface,
           menu: pygame_menu.Menu,
           image: pg.Surface = None,
           coord: tuple[int, int] | None = None) -> None:
    """
    Обновляет и отображает меню.

    Args:
        menu_surface: Поверхность для отрисовки.
        menu: Объект меню.
        image: Изображения.
        coord: Координаты для отрисовки фонового изображения.
    """
    while True:
        screen.fill(BOARD_BACKGROUND_COLOR)
        if image:
            screen.blit(image, coord)
        # Обработка звука при выборе виджета.
        events = pg.event.get()
        for event in events:
            if event.type == pg.KEYDOWN:
                if event.key in (pg.K_UP, pg.K_DOWN, pg.K_RETURN):
                    sounds['click_mouse'].play().set_volume(0.6)

        menu.update(events)
        menu.draw(menu_surface)
        pg.display.update()


def name_input() -> None:
    """Окно ввода имени игрока."""
    name_input_screen = pg.display.set_mode(SCREEN_NAME_INPUT)
    menu = pygame_menu.Menu('Введите имя', 400, 200,
                            theme=create_menu_theme((100, 0)))
    name_widget = menu.add.text_input('Имя: ', default='Player 1')
    # Лямбда обеспечивает отложеный запуск main.
    menu.add.button('Играть', lambda: [sounds['open_menu'].play(),
                                       main(name_widget.get_value())])
    menu.add.button('Назад', lambda: [sounds['open_menu'].play(),
                                      game_menu()])
    update(name_input_screen, menu)


def show_scores() -> None:
    """Отображает таблицу рекордов."""
    show_scores_screen = pg.display.set_mode(SCREEN_SHOW_SCORES)
    menu = pygame_menu.Menu('Рекорды', 600, 400,
                            theme=create_menu_theme((230, 0)))

    scores = load_scores()
    if not scores:
        menu.add.label('Пока нет рекордов!')
    else:
        for score in scores:
            menu.add.label(
                f"{score['name']}: {score['score']} ({score['date']})")

    menu.add.button('Назад', lambda: [sounds['open_menu'].play(),
                                      game_menu()])

    update(show_scores_screen, menu)


def manual() -> None:
    """Отображает инструкцию к игре."""
    manual_screen = pg.display.set_mode(SCREEN_MANUAL)
    menu = pygame_menu.Menu('Инструкция', 660, 600,
                            theme=create_menu_theme((230, 0)))
    btn = menu.add.button('Назад', lambda: [sounds['open_menu'].play(),
                                            game_menu()])
    btn.set_position(500, 500)

    update(manual_screen, menu, images['manual'], coord=(0, 0))


def game_menu() -> None:
    """Главное меню игры."""
    game_menu_screen = pg.display.set_mode(SCREEN_GAME_MENU)
    menu = pygame_menu.Menu('Меню', 200, 300, position=(25, 240, False),
                            theme=create_menu_theme((55, 0)))
    menu.add.button('Играть', lambda: [sounds['open_menu'].play(),
                                       name_input()])
    menu.add.button('Рекорды', lambda: [sounds['open_menu'].play(),
                                        show_scores()])
    menu.add.button('Правила', lambda: [sounds['open_menu'].play(),
                                        manual()])
    menu.add.button('Выход', pygame_menu.events.EXIT)

    update(game_menu_screen, menu, images['logo_menu'], (-70, -20))


def show_pause_menu(game_state) -> bool:
    """Обрабатывает паузу."""
    # Полупрозрачный оверлей.
    overlay = pg.Surface(SCREEN_SIZE, pg.SRCALPHA)
    overlay.fill((0, 0, 0, 128))  # Чёрный с 50% прозрачностью.

    # Создает текст.
    font = pg.font.Font(None, 30)
    text = font.render("Нажмите любую клавишу что бы продолжить", True,
                       (255, 255, 255))
    text_rect = text.get_rect(
        center=(AREA_SIZE[0] // 2, AREA_SIZE[1] // 2))

    # Отрисовывает текущее состояние игры.
    game_state.draw_all()

    # Добавляет оверлей и текст.
    game_state.screen.blit(overlay, (0, 0))
    game_state.screen.blit(text, text_rect)
    pg.display.update()

    # Ожидаем нажатия любой клавиши.
    # Пришлось реализовать отдельно из основной
    # функции управления это не работало.
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                raise SystemExit
            # Возвращаемся в игру при любом нажатии.
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    pg.quit()
                    raise SystemExit
                return False


def main(player_name: str = 'Player 1') -> None:
    """
    Основной игровой цикл.

    Args:
        player_name: Имя текущего игрока.
    """
    state = GameState(player_name)
    sounds['background_music'].play(-1).set_volume(0.4)

    while True:
        state.paused = handle_keys(state.snake, state)

        # Обработка паузы.
        if state.paused:
            show_pause_menu(state)
            state.paused = False
            continue

        # Активирует бонус.
        state.bonus_spawn()
        # Обновляет позицию змейки.
        state.snake.move()
        # Проверяет на столкновение с объектами.
        state.handle_collision()

        # Обновление скорости отображения.
        clock.tick(5 + state.snake.speed)

        # Отрисовка игровых объектов.
        state.draw_all()


if __name__ == '__main__':
    game_menu()
