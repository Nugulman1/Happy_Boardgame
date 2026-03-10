from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, FastAPI, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from tichu import (
    Card,
    GameState,
    RoundState,
    apply_exchange,
    can_declare_small_tichu as can_declare_small_tichu_in_round,
    can_player_pass,
    deal_initial_8,
    deal_remaining_6,
    declare_small_tichu,
    evaluate_combo,
    finalize_round,
    get_legal_plays,
    get_round_end_reason,
    init_state,
    is_game_over,
    is_round_over,
    new_round_state,
    pass_turn,
    play_cards,
    set_leader_by_mahjong,
    start_trick,
)
from tichu.cards import make_deck


Phase = Literal[
    "prepare_grand_tichu",
    "prepare_exchange",
    "trick",
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
    last_round_result: dict | None = None


class ApiError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


class CardModel(BaseModel):
    suit: str
    rank: int


class GrandTichuRequest(BaseModel):
    player_index: int
    declare: bool


class ExchangeRequest(BaseModel):
    player_index: int
    to_left: CardModel
    to_team: CardModel
    to_right: CardModel


class SmallTichuRequest(BaseModel):
    player_index: int


class PlayRequest(BaseModel):
    player_index: int
    cards: list[CardModel]
    call_rank: int | None = None


class PassRequest(BaseModel):
    player_index: int
    dragon_recipient: int | None = None


class PreviewComboRequest(BaseModel):
    viewer: int
    cards: list[CardModel]


router = APIRouter()

_sessions: dict[str, GameSession] = {}


def reset_sessions() -> None:
    _sessions.clear()


def register_tichu_api(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def handle_api_error(_, exc: ApiError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_, exc: RequestValidationError):
        first_error = exc.errors()[0] if exc.errors() else {"msg": "invalid request"}
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": str(first_error.get("msg", "invalid request")),
                }
            },
        )

    app.include_router(router)


def _get_session(game_id: str) -> GameSession:
    session = _sessions.get(game_id)
    if session is None:
        raise ApiError(404, "GAME_NOT_FOUND", "game was not found")
    return session


def _require_phase(session: GameSession, phase: Phase) -> None:
    if session.phase != phase:
        raise ApiError(409, "INVALID_PHASE", f"request is not allowed during {session.phase}")


def _validate_player_index(player_index: int) -> None:
    if not 0 <= player_index < 4:
        raise ApiError(400, "INVALID_PLAYER_INDEX", "player_index must be between 0 and 3")


def _validate_viewer(viewer: int) -> None:
    if not 0 <= viewer < 4:
        raise ApiError(400, "INVALID_VIEWER", "viewer must be between 0 and 3")


def _card_from_model(card_model: CardModel) -> Card:
    try:
        return Card(suit=card_model.suit, rank=card_model.rank)
    except ValueError as exc:
        raise ApiError(400, "INVALID_CARD", str(exc)) from exc


def _cards_from_models(cards: list[CardModel]) -> list[Card]:
    return [_card_from_model(card_model) for card_model in cards]


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


def _validate_exchange_choice(
    session: GameSession,
    player_index: int,
    choice: tuple[Card, Card, Card],
) -> None:
    if len(set(choice)) != 3:
        raise ApiError(409, "INVALID_ACTION", "exchange cards must be distinct")

    hand = session.round_state.hands[player_index]
    for card in choice:
        if card not in hand:
            raise ApiError(409, "INVALID_ACTION", "exchange card must be in the player's hand")


def _table_payload(session: GameSession) -> dict[str, object]:
    round_state = session.round_state
    leader_index: int | None = round_state.leader_index
    current_player_index: int | None = round_state.current_player_index
    if session.phase in ("prepare_grand_tichu", "prepare_exchange"):
        leader_index = None
        current_player_index = None

    return {
        "leader_index": leader_index,
        "current_player_index": current_player_index,
        "trick_index": round_state.trick_index,
        "mahjong_call_rank": round_state.mahjong_call_rank,
        "current_trick_cards": _cards_payload(round_state.current_trick_cards),
    }


def _round_result_payload(session: GameSession) -> dict[str, object] | None:
    if session.phase not in ("round_over", "game_over") or session.last_round_result is None:
        return None
    return session.last_round_result


