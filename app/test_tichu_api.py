from fastapi.testclient import TestClient

from app.main import app
from app.tichu_api import _sessions, reset_sessions
from tichu import Card, new_round_state


client = TestClient(app)


def _create_game() -> str:
    response = client.post("/games/tichu")
    assert response.status_code == 201
    payload = response.json()
    assert payload["phase"] == "prepare_grand_tichu"
    assert len(payload["state"]["viewer_hand"]) == 8
    return payload["game_id"]


def _get_state(game_id: str, viewer: int) -> dict:
    response = client.get(f"/games/{game_id}", params={"viewer": viewer})
    assert response.status_code == 200
    return response.json()


def _prepare_to_trick_phase(game_id: str) -> dict:
    for player_index in range(4):
        response = client.post(
            f"/games/{game_id}/prepare/grand-tichu",
            json={"player_index": player_index, "declare": False},
        )
        assert response.status_code == 200

    for player_index in range(4):
        hand = _get_state(game_id, player_index)["state"]["viewer_hand"]
        response = client.post(
            f"/games/{game_id}/prepare/exchange",
            json={
                "player_index": player_index,
                "to_left": hand[0],
                "to_team": hand[1],
                "to_right": hand[2],
            },
        )
        assert response.status_code == 200

    return _get_state(game_id, 0)


def _set_pass_flow_state(game_id: str) -> None:
    session = _sessions[game_id]
    session.phase = "trick"
    session.round_state = new_round_state()
    session.round_state.leader_index = 0
    session.round_state.current_player_index = 1
    session.round_state.hands = [
        [Card("S", 9)],
        [Card("S", 10)],
        [Card("S", 11)],
        [Card("S", 12)],
    ]
    session.round_state.current_trick_cards = [Card("S", 9)]
    session.round_state.current_trick_pile = [Card("S", 9)]
    session.round_state.last_played_by = 0
    session.round_state.played_first_card_players = {0}


def _set_round_finish_state(game_id: str) -> None:
    session = _sessions[game_id]
    session.phase = "trick"
    session.round_state = new_round_state()
    session.round_state.leader_index = 0
    session.round_state.current_player_index = 0
    session.round_state.hands = [
        [Card("S", 9)],
        [Card("S", 2), Card("S", 10)],
        [Card("S", 11)],
        [Card("S", 12)],
    ]


def _set_dragon_recipient_state(game_id: str) -> None:
    session = _sessions[game_id]
    session.phase = "trick"
    session.round_state = new_round_state()
    session.round_state.leader_index = 0
    session.round_state.current_player_index = 1
    session.round_state.hands = [
        [],
        [Card("S", 3)],
        [Card("S", 4)],
        [Card("S", 5)],
    ]
    session.round_state.current_trick_cards = [Card("", 22)]
    session.round_state.current_trick_pile = [Card("", 22)]
    session.round_state.last_played_by = 0
    session.round_state.played_first_card_players = {0}
    session.round_state.players_out_order = [0]


def test_create_and_viewer_snapshot() -> None:
    reset_sessions()
    game_id = _create_game()

    viewer_zero = _get_state(game_id, 0)
    viewer_one = _get_state(game_id, 1)

    assert viewer_zero["state"]["table"]["leader_index"] is None
    assert viewer_zero["state"]["table"]["current_player_index"] is None
    assert len(viewer_zero["state"]["viewer_hand"]) == 8
    assert len(viewer_one["state"]["viewer_hand"]) == 8
    assert viewer_zero["state"]["viewer_hand"] != viewer_one["state"]["viewer_hand"]
    assert viewer_zero["available_actions"]["can_declare_grand_tichu"]
    print("create/viewer snapshot OK")


def test_prepare_flow() -> None:
    reset_sessions()
    game_id = _create_game()

    for player_index, declare in enumerate((True, False, False, False)):
        response = client.post(
            f"/games/{game_id}/prepare/grand-tichu",
            json={"player_index": player_index, "declare": declare},
        )
        assert response.status_code == 200

    after_grand = _get_state(game_id, 0)
    assert after_grand["phase"] == "prepare_exchange"
    assert len(after_grand["state"]["viewer_hand"]) == 14
    assert after_grand["state"]["table"]["leader_index"] is None
    assert after_grand["state"]["table"]["current_player_index"] is None

    for player_index in range(4):
        viewer_state = _get_state(game_id, player_index)
        hand = viewer_state["state"]["viewer_hand"]
        response = client.post(
            f"/games/{game_id}/prepare/exchange",
            json={
                "player_index": player_index,
                "to_left": hand[0],
                "to_team": hand[1],
                "to_right": hand[2],
            },
        )
        assert response.status_code == 200

    after_exchange = _get_state(game_id, 0)
    assert after_exchange["phase"] == "trick"
    assert after_exchange["state"]["table"]["leader_index"] is not None
    assert after_exchange["state"]["table"]["current_player_index"] is not None
    print("prepare flow OK")


