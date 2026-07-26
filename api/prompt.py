from http.server import BaseHTTPRequestHandler
import json
import os
import base64
import io
from PIL import Image
import google.generativeai as genai

# 1. API 키 설정
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

class handler(BaseHTTPRequestHandler):
    # CORS 설정
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)

            image_data = data.get('image', '')
            if not image_data:
                self.wfile.write(json.dumps({"error": "사진이 전달되지 않았습니다."}).encode('utf-8'))
                return

            if "," in image_data:
                image_data = image_data.split(",")[1]
            image_bytes = base64.b64decode(image_data)
            
            # 2. 🔥 최신 권장 방식: PIL(Pillow) 라이브러리로 이미지 변환
            image = Image.open(io.BytesIO(image_bytes))
            
            # 3. 🔥 모호한 이름 대신, 가장 최신이고 안정적인 '정확한 세부 버전' 명시
            model = genai.GenerativeModel('gemini-1.5-flash-002')
            
            prompt = """
            첨부된 사진 속 인물의 스타일과 분위기를 분석해서, 틱톡 댄스 프롬프트에 쓸 데이터를 JSON 형식으로만 답해줘.
            부연 설명은 절대 하지 말고 오직 아래 키 값을 가진 JSON만 반환해.
            키 값: 
            "outfit" (의상 설명, 영어로),
            "move1" (어울리는 첫번째 안무, 영어로),
            "move2" (두번째 안무, 영어로),
            "move3" (마무리 안무, 영어로),
            "gender" (성별, female / male / non-binary 중 택1),
            "age_range" (연령대, teen / young adult 등 영어로),
            "song_vibe" (어울리는 노래 분위기, 영어로)
            """
            
            # 4. 프롬프트와 변환된 이미지를 함께 전달
            response = model.generate_content([prompt, image])
            
            result_text = response.text.strip()
            if result_text.startswith("```json"):
                result_text = result_text.replace("```json", "").replace("```", "").strip()
            elif result_text.startswith("```"):
                result_text = result_text.replace("```", "").strip()
                
            self.wfile.write(result_text.encode('utf-8'))

        except Exception as e:
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
