"""
참새 콜(소원/콜) 관련 순수 로직.

트릭 루프 본체 없이도 호출할 수 있도록
- 콜 선언/해제
- 콜 충족 가능성 빠른 검사
- 합법 조합 탐색
- 콜 강제 여부 판정
만 분리한다.
"""
from itertools import combinations
from typing import Iterable

from .cards import Card, RANK_MAHJONG, RANK_PHOENIX
from .combo_info import evaluate_combo, can_beat
from .state import RoundState


def _ordered_cards(cards: Iterable[Card]) -> list[Card]:
    """카드 순서를 고정하기 위해 rank, suit 기준 정렬 복사본을 반환."""

    return sorted(cards, key=lambda card: (card.rank, card.suit))


def _is_valid_call_rank(call_rank: int | None) -> bool:
    """콜 가능한 숫자(2~14)인지 확인."""

    return call_rank is not None and 2 <= call_rank <= 14


def _is_allowed_call_choice(call_rank: int | None) -> bool:
    """참새를 냈을 때 선택 가능한 콜(없음 또는 2~14)인지 확인."""

    return call_rank is None or _is_valid_call_rank(call_rank)


def can_declare_mahjong_call(played_cards: list[Card], call_rank: int | None) -> bool:
    """
    참새가 포함된 합법 조합을 내며 유효한 숫자를 콜할 수 있는지 검사.
    입력: 방금 낸 카드 목록, 콜 숫자. 출력: 가능 여부.
    전제조건: 없음. 수정하는 상태: 없음.
    """

    if not _is_allowed_call_choice(call_rank):
        return False
    if not any(card.rank == RANK_MAHJONG for card in played_cards):
        return False
    return evaluate_combo(played_cards) is not None


def set_mahjong_call(
    round_state: RoundState,
    played_cards: list[Card],
    call_rank: int | None,
) -> None:
    """
    유효한 참새 콜을 라운드 상태에 저장.
    입력: round_state(수정 대상), 방금 낸 카드, 콜 숫자. 출력: 없음.
    전제조건: played_cards는 실제 낸 카드. 수정하는 상태: round_state.mahjong_call_rank.
    """

    if not can_declare_mahjong_call(played_cards, call_rank):
        raise ValueError("invalid mahjong call")

    round_state.mahjong_call_rank = call_rank


def clear_mahjong_call(round_state: RoundState) -> None:
    """
    현재 라운드의 참새 콜을 해제.
    입력: round_state(수정 대상). 출력: 없음. 수정하는 상태: round_state.mahjong_call_rank.
    """

    round_state.mahjong_call_rank = None


def hand_can_possibly_match_mahjong_call(hand: list[Card], call_rank: int | None) -> bool:
    """
    손패에 콜 숫자 또는 봉황이 있는지만 빠르게 검사.
    입력: hand, call_rank. 출력: 가능성 여부.
    전제조건: 없음. 수정하는 상태: 없음.
    """

    if not _is_valid_call_rank(call_rank):
        return False

    has_call_rank = any(card.rank == call_rank for card in hand)
    has_phoenix = any(card.rank == RANK_PHOENIX for card in hand)
    return has_call_rank or has_phoenix


def find_legal_plays(hand: list[Card], current_trick_cards: list[Card]) -> list[list[Card]]:
    """
    현재 손패에서 낼 수 있는 모든 합법 조합을 탐색.
    입력: hand, 현재 트릭 카드 목록. 출력: 합법 조합 목록.
    전제조건: 없음. 수정하는 상태: 없음.
    """

    ordered_hand = _ordered_cards(hand)

    current_combo = None
    if current_trick_cards:
        current_combo = evaluate_combo(current_trick_cards)
        if current_combo is None:
            return []

    legal_plays: list[list[Card]] = []
    for card_count in range(1, len(ordered_hand) + 1):
        for subset in combinations(ordered_hand, card_count):
            selected_cards = list(subset)
            selected_combo = evaluate_combo(selected_cards)
            if selected_combo is None:
                continue
            if current_combo is None or can_beat(current_combo, selected_combo):
                legal_plays.append(selected_cards)

    return legal_plays


def selection_satisfies_mahjong_call(selected_cards: list[Card], call_rank: int | None) -> bool:
    """
    선택 카드가 현재 참새 콜 숫자를 충족하는지 검사.
    입력: 선택 카드, call_rank. 출력: 충족 여부.
    전제조건: 없음. 수정하는 상태: 없음.
    """

    if not _is_valid_call_rank(call_rank):
        return True

    selected_combo = evaluate_combo(selected_cards)
    if selected_combo is None:
        return False

    if any(card.rank == call_rank for card in selected_cards):
        return True

    if selected_combo.resolved_ranks is not None:
        return call_rank in selected_combo.resolved_ranks

    return False


def find_legal_plays_matching_call(
    hand: list[Card],
    current_trick_cards: list[Card],
    call_rank: int | None,
) -> list[list[Card]]:
    """
    현재 트릭 기준으로 참새 콜 숫자를 충족하는 합법 조합만 탐색.
    입력: hand, 현재 트릭 카드 목록, call_rank. 출력: 조건을 만족하는 합법 조합 목록.
    전제조건: 없음. 수정하는 상태: 없음.
    """

    if not hand_can_possibly_match_mahjong_call(hand, call_rank):
        return []

    legal_plays = find_legal_plays(hand, current_trick_cards)
    return [
        selected_cards
        for selected_cards in legal_plays
        if selection_satisfies_mahjong_call(selected_cards, call_rank)
    ]


def must_follow_mahjong_call(
    hand: list[Card],
    current_trick_cards: list[Card],
    call_rank: int | None,
) -> bool:
    """
    현재 손패와 트릭 상태에서 참새 콜을 반드시 따라야 하는지 검사.
    입력: hand, 현재 트릭 카드 목록, call_rank. 출력: bool.
    전제조건: 없음. 수정하는 상태: 없음.
    """

    return bool(find_legal_plays_matching_call(hand, current_trick_cards, call_rank))


def can_pass_with_mahjong_call(
    hand: list[Card],
    current_trick_cards: list[Card],
    call_rank: int | None,
) -> bool:
    """
    현재 참새 콜 규칙 아래에서 패스 가능한지 검사.
    입력: hand, 현재 트릭 카드 목록, call_rank. 출력: bool.
    전제조건: 없음. 수정하는 상태: 없음.
    """

    return not must_follow_mahjong_call(hand, current_trick_cards, call_rank)
