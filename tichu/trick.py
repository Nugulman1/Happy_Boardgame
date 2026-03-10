"""
3단계: 트릭 코어 상태전이.

- 현재 트릭의 최고 조합은 round_state.current_trick_cards 에 둔다.
- 트릭 전체 회수 카드 더미는 round_state.current_trick_pile 에 별도로 모은다.
- 폭탄 끼어들기와 개는 다음 단계에서 구현한다.
"""
from typing import Iterable

from .cards import Card, RANK_DOG, RANK_DRAGON, RANK_MAHJONG
from .mahjong_call import (
    can_pass_with_mahjong_call,
    find_legal_plays_matching_call,
    must_follow_mahjong_call,
    selection_satisfies_mahjong_call,
    set_mahjong_call,
)
from .combo_info import can_beat, evaluate_combo
from .state import RoundState, team_id


def _ordered_cards(cards: Iterable[Card]) -> list[Card]:
    """카드 비교와 상태 저장을 위해 rank, suit 기준 정렬 복사본을 반환."""

    return sorted(cards, key=lambda card: (card.rank, card.suit))


def _ensure_current_player(round_state: RoundState, player_index: int) -> None:
    """현재 차례 플레이어인지 검사."""

    if round_state.current_player_index != player_index:
        raise ValueError("not this player's turn")


def _clear_trick_state(round_state: RoundState) -> None:
    """트릭 종료 후 현재 트릭 상태만 비운다."""

    round_state.current_trick_cards = []
    round_state.current_trick_pile = []
    round_state.last_played_by = None
    round_state.pass_count_since_last_play = 0


def _is_dragon_trick(round_state: RoundState) -> bool:
    """현재 트릭의 승리 조합이 용 싱글인지 확인."""

    return len(round_state.current_trick_cards) == 1 and round_state.current_trick_cards[0].rank == RANK_DRAGON


def _validate_dragon_recipient(winner_index: int, dragon_recipient: int | None) -> int:
    """용 트릭 점수 수령자가 상대 팀 플레이어인지 확인."""

    if dragon_recipient is None:
        raise ValueError("dragon recipient is required")
    if not 0 <= dragon_recipient < 4:
        raise ValueError("dragon recipient must be a player index")
    if team_id(dragon_recipient) == team_id(winner_index):
        raise ValueError("dragon recipient must be on the opposing team")
    return dragon_recipient


def _record_player_out(round_state: RoundState, player_index: int) -> None:
    """손패를 모두 소모한 플레이어를 순서대로 기록."""

    if not round_state.hands[player_index] and player_index not in round_state.players_out_order:
        round_state.players_out_order.append(player_index)


def _teammate_index(player_index: int) -> int:
    """같은 팀 플레이어 인덱스를 반환."""

    return (player_index + 2) % 4


def _can_play_dog(round_state: RoundState, player_index: int) -> bool:
    """개를 낼 수 있는 조건인지 확인."""

    return (
        not round_state.current_trick_cards
        and player_index not in round_state.played_first_card_players
    )


def _active_player_indices(round_state: RoundState) -> list[int]:
    """손패가 남아 있는 플레이어 인덱스를 반환."""

    return [player_index for player_index, hand in enumerate(round_state.hands) if hand]


def _required_pass_count(round_state: RoundState) -> int:
    """현재 트릭을 끝내는 데 필요한 연속 패스 수를 계산."""

    active_count = len(_active_player_indices(round_state))
    if active_count <= 1:
        return 0
    return active_count - 1


def can_declare_small_tichu(round_state: RoundState, player_index: int) -> bool:
    """
    스몰 티츄 선언 가능 여부를 검사.
    입력: round_state, player_index. 출력: bool.
    수정하는 상태: 없음.
    """

    return (
        0 <= player_index < 4
        and bool(round_state.hands[player_index])
        and player_index not in round_state.small_tichu_declarers
        and player_index not in round_state.played_first_card_players
    )


def declare_small_tichu(round_state: RoundState, player_index: int) -> None:
    """
    스몰 티츄 선언을 저장한다.
    입력: round_state(수정 대상), player_index. 출력: 없음.
    수정하는 상태: round_state.small_tichu_declarers.
    """

    if not can_declare_small_tichu(round_state, player_index):
        raise ValueError("small tichu cannot be declared")

    round_state.small_tichu_declarers.add(player_index)


