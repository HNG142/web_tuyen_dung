import io
import json
from typing import Optional
from PyPDF2 import PdfReader # Thư viện đọc PDF
from docx import Document # Thư viện đọc DOCX
from openai import OpenAI # Thư viện kết nối OpenAI GPT
from app.config import settings # Nhập API Key từ config

# Khởi tạo client OpenAI với API Key của bạn
client = OpenAI(api_key=settings.OPENAI_API_KEY)

async def extract_text_from_pdf(file: bytes) -> Optional[str]:
    """Trích xuất văn bản từ file PDF."""
    try:
        reader = PdfReader(io.BytesIO(file))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or "" # Trích xuất văn bản từng trang
        return text
    except Exception as e:
        print(f"Lỗi khi trích xuất văn bản từ PDF: {e}")
        return None

async def extract_text_from_docx(file: bytes) -> Optional[str]:
    """Trích xuất văn bản từ file DOCX."""
    try:
        doc = Document(io.BytesIO(file))
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n" # Lấy từng đoạn văn bản
        return text
    except Exception as e:
        print(f"Lỗi khi trích xuất văn bản từ DOCX: {e}")
        return None

async def process_uploaded_file(file_content: bytes, filename: str) -> Optional[str]:
    """Xác định loại file và trích xuất văn bản tương ứng."""
    if filename.endswith(".pdf"):
        return await extract_text_from_pdf(file_content)
    elif filename.endswith(".docx"):
        return await extract_text_from_docx(file_content)
    else:
        return None # Không hỗ trợ định dạng file này

async def get_cv_jd_matching_score_and_feedback(cv_text: str, jd_text: str) -> dict:
    """
    Sử dụng GPT để đánh giá mức độ phù hợp của CV với JD.
    Trả về một dictionary chứa 'score' (điểm số) và 'feedback' (phản hồi).
    """
    prompt = f"""
    Bạn là một chuyên gia tuyển dụng. Hãy so sánh CV sau với mô tả công việc (JD) dưới đây và đưa ra đánh giá chi tiết.
    Phản hồi của bạn PHẢI là một đối tượng JSON có hai trường:
    - "score": Một số nguyên từ 0 đến 100 thể hiện mức độ phù hợp của CV với JD (0 là không phù hợp, 100 là hoàn hảo).
    - "feedback": Một đoạn văn bản cung cấp lý do cho điểm số và những điểm mạnh, điểm yếu của CV so với JD.

    CV:
    ---
    {cv_text}
    ---

    Mô tả công việc (JD):
    ---
    {jd_text}
    ---
    """
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-0125", # Hoặc "gpt-4-turbo" nếu bạn muốn độ chính xác cao hơn và sẵn sàng trả phí cao hơn
            messages=[
                {"role": "system", "content": "Bạn là một trợ lý phân tích CV/JD."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"} # Yêu cầu GPT trả về JSON
        )
        return json.loads(response.choices[0].message.content) # Chuyển chuỗi JSON thành dictionary Python
    except Exception as e:
        print(f"Lỗi khi lấy điểm phù hợp và phản hồi từ GPT: {e}")
        return {"score": 0, "feedback": "Không thể phân tích. Vui lòng thử lại."}

async def get_cv_improvement_suggestions(cv_text: str, jd_text: str) -> dict:
    """
    Sử dụng GPT để đưa ra gợi ý chỉnh sửa CV để phù hợp hơn với JD.
    Trả về một dictionary chứa 'suggestions' (danh sách các gợi ý).
    """
    prompt = f"""
    Bạn là một chuyên gia tuyển dụng. Dựa trên CV dưới đây và mô tả công việc (JD) đi kèm, hãy đưa ra các gợi ý CỤ THỂ và THỰC TẾ để chỉnh sửa CV, giúp nó phù hợp hơn với JD.
    Phản hồi của bạn PHẢI là một đối tượng JSON có một trường:
    - "suggestions": Một mảng các chuỗi, mỗi chuỗi là một gợi ý cụ thể.

    Ví dụ:
    {{
      "suggestions": [
        "Thêm các từ khóa kỹ thuật như 'Python', 'FastAPI' vào phần tóm tắt.",
        "Mô tả kinh nghiệm quản lý dự án bằng cách sử dụng các con số cụ thể (ví dụ: 'giảm 15% chi phí')."
      ]
    }}

    CV:
    ---
    {cv_text}
    ---

    Mô tả công việc (JD):
    ---
    {jd_text}
    ---
    """
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-0125", # Hoặc "gpt-4-turbo"
            messages=[
                {"role": "system", "content": "Bạn là một trợ lý cung cấp gợi ý chỉnh sửa CV."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"} # Yêu cầu GPT trả về JSON
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Lỗi khi lấy gợi ý chỉnh sửa CV từ GPT: {e}")
        return {"suggestions": ["Không thể đưa ra gợi ý. Vui lòng thử lại."]}