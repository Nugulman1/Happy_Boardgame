from __future__ import annotations

from tichu import Card
from tichu.scenario_harness import ScenarioBuilder


def _normalize_cards(cards: list[dict[str, object]]) -> list[tuple[str, int]]:
    return sorted((str(card["suit"]), int(card["rank"])) for card in cards)


def _normalize_plays(plays: list[list[dict[str, object]]]) -> list[list[tuple[str, int]]]:
    return sorted(_normalize_cards(play) for play in plays)


def _bomb_interrupt_harness(bomb_cards: list[Card], *, current_trick_cards: list[Card]) -> object:
    return (
        ScenarioBuilder("bomb_interrupt")
        .phase_name("trick")
        .viewer(3)
        .leader(0)
        .current_player(1)
        .hand(0, [Card("S", 7)])
        .hand(1, [Card("S", 10)])
        .hand(2, [Card("S", 11)])
        .hand(3, bomb_cards)
        .table(current_trick_cards, pile=current_trick_cards, last_played_by=0)
        .build()
    )


def _mahjong_follow_harness(
    name: str,
    hand: list[Card],
    current_trick_cards: list[Card],
    *,
    call_rank: int = 9,
) -> object:
    return (
        ScenarioBuilder(name)
        .phase_name("trick")
        .viewer(1)
        .leader(0)
        .current_player(1)
        .hand(0, [Card("S", 3)])
        .hand(1, hand)
        .hand(2, [Card("S", 12)])
        .hand(3, [Card("S", 13)])
        .table(current_trick_cards, pile=current_trick_cards, last_played_by=0)
        .mahjong_call(call_rank)
        .build()
    )


