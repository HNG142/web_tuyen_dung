import io
import json
import logging
import asyncio
from typing import Optional
from PyPDF2 import PdfReader 
from docx import Document 
from openai import OpenAI 
from app.config import settings 

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

client = OpenAI(api_key=settings.OPENAI_API_KEY)

async def extract_text_from_pdf(file: bytes) -> Optional[str]:
    """Trích xuất văn bản từ file PDF."""
    try:
        reader = PdfReader(io.BytesIO(file))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or "" 
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
            text += para.text + "\n" 
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
        return None 

async def get_cv_jd_matching_score_and_feedback(cv_text: str, jd_text: str) -> dict:
    """
    Sử dụng GPT để đánh giá mức độ phù hợp của CV với JD.
    Trả về một dictionary chứa 'score' (điểm số) và 'feedback' (phản hồi).
    Thêm xử lý cho trường hợp vượt quá token và retry.
    """
    prompt = f"""
    Bạn là một chuyên gia tuyển dụng. Hãy so sánh CV sau với mô tả công việc (JD) dưới đây và đưa ra đánh giá chi tiết.
    Phản hồi của bạn PHẢI là một đối tượng JSON có hai trường:
    - "score": Một số nguyên từ 0 đến 100 thể hiện mức độ phù hợp của CV với JD (0 là không phù hợp, 100 là hoàn hảo).
    - "feedback": Một đoạn văn bản cung cấp lý do cho điểm số và những điểm mạnh, điểm yếu của CV so với JD, tập trung vào sự liên quan trực tiếp đến JD.

    CV:
    ---
    {cv_text}
    ---

    Mô tả công việc (JD):
    ---
    {jd_text}
    ---
    """

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo-0125", # Hoặc "gpt-4-turbo"
                messages=[
                    {"role": "system", "content": "Bạn là một trợ lý phân tích CV/JD."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7, # Điều chỉnh khả năng sáng tạo; thấp hơn cho kết quả thực tế hơn
                timeout=30 # Thêm thời gian chờ cho cuộc gọi API
            )
            return json.loads(response.choices[0].message.content)
        except openai.APITimeoutError as e:
            logging.error(f"API Timeout (lần thử {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt) # Thời gian chờ tăng dần theo cấp số nhân
            else:
                return {"score": 0, "feedback": "Lỗi kết nối API: Hết thời gian chờ."}
        except openai.APIError as e:
            logging.error(f"Lỗi API OpenAI (lần thử {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt) # Thời gian chờ tăng dần theo cấp số nhân
            else:
                return {"score": 0, "feedback": "Lỗi từ OpenAI API. Vui lòng thử lại sau."}
        except json.JSONDecodeError as e:
            logging.error(f"Lỗi giải mã JSON từ GPT (lần thử {attempt+1}/{max_retries}): {e}. Phản hồi thô: {response.choices[0].message.content if response else 'N/A'}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt) # Thời gian chờ tăng dần theo cấp số nhân
            else:
                return {"score": 0, "feedback": "Lỗi định dạng phản hồi từ GPT. Vui lòng thử lại."}
        except Exception as e:
            logging.error(f"Lỗi không xác định khi lấy điểm phù hợp và phản hồi từ GPT: {e}")
            return {"score": 0, "feedback": "Không thể phân tích. Vui lòng thử lại."}
    return {"score": 0, "feedback": "Không thể phân tích sau nhiều lần thử. Vui lòng thử lại."}

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