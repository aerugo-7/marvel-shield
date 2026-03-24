import streamlit as st
import pandas as pd
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
import plotly.express as px
import plotly.graph_objects as go
import json
import os
import re
import time

# --- 1. 全局 UI 风格定义 (神盾局战略级标准) ---
st.set_page_config(page_title="SHIELD 战略分析系统", layout="wide")

st.markdown("""
    <style>
    /* 基础背景 */
    .stApp { background-color: #050a10; color: #ffffff !important; }
    [data-testid="stSidebar"] { background-color: #08101a; border-right: 2px solid #00ffcc; }
    
    /* 搜索框与下拉列表：强制白底黑字，无死角覆盖 */
    div[data-baseweb="select"] { background-color: #ffffff !important; color: #000000 !important; border-radius: 4px; }
    div[data-baseweb="select"] * { color: #000000 !important; }
    div[data-baseweb="popover"] * { background-color: #ffffff !important; color: #000000 !important; }
    ul[role="listbox"] { background-color: #ffffff !important; }
    li[role="option"] { background-color: #ffffff !important; color: #000000 !important; }
    li[role="option"]:hover { background-color: #00ffcc !important; }

    /* 高亮度文字 */
    p, span, label, li { color: #ffffff !important; font-size: 1.1rem !important; font-weight: 500 !important; }
    h1, h2, h3 { color: #00ffcc !important; font-weight: bold !important; border-bottom: 2px solid #1f2937; padding-bottom: 10px; }

    /* 指标卡 */
    .stMetric { background: #0d1624; border: 2px solid #3b82f6; border-radius: 8px; padding: 15px; }
    
    /* 档案卡 */
    .hero-card { border: 2px solid #3b82f6; padding: 25px; border-radius: 15px; background: rgba(13, 22, 36, 0.95); margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

path = os.path.dirname(__file__)

@st.cache_resource
def load_data():
    df = pd.read_csv(os.path.join(path, "hero_master_final.csv"))
    with open(os.path.join(path, "neighborhood_index.json"), "r", encoding='utf-8') as f:
        neighbor_idx = json.load(f)
    edges = pd.read_csv(os.path.join(path, "cleaned_hero_network.csv"))
    G = nx.from_pandas_edgelist(edges, 'hero1', 'hero2')
    return df, neighbor_idx, G

df, neighbor_idx, G_full = load_data()
hero_list = df['Chinese_Name'].tolist()
name_to_eng = dict(zip(df['Chinese_Name'], df['English_Name']))
eng_to_name = dict(zip(df['English_Name'], df['Chinese_Name']))

# --- 侧边栏 ---
st.sidebar.title("🛡️ 洞察计划中心")
module = st.sidebar.radio("任务切换", ["🌐 宇宙势力格局", "🔍 英雄档案检索", "💀 稳定性演习"], key="nav_main")

# --- 模块 1：宇宙势力格局 ---
if module == "🌐 宇宙势力格局":
    st.title("🌐 漫威宇宙社交版图分析")
    
    st.info("📑 **💡 战略综述：漫威社交网络的宏观特征**：\n"
            "1. **核心监控层**：漫威宇宙共有超过6000名英雄，但数据证明，这500位核心英雄决定了宇宙的命运。他们支撑起了整个社交网的骨架，是所有重大事件的交汇点。\n"
            "2. **极速连接能力**：分析显示，漫威宇宙是一个典型的“小世界网络”。任意两个英雄之间，即使从未谋面，平均也只需要通过 3 个中间人（3.2步）就能取得联系。这代表该宇宙的情报传递效率极高。\n"
            "3. **社交凝聚力**：这16.5万条连线代表了英雄们不仅仅是并肩作战，更在私下形成了密不透风的关系网。这种高密度的结构让宇宙在面对一般性灾难时具有极强的抗压能力。")

    c1, c2, c3 = st.columns(3)
    c1.metric("监控核心英雄(df长度)", len(df))
    c2.metric("社交紧密度", "极高 (Small-World)")
    c3.metric("总情报连线", "16.5 万条")

    st.write("### 🏆 核心影响力排行榜")
    rank_attr = st.selectbox("选择排名维度", ["人脉广度榜 ", "外交枢纽榜"], key="rank_selector")
    sort_col = 'degree_score' if "广度" in rank_attr else 'betweenness_score'
    
    top_df = df.sort_values(sort_col, ascending=False).head(15)
    fig = px.bar(top_df, x=sort_col, y='Chinese_Name', orientation='h', color=sort_col, 
                 color_continuous_scale='GnBu', labels={'Chinese_Name': '名称', sort_col: '核心分'})
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
    st.plotly_chart(fig, use_container_width=True, key="rank_chart")

# --- 模块 2：英雄档案检索 ---
elif module == "🔍 英雄档案检索":
    st.title("📑 英雄个人绝密档案")

    st.info("📑 **档案解读说明**：\n"
            "1. **风险评估**：这是由算法计算出的“战略破坏潜力”。它量化了该英雄一旦失踪或叛变，对整个社交平衡造成的冲击力。5分以上即为战略级目标，8分以上为必须严密监控的核心枢纽。\n"
            "2. **五维雷达**：名望代表社交广度；外交代表连接不同圈子的能力；忠诚代表其朋友圈中同阵营角色的占比。\n"
            "名望：代表社交面的广度（认识多少人）。\n"
            "外交：代表在互不认识的圈子之间“穿针引线”的能力。\n"
            "忠诚：代表朋友圈里“自己人”（同阵营）的比例。分值越高，圈子越纯粹。\n"
            "跨界：代表在不同能力领域（如科技、魔法、变异）游走而不受限制的能力。\n"
            "风险：即上述的战略破坏潜力指数。")

    selected_cn = st.selectbox("请输入或选择英雄姓名", hero_list, key="search_box_2")
    hero_data = df[df['Chinese_Name'] == selected_cn].iloc[0]
    eng_name = hero_data['English_Name']

    col_l, col_r = st.columns([1, 1.5])
    
    with col_l:
        st.markdown(f"""
        <div class="hero-card">
            <h2 style='color:#00ffcc; margin-top:0;'>{selected_cn}</h2>
            <p><b>🌍 所属阵营:</b> {hero_data['Primary_Team']}</p>
            <p style='color:#ff4b4b; font-size:1.3rem; font-weight:bold;'>⚠️ 风险评估: {hero_data['Risk_Level']}/10</p>
            <p><b>🚻 性别:</b> {hero_data['Gender']} | <b>⚡ 类型:</b> {hero_data['Power_Type']}</p>
            <p><b>🎬 MCU 记录:</b> {hero_data['MCU_Presence']} (约 {hero_data['Movie_Count']} 部作品)</p>
            <p><b>🎓 核心导师:</b> {hero_data['Mentor_CN']}</p>
            <hr>
            <p><b>🔥 能力描述:</b> {hero_data['Detailed_Power']}</p>
            <p><b>🕶️ 社交特质:</b> {hero_data['Social_Style']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 雷达图 (Scatterpolar 稳定版)
        categories = ['名望', '外交', '忠诚', '跨界', '风险']
        values = [hero_data['degree_score']*100, hero_data['betweenness_score']*500, hero_data['Loyalty_Score']*100, hero_data['Cross_Index']*100, int(hero_data['Risk_Level'])*10]
        fig_radar = go.Figure(data=go.Scatterpolar(r=values, theta=categories, fill='toself', line_color='#00ffcc'))
        fig_radar.update_layout(polar=dict(bgcolor='#161b22', radialaxis=dict(visible=False)), showlegend=False, height=350, paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_radar, use_container_width=True, key="radar_chart")

    with col_r:
        st.write("### 🕸️ 实时社交圈探测")
        friends = neighbor_idx.get(eng_name, [])[:20]
        sub_nodes = [eng_name] + friends
        sub_G = G_full.subgraph(sub_nodes)
        
        net = Network(height="600px", width="100%", bgcolor="#050a10", font_color="white")
        net.toggle_physics(True)
        net.barnes_hut(gravity=-1500)
        
        for n in sub_G.nodes():
            label = eng_to_name.get(n, n)
            size = 40 if n == eng_name else 18
            color = "#00ffcc" if n == eng_name else "#3b82f6"
            net.add_node(n, label=label, size=size, color=color)
        for e in sub_G.edges():
            net.add_edge(e[0], e[1], color="#334155")
        
        # 解决 Windows 路径与 React 冲突
        temp_html = os.path.join(path, "temp_render_view.html")
        net.save_graph(temp_html)
        components.html(open(temp_html, 'r', encoding='utf-8').read(), height=620)

# --- 模块 3：稳定性演习 ---
elif module == "💀 稳定性演习":
    st.title("💀 宇宙瓦解压力模拟")

    # 1. 实验目的说明
    st.info("""
    **🔬 实验目的：漫威宇宙在极端灾难下会瓦解吗？**
    
    本模块通过数学模拟，测试当英雄们失踪后，漫威社交网络的“完整性”变化：
    
    1. **为什么损毁度通常极低？**：漫威英雄之间存在海量的“备用连接”。例如你删除了美队，但钢铁侠依然认识美队的所有朋友。这种冗余设计保护了宇宙，即使随机消失几百人，剩下的幸存者依然能集结，这叫“社交韧性”。
    2. **斩首行动的致命性**：若精准抹除那些“顶级领袖”，虽然总人数变化小，但系统内部沟通的效率会遭受毁灭性打击。
    """)
    
    # 2. 设置交互区域
    col_x, col_y = st.columns(2)
    with col_x:
        attack_mode = st.radio("请选择灾难模拟模式：", ["定向斩首行动 (指定抹除核心英雄)", "灭霸的响指 (随机大规模湮灭)"], key="sim_mode_fixed")
    with col_y:
        if "定向" in attack_mode:
            targets = st.multiselect("请在下方搜索并锁定抹除目标：", hero_list, default=[hero_list[0]], key="sim_targets_fixed")
            eng_targets = [name_to_eng.get(t) for t in targets]
        else:
            num_rm = st.slider("请调整随机消失的人数比例：", 10, 500, 100, key="sim_slider_fixed")

    # 3. 模拟逻辑
    if st.button("🚀 启动模拟分析程序", key="sim_btn_fixed"):
        # 创建一个空容器用于放置结果，防止 React 渲染报错
        result_container = st.container()
        
        with result_container:
            G_sim = G_full.copy()
            initial_size = 6399 
            
            if "定向" in attack_mode:
                hubs = ["CAPTAIN AMERICA", "IRON MAN/TONY STARK ", "SPIDER-MAN/PETER PARKER", "THOR/ORINSSON"]
                is_hub_hit = any(t in hubs for t in eng_targets)
                G_sim.remove_nodes_from(eng_targets)
                target_str = ", ".join(targets)
            else:
                import random
                nodes_to_rm = random.sample(list(G_sim.nodes()), num_rm)
                G_sim.remove_nodes_from(nodes_to_rm)
                is_hub_hit = num_rm > 300
                target_str = f"{num_rm} 名随机超人类"
                
            final_size = len(max(nx.connected_components(G_sim), key=len))
            loss = (initial_size - final_size) / initial_size * 100
            
            st.write(f"### 模拟报告：已成功从时空中抹除 {target_str}")
            
            # 仪表盘：使用静态 key 防止 removeChild 报错
            fig_loss = go.Figure(go.Indicator(
                mode="gauge+number", 
                value=loss, 
                title={'text': "系统结构损毁率 (%)"}, 
                gauge={'bar': {'color': "#ff4b4b"}, 'axis': {'range': [0, 100]}}
            ))
            fig_loss.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white", height=300)
            st.plotly_chart(fig_loss, use_container_width=True, key="sim_gauge_fixed")
            
            st.write("---")
            st.write("### 🔍 情报局深度评估结论")
            
            # 方案A：损毁极小
            if loss < 0.5:
                st.success("""
                📊 **评估结果：惊人的社交韧性！**
                
                实验证明，漫威宇宙展现出极强的冗余抗性。幸存英雄之间的联系密度极高，个体的离去无法阻碍大部队的联通。这个系统像互联网一样，部分节点的失效无法撼动宇宙的社交骨架。
                """)
            
            # 方案B：精准打击了领袖
            elif is_hub_hit:
                st.warning("""
                ⚠️ **评估结果：发生结构性震荡！**
                
                警告！你移除的是网络的“核心枢纽”。虽然剩下的英雄大部分还连在一起，但他们之间沟通的“步数”大幅增加。系统变得极度疲劳和脆弱，正处于大分裂的边缘。
                """)
            
            # 方案C：损毁很大
            else:
                st.error(f"""
                🚨 **评估结果：系统凝聚力实质性受损！**
                
                关键结论：最大英雄群体的规模已显著缩减（当前规模：{final_size}人）。这意味着宇宙中出现了大量无法被联络到的“孤岛英雄”，社交秩序已经失控，宇宙正在分崩离析。
                """)