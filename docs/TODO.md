# TODO

기준 원칙: **규칙 판단은 백엔드, 화면/입력/연출은 Godot**

---

## 최우선

1. 캐릭터 프로필, 카드 모양, 테이블 등 이미지 추가 및 연결
2. UI, UX 실제 사용처럼 변경
3. 시나리오와 직접 테스트 할 부분 테스트
4. 코드 구조 이해 후 리팩토링

- 이미지/UI 자산 연결
  - 플레이어별 프로필 이미지, 카드 스프라이트, 테이블 배경을 현재 placeholder 슬롯에 연결
  - `PortraitSlot`, 카드 칩, 결과/선언 패널을 실제 자산 기준으로 교체
  - 툴팁/슬롯 이름 규칙을 실제 파일 네이밍 규칙과 맞추기

- 실제 사용 기준 UI / UX 정리
  - 현재 테스트 중심 배치를 실제 플레이 흐름 기준으로 더 다듬기
  - 플레이어 4칸 패널, 선언 배너, 결과 패널, 손패 섹션 시선 흐름 정리
  - 작은 창/스크롤 상황에서도 답답하지 않도록 정보 밀도 다시 조정
  - 로비/인게임/개발 컨트롤 분리감 더 강화

- 시나리오 기반 직접 테스트
  - room 생성, join, start, reconnect, leave 흐름 점검
  - grand/small tichu, exchange, play/pass, dragon recipient, round/game result 확인
  - 작은 창, 스크롤, viewer/actor 전환, direct dev game 경로 포함해 수동 테스트
  - [테스트 목록.md](/home/nugulman/dev/Happy_Boardgame/docs/%ED%85%8C%EC%8A%A4%ED%8A%B8%20%EB%AA%A9%EB%A1%9D.md) 기준으로 체크리스트 계속 보강

- 코드 구조 이해 후 리팩토링
  - `Main.gd`에서 레이아웃/상태 갱신/프레젠테이션 소비 책임 더 분리
  - `app/tichu_api.py`에 몰린 room/socket/auth 로직 정리
  - room 관련 코드와 game 관련 코드 분리
  - 가능하면 presentation/event 처리와 overlay UI 제어도 별도 스크립트로 이동

---

## 다음

- placeholder 연출을 더 완성도 있는 2D 연출로 교체
  - 플레이어별 기본/선언/실패 초상화 자산 연결
  - 카드 출현/회수 강조 연출 정리
  - 선언 배너와 라운드 종료 패널 시안 고정
  - 사운드/SFX 연결

- 멀티플레이 안정화 마무리
  - room/game reconnect UX 점검
  - 연결 끊김 중 버튼 비활성화/상태 메시지 다듬기
  - 4클라이언트 수동 테스트 체크리스트 정리
  - host leave / room 종료 시 다른 클라이언트 표시 보강

- Godot 구조 분리
  - `Main.gd`에서 로비 흐름과 인게임 흐름 분리
  - room 관련 코드와 game 관련 코드 분리
  - 가능하면 presentation/event 처리와 overlay UI 제어도 별도 스크립트로 이동

- 서버 구조 분리
  - `app/tichu_api.py`에 몰린 room/socket/auth 로직을 파일 단위로 정리
  - room 모델/유틸/socket manager를 나누기

---

## 그다음

- 2D 캐릭터/연출 확장
  - effect 해석 계층 위에 실제 2D 초상화 교체/리액션 붙이기
  - 티츄 선언, 실패, 승리, 라운드 종료 컷인 연결
  - 필요하면 Spine/Live2D/간단 스프라이트 애니메이션 중 어떤 방식이 맞는지 검토

- 테스트 목록 만들어 시나리오 && 직접 테스트 하며 디버깅

- 3D 전환은 추후 별도 검토
  - 현재 단계에서는 보류
  - 나중에 전문가 투입 시 2D UI 위에 별도 레이어로 붙일 수 있는 구조인지 확인

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
