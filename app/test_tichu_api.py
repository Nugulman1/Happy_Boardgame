from fastapi.testclient import TestClient

from app.main import app
from app.tichu_api import _sessions, reset_sessions


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


def test_action_and_helper_endpoints() -> None:
    reset_sessions()
    game_id = _create_game()
    for player_index in range(4):
        client.post(
            f"/games/{game_id}/prepare/grand-tichu",
            json={"player_index": player_index, "declare": False},
        )
    for player_index in range(4):
        hand = _get_state(game_id, player_index)["state"]["viewer_hand"]
        client.post(
            f"/games/{game_id}/prepare/exchange",
            json={
                "player_index": player_index,
                "to_left": hand[0],
                "to_team": hand[1],
                "to_right": hand[2],
            },
        )

    state = _get_state(game_id, 0)
    current_player = state["state"]["table"]["current_player_index"]
    current_hand = _get_state(game_id, current_player)["state"]["viewer_hand"]

    preview = client.post(
        f"/games/{game_id}/preview-combo",
        json={"viewer": current_player, "cards": [current_hand[0]]},
    )
    assert preview.status_code == 200
    assert preview.json()["is_legal_shape"]

    legal = client.get(f"/games/{game_id}/legal-plays", params={"viewer": current_player})
    assert legal.status_code == 200
    assert isinstance(legal.json()["plays"], list)

    small_tichu = client.post(
        f"/games/{game_id}/actions/small-tichu",
        json={"player_index": current_player},
    )
    assert small_tichu.status_code == 200
    assert small_tichu.json()["effects"][0]["type"] == "small_tichu_declared"

    play = client.post(
        f"/games/{game_id}/actions/play",
        json={"player_index": current_player, "cards": [current_hand[0]], "call_rank": None},
    )
    assert play.status_code == 200
    play_payload = play.json()
    assert play_payload["effects"][0]["type"] == "cards_played"
    print("action/helper endpoints OK")


def test_round_next_and_game_over() -> None:
    reset_sessions()
    game_id = _create_game()
    session = _sessions[game_id]
    session.phase = "round_over"
    session.last_round_result = {
        "end_reason": "double_victory",
        "score_deltas": [200, 0],
        "players_out_order": [0, 2],
    }

    response = client.post(f"/games/{game_id}/round/next", params={"viewer": 0})
    assert response.status_code == 200
    payload = response.json()
    assert payload["phase"] == "prepare_grand_tichu"
    assert len(payload["state"]["viewer_hand"]) == 8

    session.phase = "round_over"
    session.last_round_result = {
        "end_reason": "double_victory",
        "score_deltas": [200, 0],
        "players_out_order": [0, 2],
    }
    session.state.team_scores = [1000, 0]
    response = client.post(f"/games/{game_id}/round/next", params={"viewer": 0})
    assert response.status_code == 200
    assert response.json()["phase"] == "game_over"
    print("round next/game over OK")


def main() -> None:
    test_create_and_viewer_snapshot()
    test_prepare_flow()
    test_action_and_helper_endpoints()
    test_round_next_and_game_over()
    print("HTTP API tests passed.")


if __name__ == "__main__":
    main()
