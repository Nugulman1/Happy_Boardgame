from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Callable
from uuid import uuid4

from .cards import Card, RANK_DOG, RANK_DRAGON, RANK_MAHJONG, RANK_PHOENIX
from .combo_info import evaluate_combo
from .session_service import (
    GameSession,
    SessionActionError,
    combo_summary_payload,
    get_available_actions,
    get_legal_plays_for_viewer,
    preview_play as preview_play_action,
    submit_dragon_recipient as submit_dragon_recipient_action,
    submit_pass as submit_pass_action,
    submit_play as submit_play_action,
    submit_small_tichu as submit_small_tichu_action,
)
from .state import GameState, RoundState, init_state, new_round_state

SummaryResult = dict[str, object]


def _card_payload(card: Card) -> dict[str, int | str]:
    return {"suit": card.suit, "rank": card.rank}


def _cards_payload(cards: list[Card]) -> list[dict[str, int | str]]:
    return [_card_payload(card) for card in cards]


def _player_payload(session: GameSession, player_index: int) -> dict[str, object]:
    round_state = session.round_state
    return {
        "player_index": player_index,
        "hand_count": len(round_state.hands[player_index]),
        "is_out": player_index in round_state.players_out_order,
        "declared_grand_tichu": player_index in round_state.grand_tichu_declarers,
        "declared_small_tichu": player_index in round_state.small_tichu_declarers,
    }


def _table_payload(session: GameSession) -> dict[str, object]:
    round_state = session.round_state
    leader_index: int | None = round_state.leader_index
    current_player_index: int | None = round_state.current_player_index
    current_trick_combo = round_state.current_trick_combo
    if current_trick_combo is None and round_state.current_trick_cards:
        current_trick_combo = evaluate_combo(round_state.current_trick_cards)
    if session.phase in ("prepare_grand_tichu", "prepare_exchange"):
        leader_index = None
        current_player_index = None

    return {
        "leader_index": leader_index,
        "current_player_index": current_player_index,
        "trick_index": round_state.trick_index,
        "mahjong_call_rank": round_state.mahjong_call_rank,
        "current_trick_cards": _cards_payload(round_state.current_trick_cards),
        "current_trick_combo": combo_summary_payload(current_trick_combo),
    }


