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


def _receive_socket_snapshot(websocket) -> dict:
    payload = websocket.receive_json()
    assert payload["type"] == "snapshot"
    return payload["snapshot"]


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

    legal = client.get(f"/games/{game_id}/legal-plays", params={"viewer": current_player})
    assert legal.status_code == 200
    assert isinstance(legal.json()["plays"], list)

    non_turn_legal = client.get(f"/games/{game_id}/legal-plays", params={"viewer": other_viewer})
    assert non_turn_legal.status_code == 200
    assert non_turn_legal.json()["plays"] == []

    print("viewer serialization/helper endpoints OK")


def test_play_preview_endpoint() -> None:
    reset_sessions()
    game_id = _create_game()
    _prepare_to_trick_phase(game_id)
    session = _sessions[game_id]
    session.round_state.current_player_index = 1
    session.round_state.hands = [
        [Card("S", 3)],
        [Card("S", 4), Card("S", 8)],
        [Card("S", 5)],
        [Card("S", 6)],
    ]
    session.round_state.current_trick_cards = [Card("S", 7)]
    session.round_state.current_trick_combo = None
    session.round_state.current_trick_pile = [Card("S", 7)]

    winning_preview = client.post(
        f"/games/{game_id}/play-preview",
        json={"viewer": 1, "cards": [{"suit": "S", "rank": 8}], "call_rank": None},
    )
    assert winning_preview.status_code == 200
    assert winning_preview.json()["combo_type"] == "single"
    assert winning_preview.json()["beats_current_trick"]
    assert winning_preview.json()["can_submit_play"]
    assert winning_preview.json()["current_trick_combo"]["combo_type"] == "single"

    losing_preview = client.post(
        f"/games/{game_id}/play-preview",
        json={"viewer": 1, "cards": [{"suit": "S", "rank": 4}], "call_rank": None},
    )
    assert losing_preview.status_code == 200
    assert not losing_preview.json()["beats_current_trick"]
    assert not losing_preview.json()["can_submit_play"]
    assert losing_preview.json()["reason_code"] == "DOES_NOT_BEAT_CURRENT_TRICK"

    invalid_preview = client.post(
        f"/games/{game_id}/play-preview",
        json={
            "viewer": 1,
            "cards": [{"suit": "S", "rank": 4}, {"suit": "S", "rank": 8}],
            "call_rank": None,
        },
    )
    assert invalid_preview.status_code == 200
    assert not invalid_preview.json()["is_legal_shape"]
    assert not invalid_preview.json()["can_submit_play"]
    assert invalid_preview.json()["reason_code"] == "ILLEGAL_SHAPE"

    print("play preview endpoint OK")


def test_play_preview_respects_mahjong_call() -> None:
    reset_sessions()
    game_id = _create_game()
    _prepare_to_trick_phase(game_id)
    session = _sessions[game_id]
    session.phase = "trick"
    session.round_state = new_round_state()
    session.round_state.leader_index = 0
    session.round_state.current_player_index = 1
    session.round_state.hands = [
        [Card("S", 3)],
        [Card("S", 8), Card("S", 9)],
        [Card("S", 10)],
        [Card("S", 11)],
    ]
    session.round_state.current_trick_cards = [Card("H", 7)]
    session.round_state.current_trick_combo = None
    session.round_state.current_trick_pile = [Card("H", 7)]
    session.round_state.mahjong_call_rank = 9

    payload = client.post(
        f"/games/{game_id}/play-preview",
        json={"viewer": 1, "cards": [{"suit": "S", "rank": 8}], "call_rank": None},
    )
    assert payload.status_code == 200
    assert not payload.json()["satisfies_mahjong_call"]
    assert not payload.json()["can_submit_play"]
    assert payload.json()["reason_code"] == "MAHJONG_CALL_NOT_SATISFIED"

    matching_payload = client.post(
        f"/games/{game_id}/play-preview",
        json={"viewer": 1, "cards": [{"suit": "S", "rank": 9}], "call_rank": None},
    )
    assert matching_payload.status_code == 200
    assert matching_payload.json()["satisfies_mahjong_call"]
    assert matching_payload.json()["can_submit_play"]

    print("play preview mahjong call OK")


