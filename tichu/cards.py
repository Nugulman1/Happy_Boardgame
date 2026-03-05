"""
1단계: 카드·덱·점수 정의. 루프/행동/점수 로직 없음.
룰: tichu/rule/티츄 룰 정리.md §3. 구현 메모: tichu/구현_메모.md
"""
import random
from dataclasses import dataclass
from typing import List

# 무늬 4종. 특수 카드(참새/개/봉황/용)는 suit="" 로 둠.
SUITS = ("S", "H", "D", "C")  # Spade, Heart, Diamond, Club

# 특수 카드 rank (숫자로 바로 식별)
RANK_MAHJONG = 1   # 참새 (스트레이트 1-2-3-4-5)
RANK_DOG = 20
RANK_PHOENIX = 21
RANK_DRAGON = 22


@dataclass(frozen=True)
class Card:
    """
    카드 한 장.
    - 일반 트럼프: suit in ("S","H","D","C"), rank 2~14 (J/Q/K/A = 11,12,13,14).
    - 특수 카드: suit="", rank in (1, 20, 21, 22) → 참새, 개, 봉황, 용.
    입력: (suit, rank). 출력: 카드 객체. 전제조건: rank는 1,2..14, 20,21,22 중 하나. 수정하는 상태: 없음.
    """
    suit: str
    rank: int

    def __post_init__(self) -> None:
        if self.rank not in (1, 20, 21, 22) and (self.rank < 2 or self.rank > 14):
            raise ValueError(f"rank must be 1, 2..14, or 20,21,22, got {self.rank}")
        if self.rank in (1, 20, 21, 22):
            if self.suit != "":
                raise ValueError("special card must have suit=''")
        elif self.suit not in SUITS:
            raise ValueError(f"suit must be one of {SUITS}, got {self.suit!r}")


def make_deck(shuffle: bool = True) -> List[Card]:
    """
    표준 티츄 덱 56장 생성.
    입력: 없음 (shuffle=True면 섞어서 반환).
    출력: 길이 56인 list[Card]. 52장 트럼프(무늬 4종 × rank 2~14) + 참새(1)·개(20)·봉황(21)·용(22) 각 1장.
    전제조건: 없음. 수정하는 상태: 없음(순수 함수. shuffle 시 반환 리스트를 in-place 셔플).
    """
    deck: List[Card] = []
    for s in SUITS:
        for r in range(2, 15):
            deck.append(Card(suit=s, rank=r))
    deck.append(Card(suit="", rank=RANK_MAHJONG))
    deck.append(Card(suit="", rank=RANK_DOG))
    deck.append(Card(suit="", rank=RANK_PHOENIX))
    deck.append(Card(suit="", rank=RANK_DRAGON))
    if shuffle:
        random.shuffle(deck)
    return deck


def shuffle_deck(deck: List[Card]) -> None:
    """
    덱 리스트를 in-place 랜덤 셔플.
    입력: deck (수정 대상). 출력: 없음. 전제조건: 없음. 수정하는 상태: deck 순서.
    """
    random.shuffle(deck)


def card_points(card: Card) -> int:
    """
    카드 1장당 점수. 룰 §3 점수 표.
    입력: card. 출력: int 점수. 전제조건: 없음. 수정하는 상태: 없음.
    - 5 → 5점, 10·K(13) → 10점, 봉황(21) → -25, 용(22) → +25, 그 외 0.
    """
    r = card.rank
    if r == 5:
        return 5
    if r == 10 or r == 13:
        return 10
    if r == 21:  # 봉황
        return -25
    if r == 22:  # 용
        return 25
    return 0