def snapshot_payload(
    session: GameSession,
    viewer: int,
    *,
    effects: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    round_state = session.round_state
    response = {
        "game_id": session.game_id,
        "viewer": viewer,
        "phase": session.phase,
        "state": {
            "game": {
                "team_scores": list(session.state.team_scores),
                "round_index": session.state.round_index,
            },
            "table": _table_payload(session),
            "players": [_player_payload(session, player_index) for player_index in range(4)],
            "viewer_hand": _cards_payload(round_state.hands[viewer]),
            "players_out_order": list(round_state.players_out_order),
        },
        "available_actions": get_available_actions(session, viewer),
    }
    if session.last_round_result is not None:
        response["round_result"] = session.last_round_result
    if effects is not None:
        response["effects"] = effects
    return response


def card(suit: str, rank: int) -> Card:
    return Card(suit=suit, rank=rank)


def parse_card_token(token: str) -> Card:
    normalized = token.strip().upper()
    if not normalized:
        raise ValueError("card token cannot be empty")
    if normalized in {"M", "MAHJONG"}:
        return Card("", RANK_MAHJONG)
    if normalized in {"DOG"}:
        return Card("", RANK_DOG)
    if normalized in {"PHX", "PHOENIX"}:
        return Card("", RANK_PHOENIX)
    if normalized in {"DRAGON"}:
        return Card("", RANK_DRAGON)
    if len(normalized) < 2:
        raise ValueError(f"invalid card token: {token}")

    suit = normalized[0]
    rank_text = normalized[1:]
    rank_map = {"J": 11, "Q": 12, "K": 13, "A": 14}
    rank = rank_map.get(rank_text, None)
    if rank is None:
        try:
            rank = int(rank_text)
        except ValueError as exc:
            raise ValueError(f"invalid card token: {token}") from exc
    return Card(suit, rank)


def parse_cards(tokens: list[str]) -> list[Card]:
    return [parse_card_token(token) for token in tokens]


@dataclass
class ScenarioHarness:
    session: GameSession
    name: str
    default_viewer: int = 0

    def snapshot(self, viewer: int | None = None) -> SummaryResult:
        resolved_viewer = self.default_viewer if viewer is None else viewer
        return {
            "ok": True,
            "scenario": self.name,
            "action": "snapshot",
            "viewer": resolved_viewer,
            "snapshot": snapshot_payload(self.session, resolved_viewer),
        }

    def available_actions(self, viewer: int | None = None) -> SummaryResult:
        resolved_viewer = self.default_viewer if viewer is None else viewer
        snapshot = snapshot_payload(self.session, resolved_viewer)
        return {
            "ok": True,
            "scenario": self.name,
            "action": "available_actions",
            "viewer": resolved_viewer,
            "available_actions": snapshot["available_actions"],
            "snapshot": snapshot,
        }

    def legal_plays(self, viewer: int | None = None) -> SummaryResult:
        resolved_viewer = self.default_viewer if viewer is None else viewer
        plays = get_legal_plays_for_viewer(self.session, resolved_viewer)
        snapshot = snapshot_payload(self.session, resolved_viewer)
        return {
            "ok": True,
            "scenario": self.name,
            "action": "legal_plays",
            "viewer": resolved_viewer,
            "plays": [_cards_payload(cards) for cards in plays],
            "snapshot": snapshot,
        }

    def preview_play(
        self,
        viewer: int | None,
        cards: list[Card],
        call_rank: int | None = None,
    ) -> SummaryResult:
        resolved_viewer = self.default_viewer if viewer is None else viewer
        payload = preview_play_action(self.session, resolved_viewer, cards, call_rank)
        return {
            "ok": bool(payload.get("can_submit_play", False)),
            "scenario": self.name,
            "action": "preview_play",
            "viewer": resolved_viewer,
            "request": {
                "viewer": resolved_viewer,
                "cards": _cards_payload(cards),
                "call_rank": call_rank,
            },
            "preview": payload,
            "snapshot": snapshot_payload(self.session, resolved_viewer),
        }

    def play(
        self,
        player_index: int,
        cards: list[Card],
        call_rank: int | None = None,
        viewer: int | None = None,
    ) -> SummaryResult:
        return self._mutating_action(
            action_name="play",
            actor=player_index,
            viewer=viewer,
            request={"player_index": player_index, "cards": _cards_payload(cards), "call_rank": call_rank},
            fn=lambda: submit_play_action(self.session, player_index, cards, call_rank),
        )

    def pass_turn(
        self,
        player_index: int,
        dragon_recipient: int | None = None,
        viewer: int | None = None,
    ) -> SummaryResult:
        return self._mutating_action(
            action_name="pass",
            actor=player_index,
            viewer=viewer,
            request={"player_index": player_index, "dragon_recipient": dragon_recipient},
            fn=lambda: submit_pass_action(self.session, player_index, dragon_recipient),
        )

    def declare_small_tichu(self, player_index: int, viewer: int | None = None) -> SummaryResult:
        return self._mutating_action(
            action_name="small_tichu",
            actor=player_index,
            viewer=viewer,
            request={"player_index": player_index},
            fn=lambda: submit_small_tichu_action(self.session, player_index),
        )

    def choose_dragon_recipient(
        self,
        player_index: int,
        recipient_index: int,
        viewer: int | None = None,
    ) -> SummaryResult:
        return self._mutating_action(
            action_name="dragon_recipient",
            actor=player_index,
            viewer=viewer,
            request={"player_index": player_index, "recipient_index": recipient_index},
            fn=lambda: submit_dragon_recipient_action(self.session, player_index, recipient_index),
        )

    def _mutating_action(
        self,
        *,
        action_name: str,
        actor: int,
        viewer: int | None,
        request: dict[str, object],
        fn: Callable[[], list[dict[str, object]]],
    ) -> SummaryResult:
        resolved_viewer = actor if viewer is None else viewer
        try:
            effects = fn()
        except SessionActionError as exc:
            return {
                "ok": False,
                "scenario": self.name,
                "action": action_name,
                "viewer": resolved_viewer,
                "request": request,
                "error": {"code": exc.code, "message": exc.message},
                "snapshot": snapshot_payload(self.session, resolved_viewer),
            }

        return {
            "ok": True,
            "scenario": self.name,
            "action": action_name,
            "viewer": resolved_viewer,
            "request": request,
            "effects": effects,
            "snapshot": snapshot_payload(self.session, resolved_viewer, effects=effects),
        }


class ScenarioBuilder:
    def __init__(self, name: str = "custom_scenario") -> None:
        self.name = name
        self.state = GameState()
        init_state(self.state)
        self.round_state = new_round_state()
        self.phase = "trick"
        self.default_viewer = 0
        self.last_round_result: dict[str, object] | None = None
        self.game_id = uuid4().hex

    def phase_name(self, phase: str) -> ScenarioBuilder:
        self.phase = phase
        return self

    def viewer(self, viewer: int) -> ScenarioBuilder:
        self.default_viewer = viewer
        return self

    def team_scores(self, team_scores: list[int]) -> ScenarioBuilder:
        self.state.team_scores = list(team_scores)
        return self

    def round_index(self, round_index: int) -> ScenarioBuilder:
        self.state.round_index = round_index
        return self

    def hand(self, player_index: int, cards: list[Card]) -> ScenarioBuilder:
        self.round_state.hands[player_index] = list(cards)
        return self

    def leader(self, player_index: int) -> ScenarioBuilder:
        self.round_state.leader_index = player_index
        return self

    def current_player(self, player_index: int) -> ScenarioBuilder:
        self.round_state.current_player_index = player_index
        return self

    def trick_index(self, trick_index: int) -> ScenarioBuilder:
        self.round_state.trick_index = trick_index
        return self

    def table(
        self,
        cards: list[Card],
        *,
        pile: list[Card] | None = None,
        last_played_by: int | None = None,
        pass_count_since_last_play: int | None = None,
    ) -> ScenarioBuilder:
        self.round_state.current_trick_cards = list(cards)
        self.round_state.current_trick_combo = evaluate_combo(cards) if cards else None
        self.round_state.current_trick_pile = list(cards if pile is None else pile)
        self.round_state.last_played_by = last_played_by
        if pass_count_since_last_play is not None:
            self.round_state.pass_count_since_last_play = pass_count_since_last_play
        return self

    def mahjong_call(self, call_rank: int | None) -> ScenarioBuilder:
        self.round_state.mahjong_call_rank = call_rank
        return self

    def players_out_order(self, order: list[int]) -> ScenarioBuilder:
        self.round_state.players_out_order = list(order)
        return self

    def grand_tichu(self, player_indices: list[int] | set[int]) -> ScenarioBuilder:
        self.round_state.grand_tichu_declarers = set(player_indices)
        return self

    def small_tichu(self, player_indices: list[int] | set[int]) -> ScenarioBuilder:
        self.round_state.small_tichu_declarers = set(player_indices)
        return self

    def played_first_card(self, player_indices: list[int] | set[int]) -> ScenarioBuilder:
        self.round_state.played_first_card_players = set(player_indices)
        return self

    def won_trick_cards(self, player_index: int, cards: list[Card]) -> ScenarioBuilder:
        self.round_state.won_trick_cards[player_index] = list(cards)
        return self

    def round_result(self, payload: dict[str, object]) -> ScenarioBuilder:
        self.last_round_result = payload
        return self

    def build(self) -> ScenarioHarness:
        session = GameSession(
            game_id=self.game_id,
            state=self.state,
            round_state=self.round_state,
            phase=self.phase,
            last_round_result=self.last_round_result,
        )
        return ScenarioHarness(session=session, name=self.name, default_viewer=self.default_viewer)


def scenario_mahjong_opening_call() -> ScenarioHarness:
    return (
        ScenarioBuilder("mahjong_opening_call")
        .phase_name("trick")
        .viewer(0)
        .leader(0)
        .current_player(0)
        .hand(0, [Card("", RANK_MAHJONG), Card("S", 9)])
        .hand(1, [Card("S", 8)])
        .hand(2, [Card("S", 10)])
        .hand(3, [Card("S", 11)])
        .build()
    )


def scenario_forced_mahjong_call() -> ScenarioHarness:
    return (
        ScenarioBuilder("forced_mahjong_call")
        .phase_name("trick")
        .viewer(1)
        .leader(0)
        .current_player(1)
        .hand(0, [Card("S", 3)])
        .hand(1, [Card("S", 8), Card("S", 9)])
        .hand(2, [Card("S", 10)])
        .hand(3, [Card("S", 11)])
        .table([Card("H", 7)], pile=[Card("H", 7)], last_played_by=0)
        .mahjong_call(9)
        .build()
    )


def scenario_dragon_recipient_required() -> ScenarioHarness:
    return (
        ScenarioBuilder("dragon_recipient_required")
        .phase_name("trick")
        .viewer(3)
        .leader(0)
        .current_player(3)
        .trick_index(1)
        .hand(0, [Card("S", 9)])
        .hand(1, [Card("S", 8)])
        .hand(2, [Card("S", 7)])
        .hand(3, [Card("S", 6)])
        .table(
            [Card("", RANK_DRAGON)],
            pile=[Card("", RANK_DRAGON), Card("S", 10)],
            last_played_by=0,
            pass_count_since_last_play=2,
        )
        .build()
    )


def scenario_grand_blocks_small_tichu() -> ScenarioHarness:
    return (
        ScenarioBuilder("grand_blocks_small_tichu")
        .phase_name("trick")
        .viewer(0)
        .leader(0)
        .current_player(0)
        .hand(0, [Card("S", 9)])
        .hand(1, [Card("S", 8)])
        .hand(2, [Card("S", 10)])
        .hand(3, [Card("S", 11)])
        .grand_tichu({0})
        .build()
    )


def scenario_round_end_near() -> ScenarioHarness:
    return (
        ScenarioBuilder("round_end_near")
        .phase_name("trick")
        .viewer(2)
        .leader(2)
        .current_player(2)
        .trick_index(3)
        .hand(0, [])
        .hand(1, [Card("S", 10)])
        .hand(2, [Card("S", 11)])
        .hand(3, [Card("S", 12)])
        .players_out_order([0])
        .won_trick_cards(0, [Card("S", 5), Card("S", 13)])
        .won_trick_cards(2, [Card("H", 10)])
        .build()
    )


PREDEFINED_SCENARIOS: dict[str, Callable[[], ScenarioHarness]] = {
    "mahjong_opening_call": scenario_mahjong_opening_call,
    "forced_mahjong_call": scenario_forced_mahjong_call,
    "dragon_recipient_required": scenario_dragon_recipient_required,
    "grand_blocks_small_tichu": scenario_grand_blocks_small_tichu,
    "round_end_near": scenario_round_end_near,
}


def format_summary(result: SummaryResult) -> str:
    snapshot = result.get("snapshot", {})
    if not isinstance(snapshot, dict):
        snapshot = {}
    table_state = snapshot.get("state", {}).get("table", {}) if isinstance(snapshot.get("state", {}), dict) else {}
    action_name = str(result.get("action", "-"))
    lines = [
        "scenario=%s action=%s ok=%s" % (
            str(result.get("scenario", "-")),
            action_name,
            str(result.get("ok", False)),
        ),
        "phase=%s current_player=%s viewer=%s" % (
            str(snapshot.get("phase", "-")),
            str(table_state.get("current_player_index", "-")),
            str(result.get("viewer", "-")),
        ),
    ]

    available_actions = result.get("available_actions", snapshot.get("available_actions", {}))
    if isinstance(available_actions, dict):
        lines.append("available_actions=%s" % json.dumps(available_actions, ensure_ascii=False, sort_keys=True))

        if action_name == "preview_play":
            preview = result.get("preview", {})
            if isinstance(preview, dict):
                lines.append(
                    "preview reason=%s can_submit=%s combo=%s"
                    % (
                        str(preview.get("reason_code", "-")),
                        str(preview.get("can_submit_play", False)),
                        str(preview.get("combo_type", None)),
                    )
                )

    effects = result.get("effects", [])
    if isinstance(effects, list) and effects:
        lines.append("effects=%s" % ", ".join(str(effect.get("type", effect)) for effect in effects if isinstance(effect, dict)))

    error = result.get("error", {})
    if isinstance(error, dict) and error:
        lines.append("error=%s: %s" % (str(error.get("code", "-")), str(error.get("message", "-"))))

    return "\n".join(lines)


def run_cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scenario harness for Tichu rule experiments")
    parser.add_argument("scenario", nargs="?", help="predefined scenario name")
    parser.add_argument(
        "action",
        nargs="?",
        default="snapshot",
        choices=["snapshot", "available-actions", "preview-play", "play", "pass", "small-tichu", "dragon-recipient"],
    )
    parser.add_argument("--viewer", type=int, help="viewer index")
    parser.add_argument("--player", type=int, help="actor/player index")
    parser.add_argument("--cards", nargs="*", default=[], help="cards like M, S9, H10, DOG, PHX, DRAGON")
    parser.add_argument("--call-rank", type=int, default=None)
    parser.add_argument("--recipient", type=int, default=None)
    parser.add_argument("--json-only", action="store_true")
    parser.add_argument("--list", action="store_true", help="list predefined scenarios")
    args = parser.parse_args(argv)

    if args.list or args.scenario is None:
        print("available scenarios:")
        for scenario_name in sorted(PREDEFINED_SCENARIOS):
            print(" - %s" % scenario_name)
        return 0

    factory = PREDEFINED_SCENARIOS.get(args.scenario)
    if factory is None:
        parser.error("unknown scenario: %s" % args.scenario)

    harness = factory()
    result: SummaryResult
    if args.action == "snapshot":
        result = harness.snapshot(args.viewer)
    elif args.action == "available-actions":
        result = harness.available_actions(args.viewer)
    elif args.action == "preview-play":
        result = harness.preview_play(args.viewer, parse_cards(args.cards), args.call_rank)
    elif args.action == "play":
        player_index = harness.default_viewer if args.player is None else args.player
        result = harness.play(player_index, parse_cards(args.cards), args.call_rank, args.viewer)
    elif args.action == "pass":
        player_index = harness.default_viewer if args.player is None else args.player
        result = harness.pass_turn(player_index, args.recipient, args.viewer)
    elif args.action == "small-tichu":
        player_index = harness.default_viewer if args.player is None else args.player
        result = harness.declare_small_tichu(player_index, args.viewer)
    else:
        player_index = harness.default_viewer if args.player is None else args.player
        if args.recipient is None:
            parser.error("--recipient is required for dragon-recipient")
        result = harness.choose_dragon_recipient(player_index, args.recipient, args.viewer)

    if not args.json_only:
        print(format_summary(result))
        print("---")
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli())
