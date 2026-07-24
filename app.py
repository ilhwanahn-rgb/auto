import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# --- 페이지 기본 설정 ---
st.set_page_config(page_title="선재/이형재 인발 소성가공 종합 산출 도구", layout="wide")

# --- 탭(Tab) 글자 크기 및 굵기 커스텀 CSS ---
st.markdown("""
    <style>
    /* 1. 기본 탭 글자 크기, 굵기, 색상 대폭 강화 */
    button[data-baseweb="tab"] {
        font-size: 20px !important;
        font-weight: 800 !important;
        color: #4b5563 !important;
        padding-top: 10px !important;
        padding-bottom: 10px !important;
        padding-left: 20px !important;
        padding-right: 20px !important;
    }
    
    /* 2. 현재 선택된(활성화된) 탭 강조 스타일 */
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #1d4ed8 !important;
        border-bottom-color: #1d4ed8 !important;
        border-bottom-width: 4px !important;
    }

    /* 3. 마우스 올렸을 때(Hover) 효과 */
    button[data-baseweb="tab"]:hover {
        color: #2563eb !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🛠️ 선재/이형재 인발 소성가공 종합 산출 도구")
st.markdown("단면 감면율, 인발력(95% 설비 검증), 중량, 직진도 환산 연산을 통합 처리하는 엔지니어링 계산기입니다.")

# --- 탭 구성 ---
tab1, tab2, tab3, tab4 = st.tabs([
    "1. 형상별 감면율 & 3D", 
    "2. 인발력 산출 (TS 및 95% 설비검증)", 
    "3. 중량 계산 (Round Bar)", 
    "4. 직진도 환산"
])

# ==========================================
# 공통 헬퍼 함수 (2D 단면 정점 생성)
# ==========================================
def generate_shape_points(shape, w, h, r, n_points=120):
    if shape == "정육각형":
        pts = []
        r_center = (w - 2 * r) / np.sqrt(3)
        for i in range(6):
            angle_c = np.pi/6 + i * np.pi/3
            cx, cy = r_center * np.cos(angle_c), r_center * np.sin(angle_c)
            arc_angles = np.linspace(angle_c - np.pi/6, angle_c + np.pi/6, n_points // 6)
            for a in arc_angles:
                pts.append([cx + r * np.cos(a), cy + r * np.sin(a)])
        pts = np.array(pts)
        return pts[:, 0], pts[:, 1]
        
    elif shape == "사각형 (정/직사각)":
        hw, hh = w / 2.0 - r, h / 2.0 - r
        centers = [(hw, hh), (-hw, hh), (-hw, -hh), (hw, -hh)]
        arcs = [(0, np.pi/2), (np.pi/2, np.pi), (np.pi, 3*np.pi/2), (3*np.pi/2, 2*np.pi)]
        pts = []
        for (cx, cy), (sa, ea) in zip(centers, arcs):
            arc = np.linspace(sa, ea, n_points // 4)
            for a in arc:
                pts.append([cx + r * np.cos(a), cy + r * np.sin(a)])
        pts = np.array(pts)
        return pts[:, 0], pts[:, 1]
        
    else: # 트랙형 (장원형)
        r_track = h / 2.0
        straight_len = max(0.0, (w - h) / 2.0)
        pts = []
        for a in np.linspace(-np.pi/2, np.pi/2, n_points // 2):
            pts.append([straight_len + r_track * np.cos(a), r_track * np.sin(a)])
        for a in np.linspace(np.pi/2, 3*np.pi/2, n_points // 2):
            pts.append([-straight_len + r_track * np.cos(a), r_track * np.sin(a)])
        pts = np.array(pts)
        return pts[:, 0], pts[:, 1]

# ==========================================
# [TAB 1] 형상별 감면율 및 3D 시각화
# ==========================================
with tab1:
    st.subheader("1. 입력 소재 및 목표 형상 치수")
    
    col_in1, col_in2 = st.columns(2)
    with col_in1:
        d_in = st.number_input("입력 원형 선경 d (mm)", value=30.0, min_value=1.0, step=0.5, key="t1_din")
        shape_type = st.selectbox("목표 단면 형상", ["정육각형", "사각형 (정/직사각)", "이형 (트랙/장원형)"], key="t1_shape")

    with col_in2:
        if shape_type == "정육각형":
            W = st.number_input("대면 치수 W (mm)", value=28.0, step=0.5, key="t1_w")
            R = st.slider("모서리 R (mm)", 0.0, float(W/2.0), 2.9, 0.1, key="t1_r")
            H = W
            max_diag = (2 * W / np.sqrt(3)) - 2 * R * ((2 / np.sqrt(3)) - 1)
            A2 = (np.sqrt(3) / 2.0) * (W ** 2) - (2 * np.sqrt(3) - np.pi) * (R ** 2)

        elif shape_type == "사각형 (정/직사각)":
            W = st.number_input("폭 W (mm)", value=25.0, step=0.5, key="t1_w_sq")
            H = st.number_input("높이 H (mm)", value=25.0, step=0.5, key="t1_h_sq")
            R = st.slider("모서리 R (mm)", 0.0, float(min(W, H)/2.0), 1.0, 0.1, key="t1_r_sq")
            max_diag = np.sqrt(W**2 + H**2) - 2 * R * (np.sqrt(2) - 1)
            A2 = W * H - (4.0 - np.pi) * (R ** 2)

        else: # 트랙형
            W = st.number_input("전체 폭 W (mm)", value=30.0, step=0.5, key="t1_w_tr")
            H = st.number_input("높이 H (mm)", value=18.0, step=0.5, key="t1_h_tr")
            R = H / 2.0
            max_diag = W
            A2 = (W - H) * H + (np.pi / 4.0) * (H ** 2)

    A1 = (np.pi / 4.0) * (d_in ** 2)
    RA = (1.0 - A2 / A1) * 100.0 if A1 > 0 else 0.0
    elongation = A1 / A2 if A2 > 0 else 0.0
    d_eq = np.sqrt(4 * A2 / np.pi) if A2 > 0 else 0.0

    st.session_state['A1'] = A1
    st.session_state['A2'] = A2
    st.session_state['RA'] = RA
    st.session_state['d_in'] = d_in

    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("소재 원형 단면적 (A₁)", f"{A1:.2f} mm²", f"원형 직경 Ø {d_in:.2f} mm", delta_color="off")
    c2.metric("성형 후 단면적 (A₂)", f"{A2:.2f} mm²", f"등가원경 Ø {d_eq:.2f} mm", delta_color="off")
    c3.metric("최대 대각/외경 치수 (D)", f"{max_diag:.2f} mm", f"대면 W {W:.2f} mm / R {R:.2f} mm", delta_color="off")
    c4.metric("감면율 (RA)", f"{RA:.2f} %", f"연신율 {elongation:.2f} 배", delta_color="normal")

    col_l, col_r = st.columns(2)
    n_pts = 120
    x_in = (d_in / 2.0) * np.cos(np.linspace(0, 2*np.pi, n_pts, endpoint=False))
    y_in = (d_in / 2.0) * np.sin(np.linspace(0, 2*np.pi, n_pts, endpoint=False))
    x_out, y_out = generate_shape_points(shape_type, W, H, R, n_points=n_pts)

    fig_2d = go.Figure()
    fig_2d.add_trace(go.Scatter(x=x_in, y=y_in, mode='lines', name=f'입력 원형 (Ø{d_in:.1f}mm)', line=dict(color='gray', dash='dash', width=2)))
    fig_2d.add_trace(go.Scatter(x=x_out, y=y_out, mode='lines', name=f'출력 {shape_type}', fill="toself", fillcolor='rgba(37, 99, 235, 0.25)', line=dict(color='#1d4ed8', width=3)))
    fig_2d.update_layout(title="<b>2D 단면 비교 (Cross-Section Overlay)</b>", xaxis=dict(scaleanchor="y", scaleratio=1), height=420)
    col_l.plotly_chart(fig_2d, use_container_width=True)

    z_levels = np.linspace(0, 100, 30)
    X_3d, Y_3d, Z_3d = [], [], []
    for z in z_levels:
        factor = 0.0 if z <= 30 else (1.0 if z >= 80 else (z - 30) / 50.0)
        x_curr = (1 - factor) * x_in + factor * x_out
        y_curr = (1 - factor) * y_in + factor * y_out
        X_3d.extend(x_curr); Y_3d.extend(y_curr); Z_3d.extend([z] * n_pts)

    I, J, K = [], [], []
    for i in range(len(z_levels) - 1):
        for j in range(n_pts):
            next_j = (j + 1) % n_pts
            p1, p2 = i * n_pts + j, i * n_pts + next_j
            p3, p4 = (i + 1) * n_pts + j, (i + 1) * n_pts + next_j
            I.extend([p1, p2]); J.extend([p2, p4]); K.extend([p3, p3])

    fig_3d = go.Figure(data=[go.Mesh3d(x=X_3d, y=Y_3d, z=Z_3d, i=I, j=J, k=K, intensity=Z_3d, colorscale='Blues', opacity=0.9)])
    fig_3d.update_layout(title="<b>3D 솔리드 인발 파이프라인</b>", scene=dict(aspectmode='data'), height=420)
    col_r.plotly_chart(fig_3d, use_container_width=True)

# ==========================================
# [TAB 2] 인발력 산출 (강종별 TS 및 설비 95% 부하 판정)
# ==========================================
with tab2:
    st.subheader("2. 강종별 인발력 및 설비 부하(95% 한계) 검증")
    st.markdown("소재 강종의 인장강도(T.S)와 단면 변형량을 반영하여 **필요 인발력(t)**을 산출하고, **설비별 작업 가능 여부**를 검증합니다.")

    a1_val = st.session_state.get('A1', A1)
    a2_val = st.session_state.get('A2', A2)
    ra_val = st.session_state.get('RA', RA)
    d_in_val = st.session_state.get('d_in', d_in)
    
    d_out_val = np.sqrt(4 * a2_val / np.pi) if a2_val > 0 else 0.0

    st.info(f"💡 **현재 단면 조건:** 원재 선경 Ø **{d_in_val:.2f} mm** (A₁={a1_val:.2f}mm²) ➔ 제품 등가선경 Ø **{d_out_val:.2f} mm** (A₂={a2_val:.2f}mm²) | **감면율 = {ra_val:.2f} %**")

    machines_db = [
        {"name": "CD-0-2호기", "min_d": 3.8,  "max_d": 6.0,  "max_cap": 2.0},
        {"name": "CD-0-3호기", "min_d": 5.49, "max_d": 9.0,  "max_cap": 2.0},
        {"name": "CD-1호기",   "min_d": 8.0,  "max_d": 13.0, "max_cap": 5.0},
        {"name": "CD-5호기",   "min_d": 9.0,  "max_d": 15.0, "max_cap": 6.5},
        {"name": "CD-2-2호기", "min_d": 14.0, "max_d": 18.0, "max_cap": 8.0},
        {"name": "CD-3호기",   "min_d": 16.0, "max_d": 24.0, "max_cap": 15.0},
        {"name": "CD-4호기",   "min_d": 19.0, "max_d": 41.0, "max_cap": 25.0},
    ]

    steel_ts_db = {
        # --- 이미지 표 데이터 ---
        "SUM24L (W/R)": 42.0,
        "SUM22 (W/R)": 40.0,
        "SUM43 (W/R)": 69.0,
        "10A / SWRCH10A (W/R)": 36.0,
        "12A / SWRCH12A (W/R)": 39.0,
        "45K / SWRCH45K (W/R)": 65.0,
        "S45C (W/R)": 71.0,
        "SCM415 (W/R)": 60.0,
        "SCM420 (W/R)": 79.0,
        "SCM435 (W/R)": 96.0,
        "SCM440 (W/R)": 104.0,
        "SNCM220H (W/R)": 73.0,
        "SNCM220H (SL04)": 58.0,
        "SUP9 (W/R)": 95.0,
        "100CRMNS (SA열처리)": 80.0,
        "440C (W/R)": 77.0,
        "440C (W/R 열처리)": 80.0,
        "SUS316L (W/R)": 54.0,
        "SUS304 (W/R)": 58.0,
        "SNCM439 (W/R)": 110.0,
        "SNCM439 (SA열처리)": 71.0,
        "XM7 (원재)": 75.0,
        "XM7 (12% 인발시)": 94.0,

        # --- PDF 세아특수강 조직분석 자료 DB ---
        "SUYB1 (전자연철봉)": 33.5,[cite: 1]
        "SWRCH6A (냉간압조용)": 33.1,[cite: 1]
        "SWRCH8A (냉간압조용)": 34.2,[cite: 1]
        "SWRCH15K (냉간압조용)": 41.4,[cite: 1]
        "SWRCH18A (냉간압조용)": 46.4,[cite: 1]
        "SWRCH20K (냉간압조용)": 44.4,[cite: 1]
        "SWRCH22A (냉간압조용)": 47.1,[cite: 1]
        "SWRCH25K(F) (냉간압조용)": 49.5,[cite: 1]
        "SWRCH30K (냉간압조용)": 58.3,[cite: 1]
        "SWRCH35K(F) (냉간압조용)": 60.5,[cite: 1]
        "SWRCH38K(F) (냉간압조용)": 60.9,[cite: 1]
        "SWRCH45K(F) (냉간압조용)": 64.7,[cite: 1]
        "S20C (기계구조용)": 48.5,[cite: 1]
        "S25C (기계구조용)": 51.6,[cite: 1]
        "S35C (기계구조용)": 69.9,[cite: 1]
        "S48C (기계구조용)": 78.2,[cite: 1]
        "SCr415H (경화능보증)": 52.2,[cite: 1]
        "SCr420H (경화능보증)": 58.2,[cite: 1]
        "SNB16 (고온합금강볼트)": 118.2,[cite: 1]
        "SUJ2 (베어링강)": 115.0,[cite: 1]
        "SUS303C (스텐)": 52.8,[cite: 1]
        "SUS303F (스텐)": 59.9,[cite: 1]
        "SUS410 (스텐)": 57.9,[cite: 1]
        "SUS416 (스텐)": 56.8,[cite: 1]
        "SUS420J2 (스텐)": 68.5,[cite: 1]
        "SUS430F (스텐)": 56.6,[cite: 1]
        "AISI/SAE 1050SH": 82.5,[cite: 1]
        "AISI/SAE 1060S": 87.1,[cite: 1]
        "AISI/SAE 1151": 72.3,[cite: 1]
        "AISI/SAE 1541": 81.0,[cite: 1]
        "AISI/SAE 4140": 114.0,[cite: 1]
        "AISI/SAE 4037": 65.1,[cite: 1]
        "AISI/SAE 9254": 96.7,[cite: 1]
        "AISI/SAE 10B21": 51.1,[cite: 1]
        "AISI/SAE 10B30": 57.6,[cite: 1]
        "AISI/SAE 10B35": 60.8,[cite: 1]
        "AISI/SAE 10B38": 64.1,[cite: 1]
        "AISI/SAE 15B36": 79.2,[cite: 1]
        "AISI/SAE 51B20": 51.9,[cite: 1]
        "AISI/SAE 51B35": 67.9,[cite: 1]
        "POSMA45R (POSCO)": 82.6,[cite: 1]
        "POSMA45RM (POSCO)": 76.0,[cite: 1]
        "POSA1038B (POSCO)": 64.2,[cite: 1]
        "POSA1021B (POSCO)": 52.6,[cite: 1]
        "POSA5120BH (POSCO)": 53.7,[cite: 1]
        "사용자 직접 입력": 60.0
    }

    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        steel_choice = st.selectbox("강종 선택 (T.S 적용)", list(steel_ts_db.keys()), key="t2_steel")
        
        if steel_choice == "사용자 직접 입력":
            ts_kgf = st.number_input("인장강도 T.S (kgf/mm²)", value=60.0, step=5.0, key="t2_custom_ts")
        else:
            ts_kgf = steel_ts_db[steel_choice]
            
        ts_mpa = ts_kgf * 9.80665
        st.write(f"📌 **선택 강종 T.S:** `{ts_kgf:.1f} kgf/mm²` (≒ `{ts_mpa:.1f} N/mm²`)")

        v_speed = st.number_input("인발 속도 (m/min)", value=30.0, step=5.0, key="t2_speed")

    with col_f2:
        die_angle = st.number_input("다이스 전각 2α (도, degree)", value=12.0, step=1.0, key="t2_angle")
        alpha_rad = (die_angle / 2.0) * (np.pi / 180.0)
        
        mu = st.slider("다이스 마찰계수 (μ)", 0.01, 0.20, 0.07, 0.01, key="t2_mu")

    if a1_val > a2_val and a2_val > 0:
        ln_area = np.log(a1_val / a2_val)
        sigma_d = ts_mpa * ((1.0 + mu / np.tan(alpha_rad)) * ln_area + (2.0 / 3.0) * alpha_rad)
        
        force_N = a2_val * sigma_d
        force_ton = force_N / 9806.65
        
        force_kN = force_N / 1000.0
        power_kW = (force_kN * v_speed) / 60.0

        st.markdown("---")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("소요 인발력 (Calculated Force)", f"{force_ton:.2f} t", f"{force_kN:.1f} kN")
        m2.metric("인발 응력 (Drawing Stress)", f"{sigma_d:.1f} MPa", f"{sigma_d / 9.80665:.1f} kgf/mm²")
        m3.metric("소요 동력 (Power)", f"{power_kW:.2f} kW", f"{power_kW * 1.341:.1f} HP")

        st.markdown("---")
        st.markdown("### 🏭 설비별 작업 가능 여부 검증 (설비 능력 95% 제한 기준)")

        m_eval_data = []
        matched_machines = []

        for m in machines_db:
            size_ok = (m["min_d"] <= d_out_val <= m["max_d"])
            usable_cap = m["max_cap"] * 0.95
            force_ok = (force_ton <= usable_cap)
            load_ratio = (force_ton / usable_cap) * 100.0 if usable_cap > 0 else 0.0

            if size_ok and force_ok:
                status = "🟢 작업 가능 (이상없음)"
                matched_machines.append(f"**{m['name']}** (부하율 {load_ratio:.1f}%)")
            elif size_ok and not force_ok:
                status = "🔴 인발력 초과 (작업불가)"
            else:
                status = "⚪ 선경 규격 미달/초과"

            m_eval_data.append({
                "작업 호기": m["name"],
                "작업 가능 제품선경": f"{m['min_d']} ~ {m['max_d']} mm",
                "설비 Max 톤수": f"{m['max_cap']:.1f} t",
                "95% 한계 인발력": f"{usable_cap:.2f} t",
                "소요 인발력": f"{force_ton:.2f} t",
                "설비 부하율": f"{load_ratio:.1f} %",
                "판정 결과": status
            })

        if matched_machines:
            st.success(f"✅ **현재 작업 조건(Ø{d_out_val:.2f}mm / {force_ton:.2f}t)에 이상이 없는 추천 설비:** " + ", ".join(matched_machines))
        else:
            st.error(f"⚠️ **경고:** 현재 소요 인발력({force_ton:.2f}t) 및 제품선경(Ø{d_out_val:.2f}mm) 조건에 안전하게(95% 이내) 작업할 수 있는 설비가 없습니다.")

        df_m = pd.DataFrame(m_eval_data)
        st.dataframe(df_m, use_container_width=True)

    else:
        st.warning("출력 단면적(A₂)이 입력 단면적(A₁)보다 작아야 인발력 계산이 가능합니다.")

# ==========================================
# [TAB 3] 중량 계산 (독립형 Round Bar 엑셀식)
# ==========================================
with tab3:
    st.subheader("3. 선재 / 봉재 규격별 중량 계산 (Round Bar)")
    st.markdown("단면/인발력 탭과 **독립적으로 작동**하며, 직경(D), 길이(L), 비중(Sg)을 직접 입력하여 중량을 산출합니다.")

    col_w1, col_w2 = st.columns(2)
    with col_w1:
        d_calc = st.number_input("외경 직경 D (mm)", value=25.0, step=0.5, key="w_d")
        length_mm = st.number_input("제품 1본당 길이 L (mm)", value=3020.0, step=10.0, key="w_l")
        
        density_dict = {
            "Carbon Steel (7.85)": 7.85,
            "Stainless Steel 304 (7.93)": 7.93,
            "Stainless Steel 316 (7.98)": 7.98,
            "Stainless Steel 420 (7.70)": 7.70,
            "Stainless Steel 430 (7.70)": 7.70,
            "사용자 직접 입력": 7.85
        }
        mat_choice = st.selectbox("재질 비중 (Specific Gravity Sg)", list(density_dict.keys()), key="w_mat")
        
        if mat_choice == "사용자 직접 입력":
            rho = st.number_input("비중 직접 입력", value=7.85, step=0.01, key="w_rho")
        else:
            rho = density_dict[mat_choice]

    with col_w2:
        quantity = st.number_input("총 수량 (EA)", value=1, step=1, key="w_qty")
        
        calc_area = (np.pi / 4.0) * (d_calc ** 2)
        piece_weight_kg = calc_area * length_mm * rho * (10 ** -6)
        piece_weight_lb = piece_weight_kg * 2.20462
        
        total_weight_kg = piece_weight_kg * quantity
        total_weight_ton = total_weight_kg / 1000.0

    st.markdown("---")
    st.markdown("### * ACTUAL CALCULATION (계산 결과)")
    wc1, wc2, wc3 = st.columns(3)
    
    wc1.metric("단품 1본 중량 (kg)", f"{piece_weight_kg:.2f} kg", f"단면적: {calc_area:.2f} mm²", delta_color="off")
    wc2.metric("단품 1본 중량 (lb)", f"{piece_weight_lb:.2f} lb", delta_color="off")
    wc3.metric(f"총 중량 (Total Weight, {quantity}EA)", f"{total_weight_kg:.2f} kg", f"{total_weight_ton:.3f} Ton")

    st.info("💡 **적용 공식:** W (Weight) = π / 4 * L * D² * Sg (단위 변환 10⁻⁶ 적용)")

# ==========================================
# [TAB 4] 직진도 환산 (엑셀 수식 적용)
# ==========================================
with tab4:
    st.subheader("4. 환산 직진도 계산기")
    st.markdown("수요가에서 요구하는 기준 길이와 직진도를 바탕으로, 실제 생산되는 제품 길이에 맞춘 **환산 직진도**를 계산합니다.")
    
    st.info("💡 **적용 공식:** 환산 직진도 = (직진도 × 제품길이²) / 수요가길이²")

    col_s1, col_s2, col_s3 = st.columns(3)
    
    with col_s1:
        st.markdown("#### 📏 수요가 기준 (Input)")
        req_length = st.number_input("수요가길이 (mm)", value=4920.0, step=10.0, key="s_req_l")
        req_straightness = st.number_input("직진도 (mm)", value=1.000, step=0.01, format="%.3f", key="s_req_s")

    with col_s2:
        st.markdown("#### 🏭 제품 기준 (Input)")
        prod_length = st.number_input("제품길이 (mm)", value=1000.0, step=10.0, key="s_prod_l")

    if req_length > 0:
        conv_straightness = (req_straightness * (prod_length ** 2)) / (req_length ** 2)
    else:
        conv_straightness = 0.0

    with col_s3:
        st.markdown("#### ✅ 계산 결과 (Output)")
        st.metric("환산 직진도", f"{conv_straightness:.3f} mm")

    st.markdown("---")
    st.markdown("### 📊 직진도 환산 테이블 (현재 입력값 비교)")
    
    test_data = pd.DataFrame({
        "수요가길이": [4920, 400, 1000, 300, req_length],
        "직진도": [1.000, 0.060, 0.500, 0.036, req_straightness],
        "제품길이": [1000, 1000, 400, 1000, prod_length],
    })
    
    test_data["환산 직진도"] = (test_data["직진도"] * (test_data["제품길이"] ** 2)) / (test_data["수요가길이"] ** 2)
    test_data["비고"] = ["엑셀 예시 1", "엑셀 예시 2", "엑셀 예시 3", "엑셀 예시 4", "👉 현재 계산 중인 값"]
    
    st.dataframe(test_data.style.format({
        "수요가길이": "{:,.0f}",
        "직진도": "{:.3f}",
        "제품길이": "{:,.0f}",
        "환산 직진도": "{:.3f}"
    }), use_container_width=True)