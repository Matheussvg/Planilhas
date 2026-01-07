import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from fpdf import FPDF
import tempfile

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="DataSight Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS (TEMA ESCURO) ---
st.markdown("""
<style>
    .metric-card {
        background-color: #262730;
        border: 1px solid #464b5f;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.5);
    }
    div[data-testid="stMetricValue"] { color: #00D4FF !important; }
    div[data-testid="stMetricLabel"] { color: #e0e0e0 !important; }
    header {visibility: hidden;}
    .stApp { background-color: #0E1117; }
</style>
""", unsafe_allow_html=True)

# --- FUNÇÃO GERADORA DE PDF ---
class PDF(FPDF):
    def header(self):
        # Fonte Arial Bold 15
        self.set_font('Arial', 'B', 15)
        # Título
        self.cell(0, 10, 'Relatorio Executivo - DataSight Pro', 0, 1, 'C')
        # Linha separadora
        self.set_draw_color(0, 212, 255) # Azul Neon
        self.set_line_width(1)
        self.line(10, 25, 200, 25)
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def criar_pdf_profissional(total, medio, top_prod, share_top, cresc_pct, tem_data, df_top5):
    pdf = PDF()
    pdf.add_page()
    pdf.set_text_color(0, 0, 0) # Preto para o texto

    # Função auxiliar para acentos (FPDF padrão usa latin-1)
    def txt(texto):
        return texto.encode('latin-1', 'replace').decode('latin-1')

    # 1. Resumo Geral
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, txt('1. Resumo de Performance'), 0, 1)
    
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 8, txt(f'Data de Geração: {datetime.now().strftime("%d/%m/%Y")}'), 0, 1)
    pdf.cell(0, 8, txt(f'Faturamento Total: R$ {total:,.2f}'), 0, 1)
    pdf.cell(0, 8, txt(f'Ticket Médio: R$ {medio:,.2f}'), 0, 1)
    
    if tem_data:
        sinal = "+" if cresc_pct > 0 else ""
        cor = "Crescimento" if cresc_pct > 0 else "Queda"
        pdf.cell(0, 8, txt(f'Variação Mensal: {sinal}{cresc_pct:.1f}% ({cor})'), 0, 1)
    
    pdf.ln(5)

    # 2. Destaques
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, txt('2. Produto Campeão'), 0, 1)
    pdf.set_font('Arial', '', 11)
    
    pdf.multi_cell(0, 7, txt(f"O item mais vendido foi '{top_prod}', responsável por {share_top:.1f}% de toda a receita da empresa no período selecionado."))
    
    pdf.ln(5)
    
    # 3. Tabela Top 5 (Simulada)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, txt('3. Ranking Top 5 Categorias'), 0, 1)
    
    # Cabeçalho da Tabela
    pdf.set_fill_color(200, 220, 255)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(100, 10, txt('Categoria / Produto'), 1, 0, 'L', 1)
    pdf.cell(60, 10, txt('Valor (R$)'), 1, 1, 'R', 1)
    
    # Linhas da Tabela
    pdf.set_font('Arial', '', 10)
    for index, row in df_top5.iterrows():
        cat_nome = str(row.iloc[0])[:40] # Limita tamanho nome
        val_real = f"R$ {row.iloc[1]:,.2f}"
        pdf.cell(100, 10, txt(cat_nome), 1, 0, 'L')
        pdf.cell(60, 10, txt(val_real), 1, 1, 'R')

    pdf.ln(10)

    # 4. Recomendação Automática
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(200, 50, 50) # Vermelho escuro para destaque
    pdf.cell(0, 10, txt('4. Diagnóstico Automático'), 0, 1)
    
    pdf.set_font('Arial', 'I', 11)
    if share_top > 40:
        msg = "ALERTA DE RISCO: A operação apresenta alta dependência do produto campeão. Recomenda-se diversificar o portfólio para evitar quedas bruscas de receita."
    else:
        msg = "SAÚDE POSITIVA: A receita está bem distribuída entre os produtos, indicando um portfólio resiliente e equilibrado."
    
    pdf.multi_cell(0, 7, txt(msg))

    # Retorna o PDF como string binária
    return pdf.output(dest='S').encode('latin-1')

# --- LÓGICA DO SISTEMA ---

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

# --- APP VISUAL ---

