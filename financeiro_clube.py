# ============================================================================
# SISTEMA DE GESTÃO FINANCEIRA - CLUBE DE DESBRAVADORES
# Desenvolvido com Streamlit + SQLite
# ============================================================================

# Importação das bibliotecas necessárias
import streamlit as st          # Framework para criar a interface web
import sqlite3                  # Banco de dados SQLite
import pandas as pd             # Manipulação de dados e tabelas
from datetime import datetime   # Trabalhar com datas
import os                       # Operações do sistema operacional

# ============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================================
st.set_page_config(
    page_title="Financeiro - Clube de Desbravadores",
    page_icon="💰",
    layout="wide",              # Layout largo para melhor visualização
    initial_sidebar_state="expanded"
)

# ============================================================================
# CONFIGURAÇÃO DO BANCO DE DADOS
# ============================================================================

def criar_banco_dados():
    """
    Cria o banco de dados SQLite e as tabelas necessárias.
    Executa automaticamente na primeira vez que o app roda.
    """
    # Conecta ao banco de dados (cria o arquivo se não existir)
    conn = sqlite3.connect('financeiro_clube.db')
    cursor = conn.cursor()
    
    # Tabela de Transações Financeiras
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,              -- 'entrada' ou 'saida'
            valor REAL NOT NULL,             -- Valor da transação
            categoria TEXT NOT NULL,         -- Categoria (Plano de Contas)
            descricao TEXT,                  -- Descrição detalhada
            unidade TEXT,                    -- Unidade (Órion, Plêiades, etc.)
            data_transacao DATE NOT NULL,    -- Data da transação
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            responsavel TEXT                 -- Quem lançou
        )
    ''')
    
    # Tabela de Unidades do Clube
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS unidades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            lider TEXT,
            ativo BOOLEAN DEFAULT 1
        )
    ''')
    
    # Insere unidades padrão se não existirem
    unidades_padrao = [
        ('Órion', ''),
        ('Plêiades', ''),
        ('Arqueiras 10-12', ''),
        ('Sentinela 13-15', ''),
        ('Guerreiros 10-12', ''),
        ('Guardiões 13-15', ''),
        ('Geral', '')
    ]
    
    for unidade, lider in unidades_padrao:
        try:
            cursor.execute('INSERT INTO unidades (nome, lider) VALUES (?, ?)', 
                          (unidade, lider))
        except sqlite3.IntegrityError:
            pass  # Já existe, ignora
    
    conn.commit()
    conn.close()

# ============================================================================
# FUNÇÕES DE BANCO DE DADOS
# ============================================================================

