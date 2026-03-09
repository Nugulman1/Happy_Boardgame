"""
3단계: 카드 목록을 바로 족보 정보로 계산하고 비교하는 순수 로직.

이 모듈은 상태를 읽거나 수정하지 않는다.
입력으로 받은 카드 목록을 바로 해석하고, 같은 종류 족보끼리만 비교한다.
"""
from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .cards import RANK_DOG, RANK_DRAGON, RANK_MAHJONG, RANK_PHOENIX

if TYPE_CHECKING:
    from .cards import Card


@dataclass(frozen=True)
class ComboInfo:
    """
    카드 묶음을 해석한 결과.

    - card_count: 카드 장수
    - combo_type: 판정된 족보 이름
    - strength: 같은 족보끼리 우열 비교에 쓸 값
    - uses_phoenix: 봉황 사용 여부
    - resolved_ranks: 봉황을 실제로 어떤 숫자 조합으로 해석했는지 기록
    """

    card_count: int
    combo_type: str | None
    strength: tuple | None
    uses_phoenix: bool = False
    resolved_ranks: tuple[int, ...] | None = None


def _sorted_cards(cards: list["Card"]) -> list["Card"]:
    """판정을 일정하게 하기 위해 rank, suit 순으로 정렬한 복사본을 반환."""

    return sorted(cards, key=lambda card: (card.rank, card.suit))


def _rank_counts(cards: list["Card"]) -> Counter[int]:
    """카드 묶음 안에서 rank별 개수를 센다."""

    return Counter(card.rank for card in cards)


def _contains_unsupported_special(cards: list["Card"]) -> bool:
    """이번 단계에서 제외한 특수 카드가 포함되어 있는지 확인."""

    return False


def _split_phoenix(cards: list["Card"]) -> tuple[list["Card"], bool]:
    """봉황을 제외한 카드 목록과 봉황 포함 여부를 반환."""

    normal_cards = [card for card in cards if card.rank != RANK_PHOENIX]
    return normal_cards, len(normal_cards) != len(cards)


def _contains_forbidden_special_with_phoenix(cards: list["Card"]) -> bool:
    """봉황과 함께 낼 수 없는 특수 카드가 섞였는지 확인."""

    ranks = {card.rank for card in cards}
    return any(rank in ranks for rank in (RANK_DOG, RANK_MAHJONG, RANK_DRAGON))


def _is_straight(cards: list["Card"]) -> tuple[bool, int]:
    """스트레이트 여부와 최고 rank를 반환."""

    if len(cards) < 5:
        return False, 0

    ranks = [card.rank for card in cards]

    for prev_rank, next_rank in zip(ranks, ranks[1:]):
        if next_rank != prev_rank + 1:
            return False, 0

    return True, ranks[-1]


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


def _is_unsupported_bomb_shape(cards: list["Card"]) -> bool:
    """이번 단계에서 아직 처리하지 않는 폭탄 형태인지 확인."""

    return _is_four_bomb_shape(cards) or _is_straight_flush_bomb_shape(cards)


def _evaluate_four_bomb(cards: list["Card"]) -> ComboInfo | None:
    """포카드 폭탄을 판정한다."""

    if not _is_four_bomb_shape(cards):
        return None

    return ComboInfo(
        card_count=4,
        combo_type="bomb_four",
        strength=(cards[0].rank,),
    )


def _evaluate_straight_flush_bomb(cards: list["Card"]) -> ComboInfo | None:
    """스트레이트 플러시 폭탄을 판정한다."""

    if not _is_straight_flush_bomb_shape(cards):
        return None

    return ComboInfo(
        card_count=len(cards),
        combo_type="bomb_straight_flush",
        strength=(len(cards), cards[-1].rank),
    )


def _evaluate_bomb(cards: list["Card"]) -> ComboInfo | None:
    """지원하는 폭탄을 판정한다."""

    four_bomb = _evaluate_four_bomb(cards)
    if four_bomb is not None:
        return four_bomb

    return _evaluate_straight_flush_bomb(cards)


def _evaluate_single_with_phoenix(cards: list["Card"]) -> ComboInfo | None:
    """봉황 싱글을 판정한다."""

    if len(cards) != 1 or cards[0].rank != RANK_PHOENIX:
        return None

    return ComboInfo(
        card_count=1,
        combo_type="single",
        strength=(0.5,),
        uses_phoenix=True,
    )


