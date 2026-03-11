from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Literal
from uuid import uuid4

from .cards import Card, RANK_MAHJONG, make_deck
from .combo_info import ComboInfo, can_beat, evaluate_combo
from .game_loop import finalize_round, is_game_over
from .mahjong_call import can_declare_mahjong_call, selection_satisfies_mahjong_call
from .prepare import apply_exchange, deal_initial_8, deal_remaining_6, set_leader_by_mahjong
from .state import GameState, RoundState, init_state, new_round_state
from .trick import (
    can_declare_small_tichu,
    can_player_pass,
    declare_small_tichu,
    get_legal_plays,
    get_round_end_reason,
    is_round_over,
    pass_turn,
    play_cards,
    resolve_trick_end,
    start_trick,
)

Phase = Literal[
    "prepare_grand_tichu",
    "prepare_exchange",
    "trick",
    "await_dragon_recipient",
    "round_over",
    "game_over",
]


@dataclass
class GameSession:
    game_id: str
    state: GameState
    round_state: RoundState
    phase: Phase
    grand_tichu_responses: dict[int, bool] = field(default_factory=dict)
    exchange_choices: dict[int, tuple[Card, Card, Card]] = field(default_factory=dict)
    last_round_result: dict[str, object] | None = None


class SessionActionError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


def create_session() -> GameSession:
    game_id = uuid4().hex
    state = GameState()
    init_state(state)
    round_state = new_round_state()
    round_state.deck = make_deck(shuffle=True)
    deal_initial_8(round_state)
    return GameSession(
        game_id=game_id,
        state=state,
        round_state=round_state,
        phase="prepare_grand_tichu",
    )


def get_available_actions(session: GameSession, viewer: int) -> dict[str, bool]:
    round_state = session.round_state
    is_my_turn = session.phase == "trick" and viewer == round_state.current_player_index
    can_pass = False
    can_small_tichu = False
    can_choose_dragon_recipient = (
        session.phase == "await_dragon_recipient" and viewer == round_state.last_played_by
    )

    if is_my_turn:
        can_pass = can_player_pass(round_state, viewer)
        can_small_tichu = can_declare_small_tichu(round_state, viewer)

    return {
        "is_my_turn": is_my_turn,
        "can_play": is_my_turn,
        "can_pass": can_pass,
        "can_declare_small_tichu": can_small_tichu,
        "can_choose_dragon_recipient": can_choose_dragon_recipient,
        "can_declare_grand_tichu": (
            session.phase == "prepare_grand_tichu" and viewer not in session.grand_tichu_responses
        ),
    }


def get_legal_plays_for_viewer(session: GameSession, viewer: int) -> list[list[Card]]:
    if session.phase != "trick" or session.round_state.current_player_index != viewer:
        return []
    return get_legal_plays(session.round_state, viewer)


def combo_summary_payload(combo: ComboInfo | None) -> dict[str, object] | None:
    if combo is None:
        return None

    return {
        "combo_type": combo.combo_type,
        "card_count": combo.card_count,
        "strength": None if combo.strength is None else list(combo.strength),
        "uses_phoenix": combo.uses_phoenix,
        "resolved_ranks": None if combo.resolved_ranks is None else list(combo.resolved_ranks),
    }