def collect_edge_case_report() -> dict[str, object]:
    four_bomb = [Card("S", 9), Card("H", 9), Card("D", 9), Card("C", 9)]
    straight_flush_bomb = [Card("S", 5), Card("S", 6), Card("S", 7), Card("S", 8), Card("S", 9)]

    out_of_turn_four = _bomb_interrupt_harness(four_bomb, current_trick_cards=[Card("S", 8)])
    out_of_turn_straight_flush = _bomb_interrupt_harness(straight_flush_bomb, current_trick_cards=[Card("S", 8)])

    empty_table_interrupt = (
        ScenarioBuilder("bomb_interrupt_empty_table")
        .phase_name("trick")
        .viewer(3)
        .leader(1)
        .current_player(1)
        .hand(1, [Card("S", 10)])
        .hand(2, [Card("S", 11)])
        .hand(3, four_bomb)
        .build()
    )
    after_dog_interrupt = (
        ScenarioBuilder("bomb_interrupt_after_dog")
        .phase_name("trick")
        .viewer(3)
        .leader(2)
        .current_player(2)
        .trick_index(1)
        .hand(0, [])
        .hand(1, [Card("S", 10)])
        .hand(2, [Card("S", 11)])
        .hand(3, four_bomb)
        .played_first_card({0})
        .build()
    )
    opening_bomb = (
        ScenarioBuilder("opening_bomb_current_turn")
        .phase_name("trick")
        .viewer(1)
        .leader(1)
        .current_player(1)
        .hand(0, [Card("S", 3)])
        .hand(1, four_bomb)
        .hand(2, [Card("S", 11)])
        .hand(3, [Card("S", 12)])
        .build()
    )

    bomb_matrix_cases = [
        {
            "name": "bomb_four_over_weaker_bomb_four",
            "table": [Card("S", 8), Card("H", 8), Card("D", 8), Card("C", 8)],
            "selected": four_bomb,
            "expected_ok": True,
        },
        {
            "name": "bomb_four_over_stronger_bomb_four",
            "table": [Card("S", 10), Card("H", 10), Card("D", 10), Card("C", 10)],
            "selected": four_bomb,
            "expected_ok": False,
        },
        {
            "name": "straight_flush_over_bomb_four",
            "table": [Card("S", 12), Card("H", 12), Card("D", 12), Card("C", 12)],
            "selected": straight_flush_bomb,
            "expected_ok": True,
        },
        {
            "name": "bomb_four_over_straight_flush",
            "table": [Card("H", 4), Card("H", 5), Card("H", 6), Card("H", 7), Card("H", 8)],
            "selected": four_bomb,
            "expected_ok": False,
        },
        {
            "name": "straight_flush_over_weaker_straight_flush",
            "table": [Card("H", 4), Card("H", 5), Card("H", 6), Card("H", 7), Card("H", 8)],
            "selected": straight_flush_bomb,
            "expected_ok": True,
        },
        {
            "name": "straight_flush_over_stronger_straight_flush",
            "table": [Card("H", 6), Card("H", 7), Card("H", 8), Card("H", 9), Card("H", 10)],
            "selected": straight_flush_bomb,
            "expected_ok": False,
        },
    ]

    bomb_results: list[dict[str, object]] = []
    for case in bomb_matrix_cases:
        harness = (
            ScenarioBuilder(case["name"])
            .phase_name("trick")
            .viewer(1)
            .leader(0)
            .current_player(1)
            .hand(0, [Card("S", 3)])
            .hand(1, list(case["selected"]))
            .hand(2, [Card("S", 11)])
            .hand(3, [Card("S", 12)])
            .table(case["table"], pile=case["table"], last_played_by=0)
            .build()
        )
        preview = harness.preview_play(1, list(case["selected"]))
        bomb_results.append(
            {
                "name": case["name"],
                "ok": preview["ok"],
                "reason_code": preview["preview"]["reason_code"],
                "combo_type": preview["preview"]["combo_type"],
                "selected_cards": _normalize_cards(preview["request"]["cards"]),
                "table_cards": _normalize_cards(preview["snapshot"]["state"]["table"]["current_trick_cards"]),
            }
        )

    mahjong_cases = [
        {
            "name": "single_exact",
            "hand": [Card("S", 9)],
            "table": [Card("S", 8)],
            "expected": [[("S", 9)]],
        },
        {
            "name": "pair_exact",
            "hand": [Card("S", 9), Card("H", 9)],
            "table": [Card("D", 8), Card("C", 8)],
            "expected": [[("H", 9), ("S", 9)]],
        },
        {
            "name": "pair_phoenix",
            "hand": [Card("S", 9), Card("", 21)],
            "table": [Card("D", 8), Card("C", 8)],
            "expected": [[("", 21), ("S", 9)]],
        },
        {
            "name": "triple_exact",
            "hand": [Card("S", 9), Card("H", 9), Card("D", 9)],
            "table": [Card("S", 8), Card("H", 8), Card("D", 8)],
            "expected": [[("D", 9), ("H", 9), ("S", 9)]],
        },
        {
            "name": "triple_phoenix",
            "hand": [Card("S", 9), Card("H", 9), Card("", 21)],
            "table": [Card("S", 8), Card("H", 8), Card("D", 8)],
            "expected": [[("", 21), ("H", 9), ("S", 9)]],
        },
        {
            "name": "full_house_exact",
            "hand": [Card("S", 5), Card("H", 5), Card("S", 9), Card("H", 9), Card("D", 9)],
            "table": [Card("S", 4), Card("H", 4), Card("S", 8), Card("H", 8), Card("D", 8)],
            "expected": [[("D", 9), ("H", 5), ("H", 9), ("S", 5), ("S", 9)]],
        },
        {
            "name": "full_house_phoenix",
            "hand": [Card("S", 5), Card("H", 5), Card("S", 9), Card("H", 9), Card("", 21)],
            "table": [Card("S", 4), Card("H", 4), Card("S", 8), Card("H", 8), Card("D", 8)],
            "expected": [[("", 21), ("H", 5), ("H", 9), ("S", 5), ("S", 9)]],
        },
        {
            "name": "straight_exact",
            "hand": [Card("S", 7), Card("H", 8), Card("D", 9), Card("C", 10), Card("S", 11)],
            "table": [Card("S", 3), Card("H", 4), Card("D", 5), Card("C", 6), Card("S", 7)],
            "expected": [[("C", 10), ("D", 9), ("H", 8), ("S", 7), ("S", 11)]],
        },
        {
            "name": "straight_phoenix",
            "hand": [Card("S", 7), Card("H", 8), Card("D", 10), Card("C", 11), Card("", 21)],
            "table": [Card("S", 3), Card("H", 4), Card("D", 5), Card("C", 6), Card("S", 7)],
            "expected": [[("", 21), ("C", 11), ("D", 10), ("H", 8), ("S", 7)]],
        },
        {
            "name": "pair_run_exact",
            "hand": [Card("S", 8), Card("H", 8), Card("S", 9), Card("H", 9)],
            "table": [Card("S", 6), Card("H", 6), Card("D", 7), Card("C", 7)],
            "expected": [[("H", 8), ("H", 9), ("S", 8), ("S", 9)]],
        },
        {
            "name": "pair_run_phoenix",
            "hand": [Card("S", 8), Card("H", 8), Card("S", 9), Card("", 21)],
            "table": [Card("S", 6), Card("H", 6), Card("D", 7), Card("C", 7)],
            "expected": [[("", 21), ("H", 8), ("S", 8), ("S", 9)]],
        },
    ]

    mahjong_results: list[dict[str, object]] = []
    for case in mahjong_cases:
        harness = _mahjong_follow_harness(case["name"], case["hand"], case["table"])
        actions = harness.available_actions(1)
        plays = harness.legal_plays(1)
        mahjong_results.append(
            {
                "name": case["name"],
                "can_pass": actions["available_actions"]["can_pass"],
                "plays": _normalize_plays(plays["plays"]),
            }
        )

    phoenix_non_matching = _mahjong_follow_harness(
        "phoenix_non_matching",
        [Card("S", 8), Card("", 21)],
        [Card("S", 10)],
        call_rank=7,
    )

    return {
        "bomb_out_of_turn": {
            "four_bomb_preview": out_of_turn_four.preview_play(3, four_bomb)["preview"],
            "four_bomb_play": out_of_turn_four.play(3, four_bomb, None, 3),
            "straight_flush_preview": out_of_turn_straight_flush.preview_play(3, straight_flush_bomb)["preview"],
            "straight_flush_play": out_of_turn_straight_flush.play(3, straight_flush_bomb, None, 3),
        },
        "bomb_without_active_trick": {
            "empty_table_preview": empty_table_interrupt.preview_play(3, four_bomb)["preview"],
            "after_dog_preview": after_dog_interrupt.preview_play(3, four_bomb)["preview"],
            "opening_bomb_preview": opening_bomb.preview_play(1, four_bomb)["preview"],
            "opening_bomb_play": opening_bomb.play(1, four_bomb, None, 1),
        },
        "bomb_matrix": bomb_results,
        "mahjong_call_cases": mahjong_results,
        "special_cases": {
            "phoenix_non_matching_actions": phoenix_non_matching.available_actions(1)["available_actions"],
            "phoenix_non_matching_plays": _normalize_plays(phoenix_non_matching.legal_plays(1)["plays"]),
        },
    }


