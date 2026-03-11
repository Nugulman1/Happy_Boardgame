"""내부 엔진 v1 검증. 실행: python -m tichu.test_engine_v1"""
from tichu import (
    ApplyExchangeAction,
    Card,
    DeclareGrandTichuAction,
    DeclareSmallTichuAction,
    PHASE_AWAIT_EXCHANGE,
    PHASE_AWAIT_GRAND_TICHU,
    PHASE_AWAIT_TURN_ACTION,
    PHASE_GAME_FINISHED,
    PHASE_IDLE,
    PHASE_ROUND_FINISHED,
    PassTurnAction,
    PlayCardsAction,
    can_submit_action,
    create_engine,
    get_engine_snapshot,
    new_round_state,
    start_game,
    start_round,
    submit_action,
)


def assert_raises_value_error(fn, message):
    try:
        fn()
        raise AssertionError(message)
    except ValueError:
        pass


def make_exchange_choices(round_state):
    return [
        (hand[0], hand[1], hand[2])
        for hand in round_state.hands
    ]


def prepare_turn_phase_engine():
    engine = create_engine()
    start_game(engine)
    round_state = start_round(engine)
    submit_action(engine, DeclareGrandTichuAction({0, 3}))
    submit_action(engine, ApplyExchangeAction(make_exchange_choices(round_state)))
    return engine


def main():
    engine = create_engine()
    snapshot = get_engine_snapshot(engine)
    assert snapshot.phase == PHASE_IDLE
    assert snapshot.team_scores == [0, 0]
    assert not snapshot.has_round

    start_game(engine)
    snapshot = get_engine_snapshot(engine)
    assert snapshot.phase == PHASE_IDLE
    assert snapshot.round_index == 0
    print("create/start_game OK")

    round_state = start_round(engine)
    snapshot = get_engine_snapshot(engine)
    assert snapshot.phase == PHASE_AWAIT_GRAND_TICHU
    assert snapshot.has_round
    assert len(round_state.deck) == 24
    assert [len(hand) for hand in round_state.hands] == [8, 8, 8, 8]
    print("start_round phase OK")

    assert not can_submit_action(engine, ApplyExchangeAction([]))
    assert_raises_value_error(
        lambda: submit_action(engine, ApplyExchangeAction([])),
        "exchange must not be allowed before grand tichu",
    )
    assert_raises_value_error(
        lambda: submit_action(engine, PlayCardsAction(0, [Card("S", 3)])),
        "turn action must not be allowed before turn phase",
    )
    print("wrong phase protection OK")

    submit_action(engine, DeclareGrandTichuAction([1]))
    snapshot = get_engine_snapshot(engine)
    assert snapshot.phase == PHASE_AWAIT_EXCHANGE
    assert engine.round_state is not None
    assert engine.round_state.grand_tichu_declarers == {1}
    assert len(engine.round_state.deck) == 0
    assert [len(hand) for hand in engine.round_state.hands] == [14, 14, 14, 14]
    assert_raises_value_error(
        lambda: submit_action(engine, DeclareGrandTichuAction([0])),
        "grand tichu must not be allowed after grand phase",
    )
    print("grand tichu phase OK")

    choices = make_exchange_choices(engine.round_state)
    submit_action(engine, ApplyExchangeAction(choices))
    snapshot = get_engine_snapshot(engine)
    assert snapshot.phase == PHASE_AWAIT_TURN_ACTION
    assert snapshot.current_player_index == snapshot.leader_index
    assert snapshot.current_trick_cards == []
    print("exchange to first trick OK")

    current_player = engine.round_state.current_player_index
    submit_action(engine, DeclareSmallTichuAction(current_player))
    assert current_player in engine.round_state.small_tichu_declarers
    print("small tichu routing OK")

    engine = create_engine()
    start_game(engine)
    engine.round_state = new_round_state()
    engine.phase = PHASE_AWAIT_TURN_ACTION
    engine.round_state.leader_index = 0
    engine.round_state.current_player_index = 0
    engine.round_state.hands = [
        [Card("S", 9), Card("H", 9)],
        [Card("S", 10)],
        [Card("S", 11)],
        [Card("S", 12)],
    ]
    submit_action(engine, PlayCardsAction(0, [Card("S", 9)]))
    snapshot = get_engine_snapshot(engine)
    assert snapshot.current_player_index == 1
    assert snapshot.current_trick_cards == [Card("S", 9)]
    submit_action(engine, PassTurnAction(1))
    snapshot = get_engine_snapshot(engine)
    assert snapshot.current_player_index == 2
    assert snapshot.players_out_order == []
    assert snapshot.phase == PHASE_AWAIT_TURN_ACTION
    print("play/pass wrapper flow OK")

    engine = create_engine()
    start_game(engine)
    engine.game_state.team_scores = [950, 0]
    engine.round_state = new_round_state()
    engine.phase = PHASE_AWAIT_TURN_ACTION
    engine.round_state.leader_index = 0
    engine.round_state.current_player_index = 0
    engine.round_state.hands = [
        [Card("S", 9)],
        [Card("S", 2), Card("S", 10)],
        [Card("S", 11)],
        [Card("S", 12)],
    ]
    submit_action(engine, PlayCardsAction(0, [Card("S", 9)]))
    submit_action(engine, PlayCardsAction(1, [Card("S", 10)]))
    snapshot = submit_action(engine, PlayCardsAction(2, [Card("S", 11)]))
    assert snapshot.phase == PHASE_GAME_FINISHED
    assert snapshot.is_round_over
    assert snapshot.is_game_over
    assert snapshot.last_score_deltas == [200, 0]
    assert snapshot.team_scores == [1150, 0]
    assert snapshot.round_index == 1
    print("auto finalize/game finish OK")

    engine = prepare_turn_phase_engine()
    snapshot = get_engine_snapshot(engine)
    assert snapshot.phase == PHASE_AWAIT_TURN_ACTION
    assert snapshot.has_round
    assert snapshot.leader_index is not None
    assert snapshot.current_player_index is not None
    print("snapshot content OK")

    engine = create_engine()
    start_game(engine)
    engine.round_state = new_round_state()
    engine.phase = PHASE_AWAIT_TURN_ACTION
    engine.round_state.leader_index = 0
    engine.round_state.current_player_index = 0
    engine.round_state.hands = [
        [Card("S", 9)],
        [Card("S", 2), Card("S", 10)],
        [Card("S", 11)],
        [Card("S", 12)],
    ]
    submit_action(engine, PlayCardsAction(0, [Card("S", 9)]))
    submit_action(engine, PlayCardsAction(1, [Card("S", 10)]))
    snapshot = submit_action(engine, PlayCardsAction(2, [Card("S", 11)]))
    assert snapshot.phase == PHASE_ROUND_FINISHED
    assert not snapshot.is_game_over
    print("round finished phase OK")

    print("내부 엔진 v1 검증 통과.")


if __name__ == "__main__":
    main()
