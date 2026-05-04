from langgraph_agent.nodes import detect_intent, save_daily_update, manager_summary, handle_smalltalk
from langgraph.graph import StateGraph,END
from langgraph_agent.state import AgentState
state = StateGraph(AgentState)

state.add_node('detect', detect_intent)
state.add_node('save_update', save_daily_update)
state.add_node('manager_summary', manager_summary)
state.add_node('smalltalk', handle_smalltalk)   

state.set_entry_point('detect')

state.add_conditional_edges('detect',lambda state:state['intent'],{'greeting':'smalltalk','thanks':'smalltalk','follow_up':'manager_summary','daily_update':'save_update','manager_query':'manager_summary','other':'smalltalk'})

state.add_edge('save_update', END)

state.add_edge('manager_summary', END)
state.add_edge('smalltalk', END)  

chat_graph = state.compile()