# DB 기술 정리

## 목적

- 현재 메모리 기반 `room / game / seat token / reconnect` 구조를 DB 기반으로 옮기기 위한 기준 문서다.
- 목표는 "DB를 붙인다"가 아니라, 서버 재시작 후에도 방과 게임을 복구할 수 있게 만드는 것이다.

---

## 최종 선택 스택

- DB: `PostgreSQL`
- Python DB 계층: `SQLAlchemy 2.x`
- 마이그레이션: `Alembic`
- PostgreSQL 드라이버: `psycopg` 3
- API 서버: 기존 `FastAPI` 유지

한 줄 요약:

`FastAPI + PostgreSQL + SQLAlchemy + Alembic + psycopg3`

---

## 왜 이 조합을 선택하는가

### 1. PostgreSQL

- 멀티플레이 서버에서 중요한 트랜잭션, 원자성, 락 지원이 강하다.
- `room`, `game`, `seat token`, `result`, `event log`처럼 관계가 있는 데이터를 다루기 좋다.
- 서버 재시작 후 복구, 게임 결과 저장, 이후 리플레이/전적 확장까지 자연스럽게 이어진다.

### 2. SQLAlchemy 2.x

- 단순 CRUD를 넘어서 복잡한 도메인 구조를 다룰 때 유연하다.
- 현재 `tichu/` 규칙 객체와 DB 저장용 모델을 분리하기 좋다.
- 나중에 쿼리가 복잡해져도 SQL에 가까운 방식과 ORM 방식을 같이 쓸 수 있다.

### 3. Alembic

- 테이블 구조 변경 이력을 코드로 관리할 수 있다.
- `rooms`, `games`, `seat_tokens`, `game_events`를 순서대로 추가해도 안전하다.
- 팀 작업에서 "내 로컬 DB만 되는 상태"를 줄여 준다.

### 4. psycopg 3

- 새 프로젝트 기준으로 PostgreSQL 드라이버 선택지 중 가장 자연스럽다.
- SQLAlchemy와 조합하기 좋고, 이후 동기/비동기 방향 모두 대응하기 쉽다.

---

## SQLite와 PostgreSQL 차이

사용 경험 기준으로 체감이 큰 차이만 정리한다.

### SQLite

- 파일 하나로 동작한다.
- 설정이 거의 필요 없고, 개인용 테스트나 작은 도구에 매우 편하다.
- 로컬 단일 프로세스 중심 개발에는 빠르게 붙이기 좋다.

### PostgreSQL

- 별도 DB 서버 프로세스로 동작한다.
- 여러 연결과 동시성 처리에 더 강하다.
- 트랜잭션, 락, 인덱스, 제약조건, 확장 기능이 훨씬 풍부하다.
- 운영 환경과 멀티플레이 서버 구조에 더 적합하다.

### 이 프로젝트에서 중요한 차이

#### 1. 동시성

- SQLite도 트랜잭션은 있지만, 쓰기 동시성에 제약이 크다.
- PostgreSQL은 여러 사용자가 동시에 방에 들어오고, 같은 게임 상태를 읽고, 특정 시점에 한 요청만 상태를 바꾸게 제어하는 데 더 적합하다.

예:

- 플레이어 2명이 거의 동시에 액션 요청
- 재접속과 leave 요청이 겹침
- host 시작 요청과 마지막 입장 요청이 겹침

이런 상황에서 PostgreSQL 쪽이 구조적으로 안전하게 설계하기 쉽다.

#### 2. 락과 무결성

- SQLite는 단순한 앱에는 충분하지만, 멀티플레이 서버에서 "이 row를 지금 수정 중이니 다른 요청은 잠깐 기다려라" 같은 제어를 적극적으로 쓰기엔 PostgreSQL이 훨씬 낫다.
- PostgreSQL은 행 단위 잠금, 외래 키, 체크 제약, 유니크 제약을 더 적극적으로 활용하기 좋다.

#### 3. 운영 관점

- SQLite는 파일 백업과 로컬 실험엔 편하다.
- PostgreSQL은 Docker, 운영 서버, 백업, 모니터링, 확장 관점에서 더 표준적인 선택이다.

#### 4. 확장성

- SQLite는 "지금 당장 저장만 하자"에는 좋다.
- PostgreSQL은 "게임 결과 저장 -> 전적 -> 리플레이 -> 계정 -> 매칭"으로 가는 경로에 더 잘 맞는다.

정리하면:

- SQLite는 작고 빠르게 시작하기 좋은 DB
- PostgreSQL은 멀티플레이 서버와 장기 확장에 맞는 DB

---

## 왜 SQLModel이 아니라 SQLAlchemy인가

- SQLModel은 시작은 편하다.
- 하지만 이 프로젝트는 단순 게시판형 CRUD보다 게임 상태 복구와 도메인 분리가 더 중요하다.
- `app/tichu_api.py`의 세션 흐름과 `tichu/session_service.py`의 규칙 상태를 나눠서 설계해야 하므로, 더 유연한 SQLAlchemy 쪽이 맞다.
- 나중에 SQLModel로 감싼 기능보다 SQLAlchemy 자체 기능을 더 자주 쓰게 될 가능성이 높다.

즉:

- SQLModel: 빠르게 시작하기 쉬움
- SQLAlchemy: 오래 가는 구조를 만들기 쉬움

현재 프로젝트는 두 번째가 더 중요하다.

---

## 구조를 어떻게 바꿀지 큰 그림

현재는 `app/tichu_api.py` 안에 다음 책임이 많이 모여 있다.

