from typing import List, Dict, Any, Optional
from langchain.memory import ConversationSummaryBufferMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain_google_genai import GoogleGenerativeAI
import json
from datetime import datetime, timedelta

class ConversationMemoryManager:
    def __init__(self, gemini_api_key: str):
        """Initialize conversation memory with LangChain"""
        # Initialize Gemini for summarization
        self.llm = GoogleGenerativeAI(
            model="gemini-2.5-pro",
            google_api_key=gemini_api_key
        )
        
        # Initialize conversation memory
        self.memory = ConversationSummaryBufferMemory(
            llm=self.llm,
            max_token_limit=2000,
            return_messages=True
        )
        
        # Session management
        self.sessions = {}
        self.current_session_id = None
    
    def create_session(self, session_id: str) -> str:
        """Create a new conversation session"""
        self.sessions[session_id] = {
            'memory': ConversationSummaryBufferMemory(
                llm=self.llm,
                max_token_limit=2000,
                return_messages=True
            ),
            'created_at': datetime.now(),
            'last_accessed': datetime.now(),
            'message_count': 0
        }
        self.current_session_id = session_id
        return session_id
    
    def set_session(self, session_id: str):
        """Set current session"""
        if session_id not in self.sessions:
            self.create_session(session_id)
        else:
            self.sessions[session_id]['last_accessed'] = datetime.now()
        self.current_session_id = session_id
    
    def add_interaction(self, human_message: str, ai_message: str, session_id: Optional[str] = None):
        """Add a human-AI interaction to memory"""
        if session_id:
            self.set_session(session_id)
        
        if self.current_session_id is None:
            self.create_session(f"session_{datetime.now().timestamp()}")
        
        session = self.sessions[self.current_session_id]
        memory = session['memory']
        
        # Add messages to memory
        memory.chat_memory.add_user_message(human_message)
        memory.chat_memory.add_ai_message(ai_message)
        
        # Update session stats
        session['message_count'] += 2
        session['last_accessed'] = datetime.now()
    
    def get_conversation_context(self, session_id: Optional[str] = None) -> str:
        """Get conversation context for current session"""
        if session_id:
            self.set_session(session_id)
        
        if self.current_session_id is None or self.current_session_id not in self.sessions:
            return ""
        
        memory = self.sessions[self.current_session_id]['memory']
        
        try:
            # Get memory variables
            memory_vars = memory.load_memory_variables({})
            
            # Extract conversation history
            history = memory_vars.get('history', '')
            if isinstance(history, list):
                # Format messages
                context_parts = []
                for message in history:
                    if isinstance(message, HumanMessage):
                        context_parts.append(f"Human: {message.content}")
                    elif isinstance(message, AIMessage):
                        context_parts.append(f"Assistant: {message.content}")
                return "\n".join(context_parts)
            
            return str(history)
            
        except Exception as e:
            print(f"Error getting conversation context: {str(e)}")
            return ""
    
    def get_relevant_history(self, current_question: str, session_id: Optional[str] = None) -> str:
        """Get relevant conversation history based on current question"""
        context = self.get_conversation_context(session_id)
        
        if not context:
            return ""
        
        # Simple relevance check - can be enhanced with semantic similarity
        # Fix: Ensure current_question is a string
        if isinstance(current_question, list):
            current_question = ' '.join(str(item) for item in current_question)
        elif not isinstance(current_question, str):
            current_question = str(current_question)
            
        question_keywords = set(current_question.lower().split())
        context_lines = context.split('\n')
        
        relevant_lines = []
        for line in context_lines[-10:]:  # Look at last 10 messages
            line_keywords = set(line.lower().split())
            if question_keywords.intersection(line_keywords):
                relevant_lines.append(line)
        
        return '\n'.join(relevant_lines[-4:]) if relevant_lines else context.split('\n')[-2:]  # Last 2 messages as fallback
    
    def clear_session(self, session_id: Optional[str] = None):
        """Clear conversation memory for session"""
        if session_id:
            if session_id in self.sessions:
                del self.sessions[session_id]
        elif self.current_session_id:
            if self.current_session_id in self.sessions:
                del self.sessions[self.current_session_id]
            self.current_session_id = None
    
    def cleanup_old_sessions(self, hours: int = 24):
        """Clean up sessions older than specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        old_sessions = [
            session_id for session_id, session_data in self.sessions.items()
            if session_data['last_accessed'] < cutoff_time
        ]
        
        for session_id in old_sessions:
            del self.sessions[session_id]
        
        print(f"Cleaned up {len(old_sessions)} old sessions")
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about current sessions"""
        return {
            'total_sessions': len(self.sessions),
            'current_session': self.current_session_id,
            'sessions_info': {
                session_id: {
                    'message_count': data['message_count'],
                    'created_at': data['created_at'].isoformat(),
                    'last_accessed': data['last_accessed'].isoformat()
                }
                for session_id, data in self.sessions.items()
            }
        }
