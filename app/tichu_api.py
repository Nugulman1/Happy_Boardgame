from __future__ import annotations

from fastapi import APIRouter, FastAPI, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from tichu import Card
from tichu.session_service import (
    GameSession,
    SessionActionError,
    create_session,
    get_available_actions,
    get_legal_plays_for_viewer,
    preview_combo as preview_combo_payload,
    submit_dragon_recipient as submit_dragon_recipient_action,
    submit_exchange_choice,
    submit_grand_tichu_response,
    submit_pass as submit_pass_action,
    submit_play as submit_play_action,
    submit_small_tichu as submit_small_tichu_action,
)


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


class DragonRecipientRequest(BaseModel):
    player_index: int
    recipient_index: int


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
    if session.last_round_result is None:
        return None
    return session.last_round_result


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
        "available_actions": get_available_actions(session, viewer),
    }
    round_result = _round_result_payload(session)
    if round_result is not None:
        response["round_result"] = round_result
    if effects is not None:
        response["effects"] = effects
    return response


def _raise_action_error(exc: SessionActionError) -> None:
    code_to_status = {
        "INVALID_PHASE": 409,
        "ALREADY_RESPONDED": 409,
        "INVALID_ACTION": 409,
    }
    raise ApiError(code_to_status.get(exc.code, 400), exc.code, exc.message) from exc


@router.post("/games/tichu", status_code=201)
def create_tichu_game():
    session = create_session()
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
    _validate_player_index(payload.player_index)
    try:
        effects = submit_grand_tichu_response(session, payload.player_index, payload.declare)
    except SessionActionError as exc:
        _raise_action_error(exc)

    return _snapshot_response(session, payload.player_index, effects=effects)


@router.post("/games/{game_id}/prepare/exchange")
def submit_exchange(game_id: str, payload: ExchangeRequest):
    session = _get_session(game_id)
    _validate_player_index(payload.player_index)

    choice = (
        _card_from_model(payload.to_left),
        _card_from_model(payload.to_team),
        _card_from_model(payload.to_right),
    )
    try:
        effects = submit_exchange_choice(session, payload.player_index, choice)
    except SessionActionError as exc:
        _raise_action_error(exc)

    return _snapshot_response(session, payload.player_index, effects=effects)


@router.post("/games/{game_id}/actions/small-tichu")
def submit_small_tichu(game_id: str, payload: SmallTichuRequest):
    session = _get_session(game_id)
    _validate_player_index(payload.player_index)
    try:
        effects = submit_small_tichu_action(session, payload.player_index)
    except SessionActionError as exc:
        _raise_action_error(exc)

    return _snapshot_response(session, payload.player_index, effects=effects)


@router.post("/games/{game_id}/actions/play")
def submit_play(game_id: str, payload: PlayRequest):
    session = _get_session(game_id)
    _validate_player_index(payload.player_index)
    cards = _cards_from_models(payload.cards)
    try:
        effects = submit_play_action(session, payload.player_index, cards, payload.call_rank)
    except SessionActionError as exc:
        _raise_action_error(exc)

    return _snapshot_response(session, payload.player_index, effects=effects)


@router.post("/games/{game_id}/actions/pass")
def submit_pass(game_id: str, payload: PassRequest):
    session = _get_session(game_id)
    _validate_player_index(payload.player_index)
    try:
        effects = submit_pass_action(session, payload.player_index, None)
    except SessionActionError as exc:
        _raise_action_error(exc)

    return _snapshot_response(session, payload.player_index, effects=effects)


@router.post("/games/{game_id}/actions/dragon-recipient")
def submit_dragon_recipient(game_id: str, payload: DragonRecipientRequest):
    session = _get_session(game_id)
    _validate_player_index(payload.player_index)
    _validate_player_index(payload.recipient_index)
    try:
        effects = submit_dragon_recipient_action(session, payload.player_index, payload.recipient_index)
    except SessionActionError as exc:
        _raise_action_error(exc)
    return _snapshot_response(session, payload.player_index, effects=effects)


@router.get("/games/{game_id}/legal-plays")
def get_legal_plays_endpoint(game_id: str, viewer: int = Query(...)):
    _validate_viewer(viewer)
    session = _get_session(game_id)
    return {"plays": [_cards_payload(cards) for cards in get_legal_plays_for_viewer(session, viewer)]}


@router.post("/games/{game_id}/preview-combo")
def preview_combo(game_id: str, payload: PreviewComboRequest):
    _get_session(game_id)
    _validate_viewer(payload.viewer)
    cards = _cards_from_models(payload.cards)
    return preview_combo_payload(cards)
