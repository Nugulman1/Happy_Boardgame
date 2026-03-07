"""
3단계: 카드 목록을 바로 족보 정보로 계산하고 비교하는 순수 로직.

이 모듈은 상태를 읽거나 수정하지 않는다.
입력으로 받은 카드 목록을 바로 해석하고, 같은 종류 족보끼리만 비교한다.
"""
from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .cards import RANK_DOG, RANK_DRAGON, RANK_PHOENIX

if TYPE_CHECKING:
    from .cards import Card


@dataclass(frozen=True)
class ComboInfo:
    """
    카드 묶음을 해석한 결과.

    - card_count: 카드 장수
    - combo_type: 판정된 족보 이름
    - strength: 같은 족보끼리 우열 비교에 쓸 값
    - uses_phoenix: 봉황을 사용한 조합인지 여부
    """

    card_count: int
    combo_type: str | None
    strength: tuple | None
    uses_phoenix: bool = False


def _sorted_cards(cards: list["Card"]) -> list["Card"]:
    """판정을 일정하게 하기 위해 rank, suit 순으로 정렬한 복사본을 반환."""

    return sorted(cards, key=lambda card: (card.rank, card.suit))


def _rank_counts(cards: list["Card"]) -> Counter[int]:
    """카드 묶음 안에서 rank별 개수를 센다."""

    return Counter(card.rank for card in cards)


def _contains_unsupported_special(cards: list["Card"]) -> bool:
    """이번 단계에서 제외한 특수 카드가 포함되어 있는지 확인."""

    ranks = {card.rank for card in cards}
    return RANK_DOG in ranks


def _split_phoenix(cards: list["Card"]) -> tuple[list["Card"], bool]:
    """봉황을 제외한 카드 목록과 봉황 포함 여부를 반환."""

    normal_cards = [card for card in cards if card.rank != RANK_PHOENIX]
    return normal_cards, len(normal_cards) != len(cards)


def _is_straight(cards: list["Card"]) -> tuple[bool, int]:
    """스트레이트 여부와 최고 rank를 반환."""

    if len(cards) < 5:
        return False, 0

    ranks = [card.rank for card in cards]

    for prev_rank, next_rank in zip(ranks, ranks[1:]):
        if next_rank != prev_rank + 1:
            return False, 0

    return True, ranks[-1]


def _straight_high_with_phoenix(cards: list["Card"]) -> int | None:
    """봉황 1장으로 스트레이트를 만들 수 있으면 최고 rank를 반환."""

    normal_cards, uses_phoenix = _split_phoenix(cards)
    if not uses_phoenix or len(normal_cards) != len(cards) - 1:
        return None

    normal_ranks = sorted(card.rank for card in normal_cards)
    if len(set(normal_ranks)) != len(normal_ranks):
        return None

    straight_length = len(cards)
    best_high_rank = None
    max_start = 14 - straight_length + 1

    for start_rank in range(1, max_start + 1):
        candidate = set(range(start_rank, start_rank + straight_length))
        if set(normal_ranks).issubset(candidate) and len(candidate - set(normal_ranks)) == 1:
            best_high_rank = start_rank + straight_length - 1

    return best_high_rank


def _is_pair_run(cards: list["Card"]) -> tuple[bool, int, int]:
    """연속페어 여부와 최고 pair rank, pair 개수를 반환."""

    if len(cards) < 4 or len(cards) % 2 != 0:
        return False, 0, 0

    counts = _rank_counts(cards)
    if any(count != 2 for count in counts.values()):
        return False, 0, 0

    unique_ranks = sorted(counts)
    for prev_rank, next_rank in zip(unique_ranks, unique_ranks[1:]):
        if next_rank != prev_rank + 1:
            return False, 0, 0

    return True, unique_ranks[-1], len(unique_ranks)


def _pair_run_with_phoenix(cards: list["Card"]) -> tuple[bool, int, int]:
    """봉황 1장으로 연속페어를 만들 수 있으면 결과를 반환."""

    if len(cards) < 4 or len(cards) % 2 != 0:
        return False, 0, 0

    normal_cards, uses_phoenix = _split_phoenix(cards)
    if not uses_phoenix or len(normal_cards) != len(cards) - 1:
        return False, 0, 0

    counts = _rank_counts(normal_cards)
    pair_count = len(cards) // 2
    if len(counts) != pair_count:
        return False, 0, 0

    single_count_ranks = [rank for rank, count in counts.items() if count == 1]
    if len(single_count_ranks) != 1:
        return False, 0, 0

    if any(count not in (1, 2) for count in counts.values()):
        return False, 0, 0

    unique_ranks = sorted(counts)
    for prev_rank, next_rank in zip(unique_ranks, unique_ranks[1:]):
        if next_rank != prev_rank + 1:
            return False, 0, 0

    return True, unique_ranks[-1], pair_count


