from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import re
import json
import feedparser

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ python-dotenv가 설치되지 않았습니다. 환경변수를 직접 설정하세요.")

# 환경변수에서 API 키 읽기
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY 환경변수가 설정되어 있지 않습니다.")

# OpenAI 클라이언트 초기화
from openai import OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)
CORS(app)

@app.route("/analyze-blog", methods=["POST"])
def analyze():
    blog_id = request.json.get("blogId")
    if not blog_id:
        return jsonify({"error": "블로그 ID가 제공되지 않았습니다."}), 400

    rss_url = f"https://rss.blog.naver.com/{blog_id}.xml"
    feed = feedparser.parse(rss_url)

    post_count = len(feed.entries)
    blog_title = feed.feed.title if 'title' in feed.feed else blog_id
    description = feed.feed.description if 'description' in feed.feed else "네이버 블로그입니다."

    prompt = f"""
다음 블로그 정보를 바탕으로 품질을 분석해줘:
- 제목: {blog_title}
- 설명: {description}
- 포스팅 수: {post_count}

아래 항목을 포함한 JSON 형식으로 응답해줘. 다른 말은 하지 말고 JSON만 출력:
{{
  "quality": (콘텐츠 품질 점수, 0~100),
  "seo": (SEO 최적화 점수, 0~100),
  "readability": (가독성 점수, 0~100),
  "expertise": (전문성 점수, 0~100),
  "engagement": (독자 참여도 점수, 0~100),
  "score": (종합 점수, 0~100)
}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "블로그 품질 분석가로서 정확하게 분석하고 JSON으로 응답하세요."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800
        )

        content = response.choices[0].message.content.strip()
        print("[🔍 GPT 응답 디버깅]:\n", content)

        match = re.search(r"\{.*\}", content, re.DOTALL)
        if not match:
            return jsonify({"error": "GPT 응답에서 JSON을 추출할 수 없습니다.", "raw": content}), 500

        data = json.loads(match.group(0))

        # 누락된 필드를 기본값 0으로 보완
        required_keys = ["quality", "seo", "readability", "expertise", "engagement", "score"]
        for key in required_keys:
            data.setdefault(key, 0)

        return jsonify({
            "title": blog_title,
            "description": description,
            "post_count": post_count,
            **data
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
