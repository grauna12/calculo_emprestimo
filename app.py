import streamlit as st
import pandas as pd
import numpy_financial as nf

# Configuração da página com tema mais clean
st.set_page_config(
    page_title="Calculadora de Empréstimo", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado para interface mais limpa
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        margin-bottom: 2rem;
    }
    .metric-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .cost-metric {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .rate-metric {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .section-divider {
        margin: 2rem 0;
        border-top: 2px solid #f0f2f6;
    }
    .info-box {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #4CAF50;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header principal
st.markdown("""
<div class="main-header">
    <h1>Calculadora de Empréstimo</h1>
    <p style="font-size: 1.2rem; color: #666;">Sistema de Amortização Constante (SAC)</p>
</div>
""", unsafe_allow_html=True)

# Layout em duas colunas principais
col_input, col_results = st.columns([1, 2])

with col_input:
    st.markdown("### Dados do Empréstimo")
    
    # Agrupamento dos inputs em containers
    with st.container():
        st.markdown("**Valor e Condições**")
        valor_principal_solicitado = st.number_input(
            "Valor Solicitado (R$)",
            min_value=0.01,
            value=10000.0,
            step=100.0,
            format="%.2f"
        )
        
        taxa_juros_nominal_periodo = st.number_input(
            "Taxa de Juros (% ao período)",
            min_value=0.0,
            value=2.0,
            step=0.1,
            format="%.2f"
        )
        
        periodicidade = st.selectbox(
            "Periodicidade",
            ["Mensal", "Quinzenal", "Semanal"],
            index=0
        )
        
        num_parcelas = st.number_input(
            "Número de Parcelas",
            min_value=1,
            value=12,
            step=1
        )
    
    st.markdown("---")
    
    with st.container():
        st.markdown("**Custos Adicionais**")
        iof_percentual = st.number_input(
            "IOF (%)",
            min_value=0.0,
            value=0.38,
            step=0.01,
            format="%.2f"
        )
        
        taxa_abertura_credito = st.number_input(
            "Taxa de Abertura (R$)",
            min_value=0.0,
            value=0.0,
            step=1.0,
            format="%.2f"
        )

with col_results:
    if valor_principal_solicitado > 0 and num_parcelas > 0:
        # Cálculos
        valor_iof = valor_principal_solicitado * (iof_percentual / 100.0)
        valor_base_amortizacao = valor_principal_solicitado
        amortizacao_constante = valor_base_amortizacao / num_parcelas
        fluxo_caixa_t0 = valor_principal_solicitado - valor_iof - taxa_abertura_credito

        cronograma_pagamentos = []
        saldo_devedor_corrente = valor_base_amortizacao
        total_juros_pago = 0.0
        total_amortizado = 0.0
        soma_total_parcelas = 0.0

        for i in range(1, int(num_parcelas) + 1):
            juros_periodo = saldo_devedor_corrente * (taxa_juros_nominal_periodo / 100.0)
            amortizacao_neste_periodo = amortizacao_constante
            
            if i == int(num_parcelas):
                juros_periodo = saldo_devedor_corrente * (taxa_juros_nominal_periodo / 100.0)
                amortizacao_neste_periodo = saldo_devedor_corrente 
                
            parcela_total = amortizacao_neste_periodo + juros_periodo
            soma_total_parcelas += parcela_total

            saldo_devedor_anterior = saldo_devedor_corrente
            saldo_devedor_corrente -= amortizacao_neste_periodo
            total_juros_pago += juros_periodo
            total_amortizado += amortizacao_neste_periodo

            cronograma_pagamentos.append({
                "Nº Parcela": i,
                "Saldo Devedor Inicial (R$)": saldo_devedor_anterior,
                "Amortização (R$)": amortizacao_neste_periodo,
                "Juros (R$)": juros_periodo,
                "Parcela Total (R$)": parcela_total,
                "Saldo Devedor Final (R$)": max(saldo_devedor_corrente, 0) 
            })

        df_cronograma = pd.DataFrame(cronograma_pagamentos)
        
        # Custo Total da Operação em Reais
        custo_total_operacao_reais = total_juros_pago + valor_iof + taxa_abertura_credito

        fluxos_de_caixa_cet = [fluxo_caixa_t0] + [-(p["Parcela Total (R$)"]) for p in cronograma_pagamentos]
        
        cet_periodico = None
        cet_anual = None

        if fluxo_caixa_t0 <= 0: 
            st.error("Valor líquido recebido é zero ou negativo. Verifique os custos iniciais.")
        else:
            try:
                if len(fluxos_de_caixa_cet) > 1:
                     cet_periodico = nf.irr(fluxos_de_caixa_cet)
                else:
                    cet_periodico = None 

                if cet_periodico is not None and not (isinstance(cet_periodico, float) and cet_periodico != cet_periodico): 
                    num_periodos_ano = {"Mensal": 12, "Quinzenal": 26, "Semanal": 52}[periodicidade]
                    cet_anual = (1 + cet_periodico) ** num_periodos_ano - 1
                else:
                    cet_periodico = None 
                    cet_anual = None
            except Exception as e:
                st.error(f"Erro no cálculo do CET: {e}")
        
        # Resultados Principais
        st.markdown("### Resumo Financeiro")
        
        # Métricas principais em grid
        metric_cols = st.columns(2)
        
        with metric_cols[0]:
            st.metric(
                "Valor Solicitado",
                f"R$ {valor_principal_solicitado:,.2f}",
                help="Montante solicitado"
            )
            st.metric(
                "Total a Pagar",
                f"R$ {soma_total_parcelas:,.2f}",
                delta=f"+R$ {soma_total_parcelas - valor_principal_solicitado:,.2f}",
                help="Soma de todas as parcelas"
            )
        
        with metric_cols[1]:
            st.metric(
                "Valor Líquido",
                f"R$ {fluxo_caixa_t0:,.2f}",
                delta=f"-R$ {valor_iof + taxa_abertura_credito:,.2f}",
                help="Valor após descontos iniciais"
            )
            st.metric(
                "Custo Total",
                f"R$ {custo_total_operacao_reais:,.2f}",
                help="Juros + IOF + Taxas"
            )

        # Taxas Efetivas
        st.markdown("### Taxas Efetivas")
        
        tax_cols = st.columns(3)
        
        with tax_cols[0]:
            st.metric(
                f"Taxa {periodicidade}",
                f"{taxa_juros_nominal_periodo:.2f}%",
                help="Taxa nominal informada"
            )
        
        with tax_cols[1]:
            if cet_periodico is not None:
                st.metric(
                    f"CET {periodicidade}",
                    f"{cet_periodico * 100:.2f}%",
                    delta=f"{(cet_periodico - taxa_juros_nominal_periodo/100) * 100:+.2f}%",
                    help="Custo efetivo por período"
                )
            else:
                st.metric(f"CET {periodicidade}", "N/A")
        
        with tax_cols[2]:
            if cet_anual is not None:
                st.metric(
                    "CET Anual",
                    f"{cet_anual * 100:.2f}%",
                    help="Taxa anualizada para comparação"
                )
            else:
                st.metric("CET Anual", "N/A")

        # Divisor visual
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        # Detalhamento dos Custos
        st.markdown("### Detalhamento dos Custos")
        
        cost_cols = st.columns(3)
        
        with cost_cols[0]:
            st.metric("IOF", f"R$ {valor_iof:,.2f}")
        
        with cost_cols[1]:
            st.metric("Taxa Abertura", f"R$ {taxa_abertura_credito:,.2f}")
        
        with cost_cols[2]:
            st.metric("Juros Totais", f"R$ {total_juros_pago:,.2f}")

        # Cronograma de Pagamentos
        st.markdown("### Cronograma de Pagamentos")
        
        # Exibir apenas as primeiras 10 parcelas por padrão
        show_all = st.checkbox("Mostrar todas as parcelas", value=False)
        
        df_display = df_cronograma.copy()
        if not show_all and len(df_display) > 10:
            df_display = pd.concat([df_display.head(5), df_display.tail(5)])
            st.info(f"Exibindo as primeiras e últimas 5 parcelas de {len(df_cronograma)} total. Marque a opção acima para ver todas.")
        
        # Formatação da tabela
        st.dataframe(
            df_display.style.format({
                "Saldo Devedor Inicial (R$)": "R$ {:,.2f}",
                "Amortização (R$)": "R$ {:,.2f}",
                "Juros (R$)": "R$ {:,.2f}",
                "Parcela Total (R$)": "R$ {:,.2f}",
                "Saldo Devedor Final (R$)": "R$ {:,.2f}"
            }),
            use_container_width=True
        )

    else:
        st.markdown("""
        <div class="info-box">
            <h3>Bem-vindo!</h3>
            <p>Preencha os dados do empréstimo na coluna à esquerda para ver os cálculos.</p>
            <p><strong>Dica:</strong> Esta calculadora usa o Sistema SAC, onde a amortização é constante e os juros diminuem a cada parcela.</p>
        </div>
        """, unsafe_allow_html=True)

# Footer com informações
st.markdown("---")
with st.expander("Como interpretar os resultados"):
    st.markdown("""
    **Valor Solicitado:** Quantia que você está pedindo emprestado
    
    **Valor Líquido:** O que efetivamente entra no seu caixa (após IOF e taxas)
    
    **Total a Pagar:** Soma de todas as parcelas que você pagará
    
    **Custo Total:** Quanto o empréstimo custará em reais (diferença entre o total pago e valor líquido)
    
    **CET Anual:** A taxa mais importante para comparar propostas de diferentes bancos
    
    **Observações:**
    - Cálculo do IOF é estimativo
    - Sistema SAC: amortização constante, juros decrescentes
    - Pequenas diferenças podem ocorrer por arredondamentos
    """)

with st.expander("Dicas de uso"):
    st.markdown("""
    1. **Compare sempre o CET Anual** entre diferentes propostas
    2. **Atenção aos custos iniciais** (IOF + Taxas) - eles reduzem o valor que você recebe
    3. **No sistema SAC**, as primeiras parcelas são maiores que as últimas
    4. **Use esta ferramenta** para negociar melhores condições com seu banco
    """)