- HTTP 라우팅
- WebSocket 연결 관리
- room 메모리 상태
- game 메모리 상태
- seat token 처리
- room -> game 전이 흐름

DB 전환 이후에는 아래처럼 나누는 것이 목표다.

### 1. API 계층

역할:

- HTTP / WebSocket 입구
- 요청 파싱
- 인증 정보 추출
- 서비스 호출
- 응답/에러 변환

예상 위치:

- `app/api/rooms.py`
- `app/api/games.py`
- `app/api/ws_rooms.py`
- `app/api/ws_games.py`

### 2. 유스케이스 계층

역할:

- 방 생성
- 방 입장
- 게임 시작
- 액션 제출
- 재접속 복구

예상 위치:

- `app/services/room_service.py`
- `app/services/game_service.py`
- `app/services/reconnect_service.py`

여기는 "무슨 일을 할지"를 조합하는 계층이다.

### 3. 저장소 계층

역할:

- DB에서 room 읽기/쓰기
- DB에서 game 읽기/쓰기
- seat token 조회/저장
- event log 저장

예상 위치:

- `app/repositories/room_repository.py`
- `app/repositories/game_repository.py`
- `app/repositories/seat_token_repository.py`
- `app/repositories/game_event_repository.py`

여기는 SQLAlchemy 모델과 쿼리를 담당한다.

### 4. DB 모델 계층

역할:

- 테이블 구조 정의
- 관계 정의
- 인덱스/제약 정의

예상 위치:

- `app/db/models/room.py`
- `app/db/models/game.py`
- `app/db/models/seat_token.py`
- `app/db/models/game_event.py`

### 5. 게임 규칙 계층

역할:

- 티츄 규칙 판단
- 상태 전이
- 합법 액션 검증

현재 위치:

- `tichu/session_service.py`
- `tichu/*.py`

여기는 가능한 한 DB를 모르도록 유지하는 것이 좋다.

---

## 저장 대상과 메모리 대상 구분

### DB에 저장할 것

- room 기본 정보
- room 상태 (`lobby`, `in_game`, `closed`)
- 좌석 점유 상태
- seat token
- game 기본 정보
- 현재 게임/라운드 복구에 필요한 최소 상태
- 최종 결과
- 필요하면 event log

### 메모리에만 둘 수 있는 것

- 현재 WebSocket 연결 객체
- reconnect backoff 같은 UI/세션 보조 정보
- 일시적인 presentation queue

기준은 단순하다.

- 서버가 꺼져도 남아 있어야 하면 DB
- 서버가 다시 떠도 새로 만들어도 되면 메모리

---

## DB 전환 순서 큰 그림

### 1단계. DB 뼈대 추가

- `requirements.txt`에 DB 관련 패키지 추가
- SQLAlchemy engine / session 설정 추가
- Alembic 초기화
- 첫 마이그레이션 생성

### 2단계. room 저장부터 이전

- 메모리 `_rooms`를 바로 없애지 말고, 먼저 DB 기반 조회/저장 경로를 만든다.
- `create room`, `join room`, `leave room`, `start room` 흐름을 DB로 옮긴다.

이 단계 목표:

- 서버 재시작 후 room 복구 가능
- seat token 유지 가능

### 3단계. game 저장 구조 추가

- `_sessions`를 대체할 game 저장 모델 추가
- 최소 복구 가능한 게임 상태를 JSON 또는 정규화된 컬럼으로 저장
- 액션 처리 후 상태 저장을 같은 흐름에서 묶는다

이 단계 목표:

- 서버 재시작 후 게임 복구 가능
- reconnect 시 현재 상태 재조회 가능

### 4단계. room/game 흐름 분리

- API 파일에서 DB 직접 접근 제거
- 서비스 계층과 repository 계층으로 역할 분리
- `tichu/session_service.py`는 규칙 전용으로 더 선명하게 유지

### 5단계. 결과/로그 확장

- game result 저장
- event log 저장
- 이후 리플레이/전적 기능 기반 마련

---

## 상태 저장 방식 초안

초기에는 완전 정규화보다 "복구 가능한 최소 구조"가 더 중요하다.

추천 방향:

- `rooms` 테이블: 방 메타데이터
- `room_seats` 테이블: 좌석 점유/토큰/접속 기준 정보
- `games` 테이블: 현재 게임 상태 스냅샷
- `game_events` 테이블: 선택적 이벤트 로그

여기서 `games.state_snapshot`은 초기에 JSON 컬럼으로 두는 편이 현실적이다.

이유:

- 티츄 상태 구조가 이미 파이썬 객체 중심으로 만들어져 있다.
- 처음부터 모든 라운드 상태를 컬럼 단위로 쪼개면 설계 비용이 너무 크다.
- 먼저 "복구 가능"을 만들고, 이후 자주 조회하는 값만 분리하는 편이 낫다.

---

## 이 문서 기준 현재 권장 방향

- DB는 바로 `PostgreSQL`로 간다.
- ORM은 `SQLAlchemy`로 간다.
- 마이그레이션은 처음부터 `Alembic`을 붙인다.
- 드라이버는 `psycopg3`를 쓴다.
- 구조 개편은 `room 저장 -> game 저장 -> 계층 분리` 순서로 진행한다.
- 게임 규칙 계층은 DB 세부사항을 모르게 유지한다.

---

## 다음 작업 후보

1. `requirements.txt`에 DB 패키지 추가
2. `app/db/` 초기 구조 생성
3. SQLAlchemy base / session / config 추가
4. Alembic 초기화
5. `rooms`, `room_seats` 첫 테이블 설계