def _evaluate_pair_with_phoenix(cards: list["Card"]) -> ComboInfo | None:
    """봉황 포함 페어를 판정한다."""

    if len(cards) != 2:
        return None

    normal_cards, uses_phoenix = _split_phoenix(cards)
    if not uses_phoenix or len(normal_cards) != 1:
        return None

    if _contains_forbidden_special_with_phoenix(normal_cards):
        return None

    rank = normal_cards[0].rank
    return ComboInfo(
        card_count=2,
        combo_type="pair",
        strength=(rank,),
        uses_phoenix=True,
        resolved_ranks=(rank, rank),
    )


def _evaluate_triple_with_phoenix(cards: list["Card"]) -> ComboInfo | None:
    """봉황 포함 트리플을 판정한다."""

    if len(cards) != 3:
        return None

    normal_cards, uses_phoenix = _split_phoenix(cards)
    if not uses_phoenix or len(normal_cards) != 2:
        return None

    if _contains_forbidden_special_with_phoenix(normal_cards):
        return None

    if normal_cards[0].rank != normal_cards[1].rank:
        return None

    rank = normal_cards[0].rank
    return ComboInfo(
        card_count=3,
        combo_type="triple",
        strength=(rank,),
        uses_phoenix=True,
        resolved_ranks=(rank, rank, rank),
    )


def _resolve_full_house_with_phoenix(cards: list["Card"]) -> tuple[int, tuple[int, ...]] | None:
    """봉황 포함 풀하우스의 트리플 rank와 최종 숫자열을 계산한다."""

    if len(cards) != 5:
        return None

    normal_cards, uses_phoenix = _split_phoenix(cards)
    if not uses_phoenix or len(normal_cards) != 4:
        return None

    if _contains_forbidden_special_with_phoenix(normal_cards):
        return None

    counts = _rank_counts(normal_cards)
    count_values = sorted(counts.values())

    if count_values == [1, 3]:
        triple_rank = next(rank for rank, count in counts.items() if count == 3)
        pair_rank = next(rank for rank, count in counts.items() if count == 1)
    elif count_values == [2, 2]:
        pair_ranks = sorted(counts)
        pair_rank = pair_ranks[0]
        triple_rank = pair_ranks[1]
    else:
        return None

    resolved_ranks = tuple(sorted([triple_rank, triple_rank, triple_rank, pair_rank, pair_rank]))
    return triple_rank, resolved_ranks


def _evaluate_full_house_with_phoenix(cards: list["Card"]) -> ComboInfo | None:
    """봉황 포함 풀하우스를 판정한다."""

    resolved = _resolve_full_house_with_phoenix(cards)
    if resolved is None:
        return None

    triple_rank, resolved_ranks = resolved
    return ComboInfo(
        card_count=5,
        combo_type="full_house",
        strength=(triple_rank,),
        uses_phoenix=True,
        resolved_ranks=resolved_ranks,
    )


def _resolve_straight_with_phoenix(cards: list["Card"]) -> tuple[int, tuple[int, ...]] | None:
    """
    봉황 포함 스트레이트의 최고 rank와 최종 숫자열을 계산한다.

    정렬된 일반 카드 숫자를 앞에서부터 따라가며 검사한다.
    중간 한 칸 메우기와 양끝 확장을 허용하고, 가능한 경우 가장 높은 쪽으로 확정한다.
    """

    if len(cards) < 5:
        return None

    normal_cards, uses_phoenix = _split_phoenix(cards)
    if not uses_phoenix or len(normal_cards) != len(cards) - 1:
        return None

    if _contains_forbidden_special_with_phoenix(normal_cards):
        return None

    normal_ranks = sorted(card.rank for card in normal_cards)
    if len(set(normal_ranks)) != len(normal_ranks):
        return None

    resolved_ranks = [normal_ranks[0]]
    used_phoenix = False

    for rank in normal_ranks[1:]:
        prev_rank = resolved_ranks[-1]
        gap = rank - prev_rank

        if gap == 1:
            resolved_ranks.append(rank)
            continue

        if gap == 2 and not used_phoenix:
            missing_rank = prev_rank + 1
            if missing_rank == RANK_MAHJONG:
                return None
            resolved_ranks.append(missing_rank)
            resolved_ranks.append(rank)
            used_phoenix = True
            continue

        return None

    if not used_phoenix:
        if resolved_ranks[-1] < 14:
            resolved_ranks.append(resolved_ranks[-1] + 1)
        elif resolved_ranks[0] > 2:
            resolved_ranks.insert(0, resolved_ranks[0] - 1)
        else:
            return None

    if len(resolved_ranks) != len(cards):
        return None

    return resolved_ranks[-1], tuple(resolved_ranks)