def _available_actions(session: GameSession, viewer: int) -> dict[str, bool]:
    round_state = session.round_state
    is_my_turn = session.phase == "trick" and viewer == round_state.current_player_index
    can_pass = False
    can_small_tichu = False

    if is_my_turn:
        can_pass = can_player_pass(round_state, viewer)
        can_small_tichu = can_declare_small_tichu_in_round(round_state, viewer)

    return {
        "is_my_turn": is_my_turn,
        "can_play": is_my_turn,
        "can_pass": can_pass,
        "can_declare_small_tichu": can_small_tichu,
        "can_declare_grand_tichu": (
            session.phase == "prepare_grand_tichu" and viewer not in session.grand_tichu_responses
        ),
        "can_start_next_round": session.phase == "round_over",
    }


def _snapshot_response(
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
        "available_actions": _available_actions(session, viewer),
    }
    round_result = _round_result_payload(session)
    if round_result is not None:
        response["round_result"] = round_result
    if effects is not None:
        response["effects"] = effects
    return response


def _new_session() -> GameSession:
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


def _prepare_next_round(session: GameSession) -> None:
    session.round_state = new_round_state()
    session.round_state.deck = make_deck(shuffle=True)
    deal_initial_8(session.round_state)
    session.phase = "prepare_grand_tichu"
    session.grand_tichu_responses.clear()
    session.exchange_choices.clear()
    session.last_round_result = None


def _store_round_result(session: GameSession, score_deltas: list[int]) -> None:
    session.last_round_result = {
        "end_reason": get_round_end_reason(session.round_state),
        "score_deltas": score_deltas,
        "players_out_order": list(session.round_state.players_out_order),
    }
    session.phase = "round_over"


def _advance_after_action(session: GameSession) -> list[dict[str, object]]:
    if not is_round_over(session.round_state):
        return []

    score_deltas = finalize_round(session.state, session.round_state)
    _store_round_result(session, score_deltas)
    return [
        {
            "type": "round_finished",
            "end_reason": session.last_round_result["end_reason"],
            "score_deltas": score_deltas,
        }
    ]


@router.post("/games/tichu", status_code=201)
def create_tichu_game():
    session = _new_session()
    _sessions[session.game_id] = session
    return _snapshot_response(
        session,
        0,
        effects=[
            {"type": "game_created"},
            {"type": "initial_cards_dealt", "count": 8},
        ],
    )


@router.get("/games/{game_id}")
def get_game_snapshot(game_id: str, viewer: int = Query(...)):
    _validate_viewer(viewer)
    session = _get_session(game_id)
    return _snapshot_response(session, viewer)


