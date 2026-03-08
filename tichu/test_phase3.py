"""3단계 족보 판정/비교 검증. 실행: python -m tichu.test_phase3"""
from tichu import Card, can_beat, evaluate_combo


def assert_combo(
    cards,
    combo_type,
    strength,
    card_count,
    uses_phoenix=False,
    resolved_ranks=None,
):
    result = evaluate_combo(cards)
    assert result is not None
    assert result.combo_type == combo_type
    assert result.strength == strength
    assert result.card_count == card_count
    assert result.uses_phoenix is uses_phoenix
    assert result.resolved_ranks == resolved_ranks


def assert_invalid(cards):
    assert evaluate_combo(cards) is None


def main():
    assert_combo([Card("S", 7)], "single", (7,), 1)
    assert_combo([Card("", 1)], "single", (1,), 1)
    assert_combo([Card("", 22)], "single", (22,), 1)
    assert_combo([Card("S", 9), Card("H", 9)], "pair", (9,), 2)
    assert_combo([Card("S", 11), Card("H", 11), Card("D", 11)], "triple", (11,), 3)
    assert_combo(
        [Card("S", 7), Card("H", 7), Card("D", 7), Card("S", 9), Card("H", 9)],
        "full_house",
        (7,),
        5,
    )
    assert_combo(
        [Card("", 1), Card("S", 2), Card("H", 3), Card("D", 4), Card("C", 5)],
        "straight",
        (5, 5),
        5,
    )
    assert_combo(
        [Card("S", 3), Card("H", 3), Card("S", 4), Card("H", 4)],
        "pair_run",
        (4, 2),
        4,
    )
    assert_combo(
        [Card("S", 7), Card("H", 7), Card("D", 7), Card("C", 7)],
        "bomb_four",
        (7,),
        4,
    )
    assert_combo(
        [Card("S", 3), Card("S", 4), Card("S", 5), Card("S", 6), Card("S", 7)],
        "bomb_straight_flush",
        (5, 7),
        5,
    )
    assert_combo(
        [Card("S", 3), Card("S", 4), Card("S", 5), Card("S", 6), Card("S", 7), Card("S", 8)],
        "bomb_straight_flush",
        (6, 8),
        6,
    )
    print("evaluate_combo 일반 케이스 OK")

    assert_combo(
        [Card("", 21)],
        "single",
        (0.5,),
        1,
        uses_phoenix=True,
        resolved_ranks=None,
    )
    assert_combo(
        [Card("S", 9), Card("", 21)],
        "pair",
        (9,),
        2,
        uses_phoenix=True,
        resolved_ranks=(9, 9),
    )
    assert_combo(
        [Card("S", 11), Card("H", 11), Card("", 21)],
        "triple",
        (11,),
        3,
        uses_phoenix=True,
        resolved_ranks=(11, 11, 11),
    )
    assert_combo(
        [Card("S", 7), Card("H", 7), Card("D", 7), Card("S", 9), Card("", 21)],
        "full_house",
        (7,),
        5,
        uses_phoenix=True,
        resolved_ranks=(7, 7, 7, 9, 9),
    )
    assert_combo(
        [Card("S", 7), Card("H", 7), Card("D", 9), Card("C", 9), Card("", 21)],
        "full_house",
        (9,),
        5,
        uses_phoenix=True,
        resolved_ranks=(7, 7, 9, 9, 9),
    )
    assert_combo(
        [Card("S", 2), Card("H", 3), Card("D", 5), Card("C", 6), Card("", 21)],
        "straight",
        (6, 5),
        5,
        uses_phoenix=True,
        resolved_ranks=(2, 3, 4, 5, 6),
    )
    assert_combo(
        [Card("S", 6), Card("H", 7), Card("D", 8), Card("C", 10), Card("S", 11), Card("", 21)],
        "straight",
        (11, 6),
        6,
        uses_phoenix=True,
        resolved_ranks=(6, 7, 8, 9, 10, 11),
    )
    assert_combo(
        [Card("S", 4), Card("H", 5), Card("D", 6), Card("C", 7), Card("S", 8), Card("", 21)],
        "straight",
        (9, 6),
        6,
        uses_phoenix=True,
        resolved_ranks=(4, 5, 6, 7, 8, 9),
    )
    assert_combo(
        [Card("S", 10), Card("H", 11), Card("D", 12), Card("C", 13), Card("S", 14), Card("", 21)],
        "straight",
        (14, 6),
        6,
        uses_phoenix=True,
        resolved_ranks=(9, 10, 11, 12, 13, 14),
    )
    assert_combo(
        [Card("S", 3), Card("H", 3), Card("S", 4), Card("", 21)],
        "pair_run",
        (4, 2),
        4,
        uses_phoenix=True,
        resolved_ranks=(3, 3, 4, 4),
    )
    assert_combo(
        [Card("S", 3), Card("H", 3), Card("S", 4), Card("H", 4), Card("S", 5), Card("", 21)],
        "pair_run",
        (5, 3),
        6,
        uses_phoenix=True,
        resolved_ranks=(3, 3, 4, 4, 5, 5),
    )
    assert_combo(
        [Card("S", 3), Card("S", 4), Card("H", 4), Card("S", 5), Card("H", 5), Card("", 21)],
        "pair_run",
        (5, 3),
        6,
        uses_phoenix=True,
        resolved_ranks=(3, 3, 4, 4, 5, 5),
    )
    print("evaluate_combo 봉황 케이스 OK")

    assert_invalid([Card("S", 7), Card("", 20)])
    assert_invalid([Card("", 1), Card("", 21)])
    assert_invalid([Card("", 22), Card("", 21)])
    assert_invalid([Card("S", 7), Card("H", 7), Card("D", 7), Card("C", 7), Card("", 21)])
    assert_invalid([Card("S", 7), Card("H", 8), Card("D", 9), Card("C", 9), Card("", 21)])
    assert_invalid([Card("S", 2), Card("H", 3), Card("D", 5), Card("C", 7), Card("", 21)])
    assert_invalid([Card("S", 2), Card("H", 2), Card("D", 4), Card("C", 5), Card("", 21)])
    assert_invalid([Card("", 1), Card("S", 2), Card("H", 3), Card("D", 4), Card("", 21)])
    assert_invalid([Card("S", 3), Card("H", 3), Card("S", 4), Card("H", 4), Card("S", 6), Card("", 21)])
    assert_invalid([Card("S", 5), Card("H", 5), Card("S", 6), Card("H", 6), Card("S", 8), Card("", 21)])
    assert_invalid([Card("", 1), Card("S", 3), Card("H", 3), Card("S", 4), Card("", 21)])
    assert_invalid([Card("", 22), Card("S", 3), Card("H", 3), Card("S", 4), Card("", 21)])
    assert_invalid([Card("", 20), Card("S", 3), Card("H", 3), Card("S", 4), Card("", 21)])
    assert_combo(
        [Card("", 1), Card("S", 2), Card("S", 3), Card("S", 4), Card("S", 5)],
        "straight",
        (5, 5),
        5,
    )
    assert_invalid([Card("", 22), Card("S", 3), Card("S", 4), Card("S", 5), Card("S", 6)])
    assert_invalid([Card("", 20), Card("S", 3), Card("S", 4), Card("S", 5), Card("S", 6)])
    assert_invalid([Card("S", 3), Card("S", 4), Card("S", 5), Card("S", 7), Card("S", 8)])
    print("evaluate_combo 봉황 실패 케이스 OK")

    current_pair = evaluate_combo([Card("S", 9), Card("H", 9)])
    stronger_phoenix_pair = evaluate_combo([Card("D", 10), Card("", 21)])
    current_triple = evaluate_combo([Card("S", 10), Card("H", 10), Card("D", 10)])
    stronger_phoenix_triple = evaluate_combo([Card("S", 11), Card("H", 11), Card("", 21)])
    current_full_house = evaluate_combo(
        [Card("S", 7), Card("H", 7), Card("D", 7), Card("S", 9), Card("H", 9)]
    )
    stronger_phoenix_full_house = evaluate_combo(
        [Card("S", 8), Card("H", 8), Card("D", 10), Card("C", 10), Card("", 21)]
    )
    current_straight = evaluate_combo(
        [Card("S", 5), Card("H", 6), Card("D", 7), Card("C", 8), Card("S", 9)]
    )
    stronger_phoenix_straight = evaluate_combo(
        [Card("S", 6), Card("H", 7), Card("D", 9), Card("C", 10), Card("", 21)]
    )
    higher_edge_extended_straight = evaluate_combo(
        [Card("S", 4), Card("H", 5), Card("D", 6), Card("C", 7), Card("S", 8), Card("", 21)]
    )
    current_pair_run = evaluate_combo(
        [Card("S", 4), Card("H", 4), Card("S", 5), Card("H", 5)]
    )
    stronger_phoenix_pair_run = evaluate_combo(
        [Card("S", 5), Card("H", 5), Card("S", 6), Card("", 21)]
    )
    current_bomb_four = evaluate_combo(
        [Card("S", 7), Card("H", 7), Card("D", 7), Card("C", 7)]
    )
    stronger_bomb_four = evaluate_combo(
        [Card("S", 8), Card("H", 8), Card("D", 8), Card("C", 8)]
    )
    current_bomb_straight_flush = evaluate_combo(
        [Card("S", 3), Card("S", 4), Card("S", 5), Card("S", 6), Card("S", 7)]
    )
    stronger_bomb_straight_flush = evaluate_combo(
        [Card("S", 3), Card("S", 4), Card("S", 5), Card("S", 6), Card("S", 7), Card("S", 8)]
    )
    phoenix_single = evaluate_combo([Card("", 21)])
    dragon_single = evaluate_combo([Card("", 22)])
    ten_single = evaluate_combo([Card("S", 10)])

    assert current_pair is not None
    assert stronger_phoenix_pair is not None
    assert current_triple is not None
    assert stronger_phoenix_triple is not None
    assert current_full_house is not None
    assert stronger_phoenix_full_house is not None
    assert current_straight is not None
    assert stronger_phoenix_straight is not None
    assert higher_edge_extended_straight is not None
    assert current_pair_run is not None
    assert stronger_phoenix_pair_run is not None
    assert current_bomb_four is not None
    assert stronger_bomb_four is not None
    assert current_bomb_straight_flush is not None
    assert stronger_bomb_straight_flush is not None
    assert phoenix_single is not None
    assert dragon_single is not None
    assert ten_single is not None

    assert can_beat(current_pair, stronger_phoenix_pair)
    assert can_beat(current_triple, stronger_phoenix_triple)
    assert can_beat(current_full_house, stronger_phoenix_full_house)
    assert can_beat(current_straight, stronger_phoenix_straight)
    assert higher_edge_extended_straight.strength == (9, 6)
    assert can_beat(current_pair_run, stronger_phoenix_pair_run)
    assert can_beat(current_triple, current_bomb_four)
    assert can_beat(current_straight, current_bomb_straight_flush)
    assert can_beat(current_bomb_four, stronger_bomb_four)
    assert can_beat(current_bomb_four, current_bomb_straight_flush)
    assert can_beat(current_bomb_straight_flush, stronger_bomb_straight_flush)
    assert can_beat(ten_single, phoenix_single)
    assert phoenix_single.strength == (0.5,)
    assert not can_beat(dragon_single, phoenix_single)
    print("can_beat 봉황 비교 OK")

    print("3단계 족보 판정/비교 검증 통과.")


if __name__ == "__main__":
    main()