def _is_full_house(cards: list["Card"]) -> tuple[bool, int]:
    """풀하우스 여부와 트리플 rank를 반환."""

    if len(cards) != 5:
        return False, 0

    counts = _rank_counts(cards)
    if sorted(counts.values()) != [2, 3]:
        return False, 0

    for rank, count in counts.items():
        if count == 3:
            return True, rank

    return False, 0


def _full_house_with_phoenix(cards: list["Card"]) -> tuple[bool, int]:
    """봉황 1장으로 풀하우스를 만들 수 있으면 트리플 rank를 반환."""

    if len(cards) != 5:
        return False, 0

    normal_cards, uses_phoenix = _split_phoenix(cards)
    if not uses_phoenix or len(normal_cards) != 4:
        return False, 0

    counts = _rank_counts(normal_cards)
    count_values = sorted(counts.values())

    if count_values == [1, 3]:
        for rank, count in counts.items():
            if count == 3:
                return True, rank

    if count_values == [2, 2]:
        return True, max(counts)

    return False, 0


def _evaluate_single_with_phoenix(cards: list["Card"]) -> ComboInfo | None:
    """봉황 싱글을 판정한다."""

    if len(cards) != 1 or cards[0].rank != RANK_PHOENIX:
        return None

    return ComboInfo(card_count=1, combo_type="single", strength=(0.5,), uses_phoenix=True)


def _evaluate_pair_with_phoenix(cards: list["Card"]) -> ComboInfo | None:
    """봉황 포함 페어를 판정한다."""

    if len(cards) != 2:
        return None

    normal_cards, uses_phoenix = _split_phoenix(cards)
    if not uses_phoenix or len(normal_cards) != 1:
        return None

    if normal_cards[0].rank == RANK_DRAGON:
        return None

    return ComboInfo(card_count=2, combo_type="pair", strength=(normal_cards[0].rank,), uses_phoenix=True)


def _evaluate_triple_with_phoenix(cards: list["Card"]) -> ComboInfo | None:
    """봉황 포함 트리플을 판정한다."""

    if len(cards) != 3:
        return None

    normal_cards, uses_phoenix = _split_phoenix(cards)
    if not uses_phoenix or len(normal_cards) != 2:
        return None

    if normal_cards[0].rank != normal_cards[1].rank:
        return None

    if normal_cards[0].rank == RANK_DRAGON:
        return None

    return ComboInfo(card_count=3, combo_type="triple", strength=(normal_cards[0].rank,), uses_phoenix=True)


def _evaluate_full_house_with_phoenix(cards: list["Card"]) -> ComboInfo | None:
    """봉황 포함 풀하우스를 판정한다."""

    is_full_house, triple_rank = _full_house_with_phoenix(cards)
    if not is_full_house:
        return None

    return ComboInfo(card_count=5, combo_type="full_house", strength=(triple_rank,), uses_phoenix=True)


def _evaluate_straight_with_phoenix(cards: list["Card"]) -> ComboInfo | None:
    """봉황 포함 스트레이트를 판정한다."""

    high_rank = _straight_high_with_phoenix(cards)
    if high_rank is None:
        return None

    return ComboInfo(
        card_count=len(cards),
        combo_type="straight",
        strength=(high_rank, len(cards)),
        uses_phoenix=True,
    )


def _evaluate_pair_run_with_phoenix(cards: list["Card"]) -> ComboInfo | None:
    """봉황 포함 연속페어를 판정한다."""

    is_pair_run, high_pair_rank, pair_count = _pair_run_with_phoenix(cards)
    if not is_pair_run:
        return None

    return ComboInfo(
        card_count=len(cards),
        combo_type="pair_run",
        strength=(high_pair_rank, pair_count),
        uses_phoenix=True,
    )


def _is_four_bomb_shape(cards: list["Card"]) -> bool:
    """포카드 폭탄 형태를 감지해 이번 단계에서 제외한다."""

    return len(cards) == 4 and len(_rank_counts(cards)) == 1