def adicionar_transacao(tipo, valor, categoria, descricao, unidade, data, responsavel):
    """
    Adiciona uma nova transação no banco de dados.
    """
    conn = sqlite3.connect('financeiro_clube.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO transacoes (tipo, valor, categoria, descricao, unidade, data_transacao, responsavel)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (tipo, valor, categoria, descricao, unidade, data, responsavel))
    
    conn.commit()
    conn.close()

def buscar_transacoes(filtro_categoria=None, filtro_unidade=None, filtro_data_inicio=None, filtro_data_fim=None):
    """
    Busca transações com filtros opcionais.
    Retorna um DataFrame do pandas.
    """
    conn = sqlite3.connect('financeiro_clube.db')
    
    query = 'SELECT * FROM transacoes WHERE 1=1'
    params = []
    
    if filtro_categoria:
        query += ' AND categoria = ?'
        params.append(filtro_categoria)
    
    if filtro_unidade:
        query += ' AND unidade = ?'
        params.append(filtro_unidade)
    
    if filtro_data_inicio:
        query += ' AND data_transacao >= ?'
        params.append(filtro_data_inicio)
    
    if filtro_data_fim:
        query += ' AND data_transacao <= ?'
        params.append(filtro_data_fim)
    
    query += ' ORDER BY data_transacao DESC'
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    return df

def calcular_saldo():
    """
    Calcula o saldo atual (total de entradas - total de saídas).
    """
    conn = sqlite3.connect('financeiro_clube.db')
    cursor = conn.cursor()
    
    # Soma todas as entradas
    cursor.execute("SELECT SUM(valor) FROM transacoes WHERE tipo = 'entrada'")
    total_entradas = cursor.fetchone()[0] or 0
    
    # Soma todas as saídas
    cursor.execute("SELECT SUM(valor) FROM transacoes WHERE tipo = 'saida'")
    total_saidas = cursor.fetchone()[0] or 0
    
    conn.close()
    
    return total_entradas, total_saidas, total_entradas - total_saidas

def calcular_saldo_mes(mes_atual, ano_atual):
    """
    Calcula o saldo do mês atual.
    """
    conn = sqlite3.connect('financeiro_clube.db')
    cursor = conn.cursor()
    
    # Entradas do mês
    cursor.execute("""
        SELECT SUM(valor) FROM transacoes 
        WHERE tipo = 'entrada' 
        AND strftime('%m', data_transacao) = ?
        AND strftime('%Y', data_transacao) = ?
    """, (str(mes_atual).zfill(2), str(ano_atual)))
    entradas_mes = cursor.fetchone()[0] or 0
    
    # Saídas do mês
    cursor.execute("""
        SELECT SUM(valor) FROM transacoes 
        WHERE tipo = 'saida' 
        AND strftime('%m', data_transacao) = ?
        AND strftime('%Y', data_transacao) = ?
    """, (str(mes_atual).zfill(2), str(ano_atual)))
    saidas_mes = cursor.fetchone()[0] or 0
    
    conn.close()
    
    return entradas_mes, saidas_mes, entradas_mes - saidas_mes

def buscar_categorias():
    """
    Retorna a lista de categorias do Plano de Contas.
    """
    return [
        'Mensalidades',
        'Inscrições em Eventos',
        'Doações',
        'Compra de Uniformes',
        'Alimentação (Cozinha)',
        'Materiais de Instrução',
        'Administrativo',
        'Acampamento',
        'Campori',
        'Outros'
    ]

def buscar_unidades():
    """
    Retorna a lista de unidades cadastradas.
    """
    conn = sqlite3.connect('financeiro_clube.db')
    cursor = conn.cursor()
    cursor.execute('SELECT nome FROM unidades WHERE ativo = 1')
    unidades = [row[0] for row in cursor.fetchall()]
    conn.close()
    return unidades

def excluir_transacao(id_transacao):
    """
    Exclui uma transação pelo ID.
    """
    conn = sqlite3.connect('financeiro_clube.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM transacoes WHERE id = ?', (id_transacao,))
    conn.commit()
    conn.close()

# ============================================================================
# ESTILIZAÇÃO CSS PERSONALIZADA
# ============================================================================

def carregar_css():
    """
    Carrega estilos CSS personalizados para melhorar o visual.
    """
    st.markdown("""
        <style>
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            text-align: center;
        }
        .metric-card-entrada {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }
        .metric-card-saida {
            background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
        }
        .stButton>button {
            width: 100%;
            border-radius: 5px;
            font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)

# ============================================================================
# INTERFACE PRINCIPAL
# ============================================================================

def main():
    """
    Função principal que renderiza toda a interface do aplicativo.
    """
    
    # Carrega estilos personalizados
    carregar_css()
    
    # Cria o banco de dados se não existir
    criar_banco_dados()
    
    # Título do aplicativo
    st.title("💰 Gestão Financeira - Clube de Desbravadores")
    st.markdown("---")
    
    # ========================================================================
    # BARRA LATERAL DE NAVEGAÇÃO
    # ========================================================================
    st.sidebar.title("🧭 Navegação")
    menu = st.sidebar.radio(
        "Selecione a opção:",
        ["📊 Dashboard", "➕ Novo Lançamento", "📋 Fluxo de Caixa", "📈 Relatórios"],
        index=0
    )
    
    st.sidebar.markdown("---")
    st.sidebar.info("""
    **Dica:** 
    - Use o Dashboard para visão geral
    - Faça lançamentos em "Novo Lançamento"
    - Consulte o histórico em "Fluxo de Caixa"
    """)
    
    # ========================================================================
    # OPÇÃO 1: DASHBOARD
    # ========================================================================
    if menu == "📊 Dashboard":
        st.header("📊 Visão Geral Financeira")
        
        # Calcula saldos
        total_entradas, total_saidas, saldo_total = calcular_saldo()
        
        # Mês atual
        agora = datetime.now()
        entradas_mes, saidas_mes, saldo_mes = calcular_saldo_mes(agora.month, agora.year)
        
        # Exibe métricas em colunas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="💵 Saldo Atual",
                value=f"R$ {saldo_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                delta=f"Mês: R$ {saldo_mes:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            )
        
        with col2:
            st.metric(
                label="📥 Total Entradas (Geral)",
                value=f"R$ {total_entradas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                delta=f"Mês: R$ {entradas_mes:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            )
        
        with col3:
            st.metric(
                label="📤 Total Saídas (Geral)",
                value=f"R$ {total_saidas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                delta=f"Mês: R$ {saidas_mes:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            )
        
        st.markdown("---")
        
        # Gráfico de categorias
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.subheader("📊 Entradas por Categoria")
            df_entradas = buscar_transacoes(filtro_categoria=None)
            if not df_entradas.empty:
                df_entradas = df_entradas[df_entradas['tipo'] == 'entrada']
                if not df_entradas.empty:
                    agrupado = df_entradas.groupby('categoria')['valor'].sum().reset_index()
                    st.bar_chart(agrupado.set_index('categoria'))
                else:
                    st.info("Nenhuma entrada registrada")
            else:
                st.info("Nenhuma entrada registrada")
        
        with col_g2:
            st.subheader("📊 Saídas por Categoria")
            df_saidas = buscar_transacoes(filtro_categoria=None)
            if not df_saidas.empty:
                df_saidas = df_saidas[df_saidas['tipo'] == 'saida']
                if not df_saidas.empty:
                    agrupado = df_saidas.groupby('categoria')['valor'].sum().reset_index()
                    st.bar_chart(agrupado.set_index('categoria'))
                else:
                    st.info("Nenhuma saída registrada")
            else:
                st.info("Nenhuma saída registrada")
        
        st.markdown("---")
        
        # Últimos lançamentos
        st.subheader("📋 Últimos 5 Lançamentos")
        df_ultimos = buscar_transacoes().head(5)
        if not df_ultimos.empty:
            # Formata para exibição
            df_exibicao = df_ultimos.copy()
            df_exibicao['valor'] = df_exibicao['valor'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            df_exibicao['tipo'] = df_exibicao['tipo'].apply(lambda x: "📥 Entrada" if x == "entrada" else "📤 Saída")
            st.dataframe(
                df_exibicao[['data_transacao', 'tipo', 'descricao', 'valor', 'categoria', 'unidade']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Nenhum lançamento registrado ainda")
    
    # ========================================================================
    # OPÇÃO 2: NOVO LANÇAMENTO
    # ========================================================================
    elif menu == "➕ Novo Lançamento":
        st.header("➕ Novo Lançamento Financeiro")
        
        with st.form("form_lancamento", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                tipo = st.selectbox(
                    "Tipo de Lançamento",
                    ["entrada", "saida"],
                    format_func=lambda x: "📥 Entrada" if x == "entrada" else "📤 Saída"
                )
                
                valor = st.number_input(
                    "Valor (R$)",
                    min_value=0.01,
                    step=0.01,
                    format="%.2f"
                )
                
                categoria = st.selectbox(
                    "Categoria (Plano de Contas)",
                    buscar_categorias()
                )
            
            with col2:
                unidade = st.selectbox(
                    "Unidade",
                    buscar_unidades()
                )
                
                data = st.date_input(
                    "Data da Transação",
                    value=datetime.now()
                )
                
                responsavel = st.text_input(
                    "Responsável pelo Lançamento",
                    placeholder="Seu nome"
                )
            
            descricao = st.text_area(
                "Descrição Detalhada",
                placeholder="Ex: Pagamento referente à mensalidade de março..."
            )
            
            submitted = st.form_submit_button("💾 Salvar Lançamento", use_container_width=True)
            
            if submitted:
                if valor and descricao and responsavel:
                    adicionar_transacao(
                        tipo=tipo,
                        valor=valor,
                        categoria=categoria,
                        descricao=descricao,
                        unidade=unidade,
                        data=data.strftime("%Y-%m-%d"),
                        responsavel=responsavel
                    )
                    st.success("✅ Lançamento salvo com sucesso!")
                    st.balloons()
                else:
                    st.error("❌ Preencha todos os campos obrigatórios!")
    
    # ========================================================================
    # OPÇÃO 3: FLUXO DE CAIXA
    # ========================================================================
    elif menu == "📋 Fluxo de Caixa":
        st.header("📋 Fluxo de Caixa - Histórico de Lançamentos")
        
        # Filtros
        with st.expander("🔍 Filtros de Pesquisa"):
            col_f1, col_f2, col_f3 = st.columns(3)
            
            with col_f1:
                filtro_categoria = st.selectbox(
                    "Filtrar por Categoria",
                    ["Todas"] + buscar_categorias()
                )
            
            with col_f2:
                filtro_unidade = st.selectbox(
                    "Filtrar por Unidade",
                    ["Todas"] + buscar_unidades()
                )
            
            with col_f3:
                filtro_tipo = st.selectbox(
                    "Filtrar por Tipo",
                    ["Todos", "entrada", "saida"],
                    format_func=lambda x: {"Todos": "Todos", "entrada": "📥 Entrada", "saida": "📤 Saída"}.get(x, x)
                )
            
            col_f4, col_f5 = st.columns(2)
            with col_f4:
                data_inicio = st.date_input("Data Início", value=None)
            with col_f5:
                data_fim = st.date_input("Data Fim", value=None)
        
        # Busca transações com filtros
        categoria = None if filtro_categoria == "Todas" else filtro_categoria
        unidade = None if filtro_unidade == "Todas" else filtro_unidade
        tipo = None if filtro_tipo == "Todos" else filtro_tipo
        
        df = buscar_transacoes(
            filtro_categoria=categoria,
            filtro_unidade=unidade,
            filtro_data_inicio=data_inicio.strftime("%Y-%m-%d") if data_inicio else None,
            filtro_data_fim=data_fim.strftime("%Y-%m-%d") if data_fim else None
        )
        
        # Filtra por tipo se necessário
        if tipo:
            df = df[df['tipo'] == tipo]
        
        # Exibe resultados
        if not df.empty:
            st.info(f"📊 {len(df)} lançamento(s) encontrado(s)")
            
            # Formata para exibição
            df_exibicao = df.copy()
            df_exibicao['valor_formatado'] = df_exibicao['valor'].apply(
                lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            )
            df_exibicao['tipo_formatado'] = df_exibicao['tipo'].apply(
                lambda x: "📥 Entrada" if x == "entrada" else "📤 Saída"
            )
            
            # Seleciona colunas para exibição
            colunas_exibicao = [
                'id', 'data_transacao', 'tipo_formatado', 'descricao', 
                'valor_formatado', 'categoria', 'unidade', 'responsavel'
            ]
            
            # Tabela interativa
            st.dataframe(
                df_exibicao[colunas_exibicao],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": "ID",
                    "data_transacao": "Data",
                    "tipo_formatado": "Tipo",
                    "descricao": "Descrição",
                    "valor_formatado": "Valor",
                    "categoria": "Categoria",
                    "unidade": "Unidade",
                    "responsavel": "Responsável"
                }
            )
            
            # Opção de excluir
            st.markdown("---")
            st.subheader("🗑️ Excluir Lançamento")
            id_excluir = st.number_input("Digite o ID da transação para excluir", min_value=1, step=1)
            if st.button("Excluir Transação"):
                excluir_transacao(id_excluir)
                st.warning("⚠️ Transação excluída! Atualize a página para ver as mudanças.")
                st.rerun()
            
            # Exportar para CSV
            st.markdown("---")
            csv = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8')
            st.download_button(
                label="📥 Baixar Relatório em CSV",
                data=csv,
                file_name=f"fluxo_caixa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.warning("⚠️ Nenhum lançamento encontrado com os filtros selecionados.")
    
    # ========================================================================
    # OPÇÃO 4: RELATÓRIOS
    # ========================================================================
    elif menu == "📈 Relatórios":
        st.header("📈 Relatórios Financeiros")
        
        # Relatório por Unidade
        st.subheader("💰 Saldo por Unidade")
        df_completo = buscar_transacoes()
        
        if not df_completo.empty:
            # Agrupa por unidade
            unidades_df = df_completo.groupby('unidade').agg({
                'valor': lambda x: x[df_completo.loc[x.index, 'tipo'] == 'entrada'].sum() - 
                                   x[df_completo.loc[x.index, 'tipo'] == 'saida'].sum()
            }).reset_index()
            unidades_df.columns = ['Unidade', 'Saldo']
            unidades_df['Saldo_Formatado'] = unidades_df['Saldo'].apply(
                lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            )
            
            st.dataframe(
                unidades_df[['Unidade', 'Saldo_Formatado']],
                use_container_width=True,
                hide_index=True
            )
            
            # Gráfico
            st.bar_chart(unidades_df.set_index('Unidade'))
        else:
            st.info("Nenhum dado para exibir")
        
        st.markdown("---")
        
        # Relatório por Categoria
        st.subheader("📊 Resumo por Categoria")
        
        if not df_completo.empty:
            col_r1, col_r2 = st.columns(2)
            
            with col_r1:
                st.markdown("### Entradas por Categoria")
                df_entradas = df_completo[df_completo['tipo'] == 'entrada']
                if not df_entradas.empty:
                    resumo_entradas = df_entradas.groupby('categoria')['valor'].sum().reset_index()
                    resumo_entradas['valor_formatado'] = resumo_entradas['valor'].apply(
                        lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    )
                    st.dataframe(
                        resumo_entradas[['categoria', 'valor_formatado']],
                        use_container_width=True,
                        hide_index=True,
                        column_config={"categoria": "Categoria", "valor_formatado": "Total"}
                    )
                else:
                    st.info("Sem entradas")
            
            with col_r2:
                st.markdown("### Saídas por Categoria")
                df_saidas = df_completo[df_completo['tipo'] == 'saida']
                if not df_saidas.empty:
                    resumo_saidas = df_saidas.groupby('categoria')['valor'].sum().reset_index()
                    resumo_saidas['valor_formatado'] = resumo_saidas['valor'].apply(
                        lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    )
                    st.dataframe(
                        resumo_saidas[['categoria', 'valor_formatado']],
                        use_container_width=True,
                        hide_index=True,
                        column_config={"categoria": "Categoria", "valor_formatado": "Total"}
                    )
                else:
                    st.info("Sem saídas")
        else:
            st.info("Nenhum dado para exibir")
        
        st.markdown("---")
        
        # Resumo Geral
        st.subheader("📋 Resumo Geral")
        total_entradas, total_saidas, saldo = calcular_saldo()
        
        col_res1, col_res2, col_res3 = st.columns(3)
        col_res1.metric("Total Entradas", f"R$ {total_entradas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        col_res2.metric("Total Saídas", f"R$ {total_saidas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        col_res3.metric("Saldo Final", f"R$ {saldo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

# ============================================================================
# EXECUÇÃO DO APLICATIVO
# ============================================================================

if __name__ == "__main__":
    main()