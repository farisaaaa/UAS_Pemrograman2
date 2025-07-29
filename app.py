import streamlit as st
import pandas as pd
import plotly.express as px
import pickle
import os
from geopy.distance import geodesic
import folium
from streamlit_folium import st_folium

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="🚛 Optimasi Rute Logistik", layout="wide")

# =============================
# LOAD DATA
# =============================
data_path = "DataClean7_greedy.csv"
df = pd.read_csv(data_path)

# =============================
# INTERNAL CSS
# =============================
st.markdown("""
    <style>
        .big-title {
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 1rem;
        }
        .metric-box {
            background-color: #f1f3f6;
            padding: 1rem;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.05);
        }
        .metric-title {
            font-size: 1.2rem;
            color: #888;
        }
        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            color: #333;
        }
        .blue-bg {
            background: linear-gradient(90deg, #2196f3 0%, #21cbf3 100%);
            color: white;
            border-radius: 16px;
            padding: 1.5rem 1rem 1rem 1rem;
            margin-bottom: 1rem;
            box-shadow: 0px 4px 10px rgba(33, 150, 243, 0.08);
        }
        .blue-title {
            font-size: 2.2rem;
            font-weight: bold;
            color: #1565c0;
            margin-bottom: 0.5rem;
        }
        .blue-metric {
            font-size: 1.3rem;
            color: #1976d2;
            font-weight: 600;
        }
    </style>
""", unsafe_allow_html=True)

# =============================
# SIDEBAR NAVIGATION
# =============================
menu = st.sidebar.radio("Navigasi", ["📊 Dashboard", "🗺️ Rute Pengiriman"])

