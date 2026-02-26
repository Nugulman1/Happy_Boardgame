# schema/

보드게임 IR의 형식·검증 규칙. 개념·필드·예시는 [docs/코드 구조 요약.md](../docs/코드 구조 요약.md) 참고.

- **game-ir.schema.json**: IR 구조 정의(JSON Schema). 검증·자동완성용. 개념 정한 뒤 확장.
- **IR 파일**: JSON 또는 YAML, UTF-8. 경로 `games/{game_id}/game.yaml` (엔진이 여기서 로드).