def test_play_preview_allows_valid_mahjong_call_on_opening_play() -> None:
    reset_sessions()
    game_id = _create_game()
    _prepare_to_trick_phase(game_id)
    session = _sessions[game_id]
    session.phase = "trick"
    session.round_state = new_round_state()
    session.round_state.leader_index = 0
    session.round_state.current_player_index = 0
    session.round_state.hands = [
        [Card("", 1), Card("S", 9)],
        [Card("S", 8)],
        [Card("S", 10)],
        [Card("S", 11)],
    ]
    session.round_state.current_trick_cards = []
    session.round_state.current_trick_combo = None
    session.round_state.current_trick_pile = []

    payload = client.post(
        f"/games/{game_id}/play-preview",
        json={"viewer": 0, "cards": [{"suit": "", "rank": 1}], "call_rank": 9},
    )
    assert payload.status_code == 200
    assert payload.json()["can_submit_play"]
    assert payload.json()["reason_code"] == "OK"
    print("play preview opening mahjong call OK")


def test_websocket_initial_snapshot_and_action_broadcast() -> None:
    reset_sessions()
    game_id = _create_game()

    with client.websocket_connect(f"/ws/games/{game_id}?viewer=0") as viewer_zero_socket:
        with client.websocket_connect(f"/ws/games/{game_id}?viewer=1") as viewer_one_socket:
            initial_zero = _receive_socket_snapshot(viewer_zero_socket)
            initial_one = _receive_socket_snapshot(viewer_one_socket)

            assert initial_zero["viewer"] == 0
            assert initial_one["viewer"] == 1
            assert initial_zero["state"]["viewer_hand"] != initial_one["state"]["viewer_hand"]

            response = client.post(
                f"/games/{game_id}/prepare/grand-tichu",
                json={"player_index": 0, "declare": False},
            )
            assert response.status_code == 200

            updated_zero = _receive_socket_snapshot(viewer_zero_socket)
            updated_one = _receive_socket_snapshot(viewer_one_socket)

            assert updated_zero["viewer"] == 0
            assert updated_one["viewer"] == 1
            assert updated_zero["effects"][0]["type"] == "grand_tichu_declared"
            assert updated_one["effects"][0]["type"] == "grand_tichu_declared"
            assert updated_zero["state"]["viewer_hand"] != updated_one["state"]["viewer_hand"]
    print("websocket snapshot/broadcast OK")


def test_websocket_reconnect_receives_latest_snapshot() -> None:
    reset_sessions()
    game_id = _create_game()

    with client.websocket_connect(f"/ws/games/{game_id}?viewer=0") as first_socket:
        initial_snapshot = _receive_socket_snapshot(first_socket)
        assert initial_snapshot["available_actions"]["can_declare_grand_tichu"]

    response = client.post(
        f"/games/{game_id}/prepare/grand-tichu",
        json={"player_index": 0, "declare": False},
    )
    assert response.status_code == 200

    with client.websocket_connect(f"/ws/games/{game_id}?viewer=0") as second_socket:
        latest_snapshot = _receive_socket_snapshot(second_socket)
        assert not latest_snapshot["available_actions"]["can_declare_grand_tichu"]
        assert "effects" not in latest_snapshot
    print("websocket reconnect snapshot OK")


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


def test_grand_tichu_declarer_cannot_declare_small_tichu() -> None:
    reset_sessions()
    game_id = _create_game()

    for player_index in range(4):
        response = client.post(
            f"/games/{game_id}/prepare/grand-tichu",
            json={"player_index": player_index, "declare": player_index == 0},
        )
        assert response.status_code == 200

    state = _get_state(game_id, 0)
    assert state["phase"] == "prepare_exchange"

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

    trick_state = _get_state(game_id, 0)
    assert trick_state["phase"] == "trick"
    assert not trick_state["available_actions"]["can_declare_small_tichu"]

    response = client.post(
        f"/games/{game_id}/actions/small-tichu",
        json={"player_index": 0},
    )
    assert response.status_code == 409
    assert response.json()["error"]["message"] == "small tichu cannot be declared"
    print("grand tichu blocks small tichu API OK")


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
    test_play_preview_endpoint()
    test_play_preview_respects_mahjong_call()
    test_play_preview_allows_valid_mahjong_call_on_opening_play()
    test_websocket_initial_snapshot_and_action_broadcast()
    test_websocket_reconnect_receives_latest_snapshot()
    test_small_tichu_play_and_pass_flow()
    test_grand_tichu_declarer_cannot_declare_small_tichu()
    test_dragon_recipient_flow()
    test_round_finish_auto_next_round_flow()
    test_auto_game_over()
    print("HTTP API tests passed.")


if __name__ == "__main__":
    main()