def main() -> None:
    report = collect_edge_case_report()

    four_bomb_preview = report["bomb_out_of_turn"]["four_bomb_preview"]
    assert four_bomb_preview["reason_code"] == "NOT_CURRENT_PLAYER"
    assert four_bomb_preview["is_bomb"]

    four_bomb_play = report["bomb_out_of_turn"]["four_bomb_play"]
    assert not four_bomb_play["ok"]
    assert four_bomb_play["error"]["message"] == "not this player's turn"

    straight_flush_preview = report["bomb_out_of_turn"]["straight_flush_preview"]
    assert straight_flush_preview["reason_code"] == "NOT_CURRENT_PLAYER"
    assert straight_flush_preview["is_bomb"]

    straight_flush_play = report["bomb_out_of_turn"]["straight_flush_play"]
    assert not straight_flush_play["ok"]
    assert straight_flush_play["error"]["message"] == "not this player's turn"

    empty_table_preview = report["bomb_without_active_trick"]["empty_table_preview"]
    assert empty_table_preview["reason_code"] == "NOT_CURRENT_PLAYER"
    assert not empty_table_preview["can_submit_play"]

    after_dog_preview = report["bomb_without_active_trick"]["after_dog_preview"]
    assert after_dog_preview["reason_code"] == "NOT_CURRENT_PLAYER"
    assert not after_dog_preview["can_submit_play"]

    opening_bomb_preview = report["bomb_without_active_trick"]["opening_bomb_preview"]
    assert opening_bomb_preview["reason_code"] == "OK"
    assert opening_bomb_preview["can_submit_play"]

    opening_bomb_play = report["bomb_without_active_trick"]["opening_bomb_play"]
    assert opening_bomb_play["ok"]
    assert opening_bomb_play["effects"][0]["type"] == "cards_played"

    expected_bomb_results = {
        "bomb_four_over_weaker_bomb_four": True,
        "bomb_four_over_stronger_bomb_four": False,
        "straight_flush_over_bomb_four": True,
        "bomb_four_over_straight_flush": False,
        "straight_flush_over_weaker_straight_flush": True,
        "straight_flush_over_stronger_straight_flush": False,
    }
    for result in report["bomb_matrix"]:
        assert result["ok"] == expected_bomb_results[result["name"]]

    expected_mahjong_plays = {
        "single_exact": [[("S", 9)]],
        "pair_exact": [[("H", 9), ("S", 9)]],
        "pair_phoenix": [[("", 21), ("S", 9)]],
        "triple_exact": [[("D", 9), ("H", 9), ("S", 9)]],
        "triple_phoenix": [[("", 21), ("H", 9), ("S", 9)]],
        "full_house_exact": [[("D", 9), ("H", 5), ("H", 9), ("S", 5), ("S", 9)]],
        "full_house_phoenix": [[("", 21), ("H", 5), ("H", 9), ("S", 5), ("S", 9)]],
        "straight_exact": [[("C", 10), ("D", 9), ("H", 8), ("S", 7), ("S", 11)]],
        "straight_phoenix": [[("", 21), ("C", 11), ("D", 10), ("H", 8), ("S", 7)]],
        "pair_run_exact": [[("H", 8), ("H", 9), ("S", 8), ("S", 9)]],
        "pair_run_phoenix": [[("", 21), ("H", 8), ("S", 8), ("S", 9)]],
    }
    for result in report["mahjong_call_cases"]:
        assert not result["can_pass"]
        assert result["plays"] == expected_mahjong_plays[result["name"]]

    phoenix_non_matching_actions = report["special_cases"]["phoenix_non_matching_actions"]
    phoenix_non_matching_plays = report["special_cases"]["phoenix_non_matching_plays"]
    assert phoenix_non_matching_actions["can_pass"]
    assert phoenix_non_matching_plays == []

    print("scenario edge case experiments OK")


if __name__ == "__main__":
    main()
