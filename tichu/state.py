"""
1단계: 게임 상태(외부만)·라운드 상태 정의.
State = 게임 동안 유지·저장되는 값만. 라운드용(hands, deck, leader 등)은 RoundState로 while 라운드 시작 시마다 생성.
룰: tichu/rule/티츄 룰 정리.md §2·§4. 구현 메모: tichu/구현_메모.md
"""
from dataclasses import dataclass, field
from typing import List, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from .cards import Card


class GameState:
    """
    게임 동안 유지·저장되는 상태만. (외부)
    - team_scores: 팀별 누적 점수 [1팀, 2팀]. team_scores[0]=1팀, team_scores[1]=2팀. team_id(i)로 1 또는 2.
    - round_index: 현재 라운드 번호(0부터).
    라운드용(hands, deck, leader_index 등)은 state에 두지 않고 RoundState를 라운드 시작 시마다 생성해 사용.
    """

    def __init__(self) -> None:
        self.team_scores: List[int] = [0, 0]
        self.round_index: int = 0


@dataclass
class RoundState:
    """
    한 라운드용 데이터. while 라운드 시작할 때마다 새로 만들고, 준비/트릭 로직에 넘김. (내부)
    """
    hands: List[List["Card"]] = field(default_factory=lambda: [[], [], [], []])
    deck: List["Card"] = field(default_factory=list)
    leader_index: int = 0
    trick_index: int = 0
    grand_tichu_declarers: Set[int] = field(default_factory=set)


def new_round_state() -> "RoundState":
    """
    라운드 시작 시 호출. 빈 손패·빈 덱·선 0·트릭 0·라지 티츄 빈 집합.
    입력: 없음. 출력: RoundState. 전제조건: 없음. 수정하는 상태: 없음.
    """
    return RoundState(
        hands=[[], [], [], []],
        deck=[],
        leader_index=0,
        trick_index=0,
        grand_tichu_declarers=set(),
    )


def init_state(state: GameState) -> None:
    """
    게임 상태(외부)만 초기값으로 리셋. 한 게임 시작 시 한 번 호출.
    입력: state (수정 대상). 출력: 없음. 전제조건: 없음.
    수정하는 필드: team_scores, round_index.
    """
    state.team_scores = [0, 0]
    state.round_index = 0


def team_id(player_index: int) -> int:
    """
    플레이어 인덱스 → 팀 번호(1 또는 2). 1팀=0,2 / 2팀=1,3.
    team_scores 접근: state.team_scores[team_id(i) - 1]
    입력: player_index 0~3. 출력: 1 또는 2. 전제조건: 없음. 수정하는 상태: 없음.
    """
    return (player_index % 2) + 1
