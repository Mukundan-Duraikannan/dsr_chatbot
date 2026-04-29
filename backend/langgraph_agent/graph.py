from langgraph.graph import StateGraph, END
from langgraph_agent.state import AgentState
from langgraph_agent.nodes import detect_intent, save_daily_update, manager_summary

state = StateGraph(AgentState)

state.add_node('detect', detect_intent)
state.add_node('save_update', save_daily_update)
state.add_node('manager_summary', manager_summary)
state.set_entry_point('detect')
state.add_conditional_edges('detect',lambda state: state['intent'],{'daily_update': 'save_update','manager_query': 'manager_summary'})
state.add_edge('save_update', END)
state.add_edge('manager_summary', END)

chat_graph = state.compile()