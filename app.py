from flask import Flask, request, jsonify
from flask_cors import CORS
import feedparser
import requests
import re
import json

# ✅ 최신 OpenAI 라이브러리 사용 방식
import openai

# 👇 여기에 API 키 직접 입력 또는 환경변수 사용
client = openai.OpenAI(api_key="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")

app = Flask(__name__)
CORS(app)

@app.route("/analyze-blog", methods=["POST"])
def analyze():
    blog_id = request.json.get("blogId")
    rss_url = f"https://rss.blog.naver.com/{blog_id}.xml"
    feed = feedparser.parse(rss_url)

    post_count = len(feed.entries)
    blog_title = feed.feed.title if 'title' in feed.feed else blog_id
    description = feed.feed.description if 'description' in feed.feed else "네이버 블로그입니다."

    prompt = f"""다음 블로그 정보를 바탕으로 품질을 분석해줘:
- 제목: {blog_title}
- 설명: {description}
- 포스팅 수: {post_count}

콘텐츠 품질, SEO, 가독성, 전문성, 독자 참여도를 점수로 평가해줘. JSON으로만 응답."""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "블로그 품질 분석가로서 정확하게 분석하고 JSON으로 응답하세요."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800
        )

        content = response.choices[0].message.content
        match = re.search(r"\{.*\}", content, re.DOTALL)
        data = json.loads(match.group(0)) if match else {"error": "Invalid JSON format from GPT"}

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
