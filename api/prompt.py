from http.server import BaseHTTPRequestHandler
import json
import os
import base64
import google.generativeai as genai

# 1. Vercel에 설정한 GOOGLE_API_KEY 불러오기
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

class handler(BaseHTTPRequestHandler):
    # 2. CORS 설정: 브라우저(프론트엔드)에서 이 백엔드를 호출할 수 있도록 허가해주는 보안 설정
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    # 3. 사용자가 사진을 올렸을 때 실행되는 메인 로직
    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        try:
            # 웹사이트에서 보낸 데이터(사진) 읽기
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)

            image_data = data.get('image', '')
            if not image_data:
                self.wfile.write(json.dumps({"error": "사진이 전달되지 않았습니다."}).encode('utf-8'))
                return

            # 사진 데이터를 Gemini가 읽을 수 있는 형태로 변환
            if "," in image_data:
                image_data = image_data.split(",")[1]
            image_bytes = base64.b64decode(image_data)
            
            # 4. Gemini 1.5 Flash 모델에게 사진 분석 명령 내리기 (원상복구됨)
            model = genai.GenerativeModel('gemini-1.5-flash')
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
            
            image_parts = [{"mime_type": "image/jpeg", "data": image_bytes}]
            response = model.generate_content([prompt, image_parts[0]])
            
            # 5. AI의 답변에서 순수 JSON 데이터만 추출하여 프론트엔드로 보내기
            result_text = response.text.strip()
            if result_text.startswith("```json"):
                result_text = result_text.replace("```json", "").replace("```", "").strip()
            elif result_text.startswith("```"):
                result_text = result_text.replace("```", "").strip()
                
            self.wfile.write(result_text.encode('utf-8'))

        except Exception as e:
            # 에러가 났을 때 원인 알려주기
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
