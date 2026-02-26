# ============================================================
# Python 앱을 담을 Docker 이미지 정의
# ============================================================
# 빌드: docker build -t boardgame .
# 실행: docker run -p 8000:8000 boardgame
# ============================================================

# 베이스 이미지: 공식 Python 3.12 경량판. Alpine 기반이 아니라 Debian slim (호환성 좋음)
FROM python:3.12-slim

# 컨테이너 안에서 앱 코드가 놓일 작업 디렉터리. 이후 COPY, RUN은 모두 이 경로 기준
WORKDIR /app

# 의존성 파일만 먼저 복사 → 레이어 캐시 활용. requirements가 안 바뀌면 아래 pip는 재사용됨
COPY requirements.txt .

# pip로 의존성 설치. --no-cache-dir 은 이미지 용량 줄이기 위함
RUN pip install --no-cache-dir -r requirements.txt

# 앱 소스 복사. .dockerignore 에 의해 불필요한 파일은 제외됨
COPY app/ ./app/

# 컨테이너가 실행될 때 돌릴 명령.
# uvicorn이 app/main.py 의 app 객체를 로드하고, 0.0.0.0으로 listen 해야 호스트에서 접속 가능
# --reload: 코드 변경 시 자동 재시작 (docker-compose 의 volume 마운트와 함께 개발 시 유용)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
