"""4단계 참새 콜 검증. 실행: python -m tichu.test_phase4"""
from tichu import (
    Card,
    can_declare_mahjong_call,
    set_mahjong_call,
    clear_mahjong_call,
    new_round_state,
    hand_can_possibly_match_mahjong_call,
    find_legal_plays_matching_call,
    selection_satisfies_mahjong_call,
    must_follow_mahjong_call,
    can_pass_with_mahjong_call,
)


def normalize(plays):
    return sorted(
        sorted((card.suit, card.rank) for card in play)
        for play in plays
    )


def main():
    mahjong_single = [Card("", 1)]
    mahjong_straight = [Card("", 1), Card("S", 2), Card("H", 3), Card("D", 4), Card("C", 5)]
    invalid_with_mahjong = [Card("", 1), Card("S", 9)]

    assert can_declare_mahjong_call(mahjong_single, 9)
    assert can_declare_mahjong_call(mahjong_straight, 7)
    assert can_declare_mahjong_call(mahjong_single, None)
    assert not can_declare_mahjong_call(mahjong_single, 1)
    assert not can_declare_mahjong_call(mahjong_single, 20)
    assert not can_declare_mahjong_call([Card("S", 9)], 9)
    assert not can_declare_mahjong_call(invalid_with_mahjong, 9)
    print("can_declare_mahjong_call OK")

    round_state = new_round_state()
    set_mahjong_call(round_state, mahjong_single, 8)
    assert round_state.mahjong_call_rank == 8
    set_mahjong_call(round_state, mahjong_single, None)
    assert round_state.mahjong_call_rank is None
    clear_mahjong_call(round_state)
    assert round_state.mahjong_call_rank is None
    try:
        set_mahjong_call(round_state, [Card("S", 9)], 8)
        raise AssertionError("invalid mahjong call must raise")
    except ValueError:
        pass
    print("set/clear_mahjong_call OK")

    no_call_cards = [Card("S", 5), Card("H", 7), Card("D", 11)]
    phoenix_only = [Card("", 21), Card("S", 5)]
    exact_call_cards = [Card("S", 9), Card("H", 11)]

    assert not hand_can_possibly_match_mahjong_call(no_call_cards, 9)
    assert hand_can_possibly_match_mahjong_call(phoenix_only, 9)
    assert hand_can_possibly_match_mahjong_call(exact_call_cards, 9)
    assert not hand_can_possibly_match_mahjong_call(exact_call_cards, None)
    print("hand_can_possibly_match_mahjong_call OK")

    assert normalize(find_legal_plays_matching_call(no_call_cards, [], 9)) == []
    assert not selection_satisfies_mahjong_call([Card("", 21)], 9)
    assert not selection_satisfies_mahjong_call([Card("S", 8), Card("", 21)], 7)
    assert selection_satisfies_mahjong_call([Card("S", 7), Card("", 21)], 7)
    assert selection_satisfies_mahjong_call(
        [Card("S", 8), Card("H", 10), Card("D", 11), Card("C", 12), Card("", 21)],
        9,
    )
    print("selection_satisfies_mahjong_call OK")

    hand_with_match = [Card("S", 9), Card("H", 10)]
    assert must_follow_mahjong_call(hand_with_match, [], 9)
    assert not can_pass_with_mahjong_call(hand_with_match, [], 9)
    assert not selection_satisfies_mahjong_call([Card("H", 10)], 9)

    hand_with_current_trick_match = [Card("S", 9), Card("", 21)]
    current_pair = [Card("D", 8), Card("C", 8)]
    matching_pair_plays = find_legal_plays_matching_call(hand_with_current_trick_match, current_pair, 9)
    assert normalize(matching_pair_plays) == [[("", 21), ("S", 9)]]
    assert must_follow_mahjong_call(hand_with_current_trick_match, current_pair, 9)
    assert not can_pass_with_mahjong_call(hand_with_current_trick_match, current_pair, 9)

    phoenix_straight_hand = [Card("S", 8), Card("H", 10), Card("D", 11), Card("C", 12), Card("", 21)]
    matching_straights = find_legal_plays_matching_call(phoenix_straight_hand, [], 9)
    assert normalize(matching_straights) == [[("", 21), ("C", 12), ("D", 11), ("H", 10), ("S", 8)]]
    assert must_follow_mahjong_call(phoenix_straight_hand, [], 9)
    assert not can_pass_with_mahjong_call(phoenix_straight_hand, [], 9)

    phoenix_but_not_matching = [Card("S", 8), Card("", 21)]
    assert hand_can_possibly_match_mahjong_call(phoenix_but_not_matching, 7)
    assert normalize(find_legal_plays_matching_call(phoenix_but_not_matching, [], 7)) == []
    assert not must_follow_mahjong_call(phoenix_but_not_matching, [], 7)
    assert can_pass_with_mahjong_call(phoenix_but_not_matching, [], 7)

    has_call_rank_but_not_legal = [Card("S", 9), Card("H", 7)]
    current_single = [Card("D", 10)]
    assert hand_can_possibly_match_mahjong_call(has_call_rank_but_not_legal, 9)
    assert normalize(find_legal_plays_matching_call(has_call_rank_but_not_legal, current_single, 9)) == []
    assert not must_follow_mahjong_call(has_call_rank_but_not_legal, current_single, 9)
    assert can_pass_with_mahjong_call(has_call_rank_but_not_legal, current_single, 9)
    print("must_follow/can_pass_with_mahjong_call OK")

    print("4단계 참새 콜 검증 통과.")


if __name__ == "__main__":
    main()