def preview_play(
    session: GameSession,
    viewer: int,
    cards: list[Card],
    call_rank: int | None,
) -> dict[str, object]:
    round_state = session.round_state
    current_combo = round_state.current_trick_combo
    if current_combo is None and round_state.current_trick_cards:
        current_combo = evaluate_combo(round_state.current_trick_cards)

    selected_combo = evaluate_combo(cards)
    is_legal_shape = selected_combo is not None
    beats_current_trick = False
    call_rank_in_state = round_state.mahjong_call_rank
    satisfies_mahjong_call = selection_satisfies_mahjong_call(cards, call_rank_in_state)
    can_submit_play = False
    reason_code = "NOT_PLAYABLE"
    message = "play preview is not available right now"

    if session.phase != "trick":
        reason_code = "INVALID_PHASE"
        message = f"request is not allowed during {session.phase}"
    elif round_state.current_player_index != viewer:
        reason_code = "NOT_CURRENT_PLAYER"
        message = "not this player's turn"
    elif not cards:
        reason_code = "NO_CARDS_SELECTED"
        message = "select at least one card"
    elif any(card not in round_state.hands[viewer] for card in cards):
        reason_code = "CARD_NOT_IN_HAND"
        message = "selected card must be in the player's hand"
    elif not is_legal_shape:
        reason_code = "ILLEGAL_SHAPE"
        message = "selected cards are not a legal play"
    else:
        contains_mahjong = any(card.rank == RANK_MAHJONG for card in cards)
        if current_combo is None:
            beats_current_trick = True
        else:
            beats_current_trick = can_beat(current_combo, selected_combo)

        if not beats_current_trick:
            reason_code = "DOES_NOT_BEAT_CURRENT_TRICK"
            message = "selected cards do not beat the current trick"
        elif (
            call_rank_in_state is not None
            and not satisfies_mahjong_call
            and any(
                selection_satisfies_mahjong_call(legal_play, call_rank_in_state)
                for legal_play in get_legal_plays(round_state, viewer)
            )
        ):
            reason_code = "MAHJONG_CALL_NOT_SATISFIED"
            message = "selected cards do not satisfy the mahjong call"
        elif contains_mahjong and not can_declare_mahjong_call(cards, call_rank):
            reason_code = "INVALID_CALL_RANK"
            message = "invalid mahjong call"
        elif call_rank is not None and not contains_mahjong:
            reason_code = "INVALID_CALL_RANK"
            message = "mahjong call can only be declared when playing mahjong"
        else:
            try:
                preview_round_state = deepcopy(round_state)
                play_cards(preview_round_state, viewer, list(cards), call_rank)
            except ValueError as exc:
                reason_code = "INVALID_PLAY"
                message = str(exc)
            else:
                can_submit_play = True
                reason_code = "OK"
                message = "play can be submitted"

    return {
        "is_legal_shape": is_legal_shape,
        "combo_type": None if selected_combo is None else selected_combo.combo_type,
        "is_bomb": (
            False
            if selected_combo is None
            else selected_combo.combo_type in ("bomb_four", "bomb_straight_flush")
        ),
        "beats_current_trick": beats_current_trick,
        "satisfies_mahjong_call": satisfies_mahjong_call,
        "can_submit_play": can_submit_play,
        "reason_code": reason_code,
        "message": message,
        "selected_combo": combo_summary_payload(selected_combo),
        "current_trick_combo": combo_summary_payload(current_combo),
    }


def submit_grand_tichu_response(
    session: GameSession,
    player_index: int,
    declare: bool,
) -> list[dict[str, object]]:
    _clear_stale_round_result(session)
    _require_phase(session, "prepare_grand_tichu")
    if player_index in session.grand_tichu_responses:
        raise SessionActionError("ALREADY_RESPONDED", "grand tichu response already submitted")

    session.grand_tichu_responses[player_index] = declare
    if declare:
        session.round_state.grand_tichu_declarers.add(player_index)

    effects: list[dict[str, object]] = [
        {
            "type": "grand_tichu_declared",
            "player_index": player_index,
            "declare": declare,
        }
    ]
    if len(session.grand_tichu_responses) == 4:
        deal_remaining_6(session.round_state)
        session.phase = "prepare_exchange"
        effects.extend(
            [
                {"type": "remaining_cards_dealt", "count": 6},
                {"type": "phase_changed", "phase": session.phase},
            ]
        )
    return effects


