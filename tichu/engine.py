"""
내부 엔진 v1. 프론트엔드/네트워크 없이 라운드와 액션 흐름을 오케스트레이션한다.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeAlias

from .cards import Card, make_deck
from .game_loop import finalize_round, is_game_over
from .prepare import apply_exchange, deal_initial_8, deal_remaining_6, set_leader_by_mahjong
from .state import GameState, RoundState, init_state, new_round_state
from .trick import (
    declare_small_tichu,
    is_round_over,
    pass_turn,
    play_cards,
    start_trick,
)

PHASE_IDLE = "idle"
PHASE_AWAIT_GRAND_TICHU = "await_grand_tichu"
PHASE_AWAIT_EXCHANGE = "await_exchange"
PHASE_AWAIT_TURN_ACTION = "await_turn_action"
PHASE_ROUND_FINISHED = "round_finished"
PHASE_GAME_FINISHED = "game_finished"


@dataclass(frozen=True)
class DeclareGrandTichuAction:
    player_indices: list[int] | set[int]


@dataclass(frozen=True)
class ApplyExchangeAction:
    choices: list[tuple[Card, Card, Card]]


@dataclass(frozen=True)
class DeclareSmallTichuAction:
    player_index: int


@dataclass(frozen=True)
class PlayCardsAction:
    player_index: int
    selected_cards: list[Card]
    call_rank: int | None = None


@dataclass(frozen=True)
class PassTurnAction:
    player_index: int
    dragon_recipient: int | None = None


EngineAction: TypeAlias = (
    DeclareGrandTichuAction
    | ApplyExchangeAction
    | DeclareSmallTichuAction
    | PlayCardsAction
    | PassTurnAction
)


@dataclass
class EngineState:
    game_state: GameState = field(default_factory=GameState)
    round_state: RoundState | None = None
    phase: str = PHASE_IDLE
    last_score_deltas: list[int] | None = None


@dataclass(frozen=True)
class EngineSnapshot:
    team_scores: list[int]
    round_index: int
    has_round: bool
    phase: str
    leader_index: int | None
    current_player_index: int | None
    current_trick_cards: list[Card]
    players_out_order: list[int]
    is_round_over: bool
    is_game_over: bool
    last_score_deltas: list[int] | None


def create_engine() -> EngineState:
    """새 내부 엔진 런타임을 생성한다."""

    return EngineState()


def start_game(engine: EngineState) -> None:
    """게임 상태를 초기화하고 active round 를 비운다."""

    init_state(engine.game_state)
    engine.round_state = None
    engine.phase = PHASE_IDLE
    engine.last_score_deltas = None


def start_round(engine: EngineState) -> RoundState:
    """
    새 라운드를 시작하고 grand tichu 입력 대기 상태까지 진행한다.
    초기 8장 배분까지만 수행하고, 이후 결정은 submit_action 으로 받는다.
    """

    if engine.phase == PHASE_GAME_FINISHED or is_game_over(engine.game_state):
        raise ValueError("game is already over")
    if engine.round_state is not None and engine.phase in (
        PHASE_AWAIT_GRAND_TICHU,
        PHASE_AWAIT_EXCHANGE,
        PHASE_AWAIT_TURN_ACTION,
    ):
        raise ValueError("round is already in progress")

    round_state = new_round_state()
    round_state.grand_tichu_declarers = set()
    round_state.deck = make_deck(shuffle=True)
    deal_initial_8(round_state)

    engine.round_state = round_state
    engine.phase = PHASE_AWAIT_GRAND_TICHU
    engine.last_score_deltas = None
    return round_state


def can_submit_action(engine: EngineState, action: EngineAction) -> bool:
    """현재 phase 에서 액션을 받을 수 있는지 여부를 반환한다."""

    try:
        _validate_action(engine, action)
    except ValueError:
        return False
    return True


def submit_action(engine: EngineState, action: EngineAction) -> EngineSnapshot:
    """액션 1개를 적용하고 업데이트된 엔진 스냅샷을 반환한다."""

    round_state = _get_active_round(engine)
    _validate_action(engine, action)

    if isinstance(action, DeclareGrandTichuAction):
        round_state.grand_tichu_declarers = _validate_player_indices(action.player_indices)
        deal_remaining_6(round_state)
        engine.phase = PHASE_AWAIT_EXCHANGE
    elif isinstance(action, ApplyExchangeAction):
        _validate_exchange_choices(action.choices)
        apply_exchange(round_state, action.choices)
        set_leader_by_mahjong(round_state)
        start_trick(round_state)
        engine.phase = PHASE_AWAIT_TURN_ACTION
    elif isinstance(action, DeclareSmallTichuAction):
        declare_small_tichu(round_state, action.player_index)
    elif isinstance(action, PlayCardsAction):
        play_cards(round_state, action.player_index, action.selected_cards, action.call_rank)
        _finalize_round_if_needed(engine)
    elif isinstance(action, PassTurnAction):
        pass_turn(round_state, action.player_index, action.dragon_recipient)
        _finalize_round_if_needed(engine)
    else:
        raise ValueError("unsupported action")

    return get_engine_snapshot(engine)


def get_engine_snapshot(engine: EngineState) -> EngineSnapshot:
    """디버깅/테스트용 런타임 스냅샷을 반환한다."""

    round_state = engine.round_state
    return EngineSnapshot(
        team_scores=list(engine.game_state.team_scores),
        round_index=engine.game_state.round_index,
        has_round=round_state is not None,
        phase=engine.phase,
        leader_index=None if round_state is None else round_state.leader_index,
        current_player_index=None if round_state is None else round_state.current_player_index,
        current_trick_cards=[] if round_state is None else list(round_state.current_trick_cards),
        players_out_order=[] if round_state is None else list(round_state.players_out_order),
        is_round_over=False if round_state is None else is_round_over(round_state),
        is_game_over=is_game_over(engine.game_state),
        last_score_deltas=None if engine.last_score_deltas is None else list(engine.last_score_deltas),
    )


def _get_active_round(engine: EngineState) -> RoundState:
    """active round 존재 여부를 확인하고 반환한다."""

    if engine.round_state is None:
        raise ValueError("no active round")
    return engine.round_state


def _validate_action(engine: EngineState, action: EngineAction) -> None:
    """현재 phase 에서 허용된 액션인지 검사한다."""

    if engine.round_state is None:
        raise ValueError("no active round")

    if isinstance(action, DeclareGrandTichuAction):
        if engine.phase != PHASE_AWAIT_GRAND_TICHU:
            raise ValueError("grand tichu action is not allowed in the current phase")
        return
    if isinstance(action, ApplyExchangeAction):
        if engine.phase != PHASE_AWAIT_EXCHANGE:
            raise ValueError("exchange action is not allowed in the current phase")
        return
    if isinstance(action, (DeclareSmallTichuAction, PlayCardsAction, PassTurnAction)):
        if engine.phase != PHASE_AWAIT_TURN_ACTION:
            raise ValueError("turn action is not allowed in the current phase")
        return

    raise ValueError("unsupported action")


def _validate_player_indices(player_indices: list[int] | set[int]) -> set[int]:
    """grand tichu 선언 플레이어 인덱스를 검사해 set 으로 반환한다."""

    validated = set(player_indices)
    for player_index in validated:
        if not 0 <= player_index < 4:
            raise ValueError("player index must be between 0 and 3")
    return validated


def _validate_exchange_choices(choices: list[tuple[Card, Card, Card]]) -> None:
    """교환 입력 기본 형태를 검사한다."""

    if len(choices) != 4:
        raise ValueError("exchange choices must include four players")


def _finalize_round_if_needed(engine: EngineState) -> None:
    """라운드 종료 시 점수 반영과 phase 전이를 처리한다."""

    round_state = _get_active_round(engine)
    if not is_round_over(round_state):
        return

    engine.last_score_deltas = finalize_round(engine.game_state, round_state)
    if is_game_over(engine.game_state):
        engine.phase = PHASE_GAME_FINISHED
    else:
        # 라운드 결과를 조회할 수 있도록 종료된 라운드 상태는 유지한다.
        engine.phase = PHASE_ROUND_FINISHED
