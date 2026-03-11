# 서버 effects 인벤토리

기준 소스:

- [`app/tichu_api.py`](/home/nugulman/dev/Happy_Boardgame/app/tichu_api.py): 게임 생성 시 초기 effect
- [`tichu/session_service.py`](/home/nugulman/dev/Happy_Boardgame/tichu/session_service.py): 액션 처리 중 effect 생성

정리 원칙:

- 여기서 말하는 `effects`는 게임 액션 결과와 함께 내려가는 게임 이벤트 목록이다.
- `snapshot`, `action_result`, `action_error`, `room_snapshot`은 전송 envelope이지 게임 effect는 아니다.
- 재접속 시 내려가는 최신 snapshot에는 보통 `effects`가 없다. 즉, effect는 "이번 요청에서 방금 발생한 이벤트"용이다.

## 현재 effect 목록

| type | 발생 시점 | 최소 필드 | Godot 의미 | snapshot 복구 |
| --- | --- | --- | --- | --- |
| `game_created` | `POST /games/tichu` 직후 | `type` | 새 게임 시작 연출, 첫 진입 토스트 | 아니오. 생성 순간만 알림 |
| `initial_cards_dealt` | 게임 생성 직후, 또는 라운드 종료 후 다음 라운드 준비 직후 | `type`, `count` | 초반 패 분배 연출 시작 | 부분 가능. 손패/phase는 snapshot에 있지만 "방금 나눠졌다"는 순간성은 없음 |
| `grand_tichu_declared` | 플레이어가 그랜드 티츄 응답 제출 | `type`, `player_index`, `declare` | 선언 배너 또는 "선언 안 함" 로그 표시 | 예. `declared_grand_tichu` 상태와 응답 완료 여부는 snapshot에서 복구 가능 |
| `remaining_cards_dealt` | 4명 모두 grand tichu 응답 완료 후 나머지 6장 분배 | `type`, `count` | 추가 패 분배 연출 | 부분 가능. 손패 수와 phase는 snapshot에 있지만 분배 모션 자체는 effect 의존 |
| `cards_exchanged` | 4명 모두 교환 카드 제출 완료 후 | `type` | 교환 완료 연출, 교환 UI 종료 | 부분 가능. 결과 손패와 phase는 snapshot에 있지만 "교환 완료" 타이밍은 effect 의존 |
| `phase_changed` | 준비 단계 전환, 용 수령자 선택 단계 진입, 라운드 종료 후 다음 단계 진입, 게임 종료 | `type`, `phase` | 화면 모드 전환 트리거 | 예. `snapshot.phase`가 단일 소스 |
| `small_tichu_declared` | 플레이어가 스몰 티츄 선언 | `type`, `player_index` | 선언 배너, 캐릭터 리액션 | 예. `declared_small_tichu` 상태는 snapshot에서 복구 가능 |
| `cards_played` | 플레이 액션 성공 직후 | `type`, `player_index`, `cards` | 카드 이동 연출, 테이블 적재 애니메이션 | 부분 가능. 테이블 카드 상태는 snapshot에 있지만 "누가 지금 냈는지"와 즉시 연출 타이밍은 effect가 더 명확 |
| `player_passed` | 패스 액션 성공 직후 | `type`, `player_index` | 패스 표시, 말풍선/로그 | 아니오. pass 로그는 snapshot에 누적되지 않음 |
| `dragon_recipient_required` | 용 트릭에서 마지막 패스로 수령자 선택 단계 진입 | `type`, `winner_index`, `cards` | 용 수령자 선택 모달 열기 | 부분 가능. `await_dragon_recipient` phase 자체는 snapshot으로 복구 가능하지만 즉시 모달 트리거는 effect가 편함 |
| `dragon_recipient_chosen` | 용 승자가 수령자 선택 완료 | `type`, `winner_index`, `recipient_index` | 선택 확인 배너, 화살표/하이라이트 | 아니오. 선택 순간 자체는 effect 전용 |
| `turn_changed` | 다음 턴 플레이어가 정해질 때 | `type`, `player_index` | 현재 턴 하이라이트 갱신 | 예. `state.table.current_player_index`로 복구 가능 |
| `trick_won` | 일반 트릭 종료 또는 용 수령자 선택 완료 후 | `type`, `winner_index`, `cards` | 트릭 획득 연출, 카드 회수 애니메이션 | 부분 가능. 승자에 따른 이후 턴 상태는 snapshot에 남지만 획득 카드 묶음과 즉시 회수 연출은 effect 의존 |
| `round_finished` | 라운드 종료 직후 | `type`, `end_reason`, `score_deltas` | 라운드 결과 패널, 점수 증감 연출 | 예. `round_result`로 복구 가능 |
| `game_finished` | 게임 종료 직후 | `type`, `team_scores` | 최종 승패 화면, 게임 종료 배너 | 예. `phase=game_over`, `team_scores`로 복구 가능 |

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