def _is_straight_flush_bomb_shape(cards: list["Card"]) -> bool:
    """스트레이트 플러시 폭탄 형태를 감지해 이번 단계에서 제외한다."""

    if len(cards) < 5:
        return False

    suits = {card.suit for card in cards}
    if len(suits) != 1 or "" in suits:
        return False

    is_straight, _ = _is_straight(cards)
    return is_straight


def _evaluate_long_combo(cards: list["Card"]) -> ComboInfo | None:
    """5장 이상 카드 묶음에서 지원하는 족보를 판정한다."""

    card_count = len(cards)
    phoenix_pair_run = _evaluate_pair_run_with_phoenix(cards)
    if phoenix_pair_run is not None:
        return phoenix_pair_run

    phoenix_full_house = _evaluate_full_house_with_phoenix(cards)
    if phoenix_full_house is not None:
        return phoenix_full_house

    phoenix_straight = _evaluate_straight_with_phoenix(cards)
    if phoenix_straight is not None:
        return phoenix_straight

    is_pair_run, high_pair_rank, pair_count = _is_pair_run(cards)
    if is_pair_run:
        return ComboInfo(
            card_count=card_count,
            combo_type="pair_run",
            strength=(high_pair_rank, pair_count),
        )

    is_full_house, triple_rank = _is_full_house(cards)
    if is_full_house:
        return ComboInfo(
            card_count=card_count,
            combo_type="full_house",
            strength=(triple_rank,),
        )

    is_straight, high_rank = _is_straight(cards)
    if is_straight:
        return ComboInfo(
            card_count=card_count,
            combo_type="straight",
            strength=(high_rank, card_count),
        )

    return None


def evaluate_combo(cards: list["Card"]) -> ComboInfo | None:
    """
    카드 목록을 현재 단계에서 지원하는 족보 정보로 계산한다.

    지원:
    - 싱글, 페어, 트리플, 풀하우스, 스트레이트, 연속페어
    - 참새(1) 포함
    - 용 싱글

    제외:
    - 폭탄
    - 봉황
    - 개
    """

    if not cards:
        return None

    ordered_cards = _sorted_cards(cards)
    if _contains_unsupported_special(ordered_cards):
        return None

    card_count = len(ordered_cards)
    ranks = [card.rank for card in ordered_cards]

    if RANK_DRAGON in ranks:
        if card_count == 1:
            return ComboInfo(card_count=1, combo_type="single", strength=(RANK_DRAGON,))
        return None

    if _is_four_bomb_shape(ordered_cards) or _is_straight_flush_bomb_shape(ordered_cards):
        return None

    phoenix_single = _evaluate_single_with_phoenix(ordered_cards)
    if phoenix_single is not None:
        return phoenix_single

    if card_count == 1:
        return ComboInfo(
            card_count=1,
            combo_type="single",
            strength=(ordered_cards[0].rank,),
        )

    phoenix_pair = _evaluate_pair_with_phoenix(ordered_cards)
    if phoenix_pair is not None:
        return phoenix_pair

    if card_count == 2:
        if ordered_cards[0].rank == ordered_cards[1].rank:
            return ComboInfo(
                card_count=2,
                combo_type="pair",
                strength=(ordered_cards[0].rank,),
            )
        return None

    phoenix_triple = _evaluate_triple_with_phoenix(ordered_cards)
    if phoenix_triple is not None:
        return phoenix_triple

    if card_count == 3:
        if len(set(ranks)) == 1:
            return ComboInfo(
                card_count=3,
                combo_type="triple",
                strength=(ordered_cards[0].rank,),
            )
        return None

    return _evaluate_long_combo(ordered_cards)


def can_beat(current_combo: ComboInfo, selected_combo: ComboInfo) -> bool:
    """
    같은 종류 족보인지 확인하고, 같을 때만 강도를 비교한다.

    이번 단계에서는 카드 수 다름, 족보 종류 다름, 폭탄 예외 없음 기준으로만 판단한다.
    """

    if current_combo.card_count != selected_combo.card_count:
        return False

    if current_combo.combo_type != selected_combo.combo_type:
        return False

    if current_combo.strength is None or selected_combo.strength is None:
        return False

    if selected_combo.combo_type == "single" and selected_combo.uses_phoenix:
        current_rank = current_combo.strength[0]
        selected_strength = (current_rank + 0.5,)
        return selected_strength > current_combo.strength

    return selected_combo.strength > current_combo.strength
