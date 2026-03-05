"""1·2단계 검증. 실행: python -m tichu.test_phase1 (프로젝트 루트에서)"""
from tichu import (
    Card,
    make_deck,
    shuffle_deck,
    card_points,
    GameState,
    init_state,
    team_id,
    RoundState,
    new_round_state,
    run_prepare_phase,
)


def main():
    d = make_deck(shuffle=True)
    assert len(d) == 56
    norm = [c for c in d if 2 <= c.rank <= 14 and c.suit]
    spec = [c for c in d if c.rank in (1, 20, 21, 22)]
    assert len(norm) == 52 and len(spec) == 4
    print("make_deck: 56장, 52+4 OK")

    assert card_points(Card("", 21)) == -25
    assert card_points(Card("", 22)) == 25
    assert card_points(Card("S", 5)) == 5
    assert card_points(Card("H", 13)) == 10
    print("card_points OK")

    s = GameState()
    init_state(s)
    assert s.team_scores == [0, 0] and s.round_index == 0
    assert not hasattr(s, "hands")
    print("GameState, init_state (외부만) OK")

    r = new_round_state()
    assert len(r.hands) == 4 and r.leader_index == 0 and r.trick_index == 0
    assert r.grand_tichu_declarers == set()
    print("RoundState, new_round_state OK")

    print("team_id(0)=1, team_id(1)=2:", team_id(0), team_id(1))
    assert team_id(0) == 1 and team_id(1) == 2

    # 2단계: 준비 단계
    r2 = new_round_state()
    run_prepare_phase(r2)
    assert all(len(h) == 14 for h in r2.hands)
    assert len(r2.deck) == 0
    assert 0 <= r2.leader_index <= 3
    assert any(c.rank == 1 for c in r2.hands[r2.leader_index])
    print("run_prepare_phase OK (14장 each, 선=참새 보유자)")

    print("1·2단계 검증 통과.")


if __name__ == "__main__":
    main()
