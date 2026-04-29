from fastapi import APIRouter, Depends
from pydantic import BaseModel
from auth.dependencies import get_current_user
from langgraph_agent.graph import chat_graph

router = APIRouter(prefix='/chatbot', tags=['Chatbot'])

class ChatRequest(BaseModel):
    message: str

@router.post('/chat')
def chat(data:ChatRequest,user=Depends(get_current_user)):
    result=chat_graph.invoke({'message':data.message,'role':user['role'],'user_id':user['id']})
    return {'response': result['response']}