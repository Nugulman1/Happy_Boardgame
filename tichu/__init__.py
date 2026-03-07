"""
티츄 게임 로직. 1단계: 카드·덱·상태 정의. 2단계: 준비 단계.
"""
from tichu.cards import Card, make_deck, shuffle_deck, card_points
from tichu.combo_info import ComboInfo, evaluate_combo, can_beat
from tichu.state import GameState, RoundState, init_state, new_round_state, team_id
from tichu.prepare import (
    sort_hand,
    deal_initial_8,
    deal_remaining_6,
    apply_exchange,
    set_leader_by_mahjong,
    run_prepare_phase,
)
from tichu.game_loop import is_game_over, run_game

__all__ = [
    "Card",
    "make_deck",
    "shuffle_deck",
    "card_points",
    "ComboInfo",
    "evaluate_combo",
    "can_beat",
    "GameState",
    "RoundState",
    "init_state",
    "new_round_state",
    "team_id",
    "sort_hand",
    "deal_initial_8",
    "deal_remaining_6",
    "apply_exchange",
    "set_leader_by_mahjong",
    "run_prepare_phase",
    "is_game_over",
    "run_game",
]
