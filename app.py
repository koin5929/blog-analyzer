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

    # GPT에 요청할 프롬프트
    prompt = f"""
다음 블로그 정보를 기반으로 품질을 분석해주세요.
- 제목: {blog_title}
- 설명: {description}
- 포스팅 수: {post_count}

아래와 같은 JSON 형식으로만 응답하세요. 불필요한 말은 포함하지 마세요:

{{
  "overall_score": 0~100 숫자,
  "content_quality": {{
    "score": 0~100 숫자,
    "analysis": "한 줄 설명"
  }},
  "seo_optimization": {{
    "score": 0~100 숫자,
    "analysis": "한 줄 설명"
  }},
  "readability": {{
    "score": 0~100 숫자,
    "analysis": "한 줄 설명"
  }},
  "expertise": {{
    "score": 0~100 숫자,
    "analysis": "한 줄 설명"
  }},
  "engagement": {{
    "score": 0~100 숫자,
    "analysis": "한 줄 설명"
  }}
}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "너는 블로그 품질 평가자이며, 응답은 반드시 JSON으로만 하세요."},
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

        # 누락된 키 보완 (안전 처리)
        def ensure_field(section, default_score=0, default_analysis="N/A"):
            if section not in data:
                data[section] = {"score": default_score, "analysis": default_analysis}
            else:
                data[section].setdefault("score", default_score)
                data[section].setdefault("analysis", default_analysis)

        for section in ["content_quality", "seo_optimization", "readability", "expertise", "engagement"]:
            ensure_field(section)

        if "overall_score" not in data:
            data["overall_score"] = 0

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
