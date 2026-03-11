# Godot 1차 연동 최소 스펙

목표: Godot가 백엔드 HTTP API만으로 티츄 상태를 표시하고 기본 액션을 보낼 수 있도록, 1차 연동에 필요한 최소 계약을 고정한다.

원칙:
- 서버 authoritative. 규칙 판단은 백엔드가 한다.
- Godot는 응답의 최신 snapshot으로만 화면을 갱신한다.
- 1차는 HTTP 요청-응답만 사용한다. WebSocket, 실시간 push, 고급 연출 해석은 제외한다.

---

## 1. 사용할 엔드포인트

### 서버 연결 확인

- `GET /health`
  - 용도: 서버 연결 확인
  - 성공 응답:

```json
{
  "status": "ok"
}
```

### 게임 생성 / 상태 조회

- `POST /games/tichu`
  - 용도: 새 게임 생성
  - 비고: 현재 구현에서는 생성 직후 응답 `viewer`가 항상 `0`이다.

- `GET /games/{game_id}?viewer={0..3}`
  - 용도: 특정 viewer 시점 상태 조회

### 준비 단계

- `POST /games/{game_id}/prepare/grand-tichu`
  - 요청:

```json
{
  "player_index": 0,
  "declare": false
}
```

- `POST /games/{game_id}/prepare/exchange`
  - 요청:

```json
{
  "player_index": 0,
  "to_left": {"suit": "S", "rank": 3},
  "to_team": {"suit": "H", "rank": 7},
  "to_right": {"suit": "D", "rank": 10}
}
```

### 액션 단계

- `POST /games/{game_id}/actions/small-tichu`
  - 요청:

```json
{
  "player_index": 0
}
```

- `POST /games/{game_id}/actions/play`
  - 요청:

```json
{
  "player_index": 0,
  "cards": [{"suit": "S", "rank": 3}],
  "call_rank": null
}
```

- `POST /games/{game_id}/actions/pass`
  - 요청:

```json
{
  "player_index": 0
}
```

- `POST /games/{game_id}/actions/dragon-recipient`
  - 용도: 용이 최종적으로 트릭을 먹은 뒤 상대 팀 수령자 선택
  - 요청:

```json
{
  "player_index": 0,
  "recipient_index": 1
}
```

### 보조 API

- `GET /games/{game_id}/legal-plays?viewer={0..3}`
  - 현재 턴 플레이어면 합법 플레이 목록 반환
  - 1차에서는 필수 아님

- `POST /games/{game_id}/preview-combo`
  - 선택 카드가 합법 shape인지 미리 확인
  - 1차에서는 필수 아님

---

## 2. Godot가 신뢰할 응답 필드

모든 게임 snapshot 응답은 아래 구조를 기준으로 사용한다.

```json
{
  "game_id": "string",
  "viewer": 0,
  "phase": "prepare_grand_tichu",
  "state": {
    "game": {
      "team_scores": [0, 0],
      "round_index": 0
    },
    "table": {
      "leader_index": null,
      "current_player_index": null,
      "trick_index": 0,
      "mahjong_call_rank": null,
      "current_trick_cards": []
    },
    "players": [
      {
        "player_index": 0,
        "hand_count": 8,
        "is_out": false,
        "declared_grand_tichu": false,
        "declared_small_tichu": false
      }
    ],
    "viewer_hand": [],
    "players_out_order": []
  },
  "available_actions": {
    "is_my_turn": false,
    "can_play": false,
    "can_pass": false,
    "can_declare_small_tichu": false,
    "can_choose_dragon_recipient": false,
    "can_declare_grand_tichu": true,
  },
  "effects": [],
  "round_result": {
    "end_reason": "double_victory",
    "score_deltas": [200, 0],
    "players_out_order": [0, 2]
  }
}
```

### 1차에서 실제로 사용할 필드

- 최상위
  - `game_id`
  - `viewer`
  - `phase`
  - `available_actions`
  - `effects`: 선택 사용
  - `round_result`: `round_over`, `game_over`에서만 사용