def start_trick(round_state: RoundState) -> None:
    """
    새 트릭 시작 상태로 초기화.
    입력: round_state(수정 대상). 출력: 없음.
    수정하는 상태: current_trick_cards, current_trick_pile, last_played_by,
    pass_count_since_last_play, current_player_index.
    """

    _clear_trick_state(round_state)
    round_state.current_player_index = round_state.leader_index


def get_next_active_player(round_state: RoundState, from_index: int) -> int:
    """
    기준 플레이어 다음으로 손패가 남아 있는 플레이어를 순환 탐색.
    입력: round_state, from_index. 출력: 다음 활성 플레이어 인덱스.
    전제조건: 최소 1명은 손패가 남아 있음.
    """

    for offset in range(1, 5):
        candidate = (from_index + offset) % 4
        if round_state.hands[candidate]:
            return candidate

    if round_state.hands[from_index]:
        return from_index

    raise ValueError("no active player remains")


def get_legal_plays(round_state: RoundState, player_index: int) -> list[list[Card]]:
    """
    현재 참새 콜을 만족하는 합법 조합만 반환.
    입력: round_state, player_index. 출력: 콜을 만족하는 합법 조합 목록.
    수정하는 상태: 없음.
    """

    return find_legal_plays_matching_call(
        round_state.hands[player_index],
        round_state.current_trick_cards,
        round_state.mahjong_call_rank,
    )


def is_double_victory(round_state: RoundState) -> bool:
    """
    같은 팀 1등+2등으로 라운드가 즉시 끝났는지 검사.
    입력: round_state. 출력: bool.
    수정하는 상태: 없음.
    """

    if len(round_state.players_out_order) < 2:
        return False

    first_player, second_player = round_state.players_out_order[:2]
    return team_id(first_player) == team_id(second_player)


def get_round_end_reason(round_state: RoundState) -> str | None:
    """
    현재 라운드 종료 사유를 반환한다.
    입력: round_state. 출력: "double_victory", "three_players_out", 또는 None.
    수정하는 상태: 없음.
    """

    if is_double_victory(round_state):
        return "double_victory"
    if len(round_state.players_out_order) >= 3 and not round_state.current_trick_pile:
        return "three_players_out"
    return None


def is_round_over(round_state: RoundState) -> bool:
    """
    현재 라운드 종료 여부를 반환한다.
    입력: round_state. 출력: bool.
    수정하는 상태: 없음.
    """

    return get_round_end_reason(round_state) is not None


def can_player_pass(round_state: RoundState, player_index: int) -> bool:
    """
    현재 플레이어가 패스 가능한지 검사.
    입력: round_state, player_index. 출력: bool.
    수정하는 상태: 없음.
    """

    if not round_state.current_trick_cards:
        return False

    if round_state.mahjong_call_rank is None:
        return True

    return can_pass_with_mahjong_call(
        round_state.hands[player_index],
        round_state.current_trick_cards,
        round_state.mahjong_call_rank,
    )


