from typing import TypedDict, Dict, Any, Optional

from langgraph.constants import END
from langgraph.graph import StateGraph
from langgraph.pregel import Pregel

from app.analyze_review_node import analyze_review_for_graph
from app.save_result_node import save_analysis_result_node
from app.schemas import AgentState


def create_graph() -> StateGraph:
    """
    정의된 상태, 노드, 엣지를 사용하여 StateGraph 인스턴스를 생성하고 반환합니다.
    app.schemas.AgentState를 그래프의 상태 정의로 사용합니다.

    Returns:
        StateGraph: 구성된 StateGraph 인스턴스입니다.
    """
    graph = StateGraph(AgentState)

    graph.add_node("analyze_review_node", analyze_review_for_graph)
    graph.add_node("save_result_node", save_analysis_result_node)

    graph.set_entry_point("analyze_review_node")

    graph.add_edge("analyze_review_node", "save_result_node")
    graph.add_edge("save_result_node", END)

    return graph


def get_compiled_graph() -> Pregel:
    """
    create_graph()를 호출하여 StateGraph를 얻고, 이를 컴파일하여 실행 가능한 Pregel 인스턴스를 반환합니다.
    이 함수는 BentoML 서비스에서 그래프를 로드할 때 사용될 수 있습니다.

    Returns:
        Pregel: 컴파일된 그래프 (Pregel 인스턴스)입니다.
    """
    graph = create_graph()
    compiled_graph = graph.compile()
    return compiled_graph


if __name__ == "__main__":
    app = get_compiled_graph()

    # 그래프 시각화
    try:
        img_bytes = app.get_graph().draw_mermaid_png()
        if img_bytes:
            with open("graph_mermaid.png", "wb") as f:
                f.write(img_bytes)
            print("그래프 시각화 이미지가 graph_mermaid.png 로 저장되었습니다.")
        else:
            print("그래프 시각화 데이터를 생성하지 못했습니다.")
    except Exception as e:
        print(f"그래프 시각화 중 오류 발생: {e}")
        print("  Graphviz가 설치되어 있고 PATH에 설정되어 있는지 확인하세요.")
        print("  (예: pip install graphviz, brew install graphviz)")
