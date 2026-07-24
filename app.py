import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- 페이지 기본 설정 ---
st.set_page_config(page_title="선재 변형 & 감면율 3D 시각화", layout="wide")

st.title("🔩 선경 기반 단면 변형 및 감면율 3D 시각화 UI")
st.markdown("원형 선경과 목표 형상 치수를 조절하면 **치수 변화, 감면율, 2D 단면 및 3D 솔리드 형상**이 실시간 연산됩니다.")

# --- 사이드바: 입력 매개변수 ---
st.sidebar.header("1. 입력 원형 선재")
d_in = st.sidebar.number_input("원형 선경 d (mm)", value=30.0, min_value=1.0, step=0.5)

st.sidebar.header("2. 목표 출력 형상 선택")
shape_type = st.sidebar.selectbox("단면 형상", ["정육각형", "사각형 (정/직사각)", "이형 (트랙/장원형)"])

# 2D 좌표 생성 함수 (N개 정점)
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

# 형상별 치수 입력 및 단면적 계산
if shape_type == "정육각형":
    W = st.sidebar.number_input("대면 치수 W (mm)", value=28.0, step=0.5)
    R = st.sidebar.slider("모서리 R (mm)", 0.0, W/2.0, 2.9, 0.1)
    H = W
    max_diag = (2 * W / np.sqrt(3)) - 2 * R * ((2 / np.sqrt(3)) - 1)
    A2 = (np.sqrt(3) / 2.0) * (W ** 2) - (2 * np.sqrt(3) - np.pi) * (R ** 2)

elif shape_type == "사각형 (정/직사각)":
    W = st.sidebar.number_input("폭 W (mm)", value=25.0, step=0.5)
    H = st.sidebar.number_input("높이 H (mm)", value=25.0, step=0.5)
    R = st.sidebar.slider("모서리 R (mm)", 0.0, min(W, H)/2.0, 1.0, 0.1)
    max_diag = np.sqrt(W**2 + H**2) - 2 * R * (np.sqrt(2) - 1)
    A2 = W * H - (4.0 - np.pi) * (R ** 2)

else: # 이형 (트랙형)
    W = st.sidebar.number_input("전체 폭 W (mm)", value=30.0, step=0.5)
    H = st.sidebar.number_input("높이 H (mm)", value=18.0, step=0.5)
    R = H / 2.0
    max_diag = W
    A2 = (W - H) * H + (np.pi / 4.0) * (H ** 2)

# 연산
A1 = (np.pi / 4.0) * (d_in ** 2)
RA = (1.0 - A2 / A1) * 100.0
elongation = A1 / A2 if A2 > 0 else 0.0
d_eq = np.sqrt(4 * A2 / np.pi)  # 성형 후 등가원경 (mm)

# --- 상단 대시보드 지표 (mm 하단 표기 강화) ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("소재 원형 단면적 (A₁)", f"{A1:.2f} mm²", f"원형 직경 Ø {d_in:.2f} mm", delta_color="off")
c2.metric("성형 후 단면적 (A₂)", f"{A2:.2f} mm²", f"등가원경 Ø {d_eq:.2f} mm", delta_color="off")
c3.metric("최대 대각/외경 치수 (D)", f"{max_diag:.2f} mm", f"대면 W {W:.2f} mm / R {R:.2f} mm", delta_color="off")
c4.metric("감면율 (RA)", f"{RA:.2f} %", f"연신율 {elongation:.2f} 배", delta_color="normal")

st.divider()

# --- 2D / 3D 시각화 영역 ---
col_left, col_right = st.columns(2)

# 1. 2D 단면 오버레이
n_pts = 120
x_in = (d_in / 2.0) * np.cos(np.linspace(0, 2*np.pi, n_pts, endpoint=False))
y_in = (d_in / 2.0) * np.sin(np.linspace(0, 2*np.pi, n_pts, endpoint=False))
x_out, y_out = generate_shape_points(shape_type, W, H, R, n_points=n_pts)

fig_2d = go.Figure()
fig_2d.add_trace(go.Scatter(x=x_in, y=y_in, mode='lines', name=f'입력 원형 (Ø{d_in:.1f}mm)', line=dict(color='gray', dash='dash', width=2)))
fig_2d.add_trace(go.Scatter(x=x_out, y=y_out, mode='lines', name=f'출력 {shape_type}', fill="toself", fillcolor='rgba(37, 99, 235, 0.25)', line=dict(color='#1d4ed8', width=3)))

fig_2d.update_layout(
    title="<b>2D 단면 비교 (Cross-Section Overlay)</b>",
    xaxis=dict(scaleanchor="y", scaleratio=1, title="X (mm)", gridcolor='#e5e7eb'),
    yaxis=dict(title="Y (mm)", gridcolor='#e5e7eb'),
    height=480,
    plot_bgcolor='white',
    margin=dict(l=20, r=20, t=40, b=20)
)
col_left.plotly_chart(fig_2d, use_container_width=True)

# 2. 3D 입체 메쉬 (Solid Mesh3d) 시각화
z_levels = np.linspace(0, 100, 40)
X_3d, Y_3d, Z_3d = [], [], []

for z in z_levels:
    if z <= 30: # 원형 구간
        factor = 0.0
    elif z >= 80: # 목표 형상 구간
        factor = 1.0
    else: # 테이퍼 변형 구간 (30 ~ 80)
        factor = (z - 30) / 50.0
    
    x_curr = (1 - factor) * x_in + factor * x_out
    y_curr = (1 - factor) * y_in + factor * y_out
    
    X_3d.extend(x_curr)
    Y_3d.extend(y_curr)
    Z_3d.extend([z] * n_pts)

# Mesh3d 면(Face) 삼각화 연산
I, J, K = [], [], []
n_z = len(z_levels)
for i in range(n_z - 1):
    for j in range(n_pts):
        next_j = (j + 1) % n_pts
        p1 = i * n_pts + j
        p2 = i * n_pts + next_j
        p3 = (i + 1) * n_pts + j
        p4 = (i + 1) * n_pts + next_j
        
        I.extend([p1, p2])
        J.extend([p2, p4])
        K.extend([p3, p3])

fig_3d = go.Figure()
fig_3d.add_trace(go.Mesh3d(
    x=X_3d, y=Y_3d, z=Z_3d,
    i=I, j=J, k=K,
    intensity=Z_3d,
    colorscale='Blues',
    showscale=False,
    opacity=0.9,
    lighting=dict(ambient=0.5, diffuse=0.8, roughness=0.3, specular=0.5)
))

fig_3d.update_layout(
    title="<b>3D 솔리드 인발 변형 파이프라인 (Solid Mesh)</b>",
    scene=dict(
        xaxis_title="X (mm)", yaxis_title="Y (mm)", zaxis_title="진행 방향 Z (mm)",
        aspectmode='data'
    ),
    height=480,
    margin=dict(l=0, r=0, t=40, b=0)
)
col_right.plotly_chart(fig_3d, use_container_width=True)