# =============================
# PAGE 1: DASHBOARD
# =============================
if menu == "📊 Dashboard":
    st.markdown("<div class='blue-title'>📊 Dashboard Logistik</div>", unsafe_allow_html=True)
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class='blue-bg'>
            <div class='blue-metric'>Total Order</div>
            <div class='metric-value'>{len(df)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class='blue-bg'>
            <div class='blue-metric'>Jumlah Batch</div>
            <div class='metric-value'>{df["Batch_Number"].nunique()}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class='blue-bg'>
            <div class='blue-metric'>Jenis Kendaraan</div>
            <div class='metric-value'>{df["Vehicle_Assigned"].nunique()}</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class='blue-bg'>
            <div class='blue-metric'>Rata-rata Berat</div>
            <div class='metric-value'>{df["Weight"].mean():.1f} kg</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    with st.container():
        st.markdown("#### Distribusi Kategori Barang")
        palette_senada = ["#0d47a1", "#1976d2", "#42a5f5", "#00bcd4", "#90a4ae", "#0097a7", "#b3e5fc"]

        kategori_counts = df["Category"].value_counts().reset_index()
        kategori_counts.columns = ["Category", "Jumlah"]

        fig = px.bar(
            kategori_counts,
            x="Category",
            y="Jumlah",
            color="Category",
            color_discrete_sequence=palette_senada
        )
        fig.update_layout(
            plot_bgcolor="#f0f7fa",
            paper_bgcolor="#f0f7fa",
            title="Distribusi Kategori Barang (Descending)",
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Pie Chart Distribusi Kendaraan")
    fig_pie = px.pie(df, names="Vehicle_Assigned", title="Proporsi Kendaraan", color_discrete_sequence=palette_senada)
    fig_pie.update_traces(textfont_size=16)
    st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("#### Sebaran Titik Pengiriman")
    fig_scatter = px.scatter_mapbox(
        df,
        lat="Start_Latitude",
        lon="Start_Longitude",
        color="Vehicle_Assigned",
        hover_name="Branch_Start",
        zoom=10,
        mapbox_style="open-street-map",
        title="Sebaran Titik Pengiriman",
        color_discrete_sequence=palette_senada
    )
    fig_scatter.update_traces(marker=dict(size=14, opacity=0.85))
    st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown("#### Rata-rata Berat per Batch")
    batch_options = sorted(df["Batch_Number"].unique())
    selected_batch_filter = st.selectbox("Filter Batch untuk Rata-rata Berat:", batch_options)
    berat_per_batch = df[df["Batch_Number"] == selected_batch_filter].groupby("Batch_Number")["Weight"].mean().reset_index()
    st.dataframe(berat_per_batch.rename(columns={"Weight": "Rata-rata Berat (kg)"}), use_container_width=True)

    st.markdown("---")
    st.subheader("📋 Tabel Data Pengiriman")
    st.dataframe(df[["Order_ID", "Branch_Start", "Weight", "Vehicle_Assigned", "Batch_Number"]])

# =============================
# PAGE 2: RUTE PENGIRIMAN
# =============================
elif menu == "🗺️ Rute Pengiriman":
    st.title("🗺️ Optimasi Rute Pengiriman (Greedy + GA)")
    model_dir = "model_ga"

    batch_list = sorted(df["Batch_Number"].unique())
    selected_batch = st.selectbox("Pilih Batch:", batch_list)

    try:
        model_path = os.path.join(model_dir, f"model_ga_batch_{selected_batch}.pkl")
        with open(model_path, "rb") as f:
            model = pickle.load(f)

        full_route = model["route"]
        full_distance = model["distance"]
        vehicle = model["vehicle"]
        titik_awal = full_route[0]

        st.markdown(f"### 🚚 Batch {selected_batch} ({vehicle})")
        st.markdown(f"**Rute lengkap:** {' ➝ '.join(full_route)}")
        st.markdown(f"**Total jarak:** {full_distance:.2f} km")

        tujuan_akhir = st.selectbox("Pilih Titik Tujuan Akhir:", full_route[1:])

        if tujuan_akhir in full_route:
            index = full_route.index(tujuan_akhir) + 1
            sub_route = full_route[:index]
            sub_distance = 0

            coord_map = df.groupby("Branch_Start")[["Start_Latitude", "Start_Longitude"]].first().to_dict(orient="index")
            for i in range(len(sub_route) - 1):
                a = coord_map[sub_route[i]]
                b = coord_map[sub_route[i + 1]]
                sub_distance += geodesic((a["Start_Latitude"], a["Start_Longitude"]), (b["Start_Latitude"], b["Start_Longitude"])).km

            st.markdown(f"### ✨ Rute yang Dapat Dilewati: {' ➝ '.join(sub_route)}")
            st.markdown(f"**Jarak hingga titik tujuan:** {sub_distance:.2f} km")

            m = folium.Map(location=[coord_map[titik_awal]["Start_Latitude"], coord_map[titik_awal]["Start_Longitude"]], zoom_start=12)
            for point in sub_route:
                latlon = coord_map[point]
                folium.Marker([latlon["Start_Latitude"], latlon["Start_Longitude"]], tooltip=point).add_to(m)
            folium.PolyLine([(coord_map[pt]["Start_Latitude"], coord_map[pt]["Start_Longitude"]) for pt in sub_route], color="blue").add_to(m)
            st_folium(m, width=700)

            st.markdown("#### Detail Titik pada Rute")
            st.dataframe(df[df["Branch_Start"].isin(sub_route)][["Branch_Start", "Start_Latitude", "Start_Longitude", "Weight"]])

            st.markdown("#### Berat per Titik pada Rute")
            fig_weight = px.bar(
                df[df["Branch_Start"].isin(sub_route)],
                x="Branch_Start",
                y="Weight",
                title="Berat per Titik pada Rute",
                color="Weight",
                color_continuous_scale=px.colors.sequential.Blues_r
            )
            st.plotly_chart(fig_weight, use_container_width=True)

            st.markdown("#### Rata-rata Berat per Batch pada Rute")
            berat_batch_rute = df[df["Branch_Start"].isin(sub_route)].groupby("Batch_Number")["Weight"].mean().reset_index()
            fig_batch_rute = px.bar(
                berat_batch_rute,
                x="Batch_Number",
                y="Weight",
                title="Rata-rata Berat per Batch pada Rute",
                color="Weight",
                color_continuous_scale=px.colors.sequential.Blues_r
            )
            st.plotly_chart(fig_batch_rute, use_container_width=True)

            st.markdown("#### Statistik Ringkas Rute")
            df_rute = df[df["Branch_Start"].isin(sub_route)]
            st.write(f"Jumlah titik pada rute: **{len(sub_route)}**")
            st.write(f"Berat total pada rute: **{df_rute['Weight'].sum():.2f} kg**")
            st.write(f"Berat rata-rata per titik: **{df_rute['Weight'].mean():.2f} kg**")

    except FileNotFoundError:
        st.error(f"Model GA untuk batch {selected_batch} tidak ditemukan. Pastikan file model_ga_batch_{selected_batch}.pkl ada di folder model_ga.")
