"""
보드게임 플랫폼 - Python API 진입점.

이 파일은 FastAPI 앱 인스턴스를 만들고, HTTP 요청에 응답하는 라우트를 등록합니다.
Docker 컨테이너 안에서 uvicorn이 이 앱을 로드해 서버를 띄웁니다.
"""

from fastapi import FastAPI

# FastAPI 앱 인스턴스 생성.
# title, description은 API 문서(Swagger UI)에 표시됩니다.
app = FastAPI(
    title="Boardgame API",
    description="보드게임 플랫폼 백엔드 (Python)",
    version="0.1.0",
)


@app.get("/")
def root():
    """
    루트 경로(/) 요청 시 호출됩니다.
    서버가 살아 있는지, API가 응답하는지 확인할 때 사용합니다.
    """
    return {"message": "ok"}


@app.get("/health")
def health():
    """
    헬스체크용 경로. 로드밸런서나 모니터링 툴이 서버 상태를 확인할 때 호출합니다.
    """
    return {"status": "ok"}
