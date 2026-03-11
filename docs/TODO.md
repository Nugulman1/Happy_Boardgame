# TODO

기준 계획: **티츄 인게임 로직 계획** (6단계) + **Godot 프론트 연동 1차**
원칙: **규칙 판단은 백엔드, 화면/입력/연출은 Godot**

---

## 최우선

- Godot `play` 요청에 참새 콜 `call_rank` 입력 UI 추가
  - 현재 백엔드는 `POST /games/{game_id}/actions/play`의 `call_rank`를 지원하지만 Godot는 항상 `null`만 보낸다.
  - `state.table.mahjong_call_rank`도 함께 표시해 콜 상태를 화면에서 확인 가능하게 만들기
- Godot 버튼 활성/비활성 로직을 서버 `available_actions` 기준으로 정렬
  - `can_play`
  - `can_pass`
  - `can_declare_grand_tichu`
  - `can_declare_small_tichu`
  - `can_choose_dragon_recipient`
- Godot 화면에 아직 미사용인 snapshot 필드 반영
  - `state.players` 플레이어 요약
  - `state.table.leader_index`
  - `state.table.trick_index`
  - `state.players_out_order`
- Godot에 보조 API 연결
  - `GET /legal-plays`
  - `POST /preview-combo`
- POST 응답의 `effects`를 간단 로그 또는 디버그 패널로 표시

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
- 필요 시 WebSocket 전환 또는 추가
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
  - preview-combo
- HTTP 기준 핵심 플레이 흐름 테스트 재검증
  - 새 게임 생성 → 준비 단계 → 스몰 티츄/플레이/패스 → 라운드 종료 → 다음 라운드
  - viewer별 직렬화 차이 점검
  - `legal-plays`, `preview-combo` 보조 API 점검
- Godot 1차 연동 최소 스펙 문서화
  - `docs/Godot_1차_연동_최소_스펙.md`
- Godot 프로젝트 기본 구조 만들기
- HTTP 통신 클라이언트 구성
  - 백엔드 `/health` 연결 확인
  - 게임 생성/상태 조회/액션 요청 연결
- Godot 전역 상태 저장소 설계
  - `game_id`, `viewer`, `phase`, `state`, `available_actions`, `round_result`, `effects` 저장
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