- `state.game`
  - `team_scores`
  - `round_index`

- `state.table`
  - `leader_index`
  - `current_player_index`
  - `trick_index`
  - `mahjong_call_rank`
  - `current_trick_cards`

- `state.players`
  - `player_index`
  - `hand_count`
  - `is_out`
  - `declared_grand_tichu`
  - `declared_small_tichu`

- `state.viewer_hand`
  - 본인 손패 전체 표시용

- `state.players_out_order`
  - 라운드 종료 상태 표시용

### 1차에서의 사용 규칙

- 손패 UI
  - `state.viewer_hand`만 사용
- 테이블 카드 UI
  - `state.table.current_trick_cards` 사용
- 현재 턴 표시
  - `state.table.current_player_index` 사용
- 플레이어 요약 UI
  - `state.players` 사용
- 버튼 활성화
  - 프론트에서 룰 재계산하지 않고 `available_actions`만 사용
- 화면 분기
  - `phase`로 결정
  - `prepare_grand_tichu`, `prepare_exchange`, `trick`, `await_dragon_recipient`, `game_over`

---

## 3. Godot 1차 클라이언트 흐름

### 시작

1. Godot 시작 시 `GET /health`
2. 새 게임 버튼 클릭 시 `POST /games/tichu`
3. 응답에서 `game_id`, `viewer`, `phase`, `state`, `available_actions` 저장

### 이후 상태 갱신

- 모든 POST 액션 응답은 최신 snapshot으로 취급한다.
- 액션 성공 후 별도 재조회 없이 응답의 `state`, `phase`, `available_actions`로 화면 갱신
- 필요 시에만 `GET /games/{game_id}?viewer=...` 재조회
- 라운드 종료 후 게임이 끝나지 않았으면 서버가 자동으로 다음 라운드 준비 단계로 넘긴다

### 에러 처리

- 에러 응답 형식:

```json
{
  "error": {
    "code": "INVALID_ACTION",
    "message": "selected cards are not a legal play"
  }
}
```

- 1차에서는 `message`를 그대로 표시하거나 디버그 로그로 남긴다.

### effects 처리

- `effects`는 1차에서 필수 계약이 아니다.
- 우선순위:
  - 1순위: `state`, `phase`, `available_actions`
  - 2순위: `effects`
- 1차에서는 `effects`를 디버그 로그 또는 간단한 텍스트 표시까지만 사용한다.

---

## 4. 1차 UI 범위

반드시 구현할 것:
- 서버 연결 상태 표시
- 새 게임 생성
- 손패 표시
- 테이블 카드 표시
- 현재 턴 표시
- 버튼 활성/비활성 표시
- 그랜드 티츄 / 교환 / 스몰 티츄 / 플레이 / 패스 / 용 수령자 선택
- 다음 라운드 버튼은 없음. 자동 전환

1차에서 제외:
- WebSocket
- 실시간 멀티플레이 push 동기화
- `effects` 기반 고급 연출
- `legal-plays`, `preview-combo` 기반 고급 UX

---

## 5. 체크리스트

- `GET /health` 성공 시 연결 상태가 표시된다.
- `POST /games/tichu` 후 `game_id`, `phase`, `viewer_hand`가 저장된다.
- `GET /games/{game_id}` 호출 시 viewer별 손패가 다르게 보인다.
- `phase`에 따라 준비 화면과 플레이 화면이 바뀐다.
- `available_actions` 값에 따라 버튼 활성/비활성이 바뀐다.
- `POST /actions/play` 성공 시 응답 `state.table.current_trick_cards`가 갱신된다.
- `POST /actions/pass` 성공 시 응답 `state.table.current_player_index`가 갱신된다.
- 라운드 종료 직후 자동 전환된 snapshot에도 `round_result`가 표시된다.
- 자동 전환 후 새 라운드의 초기 손패 8장이 표시된다.
