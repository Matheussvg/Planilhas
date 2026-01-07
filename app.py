import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="DataSight Dark",
    page_icon="🌑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS PERSONALIZADO (ADAPTADO PARA DARK MODE) ---
st.markdown("""
<style>
    /* Estilo dos Cards de KPI */
    .metric-card {
        background-color: #262730; /* Fundo cinza escuro */
        border: 1px solid #464b5f;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.5);
    }
    /* Forçar texto branco nas métricas caso o tema falhe */
    div[data-testid="stMetricValue"] {
        color: #00D4FF !important; /* Azul Neon */
    }
    div[data-testid="stMetricLabel"] {
        color: #e0e0e0 !important;
    }
    /* Ajuste para remover bordas brancas indesejadas */
    header {visibility: hidden;}
    .stApp { background-color: #0E1117; }
</style>
""", unsafe_allow_html=True)

# --- FUNÇÕES DE LÓGICA ---

def processar_datas(df, col_data):
    try:
        df[col_data] = pd.to_datetime(df[col_data], dayfirst=True, errors='coerce')
        df = df.dropna(subset=[col_data])
        return df
    except:
        return df

def gerar_analise_temporal(df, col_data, col_valor):
    if col_data == "Nenhuma":
        return None, None
    df_temp = df.set_index(col_data).resample('M')[col_valor].sum()
    if len(df_temp) < 2:
        return 0, 0
    atual = df_temp.iloc[-1]
    anterior = df_temp.iloc[-2]
    crescimento_pct = ((atual - anterior) / anterior) * 100 if anterior > 0 else 0
    return atual, crescimento_pct

def gerar_relatorio_texto(total, medio, top_prod, share_top, cresc_pct, tem_data):
    sinal = "+" if cresc_pct > 0 else ""
    texto_data = f"Variação Mensal: {sinal}{cresc_pct:.1f}%" if tem_data else "Sem dados temporais."
    
    return f"""
    RELATÓRIO DARK MODE - DATASIGHT
    --------------------------------
    Faturamento: R$ {total:,.2f}
    Ticket Médio: R$ {medio:,.2f}
    {texto_data}
    
    Top Produto: {top_prod} ({share_top:.1f}% do total)
    --------------------------------
    """

# --- APP PRINCIPAL ---

st.title("🌑 DataSight AI")
st.markdown("<h3 style='color: #888;'>Intelligence Dashboard</h3>", unsafe_allow_html=True)

# 1. UPLOAD
with st.expander("📂 Carregar Dados (CSV/Excel)", expanded=True):
    uploaded_file = st.file_uploader("", type=["csv", "xlsx"])

if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        df_raw = pd.read_csv(uploaded_file)
    else:
        df_raw = pd.read_excel(uploaded_file)
        
    cols = df_raw.columns.tolist()

    # Mapeamento
    st.info("👇 Configure as colunas")
    c1, c2, c3 = st.columns(3)
    col_val = c1.selectbox("Valor (R$)", cols, index=len(cols)-1)
    col_cat = c2.selectbox("Categoria", cols, index=0)
    col_data = c3.selectbox("Data (Opcional)", ["Nenhuma"] + cols)
    
    # Processamento
    df = df_raw.copy()
    df[col_val] = pd.to_numeric(df[col_val], errors='coerce').fillna(0)
    if col_data != "Nenhuma":
        df = processar_datas(df, col_data).sort_values(by=col_data)

    st.markdown("---")

    # Filtros Sidebar
    st.sidebar.header("🔍 Filtros")
    cats = df[col_cat].unique().tolist()
    sel_cats = st.sidebar.multiselect("Categorias", cats, default=cats)
    
    if sel_cats:
        df_filtered = df[df[col_cat].isin(sel_cats)]
    else:
        df_filtered = df

    # --- KPIs ---
    total = df_filtered[col_val].sum()
    medio = df_filtered[col_val].mean()
    atual_mes, cresc_pct = 0, 0
    delta_msg = None
    
    if col_data != "Nenhuma":
        atual_mes, cresc_pct = gerar_analise_temporal(df_filtered, col_data, col_val)
        delta_msg = f"{cresc_pct:.1f}% vs mês anterior"

    # Exibição KPIs
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Faturamento", f"R$ {total:,.2f}")
    k2.metric("Ticket Médio", f"R$ {medio:,.2f}")
    k3.metric("Vendas", len(df_filtered))
    if delta_msg:
        k4.metric("Tendência", f"R$ {atual_mes:,.2f}", delta=delta_msg)
    else:
        k4.metric("Status", "---")

    # --- GRÁFICOS (TEMPLATE ESCURO) ---
    st.markdown("### 📊 Visão Geral")
    
    tab1, tab2 = st.tabs(["Linha do Tempo", "Distribuição"])
    
    with tab1:
        if col_data != "Nenhuma":
            df_time = df_filtered.set_index(col_data).resample('D')[col_val].sum().reset_index()
            # "plotly_dark" é o segredo para gráficos pretos
            fig_line = px.line(df_time, x=col_data, y=col_val, title="Evolução Diária", template="plotly_dark")
            fig_line.update_traces(line_color='#00D4FF') # Linha Azul Neon
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.warning("Selecione a coluna de Data.")

    with tab2:
        c_g1, c_g2 = st.columns(2)
        
        df_rank = df_filtered.groupby(col_cat)[col_val].sum().reset_index().sort_values(by=col_val, ascending=False)
        
        # Barras
        fig_bar = px.bar(df_rank.head(10), x=col_val, y=col_cat, orientation='h', title="Top Categorias", template="plotly_dark")
        fig_bar.update_traces(marker_color='#00D4FF')
        c_g1.plotly_chart(fig_bar, use_container_width=True)
        
        # Pizza
        fig_pie = px.pie(df_rank, values=col_val, names=col_cat, title="Share", template="plotly_dark")
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        c_g2.plotly_chart(fig_pie, use_container_width=True)

    # --- EXPORTAÇÃO ---
    st.markdown("---")
    top_nome = df_rank.iloc[0][col_cat] if not df_rank.empty else "N/A"
    top_val = df_rank.iloc[0][col_val] if not df_rank.empty else 0
    share = (top_val / total * 100) if total > 0 else 0
    
    txt = gerar_relatorio_texto(total, medio, top_nome, share, cresc_pct, col_data != "Nenhuma")
    
    col_btn, _ = st.columns([1,3])
    with col_btn:
        st.download_button("📥 Baixar Relatório", data=txt, file_name="relatorio_dark.txt")

else:
    st.info("👆 Faça o upload da planilha para ativar o Dashboard.")