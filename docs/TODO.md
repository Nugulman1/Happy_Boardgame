# TODO

기준 계획: **티츄 인게임 로직 계획** (6단계) + **Godot 프론트 연동 1차**
원칙: **규칙 판단은 백엔드, 화면/입력/연출은 Godot**

---

## 최우선

- socket 실험
  - viewer 전환 중 중복 연결/기존 연결 정리 동작 점검
  - 액션 HTTP 응답과 WebSocket push의 중복 반영 없는지 확인
  - 연결 끊김/재연결 시 최신 snapshot 복구 흐름 점검
  - Godot에서 실제 장시간 실행 시 소켓 상태 표시와 helper API 동작 같이 확인
- WebSocket 전환
  - 현재는 하이브리드(WebSocket push + HTTP action)까지 연결됐다.
  - 액션을 WebSocket으로 올릴지, helper API를 유지할지 다음 단계 방향 정리
  - reconnect/backoff, 연결 상태 표시, viewer 고정 정책을 실제 사용 기준으로 다듬기
- 멀티플레이 세션 계층 설계
  - viewer 고정 클라이언트 기준으로 actor 테스트 UI를 어떻게 대체할지 정리
  - 방 입장, 재접속, 관전자 여부, 턴 주체 검증 책임을 HTTP/WebSocket 경계에서 정리
- Godot helper UX 정리
  - 참새 콜 강제 상황에서 `legal-plays`와 `play-preview` 메시지를 더 직관적으로 노출
  - exchange 구간도 서버 계약 기반으로 활성/비활성 신호를 정리할지 결정

---

## 다음

- Godot UI 구조 정리
  - 단일 테스트 화면에서 섹션 분리
  - 플레이어 요약/테이블/로그 영역 분리
- 에러 응답을 Godot UI/로그에 더 명확히 표시하는 흐름 보강
- helper API 연동 후 선택 카드 UX 다듬기
  - 현재 선택 카드 하이라이트와 합법 조합 안내 정리

---

## 그다음

- 서버 응답의 게임 이벤트를 Godot 연출로 해석하는 계층 만들기
- 캐릭터 애니메이션/카드 이동 연출 연결
- 액션 결과에 따른 이펙트 재생 규칙 정리
- UI/연출과 실제 규칙 상태의 동기화 테스트

---

## 추후

- Godot 엔진 고도화
  - 씬 구조 정리
  - 공용 컴포넌트화
  - 리소스 관리
- 세션/게임 서버 계층 확장
  - 방 관리
  - 액션 브로드캐스트
  - 재접속
  - 저장
- 멀티플레이 실시간 동기화 개선

---

## 보류

- DB 영속화
- 로그인/계정
- 매칭 시스템

---

## 완료

- 티츄 인게임 로직 3단계 일부
- 티츄 인게임 로직 4단계
- 티츄 인게임 로직 5단계 코어
- 티츄 인게임 로직 6단계 점수 처리
- API 관련 코드 점검
  - 세션 저장 구조 점검
  - 직렬화/응답 필드 점검
  - phase 전이 및 effects 점검
  - 엔드포인트/에러 응답 점검
- 백엔드 코드 구조 점검
  - 규칙 함수와 API 계층 분리
  - `game_id` 기준 메모리 저장 구조 정리
  - 에러 응답 형식 통일
- 백엔드 게임 세션/API 계층 만들기
- `GameState`, `RoundState` HTTP 응답용 JSON 직렬화 규칙 정리
- 티츄 준비/액션 흐름용 엔드포인트 설계 및 1차 구현
  - 새 게임 시작
  - 현재 상태 조회
  - 그랜드 티츄 선언
  - 카드 교환
  - 스몰 티츄 선언
  - 카드 내기
  - 패스
  - 용 수령자 선택
  - 자동 다음 라운드 / game over 전환
- 보조 API 1차 구현
  - legal-plays
  - play-preview
- 하이브리드 WebSocket 전환 1차
  - `WS /ws/games/{game_id}?viewer=...`
  - `game_id -> viewer -> websocket` 메모리 연결 관리자
  - HTTP 액션 성공 후 viewer별 snapshot 브로드캐스트
  - Godot `WebSocketPeer` 연결/폴링과 snapshot 반영
  - HTTP 액션 응답과 WebSocket push 중복 반영 방지
- HTTP 기준 핵심 플레이 흐름 테스트 재검증
  - 새 게임 생성 → 준비 단계 → 스몰 티츄/플레이/패스 → 라운드 종료 → 다음 라운드
  - viewer별 직렬화 차이 점검
  - `legal-plays`, `play-preview` 보조 API 점검
- WebSocket 테스트 추가
  - 초기 snapshot 수신
  - 액션 broadcast
  - reconnect 시 최신 snapshot 수신
- Godot 1차 연동 최소 스펙 문서화
  - `docs/Godot_1차_연동_최소_스펙.md`
- Godot 프로젝트 기본 구조 만들기
- HTTP 통신 클라이언트 구성
  - 백엔드 `/health` 연결 확인
  - 게임 생성/상태 조회/액션 요청 연결
- Godot 전역 상태 저장소 설계
  - `game_id`, `viewer`, `phase`, `state`, `available_actions`, `round_result`, `effects`, `legal_plays`, `play_preview` 저장
  - 액션 응답 snapshot 기준 상태 갱신
- 서버 상태를 화면에 반영하는 기본 테스트 UI 만들기
  - 손패
  - 테이블 카드
  - 현재 턴
  - round result / game over
- 사용자 입력을 서버 액션으로 보내는 1차 흐름 만들기
  - grand tichu
  - exchange
  - small tichu
  - play
  - pass
  - dragon recipient 선택
- Godot 테스트 UI에 현재 라운드 정보 반영
  - `mahjong_call_rank`
  - `leader_index`, `trick_index`
  - `state.players`
  - `players_out_order`
- Godot 액션 버튼을 `available_actions` 기준으로 정렬
  - `play`
  - `pass`
  - `grand tichu`
  - `small tichu`
  - `dragon recipient`
- Godot helper API 1차 연동
  - `GET /legal-plays`
  - `POST /games/{game_id}/play-preview`
- Godot `play` 요청에 참새 콜 `call_rank` 입력 UI 추가
- POST 응답의 `effects` 로그 표시
- 시나리오 하네스 추가
  - `tichu/scenario_harness.py`
  - 고정 시나리오/CLI로 참새 콜, 용 수령자, 라운드 종료 직전 흐름 재현
- 시나리오 하네스 예외상황 실험 추가
  - `legal_plays()` 조회 지원
  - 폭탄 예외상황, 참새 콜 강제 패스 차단, 봉황 포함 케이스 실험
  - 결과 문서 `docs/예외상황 테스트.md`
