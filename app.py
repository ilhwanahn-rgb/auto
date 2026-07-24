import streamlit as st
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="선제/이형재 인발 종합 산출 도구", layout="wide")

st.title("🛠️ 선재/이형재 인발 소성가공 종합 산출 도구")
st.markdown("단면 감면율, 인발력, 중량, 직진도 환산 연산을 원스톱으로 처리하는 엔지니어링 계산기입니다.")

# 탭 구성
tab1, tab2, tab3, tab4 = st.tabs([
    "1. 형상별 감면율 & 3D", 
    "2. 인발력 산출 (TS)", 
    "3. 중량 계산", 
    "4. 직진도 환산"
])

# ==========================================
# 공통 헬퍼 함수
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
        
    else: # 트랙형
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
    RA = (1.0 - A2 / A1) * 100.0
    elongation = A1 / A2 if A2 > 0 else 0.0
    d_eq = np.sqrt(4 * A2 / np.pi)

    # 세션 상태에 공통 연산값 저장 (다른 탭 연동용)
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

    # 2D & 3D 렌더링
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

    # 3D Mesh
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
# [TAB 2] 인발력 계산 (Siebel 공식)
# ==========================================
with tab2:
    st.subheader("2. 강종별 인발력 및 소요 동력 연산")
    
    # 탭1에서 단면적 정보 가져오기
    a1_val = st.session_state.get('A1', A1)
    a2_val = st.session_state.get('A2', A2)
    ra_val = st.session_state.get('RA', RA)

    st.info(f"💡 현재 설정된 단면 조건: **입력 A₁ = {a1_val:.2f} mm²** | **출력 A₂ = {a2_val:.2f} mm²** | **감면율 = {ra_val:.2f} %**")

    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        steel_presets = {
            "저탄소강 (S10C, S15C 등) [TS ~400 MPa]": 400.0,
            "중탄소강 (S45C 등) [TS ~650 MPa]": 650.0,
            "고탄소강 (SWRS 계열) [TS ~1000 MPa]": 1000.0,
            "합금강 (SCM440 등) [TS ~900 MPa]": 900.0,
            "오스테나이트 스텐 (SUS304 등) [TS ~750 MPa]": 750.0,
            "사용자 직접 입력": 500.0
        }
        steel_choice = st.selectbox("강종 선택 (대표 인장강도)", list(steel_presets.keys()))
        if steel_choice == "사용자 직접 입력":
            ts_input = st.number_input("인장강도 TS (N/mm²)", value=500.0, step=50.0)
        else:
            ts_input = steel_presets[steel_choice]
            st.caption(f"적용 인장강도: {ts_input:.0f} N/mm² (MPa)")

        v_speed = st.number_input("인발 속도 (m/min)", value=30.0, step=5.0)

    with col_f2:
        die_angle = st.number_input("다이스 전각 2α (도, degree)", value=12.0, step=1.0)
        alpha_rad = (die_angle / 2.0) * (np.pi / 180.0) # 반각 radian
        
        mu = st.slider("다이스 마찰계수 (μ)", 0.01, 0.20, 0.07, 0.01)

    # Siebel 공식 계산
    if a1_val > a2_val and a2_val > 0:
        ln_area = np.log(a1_val / a2_val)
        # 인발 응력 σ_d
        sigma_d = ts_input * ((1.0 + mu / np.tan(alpha_rad)) * ln_area + (2.0 / 3.0) * alpha_rad)
        # 총 인발력 F (N -> kN)
        force_kN = (a2_val * sigma_d) / 1000.0
        # 소요 동력 P (kW)
        power_kW = (force_kN * v_speed) / 60.0
        # 소재 항복 한계 점검
        yield_ratio = (sigma_d / ts_input) * 100.0

        st.markdown("---")
        fc1, fc2, fc3, fc4 = st.columns(4)
        fc1.metric("총 인발력 (Force)", f"{force_kN:.2f} kN", f"{force_kN * 101.97:.1f} kgf")
        fc2.metric("인발 응력 (Drawing Stress)", f"{sigma_d:.1f} MPa")
        fc3.metric("필요 소요 동력", f"{power_kW:.2f} kW", f"{power_kW * 1.341:.1f} HP")
        
        delta_label = "안전" if yield_ratio < 80 else "단선 위험 주의!"
        fc4.metric("응력/TS 비율", f"{yield_ratio:.1f} %", delta_label, delta_color="normal" if yield_ratio < 80 else "inverse")

    else:
        st.warning("출력 단면적(A₂)이 입력 단면적(A₁)보다 작아야 인발력 계산이 가능합니다.")

