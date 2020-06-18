from manimlib.imports import *


def boolian_linear_combo(bools):
    return reduce(op.xor, [b * n for n, b in enumerate(bools)], 0)


def string_to_bools(message):
    # For easter eggs on the board
    bits = bin(int.from_bytes(message.encode(), 'big'))[2:]
    bits = (len(message) * 8 - len(bits)) * '0' + bits
    return [bool(int(b)) for b in bits]


def layer_mobject(mobject, nudge=1e-6):
    for i, sm in enumerate(mobject.family_members_with_points()):
        sm.shift(i * nudge * OUT)


class Chessboard(SGroup):
    CONFIG = {
        "shape": (8, 8),
        "height": 7,
        "depth": 0.25,
        "colors": [LIGHT_GREY, DARKER_GREY],
        "gloss": 0.2,
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        nr, nc = self.shape
        cube = Cube(square_resolution=(3, 3))
        # Replace top square with something slightly higher res
        top_square = Square3D(resolution=(5, 5))
        top_square.replace(cube[0])
        cube.replace_submobject(0, top_square)
        self.add(*[cube.copy() for x in range(nc * nr)])
        self.arrange_in_grid(buff=0)
        self.set_height(self.height)
        self.set_depth(self.depth, stretch=True)
        for i, j in it.product(range(nr), range(nc)):
            color = self.colors[(i + j) % 2]
            self[i * nc + j].set_color(color)
        self.center()
        self.set_gloss(self.gloss)


class Coin(Group):
    CONFIG = {
        "disk_resolution": (4, 51),
        "height": 1,
        "depth": 0.1,
        "color": GOLD_D,
        "tails_color": RED,
        "include_labels": True,
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        res = self.disk_resolution
        self.top = Disk3D(resolution=res, gloss=0.2)
        self.bottom = self.top.copy()
        self.top.shift(OUT)
        self.bottom.shift(IN)
        self.edge = Cylinder(height=2, resolution=(res[1], 2))
        self.add(self.top, self.bottom, self.edge)
        self.rotate(90 * DEGREES, OUT)
        self.set_color(self.color)
        self.bottom.set_color(RED)

        if self.include_labels:
            labels = VGroup(
                TextMobject("H"),
                TextMobject("T"),
            )
            for label, vect in zip(labels, [OUT, IN]):
                label.shift(1.02 * vect)
                label.set_height(0.8)
            labels[1].flip(RIGHT)
            labels.apply_depth_test()
        else:
            labels = Group(Mobject(), Mobject())
        self.add(*labels)
        self.labels = labels

        self.set_height(self.height)
        self.set_depth(self.depth, stretch=True)

    def is_heads(self):
        return self.top.get_center()[2] > self.bottom.get_center()[2]

    def flip(self, axis=RIGHT):
        super().flip(axis)


class CoinsOnBoard(Group):
    CONFIG = {
        "proportion_of_square_height": 0.7,
        "coin_config": {},
    }

    def __init__(self, chessboard, **kwargs):
        super().__init__(**kwargs)
        prop = self.proportion_of_square_height
        for cube in chessboard:
            coin = Coin(**self.coin_config)
            coin.set_height(prop * cube.get_height())
            coin.next_to(cube, OUT, buff=0)
            self.add(coin)

    def flip_at_random(self, p=0.5):
        for coin in self:
            if random.random() < p:
                coin.flip()
        return self

    def flip_by_message(self, message):
        heads = string_to_bools(message)
        for coin, head in zip(self, heads):
            if not head:
                coin.flip()
        return self


class Key(SVGMobject):
    CONFIG = {
        "file_name": "key",
        "fill_color": GOLD,
        "fill_opacity": 1,
        "stroke_color": GOLD,
        "stroke_width": 0,
        "gloss": 0.5,
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rotate(PI / 2, OUT)


class FlipCoin(Animation):
    CONFIG = {
        "axis": RIGHT,
        "run_time": 1,
        "shift_dir": OUT,
    }

    def __init__(self, coin, **kwargs):
        super().__init__(coin, **kwargs)
        self.shift_vect = coin.get_height() * self.shift_dir / 2

    def interpolate_mobject(self, alpha):
        coin = self.mobject
        for sm, start_sm in self.families:
            sm.points[:] = start_sm.points
        coin.rotate(alpha * PI, axis=self.axis)
        coin.shift(4 * alpha * (1 - alpha) * self.shift_vect)
        return coin


# Scenes
class IntroducePuzzle(Scene):
    CONFIG = {
        "camera_class": ThreeDCamera,
    }

    def construct(self):
        # Setup
        frame = self.camera.frame

        chessboard = Chessboard()
        chessboard.move_to(ORIGIN, OUT)

        grid = NumberPlane(
            x_range=(0, 8), y_range=(0, 8),
            faded_line_ratio=0
        )
        grid.match_height(chessboard)
        grid.next_to(chessboard, OUT, 1e-8)
        low_grid = grid.copy()
        low_grid.next_to(chessboard, IN, 1e-8)
        grid.add(low_grid)
        grid.set_stroke(GREY, width=2)
        grid.set_gloss(0.5)
        grid.prepare_for_nonlinear_transform(0)

        coins = CoinsOnBoard(chessboard)
        coins.set_gloss(0.2)
        coins_to_flip = Group()
        head_bools = string_to_bools('3b1b  :)')
        for coin, heads in zip(coins, head_bools):
            if not heads:
                coins_to_flip.add(coin)
        coins_to_flip.shuffle()

        count_label = VGroup(
            Integer(0, edge_to_fix=RIGHT),
            TextMobject("Coins")
        )
        count_label.arrange(RIGHT, aligned_edge=DOWN)
        count_label.to_corner(UL)
        count_label.fix_in_frame()

        # Draw board and coins
        frame.set_rotation(-25 * DEGREES, 70 * DEGREES, 0)
        self.play(
            FadeIn(chessboard),
            ShowCreationThenDestruction(grid, lag_ratio=0.01),
            frame.set_theta, 0,
            frame.set_phi, 45 * DEGREES,
            run_time=3,
        )
        self.wait()

        self.add(count_label)
        self.play(
            ShowIncreasingSubsets(coins),
            UpdateFromFunc(count_label[0], lambda m, c=coins: m.set_value(len(c))),
            rate_func=bezier([0, 0, 1, 1]),
            run_time=2,
        )
        self.wait()
        self.play(LaggedStartMap(FlipCoin, coins_to_flip, run_time=6, lag_ratio=0.1))
        self.add(coins)
        coins.unlock_shader_data()
        self.wait()

        # Show key
        key = Key()
        key.rotate(PI / 4, RIGHT)
        key.move_to(3 * OUT)
        key.scale(0.8)
        key.to_edge(LEFT, buff=1)

        k = boolian_linear_combo(head_bools) ^ 63  # To make the flip below the actual solution
        key_cube = Cube(resolution=(6, 6))
        key_cube.match_color(chessboard[k])
        key_cube.replace(chessboard[k], stretch=True)
        chessboard.replace_submobject(k, key_cube)
        key_square = key_cube[0]
        chessboard.generate_target()
        chessboard.save_state()
        for i, cube in enumerate(chessboard.target):
            if i == k:
                cube[0].set_color(MAROON_E)
            else:
                cube.set_color(interpolate_color(cube.get_color(), BLACK, 0.8))

        key.generate_target()
        key.target.rotate(PI / 4, LEFT)
        key.target.set_width(0.7 * key_square.get_width())
        key.target.next_to(key_square, IN, buff=SMALL_BUFF)

        self.play(FadeIn(key, LEFT))
        self.wait()
        self.play(
            FadeOut(coins, lag_ratio=0.01),
            MoveToTarget(chessboard),
        )
        ks_top = key_square.get_top()
        self.play(
            Rotate(key_square, PI / 2, axis=LEFT, about_point=ks_top),
            MoveToTarget(key),
            frame.set_phi, 60 * DEGREES,
            run_time=2,
        )
        self.play(
            Rotate(key_square, PI / 2, axis=RIGHT, about_point=ks_top),
            run_time=2,
        )
        chessboard.unlock_shader_data()
        chessboard.saved_state[k][0].match_color(key_square)
        self.play(
            chessboard.restore,
            FadeIn(coins),
            frame.set_phi, 20 * DEGREES,
            frame.move_to, 2 * LEFT,
            run_time=3
        )

        # State goal
        goal = TextMobject(
            "Communicate where\\\\the key is",
            " by turning\\\\over one coin.",
            alignment=""
        )
        goal.next_to(count_label, DOWN, LARGE_BUFF, LEFT)
        goal.fix_in_frame()
        goal[1].set_color(YELLOW)

        self.play(FadeIn(goal[0]))
        self.wait()
        self.play(FadeIn(goal[1]))
        self.wait()

        coin = coins[63]
        rect = SurroundingRectangle(coin, color=TEAL)

        self.play(FadeInFromLarge(rect))
        self.play(FlipCoin(coin), FadeOut(rect))


class FromCoinToSquareMaps(Scene):
    CONFIG = {
        "camera_class": ThreeDCamera,
        "messages": [
            "Please, ",
            "go watch",
            "Stand-up",
            "Maths on",
            "YouTube."
        ],
        "flip_lag_ratio": 0.05,
    }

    def construct(self):
        messages = self.messages

        board1 = Chessboard()
        board1.set_width(5.5)
        board1.to_corner(DL)

        board2 = board1.copy()
        board2.to_corner(DR)

        coins = CoinsOnBoard(board1)
        bools = string_to_bools(messages[0])
        for coin, head in zip(coins, bools):
            if not head:
                coin.flip(RIGHT)

        for cube in board2:
            cube.original_color = cube.get_color()

        arrow = Arrow(board1.get_right(), board2.get_left())
        arrow.tip.set_stroke(width=0)

        title1 = TextMobject("Pattern of coins")
        title2 = TextMobject("Individual square")

        for title, board in [(title1, board1), (title2, board2)]:
            title.scale(0.5 / title[0][0].get_height())
            title.next_to(board, UP, MED_LARGE_BUFF)

        title2.align_to(title1, UP)

        def get_special_square(coins=coins, board=board2):
            bools = [coin.is_heads() for coin in coins]
            return board[boolian_linear_combo(bools)]

        self.add(board1)
        self.add(title1)
        self.add(coins)

        self.play(
            GrowArrow(arrow),
            FadeIn(board2, 2 * LEFT)
        )
        square = get_special_square()
        rect = SurroundingRectangle(square, buff=0)
        rect.set_color(PINK)
        rect.next_to(square, OUT, buff=0.01)
        self.play(
            square.set_color, MAROON_C,
            ShowCreation(rect),
            FadeIn(title2)
        )

        for message in messages[1:]:
            new_bools = string_to_bools(message)
            coins_to_flip = Group()
            for coin, to_heads in zip(coins, new_bools):
                if coin.is_heads() ^ to_heads:
                    coins_to_flip.add(coin)
            coins_to_flip.shuffle()
            self.play(LaggedStartMap(
                FlipCoin, coins_to_flip,
                lag_ratio=self.flip_lag_ratio,
                run_time=1,
            ))

            new_square = get_special_square()
            self.play(
                square.set_color, square.original_color,
                new_square.set_color, MAROON_C,
                rect.move_to, new_square, OUT,
                rect.shift, 0.01 * OUT,
            )
            square = new_square
            self.wait()


class FromCoinToSquareMapsSingleFlips(FromCoinToSquareMaps):
    CONFIG = {
        "messages": [
            "FlipBits",
            "BlipBits",
            "ClipBits",
            "ChipBits",
            "ChipBats",
            "ChipRats",
        ]
    }


class DiagramOfProgression(ThreeDScene):
    def construct(self):
        # Setup panels
        P1_COLOR = BLUE_C
        P2_COLOR = RED

        rect = Rectangle(4, 2)
        rect.set_fill(GREY_E, 1)
        panels = Group()
        for x in range(4):
            panels.add(Group(rect.copy()))
        panels.arrange_in_grid(buff=1)
        panels[::2].shift(0.5 * LEFT)
        panels.set_width(FRAME_WIDTH - 2)
        panels.center().to_edge(DOWN)

        chessboard = Chessboard()
        chessboard.set_height(0.9 * panels[0].get_height())
        coins = CoinsOnBoard(
            chessboard,
            coin_config={
                "disk_resolution": (2, 25),
                "include_labels": False,
            }
        )
        coins.flip_by_message("Tau > Pi")

        for panel in panels[1:]:
            cb = chessboard.copy()
            co = coins.copy()
            cb.next_to(panel.get_right(), LEFT)
            co.next_to(cb, OUT, 0)
            panel.chessboard = cb
            panel.coins = co
            panel.add(cb, co)

        kw = {
            "tex_to_color_map": {
                "Prisoner 1": P1_COLOR,
                "Prisoner 2": P2_COLOR,
            }
        }
        titles = VGroup(
            TextMobject("Prisoners conspire", **kw),
            TextMobject("Prisoner 1 sees key", **kw),
            TextMobject("Prisoner 1 flips coin", **kw),
            TextMobject("Prisoner 2 guesses key square", **kw),
        )

        for panel, title in zip(panels, titles):
            title.next_to(panel, UP)
            panel.title = title
            panel.add(title)

        # Darken first chessboard
        for coin in panels[1].coins:
            coin.remove(coin.edge)
            if coin.is_heads():
                coin.remove(coin.bottom)
                coin.remove(coin.labels[1])
            else:
                coin.remove(coin.top)
                coin.remove(coin.labels[0])
            coin.set_opacity(0.25)

        # Add characters
        prisoner1 = PiCreature(color=P1_COLOR)
        prisoner2 = PiCreature(color=P2_COLOR)
        pis = VGroup(prisoner1, prisoner2)
        pis.arrange(RIGHT, buff=1)
        pis.set_height(1.5)

        p0_pis = pis.copy()
        p0_pis.set_height(2.0, about_edge=DOWN)
        p0_pis[1].flip()
        p0_pis.next_to(panels[0].get_bottom(), UP, SMALL_BUFF)
        p0_pis[0].change("pondering", p0_pis[1].eyes)
        p0_pis[1].change("speaking", p0_pis[0].eyes)
        panels[0].add(p0_pis)

        p1_pi = pis[0].copy()
        p1_pi.next_to(panels[1].get_corner(DL), UR, SMALL_BUFF)
        p1_pi.change("happy")
        key = Key()
        key.set_height(0.5)
        key.next_to(p1_pi, UP)
        key.set_color(YELLOW)
        key_cube = panels[1].chessboard[18]
        key_square = Square()
        key_square.replace(key_cube)
        key_square.set_stroke(width=3)
        key_square.match_color(key)
        p1_pi.look_at(key_square)
        key_arrow = Arrow(
            key.get_right() + SMALL_BUFF * UP,
            key_square.get_corner(UL),
            path_arc=-45 * DEGREES,
            buff=SMALL_BUFF
        )
        key_arrow.tip.set_stroke(width=0)
        key_arrow.match_color(key)
        panels[1].add(p1_pi, key)

        p2_pi = pis[0].copy()
        p2_pi.next_to(panels[2].get_corner(DL), UR, SMALL_BUFF)
        p2_pi.change("tease")
        flip_coin = panels[2].coins[38]
        panels[3].coins[38].flip()
        flip_square = Square()
        flip_square.replace(panels[2].chessboard[38])
        flip_square.set_stroke(BLUE, 5)
        for coin in panels[2].coins:
            if coin is not flip_coin:
                coin.remove(coin.edge)
                if coin.is_heads():
                    coin.remove(coin.bottom)
                    coin.remove(coin.labels[1])
                else:
                    coin.remove(coin.top)
                    coin.remove(coin.labels[0])
                coin.set_opacity(0.25)
        panels[2].add(p2_pi)

        p3_pi = pis[1].copy()
        p3_pi.next_to(panels[3].get_corner(DL), UR, SMALL_BUFF)
        p3_pi.shift(MED_LARGE_BUFF * RIGHT)
        p3_pi.change("confused")
        panels[3].add(p3_pi)

        # Animate each panel in
        self.play(FadeIn(panels[1], DOWN))
        self.play(
            ShowCreation(key_arrow),
            FadeInFromLarge(key_square),
        )
        self.wait()

        self.play(FadeIn(panels[2], UP))
        self.play(
            ShowCreation(flip_square),
            FlipCoin(flip_coin),
            p2_pi.look_at, flip_coin,
        )
        self.wait()

        self.play(FadeIn(panels[3], LEFT))
        self.wait()

        self.play(FadeIn(panels[0]))
        self.wait()