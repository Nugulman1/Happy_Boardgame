# TODO

기준 원칙: **규칙 판단은 백엔드, 화면/입력/연출은 Godot**

---

## 최우선

- 3D 캐릭터 만들어서 넣기
  - 3D 캐릭터 자산 확보 방식 결정
  - 최소 1캐릭터로 Godot 씬에 붙일 수 있는 구조 만들기
  - 가능하면 `idle`, `declare`, `react` 정도 재생 가능한 상태까지 맞추기

- UI / UX 개선
  - 현재 테스트 UI를 실제 플레이 화면 구조에 가깝게 다듬기
  - 임시 announcement / table motion / score summary를 더 보기 좋은 배너/패널 형태로 정리
  - 로비/인게임 섹션 재배치
  - 상태/오류/버튼 피드백 정리

- 연출/UI 테스트 추가
  - Godot presentation event 수동 테스트 체크리스트 만들기
  - 선언 배너, 카드 이동, 턴 강조, 라운드 점수 표시 확인 항목 정리
  - 가능하면 headless 로드 외에 최소 smoke test 범위 늘리기

---

## 다음

- placeholder 연출을 실제 연출로 교체
  - `cards_played`를 실제 카드 이동 애니메이션으로 바꾸기
  - `trick_won`을 카드 회수/획득 연출로 바꾸기
  - `grand_tichu_declared`, `small_tichu_declared`를 실제 선언 배너로 바꾸기
  - 사운드/SFX 연결

- 멀티플레이 안정화 마무리
  - room/game reconnect UX 점검
  - 연결 끊김 중 버튼 비활성화/상태 메시지 다듬기
  - 4클라이언트 수동 테스트 체크리스트 정리
  - host leave / room 종료 시 다른 클라이언트 표시 보강

- Godot 구조 분리
  - `Main.gd`에서 로비 흐름과 인게임 흐름 분리
  - room 관련 코드와 game 관련 코드 분리
  - 가능하면 presentation/event 처리도 별도 스크립트로 이동

- 서버 구조 분리
  - `app/tichu_api.py`에 몰린 room/socket/auth 로직을 파일 단위로 정리
  - room 모델/유틸/socket manager를 나누기

---

## 그다음

- 캐릭터 애니메이션/카드 연출 확장
  - effect 해석 계층 위에 실제 캐릭터 리액션 붙이기
  - 티츄 선언, 승리, 패배, 라운드 종료 컷인 연결
  - 2D placeholder를 유지할지, SubViewport 기반 3D로 갈지 최종 방향 고정

---

## 추후

- DB 영속화
  - room / game 저장
  - 재시작 후 복구
  - 리플레이 / 전적

- 로그인/계정

- 매칭 시스템 / 관전자

- 타이머 룰 옵션
  - 레디
  - 액션 제한 시간

- 튜토리얼 / 가이드

- AI / 자동 플레이 실험

---
