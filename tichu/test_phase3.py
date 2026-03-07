"""3단계 족보 판정/비교 검증. 실행: python -m tichu.test_phase3"""
from tichu import Card, can_beat, evaluate_combo, new_round_state


def assert_combo(cards, combo_type, strength, card_count):
    result = evaluate_combo(cards)
    assert result is not None
    assert result.combo_type == combo_type
    assert result.strength == strength
    assert result.card_count == card_count


def assert_combo_with_phoenix(cards, combo_type, strength, card_count):
    result = evaluate_combo(cards)
    assert result is not None
    assert result.combo_type == combo_type
    assert result.strength == strength
    assert result.card_count == card_count
    assert result.uses_phoenix is True


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
        [Card("S", 8), Card("H", 9), Card("D", 10), Card("C", 11), Card("S", 12)],
        "straight",
        (12, 5),
        5,
    )
    assert_combo(
        [Card("S", 3), Card("H", 3), Card("S", 4), Card("H", 4)],
        "pair_run",
        (4, 2),
        4,
    )
    assert_combo(
        [
            Card("S", 3),
            Card("H", 3),
            Card("S", 4),
            Card("H", 4),
            Card("S", 5),
            Card("H", 5),
        ],
        "pair_run",
        (5, 3),
        6,
    )
    print("evaluate_combo 성공 케이스 OK")

    assert_combo_with_phoenix([Card("", 21)], "single", (0.5,), 1)
    assert_combo_with_phoenix([Card("S", 9), Card("", 21)], "pair", (9,), 2)
    assert_combo_with_phoenix([Card("S", 11), Card("H", 11), Card("", 21)], "triple", (11,), 3)
    assert_combo_with_phoenix(
        [Card("S", 7), Card("H", 7), Card("D", 7), Card("S", 9), Card("", 21)],
        "full_house",
        (7,),
        5,
    )
    assert_combo_with_phoenix(
        [Card("S", 7), Card("H", 7), Card("D", 9), Card("C", 9), Card("", 21)],
        "full_house",
        (9,),
        5,
    )
    assert_combo_with_phoenix(
        [Card("", 1), Card("S", 2), Card("H", 3), Card("D", 5), Card("", 21)],
        "straight",
        (5, 5),
        5,
    )
    assert_combo_with_phoenix(
        [Card("S", 3), Card("H", 3), Card("S", 4), Card("", 21)],
        "pair_run",
        (4, 2),
        4,
    )
    print("evaluate_combo 봉황 케이스 OK")

    assert_invalid([Card("S", 7), Card("", 20)])
    assert_invalid([Card("", 22), Card("S", 9)])
    assert_invalid([Card("S", 7), Card("H", 7), Card("D", 7), Card("C", 7)])
    assert_invalid(
        [Card("S", 3), Card("S", 4), Card("S", 5), Card("S", 6), Card("S", 7)]
    )
    assert_invalid(
        [Card("S", 3), Card("H", 4), Card("D", 4), Card("C", 5), Card("S", 6)]
    )
    assert_invalid(
        [
            Card("S", 3),
            Card("H", 3),
            Card("S", 4),
            Card("H", 4),
            Card("S", 6),
            Card("H", 6),
        ]
    )
    assert_invalid([Card("", 21), Card("", 22)])
    assert_invalid([Card("S", 7), Card("H", 7), Card("D", 7), Card("C", 7), Card("", 21)])
    print("evaluate_combo 실패 케이스 OK")

    current_pair = evaluate_combo([Card("S", 9), Card("H", 9)])
    stronger_pair = evaluate_combo([Card("D", 10), Card("C", 10)])
    weaker_pair = evaluate_combo([Card("D", 8), Card("C", 8)])
    current_straight = evaluate_combo(
        [Card("S", 5), Card("H", 6), Card("D", 7), Card("C", 8), Card("S", 9)]
    )
    stronger_straight = evaluate_combo(
        [Card("S", 6), Card("H", 7), Card("D", 8), Card("C", 9), Card("S", 10)]
    )
    longer_straight = evaluate_combo(
        [Card("S", 6), Card("H", 7), Card("D", 8), Card("C", 9), Card("S", 10), Card("H", 11)]
    )
    pair_run = evaluate_combo([Card("S", 3), Card("H", 3), Card("S", 4), Card("H", 4)])
    phoenix_single = evaluate_combo([Card("", 21)])
    dragon_single = evaluate_combo([Card("", 22)])

    assert current_pair is not None
    assert stronger_pair is not None
    assert weaker_pair is not None
    assert current_straight is not None
    assert stronger_straight is not None
    assert longer_straight is not None
    assert pair_run is not None
    assert phoenix_single is not None
    assert dragon_single is not None

    assert can_beat(current_pair, stronger_pair)
    assert not can_beat(current_pair, weaker_pair)
    assert not can_beat(current_pair, current_straight)
    assert can_beat(current_straight, stronger_straight)
    assert not can_beat(current_straight, longer_straight)
    assert not can_beat(current_pair, pair_run)
    assert can_beat(current_pair, phoenix_single) is False
    assert can_beat(evaluate_combo([Card("S", 10)]) , phoenix_single)
    assert can_beat(phoenix_single, dragon_single)
    print("can_beat OK")

    round_state = new_round_state()
    assert round_state.current_trick_cards == []
    skipped_compare = round_state.current_trick_cards == []
    assert skipped_compare
    print("현재 트릭 비어 있음 시나리오 OK")

    print("3단계 족보 판정/비교 검증 통과.")


if __name__ == "__main__":
    main()