def _evaluate_straight_with_phoenix(cards: list["Card"]) -> ComboInfo | None:
    """봉황 포함 스트레이트를 판정한다."""

    resolved = _resolve_straight_with_phoenix(cards)
    if resolved is None:
        return None

    high_rank, resolved_ranks = resolved
    return ComboInfo(
        card_count=len(cards),
        combo_type="straight",
        strength=(high_rank, len(cards)),
        uses_phoenix=True,
        resolved_ranks=resolved_ranks,
    )


def _resolve_pair_run_with_phoenix(cards: list["Card"]) -> tuple[int, int, tuple[int, ...]] | None:
    """봉황 포함 연페어의 최고 pair rank, pair 개수, 최종 숫자열을 계산한다."""

    if len(cards) < 4 or len(cards) % 2 != 0:
        return None

    normal_cards, uses_phoenix = _split_phoenix(cards)
    if not uses_phoenix or len(normal_cards) != len(cards) - 1:
        return None

    if _contains_forbidden_special_with_phoenix(normal_cards):
        return None

    counts = _rank_counts(normal_cards)
    single_ranks = [rank for rank, count in counts.items() if count == 1]
    pair_ranks = [rank for rank, count in counts.items() if count == 2]

    if len(single_ranks) != 1:
        return None
    if len(pair_ranks) + len(single_ranks) != len(counts):
        return None

    unique_ranks = sorted(counts)
    for prev_rank, next_rank in zip(unique_ranks, unique_ranks[1:]):
        if next_rank != prev_rank + 1:
            return None

    resolved_ranks: list[int] = []
    for rank in unique_ranks:
        resolved_ranks.extend((rank, rank))

    pair_count = len(cards) // 2
    high_pair_rank = unique_ranks[-1]
    return high_pair_rank, pair_count, tuple(resolved_ranks)


def _evaluate_pair_run_with_phoenix(cards: list["Card"]) -> ComboInfo | None:
    """봉황 포함 연페어를 판정한다."""

    resolved = _resolve_pair_run_with_phoenix(cards)
    if resolved is None:
        return None

    high_pair_rank, pair_count, resolved_ranks = resolved
    return ComboInfo(
        card_count=len(cards),
        combo_type="pair_run",
        strength=(high_pair_rank, pair_count),
        uses_phoenix=True,
        resolved_ranks=resolved_ranks,
    )


def _evaluate_long_combo(cards: list["Card"]) -> ComboInfo | None:
    """5장 이상 카드 묶음에서 지원하는 족보를 판정한다."""

    card_count = len(cards)

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


def _evaluate_combo_with_phoenix(
    ordered_cards: list["Card"],
    normal_cards: list["Card"],
) -> ComboInfo | None:
    """봉황이 포함된 조합만 판정한다."""

    card_count = len(ordered_cards)
    if len(normal_cards) != card_count - 1:
        return None

    if card_count > 1 and _contains_forbidden_special_with_phoenix(normal_cards):
        return None

    if _is_unsupported_bomb_shape(ordered_cards):
        return None

    phoenix_single = _evaluate_single_with_phoenix(ordered_cards)
    if phoenix_single is not None:
        return phoenix_single

    phoenix_pair = _evaluate_pair_with_phoenix(ordered_cards)
    if phoenix_pair is not None:
        return phoenix_pair

    phoenix_triple = _evaluate_triple_with_phoenix(ordered_cards)
    if phoenix_triple is not None:
        return phoenix_triple

    phoenix_full_house = _evaluate_full_house_with_phoenix(ordered_cards)
    if phoenix_full_house is not None:
        return phoenix_full_house

    phoenix_straight = _evaluate_straight_with_phoenix(ordered_cards)
    if phoenix_straight is not None:
        return phoenix_straight

    phoenix_pair_run = _evaluate_pair_run_with_phoenix(ordered_cards)
    if phoenix_pair_run is not None:
        return phoenix_pair_run

    return None