st.title("🌑 DataSight Pro")
st.markdown("<h3 style='color: #888;'>Intelligence Dashboard</h3>", unsafe_allow_html=True)

with st.expander("📂 Carregar Dados (CSV/Excel)", expanded=True):
    uploaded_file = st.file_uploader("", type=["csv", "xlsx"])

if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        df_raw = pd.read_csv(uploaded_file)
    else:
        df_raw = pd.read_excel(uploaded_file)
        
    cols = df_raw.columns.tolist()

    st.info("👇 Configure as colunas para análise")
    c1, c2, c3 = st.columns(3)
    col_val = c1.selectbox("Valor (R$)", cols, index=len(cols)-1)
    col_cat = c2.selectbox("Categoria/Produto", cols, index=0)
    col_data = c3.selectbox("Data (Opcional)", ["Nenhuma"] + cols)
    
    df = df_raw.copy()
    df[col_val] = pd.to_numeric(df[col_val], errors='coerce').fillna(0)
    if col_data != "Nenhuma":
        df = processar_datas(df, col_data).sort_values(by=col_data)

    st.markdown("---")

    # Filtros
    st.sidebar.header("🔍 Filtros")
    cats = df[col_cat].unique().tolist()
    sel_cats = st.sidebar.multiselect("Filtrar Categoria", cats, default=cats)
    
    if sel_cats:
        df_filtered = df[df[col_cat].isin(sel_cats)]
    else:
        df_filtered = df

    # KPIs
    total = df_filtered[col_val].sum()
    medio = df_filtered[col_val].mean()
    atual_mes, cresc_pct = 0, 0
    delta_msg = None
    
    if col_data != "Nenhuma":
        atual_mes, cresc_pct = gerar_analise_temporal(df_filtered, col_data, col_val)
        delta_msg = f"{cresc_pct:.1f}% vs mês anterior"

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Faturamento", f"R$ {total:,.2f}")
    k2.metric("Ticket Médio", f"R$ {medio:,.2f}")
    k3.metric("Transações", len(df_filtered))
    if delta_msg:
        k4.metric("Tendência", f"R$ {atual_mes:,.2f}", delta=delta_msg)
    else:
        k4.metric("Status", "---")

    # Gráficos
    st.markdown("### 📊 Visão Geral")
    tab1, tab2 = st.tabs(["Linha do Tempo", "Distribuição"])
    
    with tab1:
        if col_data != "Nenhuma":
            df_time = df_filtered.set_index(col_data).resample('D')[col_val].sum().reset_index()
            fig_line = px.line(df_time, x=col_data, y=col_val, title="Evolução Diária", template="plotly_dark")
            fig_line.update_traces(line_color='#00D4FF')
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.warning("Selecione a coluna de Data para ver o gráfico temporal.")

    with tab2:
        c_g1, c_g2 = st.columns(2)
        df_rank = df_filtered.groupby(col_cat)[col_val].sum().reset_index().sort_values(by=col_val, ascending=False)
        
        fig_bar = px.bar(df_rank.head(10), x=col_val, y=col_cat, orientation='h', title="Top 10 Categorias", template="plotly_dark")
        fig_bar.update_traces(marker_color='#00D4FF')
        c_g1.plotly_chart(fig_bar, use_container_width=True)
        
        fig_pie = px.pie(df_rank, values=col_val, names=col_cat, title="Share de Receita", template="plotly_dark")
        c_g2.plotly_chart(fig_pie, use_container_width=True)

    # --- BOTÃO DE DOWNLOAD PDF ---
    st.markdown("---")
    
    # Preparar dados para o PDF
    top_nome = df_rank.iloc[0][col_cat] if not df_rank.empty else "N/A"
    top_val = df_rank.iloc[0][col_val] if not df_rank.empty else 0
    share = (top_val / total * 100) if total > 0 else 0
    
    # Gerar o arquivo PDF em memória
    pdf_bytes = criar_pdf_profissional(
        total, medio, top_nome, share, cresc_pct, 
        col_data != "Nenhuma", df_rank.head(5)
    )
    
    col_btn, _ = st.columns([1,3])
    with col_btn:
        st.download_button(
            label="📄 Baixar Relatório PDF Profissional",
            data=pdf_bytes,
            file_name="Relatorio_DataSight.pdf",
            mime="application/pdf"
        )

else:
    st.info("👆 Faça o upload da planilha para começar.")
