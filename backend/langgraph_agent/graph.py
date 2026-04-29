from langgraph.graph import StateGraph, END
from langgraph_agent.state import AgentState
from langgraph_agent.nodes import detect_intent, save_daily_update, manager_summary

workflow = StateGraph(AgentState)

workflow.add_node('detect', detect_intent)
workflow.add_node('save_update', save_daily_update)
workflow.add_node('manager_summary', manager_summary)

workflow.set_entry_point('detect')
workflow.add_conditional_edges(
    'detect',
    lambda state: state['intent'],
    {
        'daily_update': 'save_update',
        'manager_query': 'manager_summary'
    }
)

workflow.add_edge('save_update', END)
workflow.add_edge('manager_summary', END)

chat_graph = workflow.compile()