def submit_exchange_choice(
    session: GameSession,
    player_index: int,
    choice: tuple[Card, Card, Card],
) -> list[dict[str, object]]:
    _clear_stale_round_result(session)
    _require_phase(session, "prepare_exchange")
    if player_index in session.exchange_choices:
        raise SessionActionError("ALREADY_RESPONDED", "exchange choice already submitted")

    _validate_exchange_choice(session, player_index, choice)
    session.exchange_choices[player_index] = choice

    effects: list[dict[str, object]] = []
    if len(session.exchange_choices) == 4:
        ordered_choices = [session.exchange_choices[index] for index in range(4)]
        try:
            apply_exchange(session.round_state, ordered_choices)
        except ValueError as exc:
            session.exchange_choices.pop(player_index, None)
            raise SessionActionError("INVALID_ACTION", str(exc)) from exc
        set_leader_by_mahjong(session.round_state)
        start_trick(session.round_state)
        session.phase = "trick"
        effects.extend(
            [
                {"type": "cards_exchanged"},
                {"type": "phase_changed", "phase": session.phase},
                {"type": "turn_changed", "player_index": session.round_state.current_player_index},
            ]
        )
    return effects


def submit_small_tichu(session: GameSession, player_index: int) -> list[dict[str, object]]:
    _clear_stale_round_result(session)
    _require_phase(session, "trick")
    try:
        declare_small_tichu(session.round_state, player_index)
    except ValueError as exc:
        raise SessionActionError("INVALID_ACTION", str(exc)) from exc
    return [{"type": "small_tichu_declared", "player_index": player_index}]


def submit_play(
    session: GameSession,
    player_index: int,
    cards: list[Card],
    call_rank: int | None,
) -> list[dict[str, object]]:
    _clear_stale_round_result(session)
    _require_phase(session, "trick")
    try:
        play_cards(session.round_state, player_index, cards, call_rank)
    except ValueError as exc:
        raise SessionActionError("INVALID_ACTION", str(exc)) from exc

    effects: list[dict[str, object]] = [
        {
            "type": "cards_played",
            "player_index": player_index,
            "cards": _cards_payload(cards),
        }
    ]
    effects.extend(_advance_after_action(session))
    if session.phase == "trick":
        effects.append(
            {
                "type": "turn_changed",
                "player_index": session.round_state.current_player_index,
            }
        )
    return effects


def submit_pass(
    session: GameSession,
    player_index: int,
    dragon_recipient: int | None,
) -> list[dict[str, object]]:
    _clear_stale_round_result(session)
    _require_phase(session, "trick")

    previous_last_played_by = session.round_state.last_played_by
    previous_trick_cards = list(session.round_state.current_trick_cards)
    if _awaits_dragon_recipient_after_pass(session.round_state):
        if session.round_state.current_player_index != player_index:
            raise SessionActionError("INVALID_ACTION", "not this player's turn")
        if not can_player_pass(session.round_state, player_index):
            raise SessionActionError("INVALID_ACTION", "player cannot pass")
        if previous_last_played_by is None:
            raise SessionActionError("INVALID_ACTION", "dragon trick has no winner")

        session.round_state.pass_count_since_last_play += 1
        session.round_state.current_player_index = previous_last_played_by
        session.phase = "await_dragon_recipient"
        return [
            {"type": "player_passed", "player_index": player_index},
            {
                "type": "dragon_recipient_required",
                "winner_index": previous_last_played_by,
                "cards": _cards_payload(previous_trick_cards),
            },
            {"type": "phase_changed", "phase": session.phase},
        ]

    try:
        pass_turn(session.round_state, player_index, dragon_recipient)
    except ValueError as exc:
        raise SessionActionError("INVALID_ACTION", str(exc)) from exc

    effects: list[dict[str, object]] = [{"type": "player_passed", "player_index": player_index}]
    if (
        session.round_state.trick_index > 0
        and not session.round_state.current_trick_cards
        and previous_last_played_by is not None
    ):
        trick_won_effect: dict[str, object] = {
            "type": "trick_won",
            "winner_index": previous_last_played_by,
            "cards": _cards_payload(previous_trick_cards),
        }
        effects.append(trick_won_effect)

    effects.extend(_advance_after_action(session))
    if session.phase == "trick":
        effects.append(
            {
                "type": "turn_changed",
                "player_index": session.round_state.current_player_index,
            }
        )
    return effects


