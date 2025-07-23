from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import feedparser
import requests
import re
import json

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # 모든 도메인에서 CORS 허용

# ✅ 직접 OpenAI API 키 입력 (주의: 공개 저장소에 올릴 경우 위험!)
openai.api_key = "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"

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
        res = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "블로그 품질 분석가로서 정확하게 분석하고 JSON으로 응답하세요."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800
        )

        content = res.choices[0].message.content
        match = re.search(r"\{.*\}", content, re.DOTALL)

        data = json.loads(match.group(0)) if match else {"error": "Invalid JSON"}

        return jsonify({
            "title": blog_title,
            "description": description,
            "post_count": post_count,
            **data
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Render 배포용 포트 설정
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
