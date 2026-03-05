"""
메인 게임 루프. 한 게임 = while 하나. 공통 설계 §1.
"""
from .state import GameState, init_state, new_round_state
from .prepare import run_prepare_phase


def is_game_over(state: GameState) -> bool:
    """
    게임 종료 여부. 팀 점수 1000점 도달 시 True.
    입력: state (읽기만). 출력: bool. 전제조건: 없음. 수정하는 상태: 없음.
    """
    return max(state.team_scores) >= 1000


def run_game(state: GameState) -> None:
    """
    한 게임 전체 실행. init_state 후 라운드를 반복하며 준비 단계 실행.
    입력: state (수정 대상). 출력: 없음. 수정하는 상태: state 및 라운드 내부.
    """
    init_state(state)
    while not is_game_over(state):
        round_state = new_round_state()
        run_prepare_phase(round_state)
        # run_trick_phase(round_state, state)  # 3단계~
        # apply_round_scores(state, round_state)
        state.round_index += 1
