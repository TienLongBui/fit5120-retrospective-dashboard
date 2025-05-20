import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from textblob import TextBlob
import plotly.express as px

st.set_page_config(layout="wide")
st.title("📊 Retrospective Interactive Dashboard")

use_local = st.sidebar.checkbox("Use local file (dev only)")

if use_local:
    uploaded_file = "/Users/tealesbui/Downloads/Retrospective form (Responses).xlsx"
else:
    uploaded_file = st.sidebar.file_uploader("Upload Excel file", type=["xlsx"])

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)
    sheet_names = xls.sheet_names
    df_all = pd.concat([xls.parse(sheet).assign(Retrospective=sheet) for sheet in sheet_names], ignore_index=True)

    group_columns = {
        "Psychological Safety": df_all.columns[2:5],
        "Dependability": df_all.columns[5:8],
        "Structure & Clarity": df_all.columns[8:11],
        "Meaning": df_all.columns[11:14],
        "Impact": df_all.columns[14:17],
        "Personal Reflection": df_all.columns[17:23],
    }

    likert_cols = df_all.columns[2:-2]  # skip Timestamp, Score, free-text
    retrospectives = df_all["Retrospective"].unique().tolist()

    # Define written reflections
    written_reflections = []
    if "Iteration 3" in sheet_names:
        df_iter3 = xls.parse("Iteration 3")
        written_reflections = df_iter3.columns[23:30]

    tab1, tab2 = st.tabs(["📈 Quantitative Analysis", "📝 Textual Reflections"])

    with tab1:
        selected_retros = st.sidebar.multiselect("Filter retrospectives", options=retrospectives, default=retrospectives)
        selected_group = st.sidebar.selectbox("Select a question group", options=list(group_columns.keys()))
        selected_view = st.sidebar.radio("Analyze by", ["Grouped Theme", "Individual Question"])

        df_filtered = df_all[df_all["Retrospective"].isin(selected_retros)]

        if selected_view == "Grouped Theme":
            group_cols = group_columns[selected_group]
            group_df = df_filtered.copy()
            for col in group_cols:
                group_df[col] = pd.to_numeric(group_df[col], errors='coerce')

            avg_group = group_df.groupby("Retrospective")[group_cols].mean().mean(axis=1).reset_index()
            avg_group.columns = ["Retrospective", "Mean Score"]

            st.subheader(f"Average Score for Group: '{selected_group}'")
            fig3, ax3 = plt.subplots(figsize=(10, 5))
            sns.barplot(data=avg_group, x="Retrospective", y="Mean Score", palette="Set2", ax=ax3)

            for p in ax3.patches:
                height = p.get_height()
                ax3.text(p.get_x() + p.get_width() / 2., height + 0.05,
                         f'{height:.2f}', ha="center", fontsize=8)

            overall_avg = avg_group["Mean Score"].mean()
            ax3.axhline(overall_avg, color="gray", linestyle="--")
            ax3.text(-0.4, overall_avg + 0.1, f"Overall Avg: {overall_avg:.2f}", color="gray")

            ax3.set_ylim(0, 5.5)
            st.pyplot(fig3)

        else:
            group_cols = group_columns[selected_group]
            selected_q = st.sidebar.selectbox("Select a question", options=group_cols)
            show_average_line = st.sidebar.checkbox("Show average line", value=True)

            st.subheader(f"Average Score for: '{selected_q}'")
            avg_df = df_filtered.groupby("Retrospective")[selected_q].mean().reset_index()
            fig1, ax1 = plt.subplots(figsize=(10, 5))
            sns.barplot(data=avg_df, x="Retrospective", y=selected_q, palette="Set2", ax=ax1)
            for p in ax1.patches:
                height = p.get_height()
                ax1.text(p.get_x() + p.get_width() / 2., height + 0.05,
                         f'{height:.2f}', ha="center", fontsize=8)
            if show_average_line:
                overall_mean = df_filtered[selected_q].mean()
                ax1.axhline(overall_mean, color="gray", linestyle="--")
                ax1.text(-0.4, overall_mean + 0.1, f"Overall Avg: {overall_mean:.2f}", color="gray")
            ax1.set_ylim(0, 5.5)
            st.pyplot(fig1)

            st.subheader(f"Score Distribution for: '{selected_q}'")
            fig2, ax2 = plt.subplots(figsize=(10, 5))
            sns.boxplot(data=df_filtered, x="Retrospective", y=selected_q, palette="Pastel1", ax=ax2)
            ax2.set_ylim(0, 5.5)
            st.pyplot(fig2)

        st.subheader("📈 Overall Mean Scores Across Retrospectives")
        mean_only = df_filtered[likert_cols].copy()
        for col in likert_cols:
            mean_only[col] = pd.to_numeric(mean_only[col], errors='coerce')
        mean_scores = mean_only.groupby(df_filtered["Retrospective"]).mean().mean(axis=1).reset_index()
        mean_scores.columns = ["Retrospective", "Overall Mean"]
        fig4, ax4 = plt.subplots(figsize=(10, 4))
        sns.lineplot(data=mean_scores, x="Retrospective", y="Overall Mean", marker="o", ax=ax4)
        ax4.set_ylim(0, 5.5)
        st.pyplot(fig4)

    with tab2:
        st.subheader("📝 Written Reflections Analysis (Iteration 3 only)")

        if "Iteration 3" in sheet_names:
            df_iter3 = xls.parse("Iteration 3")

            text_cols = [
                col for col in df_iter3.columns
                if df_iter3[col].dtype == 'object'
                and df_iter3[col].dropna().apply(lambda x: len(str(x))).mean() > 30
            ]

            if text_cols:
                selected_col = st.selectbox("Select a reflection question", text_cols)
                text_data = df_iter3[selected_col].dropna().astype(str)
                text_data = text_data[text_data.str.strip() != ""]

                if not text_data.empty:
                    st.subheader(f"📄 All Responses for: {selected_col}")
                    for i, val in enumerate(text_data):
                        st.markdown(f"**{i+1}.** {val}")

                    all_text = " ".join(text_data.tolist()).strip()

                    if len(all_text.split()) > 1:
                        st.subheader("☁️ Word Cloud")
                        wordcloud = WordCloud(width=1000, height=500, background_color="white").generate(all_text)
                        fig, ax = plt.subplots(figsize=(10, 5))
                        ax.imshow(wordcloud, interpolation="bilinear")
                        ax.axis("off")
                        st.pyplot(fig)

                        st.subheader("💬 Sentiment Analysis")
                        sentiments = text_data.apply(lambda x: TextBlob(x).sentiment.polarity)
                        sentiment_df = pd.DataFrame({
                            "Response": text_data,
                            "Sentiment Polarity": sentiments
                        })
                        st.markdown(f"📌 **Number of Responses:** {len(text_data)}")
                        st.markdown(f"📌 **Average Sentiment Polarity:** {sentiment_df['Sentiment Polarity'].mean():.2f}")

                        with st.expander("🟢 Top 3 Most Positive Responses"):
                            st.write(sentiment_df.sort_values(by="Sentiment Polarity", ascending=False).head(3))

                        with st.expander("🔴 Top 3 Most Negative Responses"):
                            st.write(sentiment_df.sort_values(by="Sentiment Polarity", ascending=True).head(3))

                        fig_hist = px.histogram(sentiment_df, x="Sentiment Polarity", nbins=10,
                                               title="Sentiment Polarity Distribution",
                                               color_discrete_sequence=["#6CA0DC"])
                        st.plotly_chart(fig_hist, use_container_width=True)

                    else:
                        st.warning("⚠️ Not enough words to generate Word Cloud.")
                else:
                    st.warning("⚠️ No valid text responses found in the selected column.")
            else:
                st.warning("⚠️ No long-form text responses detected in Iteration 3.")
        else:
            st.warning("⚠️ Sheet 'Iteration 3' not found.")

else:
    st.info("👈 Please upload a retrospective Excel file to begin.")