def test_viewer_serialization_and_helper_endpoints() -> None:
    reset_sessions()
    game_id = _create_game()
    state = _prepare_to_trick_phase(game_id)
    current_player = state["state"]["table"]["current_player_index"]
    assert current_player is not None

    current_view = _get_state(game_id, current_player)
    other_viewer = (current_player + 1) % 4
    other_view = _get_state(game_id, other_viewer)
    current_hand = current_view["state"]["viewer_hand"]

    assert current_view["state"]["table"] == other_view["state"]["table"]
    assert current_view["available_actions"]["is_my_turn"]
    assert current_view["available_actions"]["can_play"]
    assert not other_view["available_actions"]["is_my_turn"]
    assert current_view["state"]["viewer_hand"] != other_view["state"]["viewer_hand"]

    preview = client.post(
        f"/games/{game_id}/preview-combo",
        json={"viewer": current_player, "cards": [current_hand[0]]},
    )
    assert preview.status_code == 200
    assert preview.json()["is_legal_shape"]
    assert preview.json()["combo_type"] == "single"

    invalid_preview = client.post(
        f"/games/{game_id}/preview-combo",
        json={"viewer": current_player, "cards": [current_hand[0], current_hand[1]]},
    )
    assert invalid_preview.status_code == 200
    assert not invalid_preview.json()["is_legal_shape"]

    legal = client.get(f"/games/{game_id}/legal-plays", params={"viewer": current_player})
    assert legal.status_code == 200
    assert isinstance(legal.json()["plays"], list)

    non_turn_legal = client.get(f"/games/{game_id}/legal-plays", params={"viewer": other_viewer})
    assert non_turn_legal.status_code == 200
    assert non_turn_legal.json()["plays"] == []

    print("viewer serialization/helper endpoints OK")


