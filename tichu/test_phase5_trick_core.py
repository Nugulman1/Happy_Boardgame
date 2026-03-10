"""5단계 전 트릭 코어 검증. 실행: python -m tichu.test_phase5_trick_core"""
from tichu import (
    Card,
    can_player_pass,
    get_legal_plays,
    new_round_state,
    pass_turn,
    play_cards,
    resolve_trick_end,
    start_trick,
)


def assert_raises_value_error(fn, message):
    try:
        fn()
        raise AssertionError(message)
    except ValueError:
        pass


def main():
    round_state = new_round_state()
    round_state.leader_index = 2
    start_trick(round_state)
    assert round_state.current_player_index == 2
    assert not can_player_pass(round_state, 2)
    print("start_trick/can_player_pass OK")

    round_state = new_round_state()
    round_state.current_player_index = 0
    round_state.hands = [
        [Card("S", 3), Card("H", 3)],
        [Card("S", 4)],
        [Card("S", 5)],
        [Card("S", 6)],
    ]
    play_cards(round_state, 0, [Card("H", 3), Card("S", 3)])
    assert round_state.current_trick_cards == [Card("H", 3), Card("S", 3)]
    assert round_state.current_trick_pile == [Card("H", 3), Card("S", 3)]
    assert round_state.last_played_by == 0
    assert round_state.current_player_index == 1
    assert round_state.hands[0] == []
    assert round_state.players_out_order == [0]
    print("play_cards 기본 흐름 OK")

    round_state = new_round_state()
    round_state.current_player_index = 0
    round_state.hands = [
        [Card("S", 3), Card("H", 4)],
        [Card("S", 2), Card("H", 2)],
        [Card("S", 10)],
        [Card("S", 11)],
    ]
    assert_raises_value_error(
        lambda: play_cards(round_state, 1, [Card("S", 2)]),
        "wrong player turn must fail",
    )
    assert_raises_value_error(
        lambda: play_cards(round_state, 0, [Card("S", 3), Card("S", 9)]),
        "cards not in hand must fail",
    )
    play_cards(round_state, 0, [Card("S", 3)])
    assert_raises_value_error(
        lambda: play_cards(round_state, 1, [Card("S", 2), Card("H", 2)]),
        "invalid combo must fail",
    )
    assert_raises_value_error(
        lambda: play_cards(round_state, 1, [Card("S", 2)]),
        "weaker combo must fail",
    )
    print("play_cards 예외 흐름 OK")

    round_state = new_round_state()
    round_state.current_player_index = 0
    round_state.leader_index = 0
    round_state.hands = [
        [Card("", 20), Card("S", 7)],
        [Card("S", 9)],
        [Card("S", 10)],
        [Card("S", 11)],
    ]
    play_cards(round_state, 0, [Card("", 20)])
    assert round_state.hands[0] == [Card("S", 7)]
    assert round_state.current_trick_cards == []
    assert round_state.current_trick_pile == []
    assert round_state.leader_index == 2
    assert round_state.current_player_index == 2
    assert 0 in round_state.played_first_card_players

    round_state = new_round_state()
    round_state.current_player_index = 0
    round_state.hands = [
        [Card("", 20)],
        [Card("S", 9)],
        [Card("S", 10)],
        [Card("S", 11)],
    ]
    round_state.current_trick_cards = [Card("S", 8)]
    assert_raises_value_error(
        lambda: play_cards(round_state, 0, [Card("", 20)]),
        "dog cannot be played on an active trick",
    )

    round_state = new_round_state()
    round_state.current_player_index = 0
    round_state.hands = [
        [Card("", 20)],
        [Card("S", 9)],
        [Card("S", 10)],
        [Card("S", 11)],
    ]
    round_state.played_first_card_players.add(0)
    assert_raises_value_error(
        lambda: play_cards(round_state, 0, [Card("", 20)]),
        "dog cannot be played after first turn",
    )
    print("dog flow OK")

    round_state = new_round_state()
    round_state.current_player_index = 0
    round_state.hands = [
        [Card("", 1)],
        [Card("S", 9), Card("H", 10)],
        [Card("S", 8)],
        [Card("S", 7)],
    ]
    play_cards(round_state, 0, [Card("", 1)], 9)
    assert get_legal_plays(round_state, 1) == [[Card("S", 9)]]
    assert round_state.mahjong_call_rank == 9
    assert_raises_value_error(
        lambda: pass_turn(round_state, 1),
        "call follower must not pass",
    )
    play_cards(round_state, 1, [Card("S", 9)])
    assert round_state.current_player_index == 2
    print("mahjong call 연동 OK")

    round_state = new_round_state()
    round_state.leader_index = 0
    round_state.current_player_index = 0
    round_state.hands = [
        [Card("S", 9), Card("H", 9)],
        [Card("S", 10)],
        [Card("S", 11)],
        [Card("S", 12)],
    ]
    play_cards(round_state, 0, [Card("S", 9)])
    pass_turn(round_state, 1)
    pass_turn(round_state, 2)
    pass_turn(round_state, 3)
    assert round_state.trick_index == 1
    assert round_state.won_trick_cards[0] == [Card("S", 9)]
    assert round_state.leader_index == 0
    assert round_state.current_player_index == 0
    assert round_state.current_trick_cards == []
    assert round_state.current_trick_pile == []
    print("3패스 트릭 종료 OK")

    round_state = new_round_state()
    round_state.current_player_index = 2
    round_state.hands = [
        [Card("S", 9)],
        [],
        [Card("S", 11)],
        [Card("S", 12)],
    ]
    round_state.current_trick_cards = [Card("S", 8)]
    round_state.current_trick_pile = [Card("S", 8)]
    round_state.last_played_by = 0
    round_state.pass_count_since_last_play = 0
    pass_turn(round_state, 2)
    pass_turn(round_state, 3)
    assert round_state.trick_index == 1
    assert round_state.won_trick_cards[0] == [Card("S", 8)]
    assert round_state.leader_index == 0
    assert round_state.current_player_index == 0
    print("활성 인원 기준 패스 종료 OK")

    round_state = new_round_state()
    assert_raises_value_error(
        lambda: resolve_trick_end(round_state),
        "cannot resolve without last play",
    )
    print("resolve_trick_end 예외 OK")

    print("트릭 코어 검증 통과.")


if __name__ == "__main__":
    main()
