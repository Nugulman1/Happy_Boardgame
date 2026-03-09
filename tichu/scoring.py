"""
4~5단계: 라운드 점수 계산과 게임 점수 반영.

- 원투면 카드 점수는 무시하고 기본 200점만 반영한다.
- 일반 종료면 획득 트릭 점수, 꼴찌 손패 점수, 꼴찌 트릭 점수를 반영한다.
- 스몰/라지 티츄 선언 보너스는 라운드 종류와 무관하게 함께 반영한다.
"""
from .cards import card_points
from .state import GameState, RoundState, team_id
from .trick import get_round_end_reason


def _team_index(player_index: int) -> int:
    """플레이어 인덱스를 team_scores 인덱스로 변환."""

    return team_id(player_index) - 1


def _cards_points(cards) -> int:
    """카드 목록 점수를 합산."""

    return sum(card_points(card) for card in cards)


def _first_place_player(round_state: RoundState) -> int:
    """라운드 1등 플레이어를 반환."""

    if not round_state.players_out_order:
        raise ValueError("round has no finishing order")
    return round_state.players_out_order[0]


def _last_place_player(round_state: RoundState) -> int:
    """라운드 꼴찌 플레이어를 반환."""

    remaining_players = [
        player_index
        for player_index in range(4)
        if player_index not in round_state.players_out_order
    ]
    if remaining_players:
        return remaining_players[0]
    if len(round_state.players_out_order) >= 4:
        return round_state.players_out_order[-1]
    raise ValueError("round has no last place player")


def _apply_tichu_bonuses(round_state: RoundState, deltas: list[int]) -> None:
    """스몰/라지 티츄 보너스를 팀 점수 변화량에 누적."""

    first_place_player = _first_place_player(round_state)

    for player_index in round_state.small_tichu_declarers:
        team_index = _team_index(player_index)
        deltas[team_index] += 100 if player_index == first_place_player else -100

    for player_index in round_state.grand_tichu_declarers:
        team_index = _team_index(player_index)
        deltas[team_index] += 200 if player_index == first_place_player else -200


def calculate_round_score_deltas(round_state: RoundState) -> list[int]:
    """
    라운드 종료 후 팀 점수 변화량을 계산한다.
    입력: round_state. 출력: [1팀 변화량, 2팀 변화량].
    수정하는 상태: 없음.
    """

    end_reason = get_round_end_reason(round_state)
    if end_reason is None:
        raise ValueError("round is not over")

    deltas = [0, 0]
    _apply_tichu_bonuses(round_state, deltas)

    if end_reason == "double_victory":
        winning_team_index = _team_index(_first_place_player(round_state))
        deltas[winning_team_index] += 200
        return deltas

    first_place_player = _first_place_player(round_state)
    last_place_player = _last_place_player(round_state)
    opposing_team_index = 1 - _team_index(last_place_player)

    for player_index, won_cards in enumerate(round_state.won_trick_cards):
        team_index = _team_index(player_index)
        if player_index == last_place_player:
            team_index = opposing_team_index
        deltas[team_index] += _cards_points(won_cards)

    deltas[_team_index(first_place_player)] += _cards_points(round_state.hands[last_place_player])
    return deltas


def apply_round_scores(state: GameState, round_state: RoundState) -> list[int]:
    """
    계산된 라운드 점수를 게임 누적 점수에 반영한다.
    입력: state(수정 대상), round_state. 출력: [1팀 변화량, 2팀 변화량].
    수정하는 상태: state.team_scores.
    """

    deltas = calculate_round_score_deltas(round_state)
    state.team_scores[0] += deltas[0]
    state.team_scores[1] += deltas[1]
    return deltas
