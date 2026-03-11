"""6단계 전 종료/점수 검증. 실행: python -m tichu.test_phase6_round_scoring"""
from tichu import (
    Card,
    GameState,
    apply_round_scores,
    calculate_round_score_deltas,
    can_declare_small_tichu,
    declare_small_tichu,
    finalize_round,
    get_round_end_reason,
    is_double_victory,
    is_game_over,
    is_round_over,
    new_round_state,
    pass_turn,
    play_cards,
    resolve_trick_end,
)


def assert_raises_value_error(fn, message):
    try:
        fn()
        raise AssertionError(message)
    except ValueError:
        pass


def main():
    round_state = new_round_state()
    round_state.hands[0] = [Card("S", 9)]
    assert can_declare_small_tichu(round_state, 0)
    declare_small_tichu(round_state, 0)
    assert 0 in round_state.small_tichu_declarers
    round_state.current_player_index = 0
    play_cards(round_state, 0, [Card("S", 9)])
    assert 0 in round_state.played_first_card_players
    assert not can_declare_small_tichu(round_state, 0)
    assert_raises_value_error(
        lambda: declare_small_tichu(round_state, 0),
        "cannot declare small tichu after first play",
    )
    print("small tichu declaration OK")

    round_state = new_round_state()
    round_state.hands[1] = [Card("S", 10)]
    round_state.grand_tichu_declarers = {1}
    assert not can_declare_small_tichu(round_state, 1)
    assert_raises_value_error(
        lambda: declare_small_tichu(round_state, 1),
        "cannot declare small tichu after declaring grand tichu",
    )
    print("grand tichu blocks small tichu OK")

    round_state = new_round_state()
    round_state.small_tichu_declarers = {0}
    round_state.grand_tichu_declarers = {1}
    round_state.players_out_order = [0, 2]
    assert is_double_victory(round_state)
    assert is_round_over(round_state)
    assert get_round_end_reason(round_state) == "double_victory"
    assert calculate_round_score_deltas(round_state) == [300, -200]
    print("double victory scoring OK")

    round_state = new_round_state()
    round_state.players_out_order = [0, 1, 2]
    round_state.hands[3] = [Card("", 21), Card("S", 5)]
    round_state.won_trick_cards = [
        [Card("S", 5)],
        [Card("S", 10)],
        [Card("", 22)],
        [Card("S", 13)],
    ]
    assert is_round_over(round_state)
    assert get_round_end_reason(round_state) == "three_players_out"
    assert calculate_round_score_deltas(round_state) == [20, 10]
    print("normal round scoring OK")

    round_state = new_round_state()
    round_state.current_trick_cards = [Card("", 22)]
    round_state.current_trick_pile = [Card("", 22), Card("S", 10)]
    round_state.last_played_by = 0
    round_state.hands[0] = [Card("S", 9)]
    round_state.hands[1] = [Card("S", 8)]
    round_state.hands[2] = [Card("S", 7)]
    round_state.hands[3] = [Card("S", 6)]
    assert_raises_value_error(
        lambda: resolve_trick_end(round_state),
        "dragon trick must require recipient",
    )
    assert_raises_value_error(
        lambda: resolve_trick_end(round_state, 2),
        "dragon recipient must be opponent",
    )
    resolve_trick_end(round_state, 1)
    assert round_state.won_trick_cards[1] == [Card("", 22), Card("S", 10)]
    assert round_state.leader_index == 0
    assert round_state.current_player_index == 0
    print("dragon recipient handling OK")

    round_state = new_round_state()
    round_state.current_player_index = 0
    round_state.hands = [
        [Card("", 22)],
        [Card("S", 3)],
        [Card("S", 4)],
        [Card("S", 5)],
    ]
    play_cards(round_state, 0, [Card("", 22)])
    pass_turn(round_state, 1)
    pass_turn(round_state, 2, dragon_recipient=1)
    assert round_state.won_trick_cards[1] == [Card("", 22)]
    print("dragon pass_turn flow OK")

    state = GameState()
    round_state = new_round_state()
    round_state.players_out_order = [0, 2]
    deltas = apply_round_scores(state, round_state)
    assert deltas == [200, 0]
    assert state.team_scores == [200, 0]

    state = GameState()
    state.team_scores = [950, 0]
    round_state = new_round_state()
    round_state.players_out_order = [0, 2]
    deltas = finalize_round(state, round_state)
    assert deltas == [200, 0]
    assert state.team_scores == [1150, 0]
    assert state.round_index == 1
    assert is_game_over(state)
    print("apply/finalize round OK")

    print("종료/점수 검증 통과.")


if __name__ == "__main__":
    main()
