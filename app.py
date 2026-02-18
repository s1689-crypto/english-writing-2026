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
    }}
    
    /* タイトル */
    h1 {{
        color: #2c3e50;
        font-family: 'Helvetica Neue', sans-serif;
        text-align: center;
        font-size: 2.0rem;
        margin-bottom: 10px;
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
        margin-top: 10px;
        border: none;
    }}
    .stButton>button:hover {{
        background-color: #2980b9;
        color: white;
    }}
    
    /* テキストエリアの調整 */
    .stTextArea textarea {{
        font-size: 16px;
        line-height: 1.5;
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
except Exception as e:
    st.error("APIキーの設定エラーです。Streamlit CloudのSecrets設定を確認してください。")
    st.stop()

# --- メイン処理 ---
st.title("🎓 AI English Teacher")
st.caption("AI先生があなたの英作文を即座に添削します！")

# CSV読み込み
csv_file = "data.csv"
if not os.path.exists(csv_file):
    st.error("⚠️ 'data.csv' が見つかりません。")
else:
    try:
        df = pd.read_csv(csv_file).fillna("")
        
        # 学年とお題選択を横並び
        col1, col2 = st.columns([1, 2])
        
        with col1:
            grade = st.selectbox("📚 学年", df["学年"].unique())
        
        # 選ばれた学年でフィルタリング
        filtered_df = df[df["学年"] == grade]
        
        with col2:
            if filtered_df.empty:
                st.warning("データなし")
                st.stop()
            topic = st.selectbox("📝 課題を選択", filtered_df["お題"].unique())
        
        # データ抽出
        row = filtered_df[filtered_df["お題"] == topic].iloc[0]
        
        points = row.get('配点', 10)
        
        word_limit = row.get('語数指定', '')
        if not word_limit:
            word_limit = "なし"

        conds = [row.get(f'条件{i}', '') for i in range(1, 4)]
        conds = [c for c in conds if c] # 空文字を除外
        criteria = row.get('評価規準', '')

        # お題表示
        st.markdown(f"""
        <div class="question-box">
            <div class="question-text">{topic}</div>
        </div>
        """, unsafe_allow_html=True)

        # 条件表示
        with st.container():
            cond_text = " / ".join(conds) if conds else "特になし"
            
            m1, m2, m3 = st.columns([1, 1, 2.5])
            with m1:
                st.info(f"💯 **配点**\n\n{points}点")
            with m2:
                st.info(f"📏 **語数**\n\n{word_limit}")
            with m3:
                st.warning(f"✅ **必須条件**\n\n{cond_text}")

        # 回答入力フォーム
        student_answer = st.text_area("Answer", height=200, placeholder="ここに英語で回答を書いてください...")
        
        # 採点ボタン
        if st.button("採点する 🚀"):
            if not student_answer.strip():
                st.warning("回答が入力されていません。")
            else:
                # ★ここが修正ポイント！モデルを使い分ける魔法のコード★
                model_name = ""
                try:
                    # まず最新のFlashモデルを試す
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    response = model.generate_content("test") # 試し打ち
                    model_name = "Gemini 1.5 Flash"
                except:
                    # ダメなら安定版のProを使う（エラーを出さない！）
                    model = genai.GenerativeModel('gemini-pro')
                    model_name = "Gemini Pro"

                with st.spinner(f"AI先生 ({model_name}) が採点中... ☕"):
                    prompt = f"""
                    あなたは親切で熱心な英語教師です。
                    生徒のモチベーションが上がるように、絵文字を使いながら丁寧に採点してください。
                    
                    【課題】
                    ・お題: {topic}
                    ・学年: {grade}
                    ・配点: {points}点満点
                    ・語数指定: {word_limit}
                    ・条件: {', '.join(conds)}
                    ・評価基準: {criteria}
                    
                    【生徒の回答】
                    {student_answer}
                    
                    【出力】
                    ## 採点結果: [点数] / {points}
                    
                    ### 👩‍🏫 先生からのコメント
                    (褒めポイント)
                    
                    ### ⚠️ 改善アドバイス
                    (減点理由、条件チェック、文法修正)
                    
                    ### ✨ 模範解答 (Example)
                    """
                    
                    try:
                        response = model.generate_content(prompt)
                        st.markdown("---")
                        st.success("Check your result! 👇")
                        st.markdown(response.text)
                    except Exception as e:
                        st.error(f"エラー: {e}")

    except Exception as e:
        st.error(f"CSV読み込みエラー: {e}")