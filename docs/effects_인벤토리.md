# 서버 effects 인벤토리

기준 소스:

- [`app/tichu_api.py`](/home/nugulman/dev/Happy_Boardgame/app/tichu_api.py): 게임 생성 시 초기 effect
- [`tichu/session_service.py`](/home/nugulman/dev/Happy_Boardgame/tichu/session_service.py): 액션 처리 중 effect 생성

정리 원칙:

- 여기서 말하는 `effects`는 게임 액션 결과와 함께 내려가는 게임 이벤트 목록이다.
- `snapshot`, `action_result`, `action_error`, `room_snapshot`은 전송 envelope이지 게임 effect는 아니다.
- 재접속 시 내려가는 최신 snapshot에는 보통 `effects`가 없다. 즉, effect는 "이번 요청에서 방금 발생한 이벤트"용이다.

## 현재 effect 목록

| type | 발생 시점 | 최소 필드 | 대상 | 화면 반응 | 자산 필요 | placeholder 가능 | 우선순위 | snapshot 복구 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `game_created` | `POST /games/tichu` 직후 | `type` | 전체 화면 | 새 게임 시작 알림 | 없음 | 가능 | 나중 | 아니오 |
| `initial_cards_dealt` | 게임 생성 직후, 또는 라운드 종료 후 다음 라운드 준비 직후 | `type`, `count` | 전체 화면 | 초반 패 분배 연출 시작 | 카드 자산 있으면 좋음 | 가능 | 나중 | 부분 가능 |
| `grand_tichu_declared` | 플레이어가 그랜드 티츄 응답 제출 | `type`, `player_index`, `declare` | 상단 배너, 플레이어 패널 | 선언 배너 표시, 초상화 `declared` 상태 반영. `declare=false`는 큰 배너 없음 | 없음 | 가능 | 1차 | 예 |
| `remaining_cards_dealt` | 4명 모두 grand tichu 응답 완료 후 나머지 6장 분배 | `type`, `count` | 전체 화면 | 추가 패 분배 연출 | 카드 자산 있으면 좋음 | 가능 | 나중 | 부분 가능 |
| `cards_exchanged` | 4명 모두 교환 카드 제출 완료 후 | `type` | 교환 UI | 교환 완료 표시, 교환 UI 종료 | 없음 | 가능 | 나중 | 부분 가능 |
| `phase_changed` | 준비 단계 전환, 용 수령자 선택 단계 진입, 라운드 종료 후 다음 단계 진입, 게임 종료 | `type`, `phase` | 화면 모드 전체 | 화면 상태 전환 | 없음 | 가능 | 나중 | 예 |
| `small_tichu_declared` | 플레이어가 스몰 티츄 선언 | `type`, `player_index` | 상단 배너, 플레이어 패널 | 선언 배너 표시, 초상화 `declared` 상태 반영 | 없음 | 가능 | 1차 | 예 |
| `cards_played` | 플레이 액션 성공 직후 | `type`, `player_index`, `cards` | 테이블 | 중앙 카드 영역을 자연스럽게 갱신하고 짧게 강조 | 카드 자산 있으면 좋음 | 가능 | 2차 | 부분 가능 |
| `player_passed` | 패스 액션 성공 직후 | `type`, `player_index` | 플레이어 패널 | 패스 표시, 말풍선/로그 | 없음 | 가능 | 나중 | 아니오 |
| `dragon_recipient_required` | 용 트릭에서 마지막 패스로 수령자 선택 단계 진입 | `type`, `winner_index`, `cards` | 용 선택 UI | 선택 모달 열기 | 없음 | 가능 | 나중 | 부분 가능 |
| `dragon_recipient_chosen` | 용 승자가 수령자 선택 완료 | `type`, `winner_index`, `recipient_index` | 전체 화면 | 선택 확인 배너 | 없음 | 가능 | 나중 | 아니오 |
| `turn_changed` | 다음 턴 플레이어가 정해질 때 | `type`, `player_index` | 플레이어 패널 | 현재 턴 하이라이트 갱신 | 없음 | 가능 | 2차 | 예 |
| `trick_won` | 일반 트릭 종료 또는 용 수령자 선택 완료 후 | `type`, `winner_index`, `cards` | 테이블, 플레이어 패널 | 중앙 카드 정리와 짧은 강조 | 카드 자산 있으면 좋음 | 가능 | 2차 | 부분 가능 |
| `round_finished` | 라운드 종료 직후 | `type`, `end_reason`, `score_deltas`, `tichu_outcomes` | 중앙 결과 패널, 요약 영역, 플레이어 패널 | 라운드 결과 패널 + 점수 요약 + 선언 실패 초상화 반영 | 없음 | 가능 | 1차 | 예 |
| `game_finished` | 게임 종료 직후 | `type`, `team_scores` | 중앙 결과 패널, 요약 영역 | 최종 결과 패널 + 최종 점수 요약 | 없음 | 가능 | 1차 | 예 |

## 구현 관점 분류

### snapshot 기반으로 복구 가능한 상태 effect

- `phase_changed`
- `turn_changed`
- `grand_tichu_declared`
- `small_tichu_declared`
- `round_finished`
- `game_finished`

이 타입들은 effect를 놓쳐도 최신 snapshot만으로 현재 상태를 다시 그릴 수 있다.

### snapshot은 복구되지만 연출 타이밍은 effect가 필요한 타입

- `initial_cards_dealt`
- `remaining_cards_dealt`
- `cards_exchanged`
- `cards_played`
- `dragon_recipient_required`
- `trick_won`

이 타입들은 상태 결과 자체는 snapshot에 어느 정도 남지만, "방금 일어났다"는 연출 트리거는 effect가 담당해야 한다.

### 일회성 effect에 가까운 타입

- `game_created`
- `player_passed`
- `dragon_recipient_chosen`

이 타입들은 로그/배너/모달 같은 일회성 표현에 가깝고, 최신 snapshot만으로는 동일 이벤트를 재생성하기 어렵다.

## Godot 연결 우선순위 제안

1. `turn_changed` -> 현재 턴 강조
2. `grand_tichu_declared`, `small_tichu_declared` -> 선언 배너
3. `cards_played` -> 카드 이동 연출
4. `trick_won` -> 트릭 승자 표시
5. `round_finished`, `game_finished` -> 결과 패널
6. `dragon_recipient_required`, `dragon_recipient_chosen` -> 용 선택 UI
