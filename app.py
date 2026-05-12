"""
LuminaTech 受注予測モデル
電気工事・太陽光パネル設置の受注確率を予測するStreamlitアプリ
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────
# 会社所在地（横浜本社）
# ─────────────────────────────────────────
COMPANY_LAT = 35.4437
COMPANY_LON = 139.6380
COMPANY_NAME = "LuminaTech 横浜本社"

# ─────────────────────────────────────────
# ページ設定
# ─────────────────────────────────────────
st.set_page_config(
    page_title="LuminaTech 受注予測モデル",
    page_icon="⚡",
    layout="wide",
)

st.title("⚡ LuminaTech 受注予測モデル")
st.caption("電気工事・太陽光パネル設置の受注確率・売上予測ダッシュボード")

# ─────────────────────────────────────────
# サンプルデータ生成
# ─────────────────────────────────────────

def generate_sample_data(n: int = 300) -> pd.DataFrame:
    """
    電気工事・太陽光案件らしいリアルなサンプルデータを生成する。
    実際のCSVがない場合の代替データとして使用。
    """
    np.random.seed(42)

    # 見積提出日（2022年1月〜2024年12月）
    start = pd.Timestamp("2022-01-01")
    end = pd.Timestamp("2024-12-31")
    dates = pd.to_datetime(
        np.random.randint(start.value, end.value, size=n)
    )

    # 工事種別
    categories = np.random.choice(
        ["電気工事", "太陽光", "その他"],
        size=n,
        p=[0.45, 0.40, 0.15],
    )

    # エリア
    areas = np.random.choice(
        ["東京", "神奈川", "その他"],
        size=n,
        p=[0.40, 0.35, 0.25],
    )

    # 見積金額（カテゴリ別に現実的な金額レンジを設定）
    amounts = []
    for cat in categories:
        if cat == "電気工事":
            amounts.append(int(np.random.lognormal(13.5, 0.6)))  # 50万〜500万円程度
        elif cat == "太陽光":
            amounts.append(int(np.random.lognormal(14.2, 0.5)))  # 100万〜800万円程度
        else:
            amounts.append(int(np.random.lognormal(12.8, 0.7)))  # 30万〜200万円程度

    # 受注確率のロジック（金額・カテゴリ・エリアに依存）
    results = []
    for cat, area, amt in zip(categories, areas, amounts):
        prob = 0.50  # ベース確率

        # カテゴリ補正
        if cat == "太陽光":
            prob += 0.10
        elif cat == "電気工事":
            prob += 0.05

        # エリア補正
        if area == "東京":
            prob += 0.08
        elif area == "神奈川":
            prob += 0.05

        # 金額補正（高すぎると失注しやすい）
        if amt > 5_000_000:
            prob -= 0.15
        elif amt < 500_000:
            prob -= 0.05

        prob = np.clip(prob, 0.1, 0.9)
        results.append(np.random.binomial(1, prob))

    # エリアごとの代表都市座標（リアルな現場散布のためノイズを加える）
    other_cities = [
        (35.6050, 140.1233),  # 千葉
        (35.8617, 139.6455),  # さいたま
        (34.9757, 138.3827),  # 静岡
        (35.3628, 138.7307),  # 山梨
        (36.3912, 139.0608),  # 群馬
        (36.5657, 136.6565),  # 金沢
        (35.9056, 139.3797),  # 熊谷
        (35.0116, 135.7681),  # 京都
        (34.6937, 135.5023),  # 大阪
        (35.1815, 136.9066),  # 名古屋
    ]

    lats, lons = [], []
    for area in areas:
        if area == "東京":
            lat = 35.6812 + np.random.normal(0, 0.06)
            lon = 139.7671 + np.random.normal(0, 0.07)
        elif area == "神奈川":
            lat = 35.4478 + np.random.normal(0, 0.07)
            lon = 139.6425 + np.random.normal(0, 0.07)
        else:
            city = other_cities[np.random.randint(len(other_cities))]
            lat = city[0] + np.random.normal(0, 0.12)
            lon = city[1] + np.random.normal(0, 0.12)
        lats.append(lat)
        lons.append(lon)

    df = pd.DataFrame({
        "date": dates,
        "amount": amounts,
        "category": categories,
        "area": areas,
        "result": results,
        "lat": lats,
        "lon": lons,
    })
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df


# ─────────────────────────────────────────
# 特徴量エンジニアリング
# ─────────────────────────────────────────

def prepare_features(df: pd.DataFrame):
    """
    モデル学習用の特徴量を作成する。
    カテゴリ変数をラベルエンコーディングし、数値特徴量と結合する。
    """
    df = df.copy()

    # カテゴリ・エリアをラベルエンコード
    le_cat = LabelEncoder()
    le_area = LabelEncoder()
    df["category_enc"] = le_cat.fit_transform(df["category"])
    df["area_enc"] = le_area.fit_transform(df["area"])

    # 月・四半期を特徴量として追加（季節性を捉える）
    df["month"] = df["date"].dt.month
    df["quarter"] = df["date"].dt.quarter

    # 特徴量リスト
    feature_cols = ["amount", "category_enc", "area_enc", "month", "quarter"]
    X = df[feature_cols]
    y = df["result"]

    return X, y, le_cat, le_area, feature_cols


# ─────────────────────────────────────────
# モデル学習
# ─────────────────────────────────────────

@st.cache_resource
def train_model(df: pd.DataFrame, model_type: str):
    """
    受注予測モデルを学習し、評価指標とともに返す。
    st.cache_resource でキャッシュして再実行を抑制。
    """
    X, y, le_cat, le_area, feature_cols = prepare_features(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    if model_type == "ランダムフォレスト":
        model = RandomForestClassifier(n_estimators=200, random_state=42, class_weight="balanced")
        scaler = None  # ランダムフォレストはスケーリング不要
        model.fit(X_train, y_train)
    else:
        # ロジスティック回帰はスケーリングが必要
        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)
        model = LogisticRegression(max_iter=1000, random_state=42, class_weight="balanced")
        model.fit(X_train_s, y_train)
        X_test = X_test_s  # 評価用に置き換え

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "auc": roc_auc_score(y_test, y_prob),
        "report": classification_report(y_test, y_pred, target_names=["失注", "受注"]),
    }

    return model, scaler, le_cat, le_area, feature_cols, metrics


# ─────────────────────────────────────────
# サイドバー：データ読み込み設定
# ─────────────────────────────────────────

with st.sidebar:
    st.header("⚙️ 設定")

    # データソース選択
    data_source = st.radio(
        "データソース",
        ["サンプルデータを使用", "CSVをアップロード"],
    )

    if data_source == "CSVをアップロード":
        uploaded = st.file_uploader(
            "CSVファイルを選択",
            type=["csv"],
            help="date, amount, category, area, result の列が必要です",
        )
        if uploaded:
            df_raw = pd.read_csv(uploaded, parse_dates=["date"])
            st.success(f"✅ {len(df_raw)} 件読み込み完了")
        else:
            st.info("CSVがアップロードされるまでサンプルデータを表示します")
            df_raw = generate_sample_data()
    else:
        df_raw = generate_sample_data()
        st.info("サンプルデータ（300件）を使用中")

    st.divider()

    # モデル選択
    model_type = st.selectbox(
        "予測モデル",
        ["ランダムフォレスト", "ロジスティック回帰"],
        help="ランダムフォレストは精度重視、ロジスティック回帰は解釈性重視",
    )

    st.divider()
    st.caption("LuminaTech 受注予測システム v1.0")

# ─────────────────────────────────────────
# タブ構成
# ─────────────────────────────────────────

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 ダッシュボード",
    "🤖 モデル評価",
    "🔮 受注確率予測",
       "📋 データ確認",
    "🧠 エージェント",
])

# ─────────────────────────────────────────
# タブ1: ダッシュボード（グラフ表示）
# ─────────────────────────────────────────

with tab1:
    st.subheader("📊 受注データ概要")

    # KPI指標
    total = len(df_raw)
    won = df_raw["result"].sum()
    win_rate = won / total * 100
    total_revenue = df_raw[df_raw["result"] == 1]["amount"].sum()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("総案件数", f"{total:,} 件")
    col2.metric("受注件数", f"{won:,} 件")
    col3.metric("受注率", f"{win_rate:.1f} %")
    col4.metric("受注総額", f"¥{total_revenue:,.0f}")

    st.divider()

    # ─── 地図: 会社 → 受注現場 アーク表示 ───────────────────────────
    st.subheader("🗾 受注マップ — 会社から現場への光線")

    map_filter = st.radio(
        "表示する案件",
        ["受注のみ", "失注のみ", "すべて"],
        horizontal=True,
    )

    df_map = df_raw.copy()
    if map_filter == "受注のみ":
        df_map = df_map[df_map["result"] == 1]
    elif map_filter == "失注のみ":
        df_map = df_map[df_map["result"] == 0]

    # アークの色（受注=青緑、失注=オレンジ）
    df_map["color_r"] = df_map["result"].map({1: 0,   0: 255})
    df_map["color_g"] = df_map["result"].map({1: 200, 0: 120})
    df_map["color_b"] = df_map["result"].map({1: 255, 0: 0})
    df_map["alpha"]   = 180
    # 金額に比例してアーク幅を調整（最小1、最大8）
    df_map["arc_width"] = (
        (df_map["amount"] / df_map["amount"].max() * 7 + 1).clip(1, 8)
    )
    # tooltip用テキスト
    df_map["tooltip"] = df_map.apply(
        lambda r: f"{r['category']} / {r['area']} / ¥{r['amount']:,} / {'受注✅' if r['result'] else '失注❌'}",
        axis=1,
    )

    # 会社所在地レイヤー（大きな黄色マーカー）
    company_df = pd.DataFrame([{
        "lat": COMPANY_LAT, "lon": COMPANY_LON, "label": COMPANY_NAME
    }])

    arc_layer = pdk.Layer(
        "ArcLayer",
        data=df_map,
        get_source_position=[COMPANY_LON, COMPANY_LAT],   # 会社（固定）
        get_target_position=["lon", "lat"],                # 現場
        get_source_color=[255, 220, 0, 200],               # 黄色（会社側）
        get_target_color=["color_r", "color_g", "color_b", "alpha"],
        get_width="arc_width",
        pickable=True,
        auto_highlight=True,
    )

    scatter_layer = pdk.Layer(
        "ScatterplotLayer",
        data=df_map,
        get_position=["lon", "lat"],
        get_fill_color=["color_r", "color_g", "color_b", 220],
        get_radius=2500,
        pickable=True,
    )

    company_layer = pdk.Layer(
        "ScatterplotLayer",
        data=company_df,
        get_position=["lon", "lat"],
        get_fill_color=[255, 220, 0, 255],
        get_radius=8000,
        pickable=True,
    )

    company_text_layer = pdk.Layer(
        "TextLayer",
        data=company_df,
        get_position=["lon", "lat"],
        get_text="label",
        get_size=14,
        get_color=[255, 255, 255, 255],
        get_alignment_baseline="'bottom'",
    )

    view = pdk.ViewState(
        latitude=36.2,
        longitude=138.8,
        zoom=5.8,
        pitch=45,
        bearing=-10,
    )

    st.pydeck_chart(
        pdk.Deck(
            layers=[arc_layer, scatter_layer, company_layer, company_text_layer],
            initial_view_state=view,
            map_style="mapbox://styles/mapbox/dark-v10",
            tooltip={"text": "{tooltip}"},
        ),
        height=520,
    )

    col_leg1, col_leg2, col_leg3 = st.columns(3)
    col_leg1.info(f"🏢 会社: {COMPANY_NAME}")
    col_leg2.success(f"🔵 受注案件: {(df_raw['result']==1).sum()} 件")
    col_leg3.error(f"🟠 失注案件: {(df_raw['result']==0).sum()} 件")

    st.divider()

    # グラフ1: 月別受注額の推移
    st.subheader("📈 月別受注額の推移")

    df_won = df_raw[df_raw["result"] == 1].copy()
    df_won["year_month"] = df_won["date"].dt.to_period("M").astype(str)
    monthly = df_won.groupby("year_month")["amount"].sum().reset_index()
    monthly.columns = ["年月", "受注額"]

    fig_monthly = px.bar(
        monthly,
        x="年月",
        y="受注額",
        title="月別受注額（円）",
        color_discrete_sequence=["#1f77b4"],
        labels={"受注額": "受注額（円）"},
    )
    fig_monthly.update_layout(xaxis_tickangle=-45, height=400)
    st.plotly_chart(fig_monthly, use_container_width=True)

    col_left, col_right = st.columns(2)

    # グラフ2: 工事種別の受注率
    with col_left:
        st.subheader("🏗️ 工事種別の受注率")
        cat_stats = df_raw.groupby("category").agg(
            total=("result", "count"),
            won=("result", "sum"),
        ).reset_index()
        cat_stats["受注率(%)"] = (cat_stats["won"] / cat_stats["total"] * 100).round(1)

        fig_cat = px.bar(
            cat_stats,
            x="category",
            y="受注率(%)",
            color="category",
            text="受注率(%)",
            title="工事種別ごとの受注率",
            labels={"category": "工事種別"},
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig_cat.update_traces(texttemplate="%{text}%", textposition="outside")
        fig_cat.update_layout(showlegend=False, height=380)
        st.plotly_chart(fig_cat, use_container_width=True)

        # 詳細テーブル
        st.dataframe(
            cat_stats.rename(columns={"category": "種別", "total": "総件数", "won": "受注件数"}),
            use_container_width=True,
            hide_index=True,
        )

    # グラフ3: エリア別の受注率
    with col_right:
        st.subheader("📍 エリア別の受注率")
        area_stats = df_raw.groupby("area").agg(
            total=("result", "count"),
            won=("result", "sum"),
        ).reset_index()
        area_stats["受注率(%)"] = (area_stats["won"] / area_stats["total"] * 100).round(1)

        fig_area = px.bar(
            area_stats,
            x="area",
            y="受注率(%)",
            color="area",
            text="受注率(%)",
            title="エリアごとの受注率",
            labels={"area": "エリア"},
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig_area.update_traces(texttemplate="%{text}%", textposition="outside")
        fig_area.update_layout(showlegend=False, height=380)
        st.plotly_chart(fig_area, use_container_width=True)

        # 詳細テーブル
        st.dataframe(
            area_stats.rename(columns={"area": "エリア", "total": "総件数", "won": "受注件数"}),
            use_container_width=True,
            hide_index=True,
        )

    # グラフ4: 工事種別×エリアのヒートマップ
    st.subheader("🗺️ 工事種別 × エリア 受注率ヒートマップ")
    pivot = df_raw.groupby(["category", "area"])["result"].mean().unstack(fill_value=0) * 100
    fig_heat = px.imshow(
        pivot,
        text_auto=".1f",
        color_continuous_scale="Blues",
        title="受注率 (%) ヒートマップ",
        labels={"x": "エリア", "y": "工事種別", "color": "受注率(%)"},
        aspect="auto",
    )
    fig_heat.update_layout(height=350)
    st.plotly_chart(fig_heat, use_container_width=True)

    # グラフ5: 見積金額分布と受注/失注
    st.subheader("💰 見積金額の分布（受注 vs 失注）")
    df_plot = df_raw.copy()
    df_plot["結果"] = df_plot["result"].map({1: "受注", 0: "失注"})
    fig_box = px.box(
        df_plot,
        x="category",
        y="amount",
        color="結果",
        title="工事種別ごとの見積金額分布",
        labels={"category": "工事種別", "amount": "見積金額（円）"},
        color_discrete_map={"受注": "#2196F3", "失注": "#FF7043"},
    )
    fig_box.update_layout(height=400)
    st.plotly_chart(fig_box, use_container_width=True)


# ─────────────────────────────────────────
# タブ2: モデル評価
# ─────────────────────────────────────────

with tab2:
    st.subheader("🤖 予測モデルの評価")

    # モデル学習
    with st.spinner("モデルを学習中..."):
        model, scaler, le_cat, le_area, feature_cols, metrics = train_model(df_raw, model_type)

    col_m1, col_m2 = st.columns(2)
    col_m1.metric("正解率 (Accuracy)", f"{metrics['accuracy']:.3f}")
    col_m2.metric("AUC スコア", f"{metrics['auc']:.3f}")

    st.subheader("分類レポート")
    st.code(metrics["report"], language="text")

    # 特徴量重要度（ランダムフォレストのみ）
    if model_type == "ランダムフォレスト":
        st.subheader("📌 特徴量重要度")
        importance_df = pd.DataFrame({
            "特徴量": ["見積金額", "工事種別", "エリア", "月", "四半期"],
            "重要度": model.feature_importances_,
        }).sort_values("重要度", ascending=True)

        fig_imp = px.bar(
            importance_df,
            x="重要度",
            y="特徴量",
            orientation="h",
            title="受注予測に影響する要因の重要度",
            color="重要度",
            color_continuous_scale="Blues",
        )
        fig_imp.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig_imp, use_container_width=True)

    elif model_type == "ロジスティック回帰":
        # ロジスティック回帰の係数を可視化
        st.subheader("📌 各特徴量の係数（ロジスティック回帰）")
        coef_df = pd.DataFrame({
            "特徴量": ["見積金額", "工事種別", "エリア", "月", "四半期"],
            "係数": model.coef_[0],
        }).sort_values("係数", ascending=True)

        fig_coef = px.bar(
            coef_df,
            x="係数",
            y="特徴量",
            orientation="h",
            title="正の係数＝受注に有利、負の係数＝受注に不利",
            color="係数",
            color_continuous_scale="RdBu",
            color_continuous_midpoint=0,
        )
        fig_coef.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig_coef, use_container_width=True)


# ─────────────────────────────────────────
# タブ3: 新規案件の受注確率予測フォーム
# ─────────────────────────────────────────

with tab3:
    st.subheader("🔮 新規案件の受注確率を予測する")
    st.caption("案件情報を入力すると、AIが受注確率を算出します。")

    # モデルが未学習なら学習する
    if "model" not in dir():
        with st.spinner("モデルを準備中..."):
            model, scaler, le_cat, le_area, feature_cols, metrics = train_model(df_raw, model_type)

    with st.form("prediction_form"):
        col_f1, col_f2 = st.columns(2)

        with col_f1:
            input_date = st.date_input(
                "見積提出日",
                value=pd.Timestamp.today(),
                help="見積を提出する（した）日付",
            )
            input_amount = st.number_input(
                "見積金額（円）",
                min_value=100_000,
                max_value=50_000_000,
                value=3_000_000,
                step=100_000,
                format="%d",
                help="税抜きの見積金額を入力してください",
            )

        with col_f2:
            input_category = st.selectbox(
                "工事種別",
                options=["電気工事", "太陽光", "その他"],
            )
            input_area = st.selectbox(
                "エリア",
                options=["東京", "神奈川", "その他"],
            )

        submitted = st.form_submit_button("🔍 受注確率を予測する", use_container_width=True)

    if submitted:
        try:
            # 入力値をモデル用に変換
            input_month = pd.Timestamp(input_date).month
            input_quarter = (input_month - 1) // 3 + 1

            # カテゴリをエンコード（学習済みラベルに存在しない値は最近傍として扱う）
            cat_classes = list(le_cat.classes_)
            area_classes = list(le_area.classes_)
            cat_enc = cat_classes.index(input_category) if input_category in cat_classes else 0
            area_enc = area_classes.index(input_area) if input_area in area_classes else 0

            X_input = pd.DataFrame([{
                "amount": input_amount,
                "category_enc": cat_enc,
                "area_enc": area_enc,
                "month": input_month,
                "quarter": input_quarter,
            }])

            # ロジスティック回帰はスケーリングが必要
            if model_type == "ロジスティック回帰" and scaler is not None:
                X_input_scaled = scaler.transform(X_input)
                prob = model.predict_proba(X_input_scaled)[0][1]
            else:
                prob = model.predict_proba(X_input)[0][1]

            # 結果表示
            st.divider()
            col_r1, col_r2 = st.columns([1, 2])

            with col_r1:
                # 受注確率のゲージ表示
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=prob * 100,
                    title={"text": "受注確率 (%)"},
                    gauge={
                        "axis": {"range": [0, 100]},
                        "bar": {"color": "#1f77b4"},
                        "steps": [
                            {"range": [0, 33], "color": "#ffcccc"},
                            {"range": [33, 66], "color": "#fff3cd"},
                            {"range": [66, 100], "color": "#d4edda"},
                        ],
                        "threshold": {
                            "line": {"color": "red", "width": 4},
                            "thickness": 0.75,
                            "value": 50,
                        },
                    },
                    number={"suffix": "%", "font": {"size": 40}},
                ))
                fig_gauge.update_layout(height=300)
                st.plotly_chart(fig_gauge, use_container_width=True)

            with col_r2:
                st.markdown("### 予測結果")

                if prob >= 0.70:
                    st.success(f"✅ **受注見込み大** — 受注確率: **{prob*100:.1f}%**")
                    st.markdown("この案件は受注の可能性が高いです。積極的にフォローアップしましょう。")
                elif prob >= 0.50:
                    st.warning(f"⚠️ **受注見込み中** — 受注確率: **{prob*100:.1f}%**")
                    st.markdown("受注の可能性はありますが、競合との差別化や価格調整が鍵になります。")
                else:
                    st.error(f"❌ **受注見込み小** — 受注確率: **{prob*100:.1f}%**")
                    st.markdown("失注リスクが高めです。追加の提案や価格見直しを検討してください。")

                st.markdown("---")
                st.markdown("**入力内容のまとめ**")
                st.dataframe(pd.DataFrame({
                    "項目": ["見積提出日", "見積金額", "工事種別", "エリア"],
                    "値": [
                        str(input_date),
                        f"¥{input_amount:,}",
                        input_category,
                        input_area,
                    ],
                }), hide_index=True, use_container_width=True)

        except Exception as e:
            st.error(f"予測エラーが発生しました: {e}")
            st.info("入力値を確認し、再度お試しください。")


# ─────────────────────────────────────────
# タブ4: データ確認
# ─────────────────────────────────────────

with tab4:
    st.subheader("📋 読み込みデータの確認")

    col_d1, col_d2 = st.columns(2)
    col_d1.metric("総レコード数", f"{len(df_raw):,} 件")
    col_d2.metric("期間", f"{df_raw['date'].min().date()} 〜 {df_raw['date'].max().date()}")

    # フィルタ
    filter_cat = st.multiselect(
        "工事種別でフィルタ",
        options=df_raw["category"].unique().tolist(),
        default=df_raw["category"].unique().tolist(),
    )
    df_filtered = df_raw[df_raw["category"].isin(filter_cat)]

    # 表示
    df_display = df_filtered.copy()
    df_display["result"] = df_display["result"].map({1: "✅ 受注", 0: "❌ 失注"})
    df_display["amount"] = df_display["amount"].apply(lambda x: f"¥{x:,}")
    df_display.columns = ["見積日", "見積金額", "工事種別", "エリア", "受注結果"]

    st.dataframe(df_display, use_container_width=True, height=400)

    # CSV ダウンロード
    csv_data = df_raw.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        label="📥 データをCSVでダウンロード",
        data=csv_data,
        file_name="lumina_data.csv",
        mime="text/csv",
    )

    # データ統計
    st.subheader("📐 基本統計量")
    st.dataframe(
        df_raw[["amount"]].describe().map(lambda x: f"{x:,.0f}"),
        use_container_width=True,
    )


# ─────────────────────────────────────────
# エージェント応答ロジック
# ─────────────────────────────────────────

def _agent_help_text() -> str:
    return (
        "**質問できること（例）:**\n"
        "- 「受注率は？」— 全体の受注率を表示します\n"
        "- 「エリア別の受注率を教えて」— エリアごとの比較\n"
        "- 「工事種別の分析をして」— 種別ごとの受注状況\n"
        "- 「月別の売上推移は？」— 月次受注額の棒グラフ\n"
        "- 「見積金額の傾向は？」— 金額分布と受注の関係\n"
        "- 「サマリーを出して」— データ全体の概要\n"
        "- 「ランキングを見せて」— エリア×種別の受注率ランキング\n"
        "- 「ヘルプ」— このヘルプを表示します"
    )


def build_agent_response(question: str, df: pd.DataFrame):
    q = question.lower()
    fig = None

    if any(kw in q for kw in ["ヘルプ", "help", "使い方", "できること", "機能"]):
        return _agent_help_text(), None

    if any(kw in q for kw in ["サマリ", "概要", "まとめ", "summary", "overview", "全体"]):
        total = len(df)
        won = df["result"].sum()
        rate = won / total * 100
        revenue = df[df["result"] == 1]["amount"].sum()
        avg_amt = df["amount"].mean()
        best_area = df.groupby("area")["result"].mean().idxmax()
        best_cat = df.groupby("category")["result"].mean().idxmax()
        text = (
            f"### データ概要サマリー\n"
            f"| 項目 | 値 |\n|---|---|\n"
            f"| 総案件数 | **{total:,} 件** |\n"
            f"| 受注件数 | **{int(won):,} 件** |\n"
            f"| 受注率 | **{rate:.1f}%** |\n"
            f"| 受注総額 | **¥{revenue:,.0f}** |\n"
            f"| 平均見積金額 | **¥{avg_amt:,.0f}** |\n"
            f"| 最高受注率エリア | **{best_area}** |\n"
            f"| 最高受注率工事種別 | **{best_cat}** |"
        )
        return text, None

    if any(kw in q for kw in ["受注率", "勝率", "win rate", "受注割合"]):
        if not any(kw in q for kw in ["エリア", "area", "地域", "種別", "カテゴリ", "category"]):
            total = len(df)
            won = int(df["result"].sum())
            rate = won / total * 100
            text = (
                f"### 全体の受注率\n"
                f"- 総案件数: **{total:,} 件**\n"
                f"- 受注件数: **{won:,} 件**\n"
                f"- **受注率: {rate:.1f}%**\n\n"
            )
            if rate >= 60:
                text += "好調です！引き続き積極的な提案を続けましょう。"
            elif rate >= 45:
                text += "平均的な受注率です。提案の質向上や価格戦略の見直しが効果的かもしれません。"
            else:
                text += "受注率改善の余地があります。エリア・種別別の分析で弱点を特定しましょう。"
            return text, None

    if any(kw in q for kw in ["エリア", "area", "地域", "場所"]):
        stats = df.groupby("area").agg(
            total=("result", "count"),
            won=("result", "sum"),
            revenue=("amount", "sum"),
        ).reset_index()
        stats["受注率(%)"] = (stats["won"] / stats["total"] * 100).round(1)
        stats = stats.sort_values("受注率(%)", ascending=False)
        fig = px.bar(
            stats, x="area", y="受注率(%)", color="area", text="受注率(%)",
            title="エリア別 受注率", labels={"area": "エリア"},
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig.update_traces(texttemplate="%{text}%", textposition="outside")
        fig.update_layout(showlegend=False, height=350)
        best = stats.iloc[0]
        rows = "\n".join(
            f"| {r['area']} | {int(r['total'])} | {int(r['won'])} | {r['受注率(%)']:.1f}% | ¥{r['revenue']:,.0f} |"
            for _, r in stats.iterrows()
        )
        text = (
            f"### エリア別 受注分析\n"
            f"| エリア | 総件数 | 受注 | 受注率 | 受注額 |\n|---|---|---|---|---|\n{rows}\n\n"
            f"**最も受注率が高いエリアは「{best['area']}」（{best['受注率(%)']:.1f}%）です。**"
        )
        return text, fig

    if any(kw in q for kw in ["種別", "カテゴリ", "category", "電気工事", "太陽光", "工事"]):
        stats = df.groupby("category").agg(
            total=("result", "count"),
            won=("result", "sum"),
            revenue=("amount", "sum"),
        ).reset_index()
        stats["受注率(%)"] = (stats["won"] / stats["total"] * 100).round(1)
        stats = stats.sort_values("受注率(%)", ascending=False)
        fig = px.bar(
            stats, x="category", y="受注率(%)", color="category", text="受注率(%)",
            title="工事種別 受注率", labels={"category": "工事種別"},
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig.update_traces(texttemplate="%{text}%", textposition="outside")
        fig.update_layout(showlegend=False, height=350)
        best = stats.iloc[0]
        rows = "\n".join(
            f"| {r['category']} | {int(r['total'])} | {int(r['won'])} | {r['受注率(%)']:.1f}% | ¥{r['revenue']:,.0f} |"
            for _, r in stats.iterrows()
        )
        text = (
            f"### 工事種別 受注分析\n"
            f"| 種別 | 総件数 | 受注 | 受注率 | 受注額 |\n|---|---|---|---|---|\n{rows}\n\n"
            f"**最も受注率が高い種別は「{best['category']}」（{best['受注率(%)']:.1f}%）です。**"
        )
        return text, fig

    if any(kw in q for kw in ["月", "month", "推移", "トレンド", "trend", "売上", "時系列"]):
        df_won = df[df["result"] == 1].copy()
        df_won["year_month"] = df_won["date"].dt.to_period("M").astype(str)
        monthly = df_won.groupby("year_month")["amount"].sum().reset_index()
        monthly.columns = ["年月", "受注額"]
        fig = px.bar(
            monthly, x="年月", y="受注額", title="月別受注額の推移",
            color_discrete_sequence=["#1f77b4"], labels={"受注額": "受注額（円）"},
        )
        fig.update_layout(xaxis_tickangle=-45, height=380)
        peak_row = monthly.loc[monthly["受注額"].idxmax()]
        total_rev = monthly["受注額"].sum()
        avg_rev = monthly["受注額"].mean()
        text = (
            f"### 月別受注額の推移\n"
            f"- **受注総額**: ¥{total_rev:,.0f}\n"
            f"- **月平均受注額**: ¥{avg_rev:,.0f}\n"
            f"- **最高月**: {peak_row['年月']}（¥{peak_row['受注額']:,.0f}）\n\n"
            f"月次の詳細はグラフをご確認ください。"
        )
        return text, fig

    if any(kw in q for kw in ["金額", "amount", "見積", "価格", "費用"]):
        df_plot = df.copy()
        df_plot["結果"] = df_plot["result"].map({1: "受注", 0: "失注"})
        fig = px.box(
            df_plot, x="category", y="amount", color="結果",
            title="工事種別ごとの見積金額分布（受注 vs 失注）",
            labels={"category": "工事種別", "amount": "見積金額（円）"},
            color_discrete_map={"受注": "#2196F3", "失注": "#FF7043"},
        )
        fig.update_layout(height=380)
        won_avg = df[df["result"] == 1]["amount"].mean()
        lost_avg = df[df["result"] == 0]["amount"].mean()
        text = (
            f"### 見積金額の分析\n"
            f"- **受注案件の平均金額**: ¥{won_avg:,.0f}\n"
            f"- **失注案件の平均金額**: ¥{lost_avg:,.0f}\n\n"
            + (
                "受注案件の方が平均金額が低い傾向があります。高額案件は競合が激しい可能性があります。"
                if won_avg < lost_avg
                else "受注案件の方が平均金額が高い傾向があります。付加価値の高い提案が奏功しています。"
            )
        )
        return text, fig

    if any(kw in q for kw in ["ランキング", "ranking", "rank", "上位", "best", "一番"]):
        pivot = (
            df.groupby(["area", "category"])["result"]
            .mean().reset_index()
            .rename(columns={"result": "受注率"})
            .sort_values("受注率", ascending=False)
        )
        pivot["受注率(%)"] = (pivot["受注率"] * 100).round(1)
        fig = px.bar(
            pivot.head(9),
            x="受注率(%)",
            y=pivot.head(9).apply(lambda r: f"{r['area']}×{r['category']}", axis=1),
            orientation="h", title="エリア×工事種別 受注率ランキング（上位）",
            color="受注率(%)", color_continuous_scale="Blues",
        )
        fig.update_layout(height=400, showlegend=False, yaxis_title="")
        top = pivot.iloc[0]
        rows = "\n".join(
            f"| {i+1} | {r['area']} | {r['category']} | {r['受注率(%)']:.1f}% |"
            for i, (_, r) in enumerate(pivot.head(9).iterrows())
        )
        text = (
            f"### エリア×工事種別 受注率ランキング\n"
            f"| 順位 | エリア | 種別 | 受注率 |\n|---|---|---|---|\n{rows}\n\n"
            f"**トップは「{top['area']} × {top['category']}」（{top['受注率(%)']:.1f}%）です。**"
        )
        return text, fig

    total = len(df)
    won = int(df["result"].sum())
    rate = won / total * 100
    text = (
        f"「{question}」についての分析結果です。\n\n"
        f"現在 **{total:,} 件** のデータが読み込まれており、受注率は **{rate:.1f}%** です。\n\n"
        + _agent_help_text()
    )
    return text, None


# ─────────────────────────────────────────
# タブ5: エージェントビュー
# ─────────────────────────────────────────

with tab5:
    st.subheader("🧠 AIデータエージェント")
    st.caption("データについて日本語で質問してください。受注状況・エリア・種別・金額などを分析します。")

    if "agent_messages" not in st.session_state:
        st.session_state.agent_messages = [
            {
                "role": "assistant",
                "content": (
                    "こんにちは！LuminaTech 受注予測エージェントです。\n\n"
                    + _agent_help_text()
                ),
                "figure": None,
            }
        ]

    for msg in st.session_state.agent_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("figure") is not None:
                st.plotly_chart(msg["figure"], use_container_width=True)

    user_input = st.chat_input("例: エリア別の受注率を教えて")

    if user_input:
        st.session_state.agent_messages.append(
            {"role": "user", "content": user_input, "figure": None}
        )
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("分析中..."):
                response_text, response_fig = build_agent_response(user_input, df_raw)
            st.markdown(response_text)
            if response_fig is not None:
                st.plotly_chart(response_fig, use_container_width=True)

        st.session_state.agent_messages.append(
            {"role": "assistant", "content": response_text, "figure": response_fig}
        )

    if len(st.session_state.agent_messages) > 1:
        if st.button("🗑️ 会話をクリア", key="clear_agent"):
            st.session_state.agent_messages = [
                {
                    "role": "assistant",
                    "content": (
                        "会話をリセットしました。新しい質問をどうぞ！\n\n"
                        + _agent_help_text()
                    ),
                    "figure": None,
                }
            ]
            st.rerun()
