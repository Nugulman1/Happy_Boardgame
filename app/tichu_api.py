from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from uuid import uuid4

from fastapi import APIRouter, FastAPI, Query, WebSocket, WebSocketDisconnect, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

from tichu import Card, evaluate_combo
from tichu.session_service import (
    GameSession,
    SessionActionError,
    combo_summary_payload,
    create_session,
    get_available_actions,
    get_legal_plays_for_viewer,
    preview_play as preview_play_payload,
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


class PlayPreviewRequest(BaseModel):
    viewer: int
    cards: list[CardModel]
    call_rank: int | None = None


class RoomJoinRequest(BaseModel):
    seat_index: int


ACTION_MODELS: dict[str, type[BaseModel]] = {
    "grand_tichu": GrandTichuRequest,
    "exchange": ExchangeRequest,
    "small_tichu": SmallTichuRequest,
    "play": PlayRequest,
    "pass": PassRequest,
    "dragon_recipient": DragonRecipientRequest,
}


router = APIRouter()

_sessions: dict[str, GameSession] = {}
_rooms: dict[str, "RoomSession"] = {}
_game_to_room: dict[str, str] = {}


@dataclass
class SeatState:
    seat_index: int
    claimed: bool = False
    connected: bool = False
    seat_token: str | None = None
    last_seen_at: float | None = None


@dataclass
class RoomSession:
    room_code: str
    status: str = "lobby"
    host_seat_index: int = 0
    seats: list[SeatState] = field(default_factory=lambda: [SeatState(index) for index in range(4)])
    game_id: str | None = None


class RoomSocketManager:
    def __init__(self) -> None:
        self._connections: dict[str, dict[int, WebSocket]] = {}

    def reset(self) -> None:
        self._connections.clear()

    async def connect(self, room_code: str, seat_index: int, websocket: WebSocket) -> None:
        await websocket.accept()
        seats = self._connections.setdefault(room_code, {})
        previous = seats.get(seat_index)
        seats[seat_index] = websocket
        if previous is not None and previous is not websocket:
            try:
                await previous.close(
                    code=status.WS_1000_NORMAL_CLOSURE,
                    reason="replaced by a newer connection",
                )
            except RuntimeError:
                self.disconnect(room_code, seat_index, previous)

    def disconnect(self, room_code: str, seat_index: int, websocket: WebSocket) -> None:
        seats = self._connections.get(room_code)
        if seats is None:
            return
        if seats.get(seat_index) is not websocket:
            return
        del seats[seat_index]
        if not seats:
            del self._connections[room_code]

    def drop_room(self, room_code: str) -> None:
        self._connections.pop(room_code, None)

    async def send_snapshot(self, room: RoomSession, seat_index: int) -> None:
        websocket = self._connections.get(room.room_code, {}).get(seat_index)
        if websocket is None:
            return
        try:
            await websocket.send_json(_room_snapshot_event(room, seat_index))
        except Exception:
            self.disconnect(room.room_code, seat_index, websocket)

    async def broadcast_snapshot(self, room: RoomSession) -> None:
        for seat_index in list(self._connections.get(room.room_code, {}).keys()):
            await self.send_snapshot(room, seat_index)


class SocketManager:
    def __init__(self) -> None:
        self._connections: dict[str, dict[int, WebSocket]] = {}

    def reset(self) -> None:
        self._connections.clear()

    async def connect(self, game_id: str, viewer: int, websocket: WebSocket) -> None:
        await websocket.accept()

        viewers = self._connections.setdefault(game_id, {})
        previous = viewers.get(viewer)
        viewers[viewer] = websocket

        if previous is not None and previous is not websocket:
            try:
                await previous.close(
                    code=status.WS_1000_NORMAL_CLOSURE,
                    reason="replaced by a newer connection",
                )
            except RuntimeError:
                self.disconnect(game_id, viewer, previous)

    def disconnect(self, game_id: str, viewer: int, websocket: WebSocket) -> None:
        viewers = self._connections.get(game_id)
        if viewers is None:
            return
        if viewers.get(viewer) is not websocket:
            return

        del viewers[viewer]
        if not viewers:
            del self._connections[game_id]

    async def send_snapshot(
        self,
        session: GameSession,
        viewer: int,
        *,
        effects: list[dict[str, object]] | None = None,
    ) -> None:
        websocket = self._connections.get(session.game_id, {}).get(viewer)
        if websocket is None:
            return

        payload = _websocket_snapshot_event(session, viewer, effects=effects)
        try:
            await websocket.send_json(payload)
        except Exception:
            self.disconnect(session.game_id, viewer, websocket)

    async def broadcast_snapshot(
        self,
        session: GameSession,
        *,
        effects: list[dict[str, object]] | None = None,
    ) -> None:
        viewers = list(self._connections.get(session.game_id, {}).keys())
        for viewer in viewers:
            await self.send_snapshot(session, viewer, effects=effects)


_socket_manager = SocketManager()
_room_socket_manager = RoomSocketManager()


def reset_sessions() -> None:
    _sessions.clear()
    _rooms.clear()
    _game_to_room.clear()
    _socket_manager.reset()
    _room_socket_manager.reset()


def register_tichu_api(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def handle_api_error(_, exc: ApiError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_, exc: RequestValidationError):
        return JSONResponse(
            status_code=400,
            content={"error": _validation_error_payload(exc)},
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


def _round_result_payload(session: GameSession) -> dict[str, object] | None:
    if session.last_round_result is None:
        return None
    return session.last_round_result


def _validation_error_payload(exc: ValidationError | RequestValidationError) -> dict[str, str]:
    first_error = exc.errors()[0] if exc.errors() else {"msg": "invalid request"}
    return {
        "code": "INVALID_REQUEST",
        "message": str(first_error.get("msg", "invalid request")),
    }


def _generate_room_code() -> str:
    while True:
        code = uuid4().hex[:6].upper()
        if code not in _rooms:
            return code


def _generate_seat_token() -> str:
    return uuid4().hex


def _get_room(room_code: str) -> RoomSession:
    room = _rooms.get(room_code.upper())
    if room is None:
        raise ApiError(404, "ROOM_NOT_FOUND", "room was not found")
    return room


def _validate_room_seat_index(seat_index: int) -> None:
    if not 0 <= seat_index < 4:
        raise ApiError(400, "INVALID_SEAT_INDEX", "seat_index must be between 0 and 3")


def _find_room_seat_by_token(room: RoomSession, seat_token: str | None) -> SeatState:
    if not seat_token:
        raise ApiError(401, "SEAT_TOKEN_REQUIRED", "seat_token is required")
    for seat in room.seats:
        if seat.claimed and seat.seat_token == seat_token:
            return seat
    raise ApiError(401, "INVALID_SEAT_TOKEN", "seat_token is invalid")


def _mark_seat_connected(room: RoomSession, seat_index: int, connected: bool) -> None:
    seat = room.seats[seat_index]
    seat.connected = connected
    seat.last_seen_at = time()


def _can_start_room(room: RoomSession, seat_index: int) -> bool:
    return room.status == "lobby" and seat_index == room.host_seat_index and all(
        seat.claimed for seat in room.seats
    )


def _room_snapshot_payload(room: RoomSession, seat_index: int) -> dict[str, object]:
    return {
        "room_code": room.room_code,
        "status": room.status,
        "host_seat_index": room.host_seat_index,
        "my_seat_index": seat_index,
        "game_id": room.game_id,
        "seats": [
            {
                "seat_index": seat.seat_index,
                "claimed": seat.claimed,
                "connected": seat.connected,
            }
            for seat in room.seats
        ],
        "can_start": _can_start_room(room, seat_index),
    }


def _room_response(room: RoomSession, seat_index: int, seat_token: str) -> dict[str, object]:
    return {
        "room_code": room.room_code,
        "seat_index": seat_index,
        "seat_token": seat_token,
        "room_snapshot": _room_snapshot_payload(room, seat_index),
    }


def _room_closed_response() -> dict[str, object]:
    return {"room_closed": True}


def _room_snapshot_event(room: RoomSession, seat_index: int) -> dict[str, object]:
    return {
        "type": "room_snapshot",
        "room_code": room.room_code,
        "room_snapshot": _room_snapshot_payload(room, seat_index),
    }


def _authenticated_player_index(session: GameSession, seat_token: str | None) -> int | None:
    if session.seat_tokens_by_player is None:
        return None
    if not seat_token:
        raise ApiError(401, "SEAT_TOKEN_REQUIRED", "seat_token is required")
    for player_index, token in session.seat_tokens_by_player.items():
        if token == seat_token:
            return player_index
    raise ApiError(401, "INVALID_SEAT_TOKEN", "seat_token is invalid")


def _require_viewer_access(session: GameSession, viewer: int, seat_token: str | None) -> None:
    player_index = _authenticated_player_index(session, seat_token)
    if player_index is not None and player_index != viewer:
        raise ApiError(403, "SEAT_TOKEN_MISMATCH", "viewer does not match the authenticated seat")


def _require_player_access(session: GameSession, player_index: int, seat_token: str | None) -> None:
    authenticated_player = _authenticated_player_index(session, seat_token)
    if authenticated_player is not None and authenticated_player != player_index:
        raise ApiError(403, "SEAT_TOKEN_MISMATCH", "player_index does not match the authenticated seat")


def _player_index_from_action_payload(payload: BaseModel) -> int:
    player_index = getattr(payload, "player_index", None)
    if isinstance(player_index, int):
        return player_index
    raise ApiError(400, "INVALID_REQUEST", "action payload must include player_index")


def _get_room_for_game(session: GameSession) -> RoomSession | None:
    room_code = _game_to_room.get(session.game_id)
    if room_code is None:
        return None
    return _rooms.get(room_code)


def _sync_room_status_for_session(session: GameSession) -> None:
    room = _get_room_for_game(session)
    if room is None:
        return
    room.status = "finished" if session.phase == "game_over" else "in_game"


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


def _api_error_payload(exc: ApiError) -> dict[str, str]:
    return {"code": exc.code, "message": exc.message}


def _coerce_action_payload(action: str, payload: object) -> BaseModel:
    model_cls = ACTION_MODELS.get(action)
    if model_cls is None:
        raise ApiError(400, "INVALID_ACTION", f"unsupported action: {action}")
    if not isinstance(payload, dict):
        raise ApiError(400, "INVALID_REQUEST", "payload must be an object")
    try:
        return model_cls.model_validate(payload)
    except ValidationError as exc:
        raise ApiError(400, "INVALID_REQUEST", _validation_error_payload(exc)["message"]) from exc


def _execute_session_action(
    session: GameSession,
    action: str,
    payload: BaseModel | dict[str, object],
) -> tuple[int, list[dict[str, object]]]:
    parsed_payload = payload if isinstance(payload, BaseModel) else _coerce_action_payload(action, payload)

    if action == "grand_tichu":
        typed_payload = parsed_payload
        assert isinstance(typed_payload, GrandTichuRequest)
        _validate_player_index(typed_payload.player_index)
        try:
            effects = submit_grand_tichu_response(session, typed_payload.player_index, typed_payload.declare)
        except SessionActionError as exc:
            _raise_action_error(exc)
        return typed_payload.player_index, effects

    if action == "exchange":
        typed_payload = parsed_payload
        assert isinstance(typed_payload, ExchangeRequest)
        _validate_player_index(typed_payload.player_index)
        choice = (
            _card_from_model(typed_payload.to_left),
            _card_from_model(typed_payload.to_team),
            _card_from_model(typed_payload.to_right),
        )
        try:
            effects = submit_exchange_choice(session, typed_payload.player_index, choice)
        except SessionActionError as exc:
            _raise_action_error(exc)
        return typed_payload.player_index, effects

    if action == "small_tichu":
        typed_payload = parsed_payload
        assert isinstance(typed_payload, SmallTichuRequest)
        _validate_player_index(typed_payload.player_index)
        try:
            effects = submit_small_tichu_action(session, typed_payload.player_index)
        except SessionActionError as exc:
            _raise_action_error(exc)
        return typed_payload.player_index, effects

    if action == "play":
        typed_payload = parsed_payload
        assert isinstance(typed_payload, PlayRequest)
        _validate_player_index(typed_payload.player_index)
        cards = _cards_from_models(typed_payload.cards)
        try:
            effects = submit_play_action(session, typed_payload.player_index, cards, typed_payload.call_rank)
        except SessionActionError as exc:
            _raise_action_error(exc)
        return typed_payload.player_index, effects

    if action == "pass":
        typed_payload = parsed_payload
        assert isinstance(typed_payload, PassRequest)
        _validate_player_index(typed_payload.player_index)
        try:
            effects = submit_pass_action(session, typed_payload.player_index, None)
        except SessionActionError as exc:
            _raise_action_error(exc)
        return typed_payload.player_index, effects

    if action == "dragon_recipient":
        typed_payload = parsed_payload
        assert isinstance(typed_payload, DragonRecipientRequest)
        _validate_player_index(typed_payload.player_index)
        _validate_player_index(typed_payload.recipient_index)
        try:
            effects = submit_dragon_recipient_action(
                session,
                typed_payload.player_index,
                typed_payload.recipient_index,
            )
        except SessionActionError as exc:
            _raise_action_error(exc)
        return typed_payload.player_index, effects

    raise ApiError(400, "INVALID_ACTION", f"unsupported action: {action}")


def _websocket_snapshot_event(
    session: GameSession,
    viewer: int,
    *,
    effects: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "type": "snapshot",
        "game_id": session.game_id,
        "viewer": viewer,
        "snapshot": _snapshot_response(session, viewer, effects=effects),
    }


def _websocket_action_result_event(
    request_id: int,
    action: str,
    effects: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "type": "action_result",
        "request_id": request_id,
        "action": action,
        "ok": True,
        "effects": effects,
    }


def _websocket_action_error_event(
    request_id: int | None,
    action: str | None,
    error: dict[str, str],
) -> dict[str, object]:
    return {
        "type": "action_error",
        "request_id": request_id,
        "action": action,
        "error": error,
    }


async def _send_websocket_action_error(
    websocket: WebSocket,
    request_id: int | None,
    action: str | None,
    error: dict[str, str],
) -> None:
    await websocket.send_json(_websocket_action_error_event(request_id, action, error))


@router.post("/rooms/tichu", status_code=201)
def create_tichu_room():
    room_code = _generate_room_code()
    room = RoomSession(room_code=room_code)
    host_token = _generate_seat_token()
    host_seat = room.seats[0]
    host_seat.claimed = True
    host_seat.seat_token = host_token
    _mark_seat_connected(room, 0, True)
    _rooms[room_code] = room
    return _room_response(room, 0, host_token)


@router.post("/rooms/{room_code}/join")
async def join_tichu_room(room_code: str, payload: RoomJoinRequest):
    room = _get_room(room_code)
    if room.status != "lobby":
        raise ApiError(409, "ROOM_NOT_JOINABLE", "room is not accepting new players")
    _validate_room_seat_index(payload.seat_index)
    seat = room.seats[payload.seat_index]
    if seat.claimed:
        raise ApiError(409, "SEAT_TAKEN", "seat is already claimed")

    seat.claimed = True
    seat.seat_token = _generate_seat_token()
    _mark_seat_connected(room, payload.seat_index, True)
    await _room_socket_manager.broadcast_snapshot(room)
    return _room_response(room, payload.seat_index, seat.seat_token)


@router.get("/rooms/{room_code}")
def get_room_snapshot(room_code: str, seat_token: str = Query(...)):
    room = _get_room(room_code)
    seat = _find_room_seat_by_token(room, seat_token)
    return _room_response(room, seat.seat_index, seat_token)


@router.post("/rooms/{room_code}/start")
async def start_room_game(room_code: str, seat_token: str = Query(...)):
    room = _get_room(room_code)
    seat = _find_room_seat_by_token(room, seat_token)
    if room.status != "lobby":
        raise ApiError(409, "ROOM_NOT_IN_LOBBY", "room is not in lobby")
    if seat.seat_index != room.host_seat_index:
        raise ApiError(403, "NOT_ROOM_HOST", "only the host can start the room")
    if not all(candidate.claimed for candidate in room.seats):
        raise ApiError(409, "ROOM_NOT_READY", "all four seats must be claimed before starting")

    seat_tokens_by_player = {
        claimed_seat.seat_index: claimed_seat.seat_token
        for claimed_seat in room.seats
        if claimed_seat.seat_token is not None
    }
    session = create_session(seat_tokens_by_player=seat_tokens_by_player)
    _sessions[session.game_id] = session
    room.game_id = session.game_id
    room.status = "in_game"
    _game_to_room[session.game_id] = room.room_code
    await _room_socket_manager.broadcast_snapshot(room)
    return _room_response(room, seat.seat_index, seat_token)


@router.post("/rooms/{room_code}/leave")
async def leave_room(room_code: str, seat_token: str = Query(...)):
    room = _get_room(room_code)
    seat = _find_room_seat_by_token(room, seat_token)
    if room.status != "lobby":
        raise ApiError(409, "ROOM_NOT_IN_LOBBY", "leave is only available in lobby")

    if seat.seat_index == room.host_seat_index:
        del _rooms[room.room_code]
        _room_socket_manager.drop_room(room.room_code)
        return _room_closed_response()

    seat.claimed = False
    seat.connected = False
    seat.seat_token = None
    seat.last_seen_at = time()
    await _room_socket_manager.broadcast_snapshot(room)
    return {"room_closed": False, "room_snapshot": _room_snapshot_payload(room, seat.seat_index)}


@router.websocket("/ws/rooms/{room_code}")
async def room_socket(websocket: WebSocket, room_code: str, seat_token: str = Query(...)):
    room: RoomSession | None = None
    seat: SeatState | None = None
    try:
        room = _get_room(room_code)
        if room.status != "lobby":
            raise ApiError(409, "ROOM_NOT_IN_LOBBY", "room socket is only available in lobby")
        seat = _find_room_seat_by_token(room, seat_token)
    except ApiError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    assert room is not None
    assert seat is not None
    _mark_seat_connected(room, seat.seat_index, True)
    await _room_socket_manager.connect(room.room_code, seat.seat_index, websocket)
    await _room_socket_manager.broadcast_snapshot(room)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        _room_socket_manager.disconnect(room.room_code, seat.seat_index, websocket)
        if room.room_code in _rooms and room.status == "lobby":
            _mark_seat_connected(room, seat.seat_index, False)
            await _room_socket_manager.broadcast_snapshot(room)


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
def get_game_snapshot(game_id: str, viewer: int = Query(...), seat_token: str | None = Query(None)):
    _validate_viewer(viewer)
    session = _get_session(game_id)
    _require_viewer_access(session, viewer, seat_token)
    return _snapshot_response(session, viewer)


@router.websocket("/ws/games/{game_id}")
async def game_socket(
    websocket: WebSocket,
    game_id: str,
    viewer: int = Query(...),
    seat_token: str | None = Query(None),
):
    room: RoomSession | None = None
    try:
        _validate_viewer(viewer)
        session = _get_session(game_id)
        _require_viewer_access(session, viewer, seat_token)
    except ApiError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    room = _get_room_for_game(session)
    if room is not None:
        _mark_seat_connected(room, viewer, True)
    await _socket_manager.connect(game_id, viewer, websocket)
    try:
        await websocket.send_json(_websocket_snapshot_event(session, viewer))
        while True:
            message = await websocket.receive_json()
            request_id: int | None = None
            action: str | None = None

            if not isinstance(message, dict):
                await _send_websocket_action_error(
                    websocket,
                    request_id,
                    action,
                    {"code": "INVALID_REQUEST", "message": "message must be an object"},
                )
                continue

            raw_request_id = message.get("request_id")
            if isinstance(raw_request_id, int) and not isinstance(raw_request_id, bool):
                request_id = raw_request_id
            action = message.get("action") if isinstance(message.get("action"), str) else None

            if message.get("type") != "action":
                await _send_websocket_action_error(
                    websocket,
                    request_id,
                    action,
                    {"code": "INVALID_REQUEST", "message": "unsupported websocket message type"},
                )
                continue

            if request_id is None:
                await _send_websocket_action_error(
                    websocket,
                    request_id,
                    action,
                    {"code": "INVALID_REQUEST", "message": "request_id must be an integer"},
                )
                continue

            if action is None:
                await _send_websocket_action_error(
                    websocket,
                    request_id,
                    action,
                    {"code": "INVALID_REQUEST", "message": "action must be a string"},
                )
                continue

            try:
                current_session = _get_session(game_id)
                parsed_payload = _coerce_action_payload(action, message.get("payload"))
                _require_player_access(current_session, _player_index_from_action_payload(parsed_payload), seat_token)
                _, effects = _execute_session_action(current_session, action, parsed_payload)
                _sync_room_status_for_session(current_session)
            except ApiError as exc:
                await _send_websocket_action_error(websocket, request_id, action, _api_error_payload(exc))
                continue

            try:
                await websocket.send_json(_websocket_action_result_event(request_id, action, effects))
            except Exception:
                _socket_manager.disconnect(game_id, viewer, websocket)
            await _socket_manager.broadcast_snapshot(current_session, effects=effects)
    except WebSocketDisconnect:
        pass
    finally:
        _socket_manager.disconnect(game_id, viewer, websocket)
        if room is not None:
            _mark_seat_connected(room, viewer, False)


@router.post("/games/{game_id}/prepare/grand-tichu")
async def submit_grand_tichu(game_id: str, payload: GrandTichuRequest, seat_token: str | None = Query(None)):
    session = _get_session(game_id)
    _require_player_access(session, payload.player_index, seat_token)
    player_index, effects = _execute_session_action(session, "grand_tichu", payload)
    _sync_room_status_for_session(session)
    response = _snapshot_response(session, player_index, effects=effects)
    await _socket_manager.broadcast_snapshot(session, effects=effects)
    return response


@router.post("/games/{game_id}/prepare/exchange")
async def submit_exchange(game_id: str, payload: ExchangeRequest, seat_token: str | None = Query(None)):
    session = _get_session(game_id)
    _require_player_access(session, payload.player_index, seat_token)
    player_index, effects = _execute_session_action(session, "exchange", payload)
    _sync_room_status_for_session(session)
    response = _snapshot_response(session, player_index, effects=effects)
    await _socket_manager.broadcast_snapshot(session, effects=effects)
    return response


@router.post("/games/{game_id}/actions/small-tichu")
async def submit_small_tichu(game_id: str, payload: SmallTichuRequest, seat_token: str | None = Query(None)):
    session = _get_session(game_id)
    _require_player_access(session, payload.player_index, seat_token)
    player_index, effects = _execute_session_action(session, "small_tichu", payload)
    _sync_room_status_for_session(session)
    response = _snapshot_response(session, player_index, effects=effects)
    await _socket_manager.broadcast_snapshot(session, effects=effects)
    return response


@router.post("/games/{game_id}/actions/play")
async def submit_play(game_id: str, payload: PlayRequest, seat_token: str | None = Query(None)):
    session = _get_session(game_id)
    _require_player_access(session, payload.player_index, seat_token)
    player_index, effects = _execute_session_action(session, "play", payload)
    _sync_room_status_for_session(session)
    response = _snapshot_response(session, player_index, effects=effects)
    await _socket_manager.broadcast_snapshot(session, effects=effects)
    return response


@router.post("/games/{game_id}/actions/pass")
async def submit_pass(game_id: str, payload: PassRequest, seat_token: str | None = Query(None)):
    session = _get_session(game_id)
    _require_player_access(session, payload.player_index, seat_token)
    player_index, effects = _execute_session_action(session, "pass", payload)
    _sync_room_status_for_session(session)
    response = _snapshot_response(session, player_index, effects=effects)
    await _socket_manager.broadcast_snapshot(session, effects=effects)
    return response


@router.post("/games/{game_id}/actions/dragon-recipient")
async def submit_dragon_recipient(
    game_id: str,
    payload: DragonRecipientRequest,
    seat_token: str | None = Query(None),
):
    session = _get_session(game_id)
    _require_player_access(session, payload.player_index, seat_token)
    player_index, effects = _execute_session_action(session, "dragon_recipient", payload)
    _sync_room_status_for_session(session)
    response = _snapshot_response(session, player_index, effects=effects)
    await _socket_manager.broadcast_snapshot(session, effects=effects)
    return response


@router.get("/games/{game_id}/legal-plays")
def get_legal_plays_endpoint(
    game_id: str,
    viewer: int = Query(...),
    seat_token: str | None = Query(None),
):
    _validate_viewer(viewer)
    session = _get_session(game_id)
    _require_viewer_access(session, viewer, seat_token)
    return {"plays": [_cards_payload(cards) for cards in get_legal_plays_for_viewer(session, viewer)]}


@router.post("/games/{game_id}/play-preview")
def play_preview(game_id: str, payload: PlayPreviewRequest, seat_token: str | None = Query(None)):
    session = _get_session(game_id)
    _validate_viewer(payload.viewer)
    _require_viewer_access(session, payload.viewer, seat_token)
    cards = _cards_from_models(payload.cards)
    return preview_play_payload(session, payload.viewer, cards, payload.call_rank)
