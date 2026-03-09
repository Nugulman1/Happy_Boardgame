"""
2단계: 준비 단계. 배분·라지 티츄·6장 추가·교환·선 결정.
RoundState만 수정. State(외부)는 건드리지 않음.
함수 순서: 배분(sort_hand, deal_*) → 교환 적용(apply_exchange) → 선(set_leader_by_mahjong) → 오케스트레이션(run_prepare_phase).
"""
from typing import List, Set, Tuple

from .cards import Card, make_deck
from .state import RoundState
from .trick import start_trick


def sort_hand(hand: List[Card]) -> None:
    """
    손패를 in-place 정렬. 키: rank만 (모양은 정렬하지 않음).
    입력: hand (수정 대상). 출력: 없음. 전제조건: 없음. 수정하는 상태: hand 순서.
    """
    hand.sort(key=lambda c: c.rank)


def deal_initial_8(round_state: RoundState) -> None:
    """
    덱에서 각 플레이어에게 8장씩 배분. 끝에서 각 손패 정렬.
    전제조건: round_state.deck은 56장 셔플된 상태, round_state.hands는 빈 리스트 4개.
    수정하는 상태: round_state.deck, round_state.hands.
    """
    for i in range(4):
        for _ in range(8):
            round_state.hands[i].append(round_state.deck.pop())
        sort_hand(round_state.hands[i])


def deal_remaining_6(round_state: RoundState) -> None:
    """
    덱에서 각 플레이어에게 6장씩 추가. 끝에서 각 손패 정렬.
    전제조건: 각 손패 8장, 덱 24장.
    수정하는 상태: round_state.deck, round_state.hands.
    """
    for i in range(4):
        for _ in range(6):
            round_state.hands[i].append(round_state.deck.pop())
        sort_hand(round_state.hands[i])


def apply_exchange(
    round_state: RoundState,
    choices: List[Tuple[Card, Card, Card]],
) -> None:
    """
    ​4명이 선택한 교환을 동시에 반영. 1) 4명 손패에서 해당 3장 제거 2) choices에서 바로 상대 손패에 추가 3) 각 손패 정렬.
    수정하는 상태: round_state.hands.
    """
    for i in range(4):
        to_left, to_team, to_right = choices[i]
        hand = round_state.hands[i]
        hand.remove(to_left)
        hand.remove(to_team)
        hand.remove(to_right)
    for i in range(4):
        round_state.hands[(i + 1) % 4].append(choices[i][0])
        round_state.hands[(i + 2) % 4].append(choices[i][1])
        round_state.hands[(i + 3) % 4].append(choices[i][2])
    for j in range(4):
        sort_hand(round_state.hands[j])


def set_leader_by_mahjong(round_state: RoundState) -> None:
    """
    참새(rank 1) 보유자를 선으로 설정.
    전제조건: 교환 완료 후, 참새는 한 플레이어 손패에 1장 있음.
    수정하는 상태: round_state.leader_index.
    """
    for i in range(4):
        if any(c.rank == 1 for c in round_state.hands[i]):
            round_state.leader_index = i
            return


def run_prepare_phase(round_state: RoundState) -> None:
    """
    준비 단계 한 번에 실행: 라운드용 초기화 → 덱 생성·8장 배분 → (라지 티츄) → 6장 추가 → (교환) → 선 결정.
    라지 티츄·교환은 프론트에서 데이터 주면 그때 round_state에 반영 후 다음으로 넘어가는 식으로 처리.
    전제조건: round_state는 new_round_state()로 생성된 상태.
    수정하는 상태: round_state 전부.
    """
    round_state.grand_tichu_declarers = set()
    round_state.deck = make_deck(shuffle=True)
    deal_initial_8(round_state)
    # 라지 티츄: 프론트에서 전부 확정되면 round_state.grand_tichu_declarers 세팅 후 다음으로 넘어감
    deal_remaining_6(round_state)
    # 교환: 프론트에서 choices 받으면 apply_exchange(round_state, choices) 호출 후 다음으로
    set_leader_by_mahjong(round_state)
    start_trick(round_state)