# ==========================================
# [TAB 3] 중량 계산 (선경 * 길이)
# ==========================================
with tab3:
    st.subheader("3. 선재 / 봉재 규격별 중량 계산")

    a2_val = st.session_state.get('A2', A2)

    col_w1, col_w2 = st.columns(2)
    with col_w1:
        density_dict = {
            "철강 (Steel - 7.85 g/cm³)": 7.85,
            "스테인리스 (SUS304/316 - 7.93 g/cm³)": 7.93,
            "구리 (Copper - 8.96 g/cm³)": 8.96,
            "알루미늄 (Aluminum - 2.70 g/cm³)": 2.70,
            "사용자 직접 입력": 7.85
        }
        mat_choice = st.selectbox("재질 (밀도)", list(density_dict.keys()))
        rho = st.number_input("밀도 (g/cm³)", value=density_dict[mat_choice]) if mat_choice == "사용자 직접 입력" else density_dict[mat_choice]

        use_custom_a = st.checkbox("단면적 직접 입력하기 (기본값: 1번 탭 결과 연동)")
        if use_custom_a:
            calc_area = st.number_input("적용 단면적 (mm²)", value=a2_val, step=10.0)
        else:
            calc_area = a2_val
            st.caption(f"적용 단면적: {calc_area:.2f} mm²")

    with col_w2:
        length_m = st.number_input("제품 1본당 길이 (m)", value=6.0, step=0.5)
        quantity = st.number_input("총 수량 (EA)", value=100, step=10)

    # 중량 계산
    unit_weight_m = calc_area * rho * 0.001 # kg/m
    piece_weight = unit_weight_m * length_m # kg/ea
    total_weight = piece_weight * quantity  # kg

    st.markdown("---")
    wc1, wc2, wc3 = st.columns(3)
    wc1.metric("미터당 중량 (Unit Weight)", f"{unit_weight_m:.3f} kg/m")
    wc2.metric(f"1본 당 중량 ({length_m}m 기준)", f"{piece_weight:.2f} kg/EA")
    wc3.metric(f"총 중량 ({quantity}EA)", f"{total_weight / 1000.0:.3f} Ton", f"{total_weight:.1f} kg")

# ==========================================
# [TAB 4] 길이별 직진도 환산
# ==========================================
with tab4:
    st.subheader("4. 측정 길이별 직진도(휨/Bow) 환산")
    st.markdown("특정 측정 구간($L_1$)에서 측정한 직진도 오차를 바탕으로, 다른 기준 길이($L_2$)에서의 직진도를 곡률 반지름 기준으로 환산합니다.")

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.markdown("##### 📏 현재 측정 조건")
        l1 = st.number_input("측정 게이지 길이 L₁ (mm)", value=1000.0, step=100.0)
        h1 = st.number_input("측정된 휨/직진도 h₁ (mm)", value=1.00, step=0.1)

    with col_s2:
        st.markdown("##### 🎯 환산 목표 조건")
        l2 = st.number_input("목표 환산 길이 L₂ (mm)", value=2000.0, step=100.0)
        spec_h2 = st.number_input("목표 직진도 허용 스펙 (mm) [선택]", value=3.0, step=0.5)

    if h1 > 0 and l1 > 0:
        # 곡률 반지름 R_c (m 단위로 환산)
        R_c_mm = (l1 ** 2) / (8.0 * h1)
        R_c_m = R_c_mm / 1000.0
        
        # L2에서의 휨 h2
        h2 = h1 * ((l2 / l1) ** 2)

        st.markdown("---")
        sc1, sc2, sc3 = st.columns(3)
        sc1.metric(f"목표 길이({l2:.0f}mm) 환산 휨", f"{h2:.2f} mm")
        sc2.metric("추정 곡률 반지름 (R_c)", f"{R_c_m:.2f} m")
        
        pass_fail = "합격 (PASS)" if h2 <= spec_h2 else "불합격 (FAIL)"
        sc3.metric("스펙 판정 결과", pass_fail, f"허용 {spec_h2:.2f} mm 대비", delta_color="normal" if h2 <= spec_h2 else "inverse")

        # 2D Arc 그래프 시각화
        x_arc = np.linspace(-l2/2.0, l2/2.0, 200)
        # 원 방정식 근사: y = h2 - (x^2 / (2 R_c))
        y_arc = h2 - (x_arc**2) / (2.0 * R_c_mm)

        fig_arc = go.Figure()
        fig_arc.add_trace(go.Scatter(x=x_arc, y=y_arc, mode='lines', name='선재 휨 형상', line=dict(color='red', width=2.5)))
        fig_arc.add_trace(go.Scatter(x=[-l2/2.0, l2/2.0], y=[0, 0], mode='lines+markers', name='직진 기준선', line=dict(color='black', dash='dash')))
        fig_arc.update_layout(
            title=f"<b>길이 {l2:.0f}mm 구간의 휨 프로파일 (배율 변형 시각화)</b>",
            xaxis_title="길이 X (mm)", yaxis_title="휨 변위 Y (mm)",
            height=350
        )
        st.plotly_chart(fig_arc, use_container_width=True)

    else:
        st.warning("측정된 휨(h₁)은 0보다 커야 연산이 가능합니다.")