@router.post("/games/{game_id}/prepare/grand-tichu")
def submit_grand_tichu(game_id: str, payload: GrandTichuRequest):
    session = _get_session(game_id)
    _require_phase(session, "prepare_grand_tichu")
    _validate_player_index(payload.player_index)
    if payload.player_index in session.grand_tichu_responses:
        raise ApiError(409, "ALREADY_RESPONDED", "grand tichu response already submitted")

    session.grand_tichu_responses[payload.player_index] = payload.declare
    if payload.declare:
        session.round_state.grand_tichu_declarers.add(payload.player_index)

    effects: list[dict[str, object]] = [
        {
            "type": "grand_tichu_declared",
            "player_index": payload.player_index,
            "declare": payload.declare,
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

    return _snapshot_response(session, payload.player_index, effects=effects)


@router.post("/games/{game_id}/prepare/exchange")
def submit_exchange(game_id: str, payload: ExchangeRequest):
    session = _get_session(game_id)
    _require_phase(session, "prepare_exchange")
    _validate_player_index(payload.player_index)
    if payload.player_index in session.exchange_choices:
        raise ApiError(409, "ALREADY_RESPONDED", "exchange choice already submitted")

    choice = (
        _card_from_model(payload.to_left),
        _card_from_model(payload.to_team),
        _card_from_model(payload.to_right),
    )
    _validate_exchange_choice(session, payload.player_index, choice)
    session.exchange_choices[payload.player_index] = choice

    effects: list[dict[str, object]] = []
    if len(session.exchange_choices) == 4:
        ordered_choices = [session.exchange_choices[player_index] for player_index in range(4)]
        try:
            apply_exchange(session.round_state, ordered_choices)
        except ValueError as exc:
            session.exchange_choices.pop(payload.player_index, None)
            raise ApiError(409, "INVALID_ACTION", str(exc)) from exc
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

    return _snapshot_response(session, payload.player_index, effects=effects)


@router.post("/games/{game_id}/actions/small-tichu")
def submit_small_tichu(game_id: str, payload: SmallTichuRequest):
    session = _get_session(game_id)
    _require_phase(session, "trick")
    _validate_player_index(payload.player_index)
    try:
        declare_small_tichu(session.round_state, payload.player_index)
    except ValueError as exc:
        raise ApiError(409, "INVALID_ACTION", str(exc)) from exc

    return _snapshot_response(
        session,
        payload.player_index,
        effects=[
            {"type": "small_tichu_declared", "player_index": payload.player_index},
        ],
    )


@router.post("/games/{game_id}/actions/play")
def submit_play(game_id: str, payload: PlayRequest):
    session = _get_session(game_id)
    _require_phase(session, "trick")
    _validate_player_index(payload.player_index)
    cards = _cards_from_models(payload.cards)
    try:
        play_cards(session.round_state, payload.player_index, cards, payload.call_rank)
    except ValueError as exc:
        raise ApiError(409, "INVALID_ACTION", str(exc)) from exc

    effects: list[dict[str, object]] = [
        {
            "type": "cards_played",
            "player_index": payload.player_index,
            "cards": _cards_payload(cards),
        }
    ]
    if session.phase == "trick":
        round_effects = _advance_after_action(session)
        effects.extend(round_effects)
    if session.phase == "trick":
        effects.append(
            {
                "type": "turn_changed",
                "player_index": session.round_state.current_player_index,
            }
        )

    return _snapshot_response(session, payload.player_index, effects=effects)


@router.post("/games/{game_id}/actions/pass")
def submit_pass(game_id: str, payload: PassRequest):
    session = _get_session(game_id)
    _require_phase(session, "trick")
    _validate_player_index(payload.player_index)

    previous_last_played_by = session.round_state.last_played_by
    previous_trick_cards = list(session.round_state.current_trick_cards)
    previous_trick_index = session.round_state.trick_index
    try:
        pass_turn(session.round_state, payload.player_index, payload.dragon_recipient)
    except ValueError as exc:
        raise ApiError(409, "INVALID_ACTION", str(exc)) from exc

    effects: list[dict[str, object]] = [
        {"type": "player_passed", "player_index": payload.player_index}
    ]
    if session.round_state.trick_index > previous_trick_index and previous_last_played_by is not None:
        trick_won_effect = {
            "type": "trick_won",
            "winner_index": previous_last_played_by,
            "cards": _cards_payload(previous_trick_cards),
        }
        if len(previous_trick_cards) == 1 and previous_trick_cards[0].rank == 22:
            trick_won_effect["recipient_index"] = (
                payload.dragon_recipient if payload.dragon_recipient is not None else previous_last_played_by
            )
        effects.append(trick_won_effect)

    if session.phase == "trick":
        round_effects = _advance_after_action(session)
        effects.extend(round_effects)
    if session.phase == "trick":
        effects.append(
            {
                "type": "turn_changed",
                "player_index": session.round_state.current_player_index,
            }
        )

    return _snapshot_response(session, payload.player_index, effects=effects)


@router.post("/games/{game_id}/round/next")
def start_next_round(game_id: str, viewer: int = Query(...)):
    _validate_viewer(viewer)
    session = _get_session(game_id)
    _require_phase(session, "round_over")

    effects: list[dict[str, object]] = []
    if is_game_over(session.state):
        session.phase = "game_over"
        effects.extend(
            [
                {"type": "phase_changed", "phase": session.phase},
                {"type": "game_finished", "team_scores": list(session.state.team_scores)},
            ]
        )
        return _snapshot_response(session, viewer, effects=effects)

    _prepare_next_round(session)
    effects.extend(
        [
            {"type": "phase_changed", "phase": session.phase},
            {"type": "initial_cards_dealt", "count": 8},
        ]
    )
    return _snapshot_response(session, viewer, effects=effects)


@router.get("/games/{game_id}/legal-plays")
def get_legal_plays_endpoint(game_id: str, viewer: int = Query(...)):
    _validate_viewer(viewer)
    session = _get_session(game_id)
    if session.phase != "trick" or session.round_state.current_player_index != viewer:
        return {"plays": []}
    return {
        "plays": [
            _cards_payload(cards)
            for cards in get_legal_plays(session.round_state, viewer)
        ]
    }


@router.post("/games/{game_id}/preview-combo")
def preview_combo(game_id: str, payload: PreviewComboRequest):
    _get_session(game_id)
    _validate_viewer(payload.viewer)
    cards = _cards_from_models(payload.cards)
    combo = evaluate_combo(cards)
    combo_type = combo.combo_type if combo is not None else None
    return {
        "combo_type": combo_type,
        "is_legal_shape": combo is not None,
        "is_bomb": combo_type in ("bomb_four", "bomb_straight_flush"),
    }