def play_cards(
    round_state: RoundState,
    player_index: int,
    selected_cards: list[Card],
    call_rank: int | None = None,
) -> None:
    """
    현재 차례 플레이어가 카드를 제출한다.
    입력: round_state(수정 대상), player_index, selected_cards, optional call_rank.
    출력: 없음.
    수정하는 상태: hands, current_trick_cards, current_trick_pile, last_played_by,
    pass_count_since_last_play, mahjong_call_rank, current_player_index, players_out_order.
    """

    _ensure_current_player(round_state, player_index)
    if is_round_over(round_state):
        raise ValueError("round is already over")
    if not selected_cards:
        raise ValueError("selected cards must not be empty")

    ordered_selected_cards = _ordered_cards(selected_cards)
    selected_combo = evaluate_combo(ordered_selected_cards)
    if selected_combo is None:
        raise ValueError("selected cards are not a legal play")

    current_trick_cards = round_state.current_trick_cards
    if selected_combo.combo_type == "dog":
        if not _can_play_dog(round_state, player_index):
            raise ValueError("selected cards are not a legal play")
        if call_rank is not None:
            raise ValueError("mahjong call can only be declared when playing mahjong")

        hand = round_state.hands[player_index]
        hand.remove(ordered_selected_cards[0])
        round_state.played_first_card_players.add(player_index)
        _record_player_out(round_state, player_index)
        round_state.leader_index = _teammate_index(player_index)
        start_trick(round_state)
        return

    if current_trick_cards:
        current_combo = evaluate_combo(current_trick_cards)
        if current_combo is None or not can_beat(current_combo, selected_combo):
            raise ValueError("selected cards are not a legal play")

    call_rank_in_state = round_state.mahjong_call_rank
    if (
        call_rank_in_state is not None
        and must_follow_mahjong_call(
            round_state.hands[player_index],
            current_trick_cards,
            call_rank_in_state,
        )
        and not selection_satisfies_mahjong_call(ordered_selected_cards, call_rank_in_state)
    ):
        raise ValueError("selected cards are not a legal play")

    contains_mahjong = any(card.rank == RANK_MAHJONG for card in ordered_selected_cards)
    if contains_mahjong:
        set_mahjong_call(round_state, ordered_selected_cards, call_rank)
    elif call_rank is not None:
        raise ValueError("mahjong call can only be declared when playing mahjong")

    hand = round_state.hands[player_index]
    for card in ordered_selected_cards:
        hand.remove(card)

    round_state.played_first_card_players.add(player_index)
    round_state.current_trick_cards = ordered_selected_cards
    round_state.current_trick_pile.extend(ordered_selected_cards)
    round_state.last_played_by = player_index
    round_state.pass_count_since_last_play = 0

    _record_player_out(round_state, player_index)
    if is_double_victory(round_state):
        round_state.current_player_index = player_index
        return

    active_players = _active_player_indices(round_state)
    if active_players:
        round_state.current_player_index = get_next_active_player(round_state, player_index)
    else:
        round_state.current_player_index = player_index


def pass_turn(
    round_state: RoundState,
    player_index: int,
    dragon_recipient: int | None = None,
) -> None:
    """
    현재 차례 플레이어가 패스한다.
    입력: round_state(수정 대상), player_index. 출력: 없음.
    수정하는 상태: pass_count_since_last_play, current_player_index, leader_index, trick_index,
    won_trick_cards 및 새 트릭 상태.
    """

    _ensure_current_player(round_state, player_index)
    if is_round_over(round_state):
        raise ValueError("round is already over")
    if not can_player_pass(round_state, player_index):
        raise ValueError("player cannot pass")

    round_state.pass_count_since_last_play += 1
    if round_state.pass_count_since_last_play >= _required_pass_count(round_state):
        resolve_trick_end(round_state, dragon_recipient)
        return

    round_state.current_player_index = get_next_active_player(round_state, player_index)


def resolve_trick_end(round_state: RoundState, dragon_recipient: int | None = None) -> None:
    """
    현재 트릭을 종료하고 승자에게 카드 더미를 넘긴다.
    입력: round_state(수정 대상). 출력: 없음.
    수정하는 상태: won_trick_cards, leader_index, trick_index 및 새 트릭 상태.
    """

    if round_state.last_played_by is None:
        raise ValueError("cannot resolve trick without a winning play")

    winner_index = round_state.last_played_by
    recipient_index = winner_index
    if _is_dragon_trick(round_state):
        recipient_index = _validate_dragon_recipient(winner_index, dragon_recipient)

    round_state.won_trick_cards[recipient_index].extend(round_state.current_trick_pile)

    if round_state.hands[winner_index]:
        round_state.leader_index = winner_index
    else:
        active_players = _active_player_indices(round_state)
        if active_players:
            round_state.leader_index = get_next_active_player(round_state, winner_index)
        else:
            round_state.leader_index = winner_index

    round_state.trick_index += 1
    if len(round_state.players_out_order) >= 3:
        _clear_trick_state(round_state)
        round_state.current_player_index = round_state.leader_index
        return
    start_trick(round_state)
