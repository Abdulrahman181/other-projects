"""Streamlit dashboard for the SHEGLAM product export.

The dashboard deliberately fails closed when its source CSV is absent or invalid;
it never creates placeholder rows or reports fabricated metrics.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import streamlit as st

from data_utils import DataValidationError, load_products

REPOSITORY_DIR = Path(__file__).resolve().parent
_configured_path = Path(os.getenv("SHEGLAM_DATA_PATH", "sheglam_products.csv")).expanduser()
DATA_PATH = _configured_path if _configured_path.is_absolute() else REPOSITORY_DIR / _configured_path


st.set_page_config(page_title="SHEGLAM Product Analysis", page_icon="💄", layout="wide")
st.title("SHEGLAM Product Analysis Dashboard")
st.markdown("[Visit the SHEGLAM website](https://www.sheglam.com/)")

try:
    df = load_products(DATA_PATH)
except FileNotFoundError as exc:
    st.error(str(exc))
    st.info("Set SHEGLAM_DATA_PATH to another CSV path or collect the data first.")
    st.stop()
except DataValidationError as exc:
    st.error(f"Product data is invalid: {exc}")
    st.stop()

st.caption(f"Source: `{DATA_PATH}` · {len(df):,} rows loaded")

with st.sidebar:
    st.header("Filter options")
    categories = sorted(df["Category"].dropna().unique().tolist())
    selected_categories = st.multiselect(
        "Category", categories, default=categories, key="category_filter"
    )

filtered_df = df[df["Category"].isin(selected_categories)].copy()
tab_dashboard, tab_visuals, tab_collections = st.tabs(
    ["Dashboard", "Visualizations", "Collections"]
)

with tab_dashboard:
    st.subheader("Filtered products")
    if filtered_df.empty:
        st.info("Select at least one category to view products.")
    else:
        st.write(f"Total results: {len(filtered_df):,}")
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)

        st.header("Descriptive statistics")
        numeric = filtered_df[["Price", "Stars"]].dropna(how="all")
        if numeric.empty:
            st.info("No valid Price or Stars values are available for statistics.")
        else:
            st.dataframe(numeric.describe().round(2), use_container_width=True)

        category_stats = (
            filtered_df.groupby("Category", observed=True)[["Price", "Stars"]]
            .mean(numeric_only=True)
            .round(2)
        )
        subcategory_stats = (
            filtered_df.groupby("Subcategory", observed=True)[["Price", "Stars"]]
            .mean(numeric_only=True)
            .round(2)
        )
        st.subheader("Average price and rating by category")
        st.dataframe(category_stats, use_container_width=True)
        st.subheader("Average price and rating by subcategory")
        st.dataframe(subcategory_stats, use_container_width=True)

        seller_rows = filtered_df.dropna(subset=["Best Seller"])
        seller_counts = seller_rows["Category"].where(
            seller_rows["Best Seller"].eq(1)
        ).dropna().value_counts()
        st.subheader("Best sellers by category")
        st.dataframe(
            seller_counts.rename("Best Seller Count").to_frame(),
            use_container_width=True,
        )

        top_rated = (
            filtered_df.dropna(subset=["Stars"])
            .loc[lambda frame: frame["Stars"].ge(4.5)]
            .sort_values(["Stars", "Price"], ascending=[False, True], na_position="last")
            .head(10)
        )
        st.subheader("Top-rated products (4.5+ stars)")
        if top_rated.empty:
            st.info("No products meet the 4.5-star threshold in this selection.")
        else:
            st.dataframe(
                top_rated[["Name", "Stars", "Category", "Price"]],
                use_container_width=True,
                hide_index=True,
            )

with tab_visuals:
    if filtered_df.empty:
        st.info("Select at least one category to view visualizations.")
    else:
        category_stats = (
            filtered_df.groupby("Category", observed=True)[["Price", "Stars"]]
            .mean(numeric_only=True)
            .dropna(how="all")
            .sort_values("Price", ascending=False, na_position="last")
        )
        if category_stats.empty:
            st.info("No valid numeric data is available for category charts.")
        elif category_stats["Price"].dropna().empty:
            st.info("No valid prices are available for the category chart.")
        else:
            st.header("Average price and rating by category")
            fig, ax = plt.subplots(figsize=(10, 6))
            price_stats = category_stats["Price"].dropna()
            sns.barplot(
                x=price_stats.index,
                y=price_stats,
                color="#CCCCFF",
                ax=ax,
            )
            ax.set_ylabel("Average price (USD)")
            ax.set_xlabel("Category")
            ax.tick_params(axis="x", rotation=45)
            rating_stats = category_stats["Stars"].reindex(price_stats.index).dropna()
            if not rating_stats.empty:
                ax2 = ax.twinx()
                ax2.plot(
                    rating_stats.index,
                    rating_stats,
                    color="#B388EB",
                    marker="o",
                )
                ax2.set_ylabel("Average stars")
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

        st.header("Product distribution by category")
        counts = filtered_df["Category"].value_counts()
        if counts.empty:
            st.info("No category values are available.")
        else:
            fig, ax = plt.subplots(figsize=(8, 5))
            sns.barplot(x=counts.index, y=counts.values, color="#FFB6C1", ax=ax)
            ax.set_xlabel("Category")
            ax.set_ylabel("Products")
            ax.tick_params(axis="x", rotation=45)
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

        st.header("Best sellers vs regular products")
        seller_stats = (
            filtered_df.dropna(subset=["Best Seller"])
            .assign(ProductType=lambda frame: frame["Best Seller"].map({0: "Regular", 1: "Best seller"}))
            .groupby("ProductType", observed=True)[["Price", "Stars"]]
            .mean(numeric_only=True)
            .round(2)
        )
        if seller_stats.empty:
            st.info("No valid Best Seller flags are available.")
        else:
            st.dataframe(seller_stats, use_container_width=True)
            traces = []
            for metric in ("Price", "Stars"):
                values = seller_stats[metric].dropna()
                if not values.empty:
                    traces.append(go.Bar(x=values.index, y=values, name=metric))
            if traces:
                fig = go.Figure(traces)
                fig.update_layout(barmode="group", yaxis_title="Average value")
                st.plotly_chart(fig, use_container_width=True)

        st.header("Price and rating distributions")
        col_price, col_stars = st.columns(2)
        with col_price:
            prices = filtered_df["Price"].dropna()
            if prices.empty:
                st.info("No valid prices.")
            else:
                fig, ax = plt.subplots()
                sns.histplot(prices, bins=20, kde=False, ax=ax, color="hotpink")
                ax.set_xlabel("Price (USD)")
                st.pyplot(fig)
                plt.close(fig)
        with col_stars:
            stars = filtered_df["Stars"].dropna()
            if stars.empty:
                st.info("No valid ratings.")
            else:
                fig, ax = plt.subplots()
                sns.histplot(stars, bins=10, kde=False, ax=ax, color="hotpink")
                ax.set_xlabel("Stars")
                st.pyplot(fig)
                plt.close(fig)

        st.header("Common words in product names")
        text = " ".join(filtered_df["Name"].dropna().astype(str))
        if not text.strip():
            st.info("No product names are available for a word cloud.")
        else:
            try:
                from wordcloud import WordCloud
            except ImportError:
                st.warning("Install the optional `wordcloud` dependency to enable this chart.")
            else:
                wordcloud = WordCloud(
                    width=800, height=400, background_color="white", colormap="pink"
                ).generate(text)
                fig, ax = plt.subplots(figsize=(10, 5))
                ax.imshow(wordcloud, interpolation="bilinear")
                ax.axis("off")
                st.pyplot(fig)
                plt.close(fig)

with tab_collections:
    if filtered_df.empty:
        st.info("Select at least one category to view collections.")
    else:
        collection_patterns = [
            r"Adventure\s*Time",
            r"Harry\s*Potter\s*\|\s*SHEGLAM\s*2\.0",
            r"Harley\s*Quinn",
            r"Rick\s*and\s*Morty",
            r"Crimson\s*Butterfly",
            r"Hello\s*Kitty\s*\|\s*SHEGLAM",
            r"The\s*Powerpuff\s*Girls",
            r"Ember\s*Rose",
            r"Cosmic\s*Come\s*Up",
            r"Harry\s*Potter\s*\|\s*SHEGLAM\s*1\.0",
            r"Chroma\s*Zone\s*2\.0",
            r"Care\s*Bears",
            r"Corpse\s*Bride",
            r"Marilyn\s*Monroe",
            r"Frida\s*Kahlo",
            r"Willy\s*Wonka",
        ]
        combined_pattern = re.compile("|".join(collection_patterns), re.IGNORECASE)
        collections_df = filtered_df.assign(
            Collection=filtered_df["Name"].str.extract(
                f"({combined_pattern.pattern})", flags=re.IGNORECASE, expand=False
            )
        ).dropna(subset=["Collection"])

        if collections_df.empty:
            st.info("No known collection names were found in the selected products.")
        else:
            avg_price = (
                collections_df.groupby("Collection", observed=True)["Price"]
                .mean()
                .dropna()
                .round(2)
                .sort_values(ascending=False)
            )
            if avg_price.empty:
                st.info("No valid prices are available for collection analysis.")
            else:
                fig = px.scatter(
                    avg_price.reset_index(),
                    x="Collection",
                    y="Price",
                    size="Price",
                    title="Average price by collection",
                )
                fig.update_layout(yaxis_title="Average price (USD)")
                st.plotly_chart(fig, use_container_width=True)

            collection_summary = (
                collections_df.dropna(subset=["Best Seller"])
                .groupby("Collection", observed=True)["Best Seller"]
                .agg(Total="count", Best=lambda values: values.eq(1).sum())
                .reset_index()
            )
            if collection_summary.empty:
                st.info("No valid Best Seller flags are available for collections.")
            else:
                fig = go.Figure(
                    [
                        go.Bar(
                            x=collection_summary["Collection"],
                            y=collection_summary["Total"],
                            name="Total products",
                        ),
                        go.Bar(
                            x=collection_summary["Collection"],
                            y=collection_summary["Best"],
                            name="Best sellers",
                        ),
                    ]
                )
                fig.update_layout(
                    barmode="group",
                    yaxis_title="Count",
                    xaxis_tickangle=-45,
                )
                st.plotly_chart(fig, use_container_width=True)
