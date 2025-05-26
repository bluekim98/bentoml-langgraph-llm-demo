from langgraph.pregel import Pregel

from app.graph import get_compiled_graph


def test_get_compiled_graph_returns_valid_app():
    """
    get_compiled_graph() 함수가 유효한 Pregel 인스턴스를 반환하는지 테스트합니다.
    """
    # 처리 과정 1: 그래프 컴파일
    app = get_compiled_graph()

    # 처리 과정 2: 반환 값 검증
    assert app is not None, "컴파일된 앱은 None이 아니어야 합니다."
    assert isinstance(app, Pregel), f"컴파일된 앱은 Pregel 인스턴스여야 합니다. 실제 타입: {type(app)}" 