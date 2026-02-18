import streamlit as st
import pandas as pd
import google.generativeai as genai
import os

# --- ページ設定 ---
st.set_page_config(page_title="AI英作文添削", page_icon="🎓", layout="centered")

# --- 🎨 デザイン設定（図書館背景・読みやすさ重視） ---
background_image_url = "https://images.unsplash.com/photo-1507842217343-583bb7260b66?q=80&w=2670&auto=format&fit=crop"

st.markdown(f"""
<style>
    .stApp {{
        background-image: url("{background_image_url}");
        background-size: cover;
        background-attachment: fixed;
    }}
    .stMainBlockContainer {{
        background-color: rgba(255, 255, 255, 0.95);
        padding: 40px 30px;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }}
    h1 {{
        color: #2c3e50;
        text-align: center;
        font-size: 2.2rem;
    }}
    .question-box {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 25px 20px;
        border-radius: 12px;
        margin: 20px 0;
        text-align: center;
    }}
    .question-text {{
        font-size: 1.6rem;
        font-weight: bold;
    }}
    .stButton>button {{
        width: 100%;
        background-color: #3498db;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        height: 55px;
    }}
</style>
""", unsafe_allow_html=True)

# --- APIキーの設定 ---
try:
    api_key = st.secrets["GEMINI_API_KEY"] if "GEMINI_API_KEY" in st.secrets else st.secrets["general"]["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except Exception:
    st.error("APIキーをSecretsに設定してください。")
    st.stop()

# --- 🤖 モデル設定：Gemini 2.5 Pro を直接指定 ---
try:
    # 2.5 Pro を使用
    model = genai.GenerativeModel('gemini-2.5-pro')
except Exception as e:
    st.error(f"モデルの起動に失敗しました: {e}")
    st.stop()

# --- メイン処理 ---
st.title("🎓 AI English Teacher")
st.caption("🚀 使用モデル: Gemini 2.5 Pro")

# CSV読み込み
csv_file = "data.csv"
if not os.path.exists(csv_file):
    st.error("⚠️ 'data.csv' が見つかりません。")
else:
    try:
        df = pd.read_csv(csv_file).fillna("")
        
        col1, col2 = st.columns([1, 2])
        with col1:
            grade = st.selectbox("📚 学年", df["学年"].unique())
        
        filtered_df = df[df["学年"] == grade]
        with col2:
            topic = st.selectbox("📝 課題を選択", filtered_df["お題"].unique())
        
        row = filtered_df[filtered_df["お題"] == topic].iloc[0]
        points = row.get('配点', 10)
        word_limit = str(row.get('語数指定', 'なし'))
        if word_limit == "nan" or not word_limit: word_limit = "なし"

        conds = [str(row.get(f'条件{i}', '')).strip() for i in range(1, 4)]
        conds = [c for c in conds if c and c != "nan"]

        st.markdown(f'<div class="question-box"><div class="question-text">{topic}</div></div>', unsafe_allow_html=True)

        # 条件表示
        m1, m2, m3 = st.columns([1, 1, 2.5])
        with m1: st.info(f"💯 **配点**\n\n{points}点")
        with m2: st.info(f"📏 **語数**\n\n{word_limit}")
        with m3: st.warning(f"✅ **条件**\n\n{' / '.join(conds) if conds else 'なし'}")

        student_answer = st.text_area("Answer:", height=200, placeholder="Write here...")
        
        if st.button("採点する 🚀"):
            if not student_answer.strip():
                st.warning("入力してください。")
            else:
                with st.spinner("Gemini 2.5 Pro が精緻に採点中..."):
                    prompt = f"""
                    あなたはプロの英語教師です。以下の基準で採点・添削してください。
                    お題: {topic}, 配点: {points}, 語数: {word_limit}, 条件: {', '.join(conds)}
                    生徒の回答: {student_answer}
                    日本語で、点数、褒め言葉、改善点、模範解答を出力してください。
                    """
                    response = model.generate_content(prompt)
                    st.markdown("---")
                    st.markdown(response.text)

    except Exception as e:
        st.error(f"エラー: {e}")