def test_small_tichu_play_and_pass_flow() -> None:
    reset_sessions()
    game_id = _create_game()
    state = _prepare_to_trick_phase(game_id)
    current_player = state["state"]["table"]["current_player_index"]
    assert current_player is not None
    current_hand = _get_state(game_id, current_player)["state"]["viewer_hand"]

    small_tichu = client.post(
        f"/games/{game_id}/actions/small-tichu",
        json={"player_index": current_player},
    )
    assert small_tichu.status_code == 200
    assert small_tichu.json()["effects"][0]["type"] == "small_tichu_declared"
    assert small_tichu.json()["state"]["players"][current_player]["declared_small_tichu"]

    play = client.post(
        f"/games/{game_id}/actions/play",
        json={"player_index": current_player, "cards": [current_hand[0]], "call_rank": None},
    )
    assert play.status_code == 200
    play_payload = play.json()
    assert play_payload["effects"][0]["type"] == "cards_played"
    assert play_payload["effects"][-1]["type"] == "turn_changed"
    assert play_payload["phase"] == "trick"

    reset_sessions()
    game_id = _create_game()
    _set_pass_flow_state(game_id)

    response = client.post(
        f"/games/{game_id}/actions/pass",
        json={"player_index": 1},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["effects"][0]["type"] == "player_passed"
    assert payload["effects"][-1] == {"type": "turn_changed", "player_index": 2}
    assert payload["state"]["table"]["current_player_index"] == 2
    print("small tichu/play/pass flow OK")


def test_dragon_recipient_flow() -> None:
    reset_sessions()
    game_id = _create_game()
    _set_dragon_recipient_state(game_id)

    first_pass = client.post(
        f"/games/{game_id}/actions/pass",
        json={"player_index": 1},
    )
    assert first_pass.status_code == 200
    assert first_pass.json()["phase"] == "trick"
    assert first_pass.json()["effects"][-1] == {"type": "turn_changed", "player_index": 2}

    second_pass = client.post(
        f"/games/{game_id}/actions/pass",
        json={"player_index": 2},
    )
    assert second_pass.status_code == 200
    second_payload = second_pass.json()
    assert second_payload["phase"] == "await_dragon_recipient"
    assert second_payload["effects"][1]["type"] == "dragon_recipient_required"
    assert "trick_won" not in [effect["type"] for effect in second_payload["effects"]]

    winner_view = _get_state(game_id, 0)
    assert winner_view["phase"] == "await_dragon_recipient"
    assert winner_view["available_actions"]["can_choose_dragon_recipient"]

    recipient = client.post(
        f"/games/{game_id}/actions/dragon-recipient",
        json={"player_index": 0, "recipient_index": 1},
    )
    assert recipient.status_code == 200
    recipient_payload = recipient.json()
    assert recipient_payload["phase"] == "trick"
    assert recipient_payload["effects"][0]["type"] == "dragon_recipient_chosen"
    assert recipient_payload["effects"][1]["type"] == "trick_won"
    assert recipient_payload["effects"][1]["recipient_index"] == 1
    print("dragon recipient flow OK")


def test_round_finish_auto_next_round_flow() -> None:
    reset_sessions()
    game_id = _create_game()
    _set_round_finish_state(game_id)

    play_open = client.post(
        f"/games/{game_id}/actions/play",
        json={"player_index": 0, "cards": [{"suit": "S", "rank": 9}], "call_rank": None},
    )
    assert play_open.status_code == 200
    assert play_open.json()["effects"][-1] == {"type": "turn_changed", "player_index": 1}

    play_reply = client.post(
        f"/games/{game_id}/actions/play",
        json={"player_index": 1, "cards": [{"suit": "S", "rank": 10}], "call_rank": None},
    )
    assert play_reply.status_code == 200
    assert play_reply.json()["effects"][-1] == {"type": "turn_changed", "player_index": 2}

    play_finish = client.post(
        f"/games/{game_id}/actions/play",
        json={"player_index": 2, "cards": [{"suit": "S", "rank": 11}], "call_rank": None},
    )
    assert play_finish.status_code == 200
    finish_payload = play_finish.json()
    assert finish_payload["phase"] == "prepare_grand_tichu"
    assert finish_payload["effects"][0]["type"] == "cards_played"
    assert finish_payload["effects"][1]["type"] == "round_finished"
    assert finish_payload["effects"][2] == {"type": "phase_changed", "phase": "prepare_grand_tichu"}
    assert finish_payload["effects"][3] == {"type": "initial_cards_dealt", "count": 8}
    assert finish_payload["round_result"]["end_reason"] == "double_victory"
    assert finish_payload["round_result"]["players_out_order"] == [0, 2]
    assert len(finish_payload["state"]["viewer_hand"]) == 8

    snapshot = _get_state(game_id, 0)
    assert snapshot["phase"] == "prepare_grand_tichu"
    assert snapshot["round_result"]["players_out_order"] == [0, 2]
    assert "can_start_next_round" not in snapshot["available_actions"]
    print("round finish/auto next round flow OK")


def test_auto_game_over() -> None:
    reset_sessions()
    game_id = _create_game()
    session = _sessions[game_id]
    _set_round_finish_state(game_id)
    session.state.team_scores = [1000, 0]

    response = client.post(
        f"/games/{game_id}/actions/play",
        json={"player_index": 0, "cards": [{"suit": "S", "rank": 9}], "call_rank": None},
    )
    assert response.status_code == 200
    response = client.post(
        f"/games/{game_id}/actions/play",
        json={"player_index": 1, "cards": [{"suit": "S", "rank": 10}], "call_rank": None},
    )
    assert response.status_code == 200
    response = client.post(
        f"/games/{game_id}/actions/play",
        json={"player_index": 2, "cards": [{"suit": "S", "rank": 11}], "call_rank": None},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["phase"] == "game_over"
    assert payload["effects"][-1]["type"] == "game_finished"
    assert payload["round_result"]["score_deltas"] == [200, 0]
    print("auto game over OK")


def main() -> None:
    test_create_and_viewer_snapshot()
    test_prepare_flow()
    test_viewer_serialization_and_helper_endpoints()
    test_small_tichu_play_and_pass_flow()
    test_dragon_recipient_flow()
    test_round_finish_auto_next_round_flow()
    test_auto_game_over()
    print("HTTP API tests passed.")


if __name__ == "__main__":
    main()