def submit_dragon_recipient(
    session: GameSession,
    player_index: int,
    recipient_index: int,
) -> list[dict[str, object]]:
    _require_phase(session, "await_dragon_recipient")
    if session.round_state.last_played_by != player_index:
        raise SessionActionError("INVALID_ACTION", "only the dragon winner can choose recipient")

    previous_trick_cards = list(session.round_state.current_trick_cards)
    try:
        resolve_trick_end(session.round_state, recipient_index)
    except ValueError as exc:
        raise SessionActionError("INVALID_ACTION", str(exc)) from exc

    session.phase = "trick"
    effects: list[dict[str, object]] = [
        {
            "type": "dragon_recipient_chosen",
            "winner_index": player_index,
            "recipient_index": recipient_index,
        },
        {
            "type": "trick_won",
            "winner_index": player_index,
            "recipient_index": recipient_index,
            "cards": _cards_payload(previous_trick_cards),
        },
    ]
    effects.extend(_advance_after_action(session))
    if session.phase == "trick":
        effects.append(
            {
                "type": "turn_changed",
                "player_index": session.round_state.current_player_index,
            }
        )
    return effects


def _require_phase(session: GameSession, phase: Phase) -> None:
    if session.phase != phase:
        raise SessionActionError("INVALID_PHASE", f"request is not allowed during {session.phase}")


def _validate_exchange_choice(
    session: GameSession,
    player_index: int,
    choice: tuple[Card, Card, Card],
) -> None:
    if len(set(choice)) != 3:
        raise SessionActionError("INVALID_ACTION", "exchange cards must be distinct")

    hand = session.round_state.hands[player_index]
    for card in choice:
        if card not in hand:
            raise SessionActionError("INVALID_ACTION", "exchange card must be in the player's hand")


def _prepare_next_round(session: GameSession) -> None:
    session.round_state = new_round_state()
    session.round_state.deck = make_deck(shuffle=True)
    deal_initial_8(session.round_state)
    session.phase = "prepare_grand_tichu"
    session.grand_tichu_responses.clear()
    session.exchange_choices.clear()


def _store_round_result(session: GameSession, score_deltas: list[int]) -> None:
    session.last_round_result = {
        "end_reason": get_round_end_reason(session.round_state),
        "score_deltas": score_deltas,
        "players_out_order": list(session.round_state.players_out_order),
    }


def _advance_after_action(session: GameSession) -> list[dict[str, object]]:
    if not is_round_over(session.round_state):
        return []

    score_deltas = finalize_round(session.state, session.round_state)
    _store_round_result(session, score_deltas)
    effects: list[dict[str, object]] = [
        {
            "type": "round_finished",
            "end_reason": session.last_round_result["end_reason"],
            "score_deltas": score_deltas,
        }
    ]
    if is_game_over(session.state):
        session.phase = "game_over"
        effects.extend(
            [
                {"type": "phase_changed", "phase": session.phase},
                {"type": "game_finished", "team_scores": list(session.state.team_scores)},
            ]
        )
        return effects

    _prepare_next_round(session)
    effects.extend(
        [
            {"type": "phase_changed", "phase": session.phase},
            {"type": "initial_cards_dealt", "count": 8},
        ]
    )
    return effects


def _cards_payload(cards: list[Card]) -> list[dict[str, int | str]]:
    return [{"suit": card.suit, "rank": card.rank} for card in cards]


def _awaits_dragon_recipient_after_pass(round_state: RoundState) -> bool:
    current_trick_cards = round_state.current_trick_cards
    if len(current_trick_cards) != 1 or current_trick_cards[0].rank != 22:
        return False

    active_count = sum(1 for hand in round_state.hands if hand)
    required_pass_count = max(active_count - 1, 0)
    return round_state.pass_count_since_last_play + 1 >= required_pass_count


def _clear_stale_round_result(session: GameSession) -> None:
    if session.phase in ("prepare_grand_tichu", "prepare_exchange", "trick"):
        session.last_round_result = None
