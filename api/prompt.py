from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
from urllib.error import HTTPError

class handler(BaseHTTPRequestHandler):
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
                mime_type = image_data.split(";")[0].split(":")[1]
                base64_string = image_data.split(",")[1]
            else:
                mime_type = "image/jpeg"
                base64_string = image_data

            api_key = os.environ.get("GOOGLE_API_KEY", "").strip()
            if not api_key:
                self.wfile.write(json.dumps({"error": "API 키가 설정되지 않았습니다."}).encode('utf-8'))
                return

            # 🔥 요청하신 gemini-3.6-flash 모델로 변경 완료 (v1beta 사용)
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={api_key}"

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

            payload = {
                "contents": [{
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": base64_string
                            }
                        }
                    ]
                }]
            }

            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
            
            with urllib.request.urlopen(req) as response:
                res_body = response.read().decode('utf-8')
                res_json = json.loads(res_body)
                
                result_text = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
                
                if result_text.startswith("```json"):
                    result_text = result_text.replace("```json", "").replace("```", "").strip()
                elif result_text.startswith("```"):
                    result_text = result_text.replace("```", "").strip()
                    
                self.wfile.write(result_text.encode('utf-8'))

        except HTTPError as e:
            error_msg = e.read().decode('utf-8')
            self.wfile.write(json.dumps({"error": f"구글 API 상세 에러: {error_msg}"}).encode('utf-8'))
        except Exception as e:
            self.wfile.write(json.dumps({"error": f"서버 내부 에러: {str(e)}"}).encode('utf-8'))
