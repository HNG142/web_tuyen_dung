from langchain_openai import ChatOpenAI # Kết nối với OpenAI qua LangChain
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder # Để tạo các mẫu câu hỏi cho chatbot
from langchain_core.runnables.history import RunnableWithMessageHistory # Để quản lý lịch sử trò chuyện
from langchain_core.messages import SystemMessage, HumanMessage # Các loại tin nhắn
from langchain_community.chat_message_histories import ChatMessageHistory # Để lưu lịch sử tin nhắn
from app.config import settings # Nhập API Key từ config
from openai import OpenAI # Sử dụng OpenAI client trực tiếp để đánh giá

import json # Để xử lý JSON

# Khởi tạo OpenAI client để gọi API trực tiếp (cho phần đánh giá)
openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

# Khởi tạo LangChain LLM (Large Language Model)
# temperature=0.7 giúp câu trả lời của AI tự nhiên hơn, không quá cứng nhắc
llm = ChatOpenAI(openai_api_key=settings.OPENAI_API_KEY, model="gpt-3.5-turbo-0125", temperature=0.7)

# Mẫu câu hỏi (prompt) cho chatbot phỏng vấn
interview_prompt = ChatPromptTemplate.from_messages(
    [
        # Tin nhắn hệ thống định hình vai trò của chatbot
        SystemMessage(
            "Bạn là một chatbot phỏng vấn sơ bộ cho vị trí Software Engineer. "
            "Mục tiêu của bạn là đánh giá kiến thức, kinh nghiệm và kỹ năng mềm của ứng viên. "
            "Hãy đặt câu hỏi một cách tự nhiên, chuyên nghiệp và duy trì cuộc hội thoại. "
            "Hãy nhớ chào hỏi ứng viên và kết thúc cuộc phỏng vấn một cách lịch sự. "
            "Bắt đầu bằng một câu hỏi mở để ứng viên giới thiệu về bản thân."
        ),
        # Nơi LangChain sẽ tự động chèn lịch sử cuộc trò chuyện
        MessagesPlaceholder(variable_name="history"),
        # Tin nhắn của người dùng
        HumanMessage(content="{input}"),
    ]
)

# Để đơn giản, chúng ta sẽ lưu lịch sử trò chuyện trong bộ nhớ của server.
# Trong ứng dụng thực tế, bạn nên lưu vào cơ sở dữ liệu để bền vững hơn.
store = {} # Một dictionary để lưu lịch sử cho từng session_id

def get_session_history(session_id: str) -> ChatMessageHistory:
    """Lấy hoặc tạo lịch sử trò chuyện cho một session_id cụ thể."""
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

# Tạo chuỗi hội thoại có quản lý lịch sử
interview_chain = RunnableWithMessageHistory(
    interview_prompt | llm, # Nối prompt với LLM
    get_session_history, # Hàm để lấy lịch sử
    input_messages_key="input", # Khóa cho đầu vào của người dùng
    history_messages_key="history", # Khóa cho lịch sử trò chuyện
)

async def start_interview(session_id: str) -> str:
    """Bắt đầu một phiên phỏng vấn mới và trả về tin nhắn chào mừng/câu hỏi đầu tiên."""
    # Xóa lịch sử cũ nếu session_id đã tồn tại
    if session_id in store:
        store[session_id].clear()
    
    # Tin nhắn chào mừng và câu hỏi mở đầu
    initial_prompt = "Chào bạn! Chúng ta sẽ bắt đầu buổi phỏng vấn sơ bộ cho vị trí Software Engineer. Bạn có thể giới thiệu đôi chút về bản thân và kinh nghiệm của mình không?"
    
    # LangChain RunnableWithMessageHistory cần một tin nhắn "input" để bắt đầu
    # Chúng ta sẽ thêm tin nhắn chào mừng vào lịch sử và trả về nó
    history = get_session_history(session_id)
    history.add_ai_message(initial_prompt) # Ghi tin nhắn của AI vào lịch sử
    
    return initial_prompt

async def chat_with_chatbot(session_id: str, message: str) -> str:
    """Tiếp tục cuộc trò chuyện phỏng vấn."""
    response = interview_chain.invoke(
        {"input": message}, # Tin nhắn đầu vào từ người dùng
        config={"configurable": {"session_id": session_id}} # Để LangChain biết session nào
    )
    return response.content # Nội dung phản hồi từ chatbot

async def evaluate_candidate_response(question: str, candidate_answer: str, jd_text: str) -> dict:
    """
    Đánh giá câu trả lời của ứng viên cho một câu hỏi phỏng vấn cụ thể bằng GPT.
    Trả về dictionary với 'score' (điểm) và 'feedback' (phản hồi chi tiết).
    """
    prompt = f"""
    Bạn là một chuyên gia tuyển dụng. Hãy đánh giá câu trả lời của ứng viên cho câu hỏi phỏng vấn dưới đây.
    Đánh giá dựa trên sự liên quan, rõ ràng, độ sâu của kiến thức, và mức độ phù hợp với mô tả công việc (JD).
    Phản hồi của bạn PHẢI là một đối tượng JSON có hai trường:
    - "score": Một số nguyên từ 0 đến 100 (0 là không phù hợp, 100 là xuất sắc).
    - "feedback": Một đoạn văn bản cung cấp nhận xét chi tiết về câu trả lời, bao gồm điểm mạnh và điểm cần cải thiện.

    Mô tả công việc (JD):
    ---
    {jd_text}
    ---

    Câu hỏi phỏng vấn:
    ---
    {question}
    ---

    Câu trả lời của ứng viên:
    ---
    {candidate_answer}
    ---
    """
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo-0125", # Hoặc "gpt-4-turbo"
            messages=[
                {"role": "system", "content": "Bạn là trợ lý đánh giá câu trả lời phỏng vấn."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Lỗi khi đánh giá câu trả lời ứng viên với GPT: {e}")
        return {"score": 0, "feedback": "Không thể đánh giá. Vui lòng thử lại."}