import streamlit as st
import pandas as pd
import google.generativeai as genai
import os

# --- ページ設定 ---
st.set_page_config(page_title="AI英作文添削", page_icon="🎓", layout="centered")

# --- 🎨 デザイン設定 ---
background_image_url = "https://images.unsplash.com/photo-1507842217343-583bb7260b66?q=80&w=2670&auto=format&fit=crop"

st.markdown(f"""
<style>
    /* 全体の背景画像 */
    .stApp {{
        background-image: url("{background_image_url}");
        background-size: cover;
        background-attachment: fixed;
    }}
    
    /* メインエリア（白いパネル） */
    .stMainBlockContainer {{
        background-color: rgba(255, 255, 255, 0.95);
        padding: 40px 30px;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        margin-top: 20px;
    }}
    
    /* タイトル */
    h1 {{
        color: #2c3e50;
        font-family: 'Helvetica Neue', sans-serif;
        text-align: center;
        font-size: 2.2rem;
        margin-bottom: 5px;
    }}
    
    /* お題ボックスのデザイン */
    .question-box {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 25px 20px;
        border-radius: 12px;
        margin: 20px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
    }}
    .question-text {{
        font-size: 1.6rem;
        font-weight: bold;
        line-height: 1.4;
    }}

    /* ボタン */
    .stButton>button {{
        width: 100%;
        background-color: #3498db;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        height: 55px;
        font-size: 1.1rem;
        margin-top: 20px;
        border: none;
    }}
    .stButton>button:hover {{
        background-color: #2980b9;
        color: white;
    }}
    
    /* 入力エリアのラベルや余白の調整（重なり防止） */
    .stTextArea label {{
        font-weight: bold;
        font-size: 1.1rem;
        color: #2c3e50;
        margin-bottom: 8px;
    }}
</style>
""", unsafe_allow_html=True)

# --- APIキーの設定 ---
try:
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        api_key = st.secrets["general"]["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except Exception:
    st.error("APIキーが設定されていません。Streamlit CloudのSecretsを確認してください。")
    st.stop()

# --- 🤖 AIモデル設定 (Gemini 2.0 Flash) ---
# クラウド環境で最新モデルを確実に呼び出すためのロジック
try:
    # 第一候補: Gemini 2.0 Flash
    model = genai.GenerativeModel('gemini-2.0-flash')
    # 動作確認（404エラーが出る場合はここでexceptに飛びます）
    model.generate_content("Checking model availability...")
    model_display_name = "Gemini 2.0 Flash"
except Exception:
    try:
        # 第二候補: Gemini 1.5 Flash (2.0がまだ使えない環境用)
        model = genai.GenerativeModel('gemini-1.5-flash')
        model_display_name = "Gemini 1.5 Flash"
    except Exception:
        # 最終手段: 従来のPro
        model = genai.GenerativeModel('gemini-pro')
        model_display_name = "Gemini Pro"

# --- メイン処理 ---
st.title("🎓 AI English Teacher")
st.caption(f"Powered by {model_display_name}")

# CSV読み込み
csv_file = "data.csv"
if not os.path.exists(csv_file):
    st.error("⚠️ 'data.csv' が見つかりません。")
else:
    try:
        df = pd.read_csv(csv_file).fillna("")
        
        # 1. 学年とお題の選択（横並び）
        col1, col2 = st.columns([1, 2])
        with col1:
            grade = st.selectbox("📚 学年", df["学年"].unique())
        
        filtered_df = df[df["学年"] == grade]
        with col2:
            if filtered_df.empty:
                st.warning("データなし")
                st.stop()
            topic = st.selectbox("📝 課題を選択", filtered_df["お題"].unique())
        
        # データの詳細取得
        row = filtered_df[filtered_df["お題"] == topic].iloc[0]
        points = row.get('配点', 10)
        
        # 語数指定の判定
        word_limit = str(row.get('語数指定', '')).strip()
        if not word_limit or word_limit == "nan":
            word_limit = "なし"

        # 条件のリスト化
        conds = [str(row.get(f'条件{i}', '')).strip() for i in range(1, 4)]
        conds = [c for c in conds if c and c != "nan"]
        criteria = row.get('評価規準', '')

        # 2. お題の表示（Today's Topicを削除してシンプルに）
        st.markdown(f"""
        <div class="question-box">
            <div class="question-text">{topic}</div>
        </div>
        """, unsafe_allow_html=True)

        # 3. 条件・配点の表示
        with st.container():
            cond_text = " / ".join(conds) if conds else "特になし"
            m1, m2, m3 = st.columns([1, 1, 2.5])
            with m1:
                st.info(f"💯 **配点**\n\n{points}点")
            with m2:
                st.info(f"📏 **語数**\n\n{word_limit}")
            with m3:
                st.warning(f"✅ **条件**\n\n{cond_text}")

        # 4. 解答入力フォーム
        st.write("") # スペース確保
        student_answer = st.text_area("Your Answer:", height=200, placeholder="Write your English sentences here...")
        
        # 5. 採点アクション
        if st.button("採点する 🚀"):
            if not student_answer.strip():
                st.warning("英作文を入力してください。")
            else:
                with st.spinner("AI先生が内容を確認しています..."):
                    prompt = f"""
                    あなたは親切で情熱的な英語教師です。
                    以下の基準に基づいて、生徒の英作文を日本語で添削してください。
                    生徒がもっと英語を勉強したくなるような、ポジティブで励みになる言葉を選んでください。

                    【課題詳細】
                    ・お題: {topic}
                    ・対象学年: {grade}
                    ・満点: {points}点
                    ・語数指定: {word_limit}
                    ・必須条件: {', '.join(conds)}
                    ・評価のポイント: {criteria}

                    【生徒の回答】
                    {student_answer}

                    【出力形式】
                    ## 採点結果: [点数] / {points}

                    ### 👩‍🏫 先生からのコメント
                    (まずは努力を称え、良い表現や文法を具体的に褒めてください)

                    ### ⚠️ 改善のアドバイス
                    (条件や語数が守られているか確認。間違いがあれば優しく理由を説明し、正しい表現を教えてください)

                    ### ✨ 模範解答 (Model Answer)
                    (その学年にふさわしい、自然で丁寧な英語の例を1つ提示してください)
                    """
                    
                    try:
                        response = model.generate_content(prompt)
                        st.markdown("---")
                        st.success("採点が終わりました！結果を見てみましょう。")
                        st.markdown(response.text)
                    except Exception as e:
                        st.error(f"エラーが発生しました: {e}")

    except Exception as e:
        st.error(f"データの読み込み中にエラーが発生しました: {e}")