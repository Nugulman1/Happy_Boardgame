from __future__ import annotations

import json

from tichu import Card
from tichu.scenario_harness import (
    PREDEFINED_SCENARIOS,
    ScenarioBuilder,
    format_summary,
    run_cli,
)


def test_builder_snapshot_reflects_injected_state() -> None:
    harness = (
        ScenarioBuilder("builder_snapshot")
        .phase_name("trick")
        .viewer(2)
        .leader(1)
        .current_player(2)
        .trick_index(4)
        .team_scores([120, 80])
        .round_index(3)
        .hand(2, [Card("", 1), Card("S", 9)])
        .players_out_order([0])
        .mahjong_call(9)
        .build()
    )

    result = harness.snapshot()
    snapshot = result["snapshot"]
    assert result["ok"]
    assert snapshot["viewer"] == 2
    assert snapshot["phase"] == "trick"
    assert snapshot["state"]["game"]["team_scores"] == [120, 80]
    assert snapshot["state"]["game"]["round_index"] == 3
    assert snapshot["state"]["table"]["leader_index"] == 1
    assert snapshot["state"]["table"]["current_player_index"] == 2
    assert snapshot["state"]["table"]["trick_index"] == 4
    assert snapshot["state"]["table"]["mahjong_call_rank"] == 9
    assert snapshot["state"]["players_out_order"] == [0]
    assert snapshot["state"]["viewer_hand"] == [{"suit": "", "rank": 1}, {"suit": "S", "rank": 9}]


def test_opening_mahjong_call_preview_and_play_succeed() -> None:
    harness = PREDEFINED_SCENARIOS["mahjong_opening_call"]()

    preview = harness.preview_play(0, [Card("", 1)], 9)
    assert preview["ok"]
    assert preview["preview"]["reason_code"] == "OK"

    play = harness.play(0, [Card("", 1)], 9, 0)
    assert play["ok"]
    assert play["effects"][0]["type"] == "cards_played"
    assert play["snapshot"]["state"]["table"]["mahjong_call_rank"] == 9


def test_forced_mahjong_call_blocks_non_matching_play() -> None:
    harness = PREDEFINED_SCENARIOS["forced_mahjong_call"]()

    preview = harness.preview_play(1, [Card("S", 8)], None)
    assert not preview["ok"]
    assert preview["preview"]["reason_code"] == "MAHJONG_CALL_NOT_SATISFIED"

    play = harness.play(1, [Card("S", 8)], None, 1)
    assert not play["ok"]
    assert play["error"]["code"] == "INVALID_ACTION"
    assert play["error"]["message"] == "selected cards are not a legal play"


def test_grand_tichu_declarer_cannot_declare_small_tichu() -> None:
    harness = PREDEFINED_SCENARIOS["grand_blocks_small_tichu"]()

    available_actions = harness.available_actions(0)
    assert not available_actions["available_actions"]["can_declare_small_tichu"]

    result = harness.declare_small_tichu(0, 0)
    assert not result["ok"]
    assert result["error"]["message"] == "small tichu cannot be declared"


def test_dragon_recipient_flow_updates_phase_and_effects() -> None:
    harness = PREDEFINED_SCENARIOS["dragon_recipient_required"]()

    passed = harness.pass_turn(3, None, 3)
    assert passed["ok"]
    assert passed["snapshot"]["phase"] == "await_dragon_recipient"
    assert passed["effects"][1]["type"] == "dragon_recipient_required"

    recipient = harness.choose_dragon_recipient(0, 1, 0)
    assert recipient["ok"]
    assert recipient["effects"][0]["type"] == "dragon_recipient_chosen"
    assert recipient["effects"][1]["type"] == "trick_won"


def test_round_end_near_play_finishes_round() -> None:
    harness = PREDEFINED_SCENARIOS["round_end_near"]()

    result = harness.play(2, [Card("S", 11)], None, 2)
    assert result["ok"]
    assert any(effect["type"] == "round_finished" for effect in result["effects"])
    assert result["snapshot"]["phase"] == "prepare_grand_tichu"
    assert result["snapshot"]["round_result"]["end_reason"] == "double_victory"


def test_cli_outputs_summary_and_json(capsys) -> None:
    exit_code = run_cli(["mahjong_opening_call", "preview-play", "--cards", "M", "--call-rank", "9"])
    assert exit_code == 0
    captured = capsys.readouterr().out
    assert "scenario=mahjong_opening_call action=preview_play ok=True" in captured
    assert '"reason_code": "OK"' in captured
    json.loads(captured.split("---\n", 1)[1])


def test_cli_invalid_action_includes_error_and_snapshot(capsys) -> None:
    exit_code = run_cli(["grand_blocks_small_tichu", "small-tichu", "--player", "0"])
    assert exit_code == 0
    captured = capsys.readouterr().out
    assert "error=INVALID_ACTION: small tichu cannot be declared" in captured
    assert '"snapshot"' in captured