def _evaluate_combo_without_phoenix(ordered_cards: list["Card"]) -> ComboInfo | None:
    """봉황이 없는 일반 조합만 판정한다."""

    if _contains_unsupported_special(ordered_cards):
        return None

    bomb = _evaluate_bomb(ordered_cards)
    if bomb is not None:
        return bomb

    card_count = len(ordered_cards)
    ranks = [card.rank for card in ordered_cards]

    if RANK_DRAGON in ranks:
        if card_count == 1:
            return ComboInfo(card_count=1, combo_type="single", strength=(RANK_DRAGON,))
        return None

    if RANK_DOG in ranks:
        if card_count == 1:
            return ComboInfo(card_count=1, combo_type="dog", strength=())
        return None

    if card_count == 1:
        return ComboInfo(
            card_count=1,
            combo_type="single",
            strength=(ordered_cards[0].rank,),
        )

    if card_count == 2:
        if ordered_cards[0].rank == ordered_cards[1].rank:
            return ComboInfo(
                card_count=2,
                combo_type="pair",
                strength=(ordered_cards[0].rank,),
            )
        return None

    if card_count == 3:
        if len(set(ranks)) == 1:
            return ComboInfo(
                card_count=3,
                combo_type="triple",
                strength=(ordered_cards[0].rank,),
            )
        return None

    return _evaluate_long_combo(ordered_cards)


def evaluate_combo(cards: list["Card"]) -> ComboInfo | None:
    """
    카드 목록을 현재 단계에서 지원하는 족보 정보로 계산한다.

    지원:
    - 싱글, 페어, 트리플, 풀하우스, 스트레이트, 연속페어
    - 포카드 폭탄, 스트레이트 플러시 폭탄
    - 참새(1) 포함
    - 용 싱글
    - 개
    - 봉황 싱글/페어/트리플/풀하우스/스트레이트

    제외:
    - 봉황 연속페어
    """

    if not cards:
        return None

    ordered_cards = _sorted_cards(cards)
    normal_cards, uses_phoenix = _split_phoenix(ordered_cards)

    if uses_phoenix:
        return _evaluate_combo_with_phoenix(ordered_cards, normal_cards)

    return _evaluate_combo_without_phoenix(ordered_cards)


def can_beat(current_combo: ComboInfo, selected_combo: ComboInfo) -> bool:
    """
    같은 종류 족보인지 확인하고, 같을 때만 강도를 비교한다.

    이번 단계에서는 카드 수 다름, 족보 종류 다름, 폭탄 예외 없음 기준으로만 판단한다.
    """

    if current_combo.strength is None or selected_combo.strength is None:
        return False

    if current_combo.combo_type == "dog" or selected_combo.combo_type == "dog":
        return False

    current_is_bomb = current_combo.combo_type in ("bomb_four", "bomb_straight_flush")
    selected_is_bomb = selected_combo.combo_type in ("bomb_four", "bomb_straight_flush")

    if selected_is_bomb and not current_is_bomb:
        return True
    if current_is_bomb and not selected_is_bomb:
        return False
    if current_is_bomb and selected_is_bomb:
        if current_combo.combo_type == "bomb_four" and selected_combo.combo_type == "bomb_four":
            return selected_combo.strength > current_combo.strength
        if current_combo.combo_type == "bomb_straight_flush" and selected_combo.combo_type == "bomb_straight_flush":
            return selected_combo.strength > current_combo.strength
        return selected_combo.combo_type == "bomb_straight_flush"

    if current_combo.card_count != selected_combo.card_count:
        return False

    if current_combo.combo_type != selected_combo.combo_type:
        return False

    if selected_combo.combo_type == "single" and selected_combo.uses_phoenix:
        if current_combo.strength[0] == RANK_DRAGON:
            return False
        current_rank = current_combo.strength[0]
        selected_strength = (current_rank + 0.5,)
        return selected_strength > current_combo.strength

    return selected_combo.strength > current_combo.strength
