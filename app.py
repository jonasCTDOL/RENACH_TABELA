import streamlit as st
import pandas as pd
import io
import datetime

# Função para carregar e processar o arquivo RELATÓRIO CURSO
def process_relatorio_curso(uploaded_file):
    if uploaded_file is not None:
        st.write("--- Processando Tabela RELATÓRIO CURSO ---")
        # Lê o arquivo CSV para um DataFrame, especificando 'CPF' como string
        # Utiliza 'sep=;' pois a prévia mostra ponto e vírgula como separador
        try:
            df_relatorio_curso = pd.read_csv(io.StringIO(uploaded_file.getvalue().decode('utf-8')), sep=';', dtype={'CPF': str})
            st.write("Prévia da tabela RELATÓRIO CURSO carregada:")
            st.dataframe(df_relatorio_curso.head())

            # --- Início do tratamento df_relatorio_curso ---

            # Mantém a coluna original do CPF antes de limpar
            df_relatorio_curso['CPF_Original'] = df_relatorio_curso['CPF']

            # Converte as colunas de data para o formato datetime
            df_relatorio_curso['Data de matrícula'] = pd.to_datetime(df_relatorio_curso['Data de matrícula'], format='%d/%m/%Y', errors='coerce')
            df_relatorio_curso['Data de conclusão'] = pd.to_datetime(df_relatorio_curso['Data de conclusão'], format='%d/%m/%Y', errors='coerce')

            # Calcula a diferença em dias entre a data de conclusão e matrícula
            df_relatorio_curso['Diferença de Dias'] = (df_relatorio_curso['Data de conclusão'] - df_relatorio_curso['Data de matrícula']).dt.days

            # 2 - Identifica registros com menos de 5 dias de diferença
            df_menos_5_dias = df_relatorio_curso[df_relatorio_curso['Diferença de Dias'] < 5].copy()

            # Salva a tabela de registros com menos de 5 dias em um arquivo CSV temporário para download
            if not df_menos_5_dias.empty:
                csv_menos_5_dias_content = df_menos_5_dias.to_csv(index=False, sep=',').encode('utf-8')
                st.download_button(
                    label="Baixar ALUNOS_CURSO_MENOS_5.csv",
                    data=csv_menos_5_dias_content,
                    file_name='ALUNOS_CURSO_MENOS_5.csv',
                    mime='text/csv',
                    key='download_menos_5_dias'
                )
                st.write("Registros com menos de 5 dias identificados e disponíveis para download.")
            else:
                 st.write("Não foram encontrados registros com menos de 5 dias de diferença.")


            # 3 - Exclui os registros com menos de 5 dias do DataFrame original
            df_relatorio_curso = df_relatorio_curso[df_relatorio_curso['Diferença de Dias'] >= 5].copy()

            # Remove a coluna temporária 'Diferença de Dias'
            df_relatorio_curso = df_relatorio_curso.drop(columns=['Diferença de Dias'])

            # 4 - Ajusta as colunas CPF, data-inicio-curso e data-fim-curso
            # CPF - Somente números sem pontos e hífen (usado para mesclagem)
            # Já é lido como string, apenas remove caracteres não numéricos
            df_relatorio_curso['CPF'] = df_relatorio_curso['CPF'].str.replace(r'\D', '', regex=True)

            # data-inicio-curso formato YYYYMMDD
            # Converte para string no formato YYYYMMDD, tratando NaT (Not a Time)
            df_relatorio_curso['data-inicio-curso'] = df_relatorio_curso['Data de matrícula'].dt.strftime('%Y%m%d').fillna('')

            # data-fim-curso formato YYYYMMDD
            # Converte para string no formato YYYYMMDD, tratando NaT (Not a Time)
            df_relatorio_curso['data-fim-curso'] = df_relatorio_curso['Data de conclusão'].dt.strftime('%Y%m%d').fillna('')

            # --- Fim do tratamento df_relatorio_curso ---

            st.write("Prévia da tabela RELATÓRIO CURSO após tratamento:")
            st.dataframe(df_relatorio_curso[['CPF', 'CPF_Original', 'data-inicio-curso', 'data-fim-curso']].head())

            return df_relatorio_curso, df_menos_5_dias # Retorna também os registros com menos de 5 dias
        except Exception as e:
            st.error(f"Erro ao processar o arquivo RELATÓRIO CURSO: {e}")
            return pd.DataFrame(), pd.DataFrame()
    else:
        return pd.DataFrame(), pd.DataFrame()


# Função para carregar e processar o arquivo FORMULÁRIO CADASTRO
def process_formulario_cadastro(uploaded_file):
    if uploaded_file is not None:
        st.write("\n--- Processando Tabela FORMULÁRIO CADASTRO ---")
        # Lê o arquivo CSV para um DataFrame, especificando 'Identificação de usuário' como string
        # Utiliza 'sep=,' pois a prévia mostra vírgula como separador
        try:
            df_formulario_cadastro = pd.read_csv(io.StringIO(uploaded_file.getvalue().decode('utf-8')), sep=',', dtype={'Identificação de usuário': str})
            st.write("Prévia da tabela FORMULÁRIO CADASTRO carregada:")
            st.dataframe(df_formulario_cadastro.head())

            # --- Criação da nova tabela com requisitos específicos ---

            # Cria um novo DataFrame com as colunas desejadas
            df_novo_cadastro = pd.DataFrame()

            # CPF - somente Números sem ponto e traços (usado para mesclagem)
            # Utiliza a coluna 'Identificação de usuário' (já lida como string) e remove caracteres não numéricos
            df_novo_cadastro['CPF'] = df_formulario_cadastro['Identificação de usuário'].str.replace(r'\D', '', regex=True)

            # numero-cnh - somente números
            # Procura por nomes de coluna alternativos para o número da CNH
            cnh_col_names = ['QUESTÃO 1 - Informe o número da CNH:', 'Nº Registro da CNH:']
            cnh_column = next((col for col in cnh_col_names if col in df_formulario_cadastro.columns), None)

            if cnh_column:
                df_novo_cadastro['numero-cnh'] = df_formulario_cadastro[cnh_column].astype(str).str.replace(r'\D', '', regex=True)
            else:
                st.error(f"Erro: Nenhuma das colunas esperadas para o número da CNH foi encontrada no arquivo FORMULÁRIO CADASTRO. Nomes esperados: {cnh_col_names}")
                return pd.DataFrame()

            # categoria - celula com 4 campos sendo a letra da categoria e preenchimento com espaço
            # Procura por nomes de coluna alternativos para a categoria da CNH
            categoria_col_names = ['QUESTÃO 2 - Selecione a categoria da CNH:', 'Categoria da CNH:']
            categoria_column = next((col for col in categoria_col_names if col in df_formulario_cadastro.columns), None)

            if categoria_column:
                df_novo_cadastro['categoria'] = df_formulario_cadastro[categoria_column].astype(str).str.ljust(4)
            else:
                st.error(f"Erro: Nenhuma das colunas esperadas para a categoria da CNH foi encontrada no arquivo FORMULÁRIO CADASTRO. Nomes esperados: {cnh_col_names}")
                return pd.DataFrame()


            st.write("Prévia da nova tabela (CPF, numero-cnh, categoria):")
            st.dataframe(df_novo_cadastro.head())

            return df_novo_cadastro
        except Exception as e:
            st.error(f"Erro ao processar o arquivo FORMULÁRIO CADASTRO: {e}")
            return pd.DataFrame()
    else:
        return pd.DataFrame()


# Configuração da página Streamlit
st.set_page_config(layout="wide", page_title="Processamento de Dados de Curso e Cadastro")

st.title("Processamento de Dados de Curso e Cadastro")

st.write("""
Este aplicativo processa duas tabelas (Relatório de Curso e Formulário de Cadastro)
para gerar uma tabela final com informações combinadas e um arquivo separado para
alunos com diferença de dias entre matrícula e conclusão menor que 5 dias.
""")

# --- Upload dos arquivos ---
st.header("Upload dos Arquivos")
uploaded_relatorio_file = st.file_uploader("Carregue a Tabela RELATÓRIO CURSO (arquivo CSV)", type=['csv'], key='relatorio_upload')
uploaded_formulario_file = st.file_uploader("Carregue a Tabela FORMULÁRIO CADASTRO (arquivo CSV)", type=['csv'], key='formulario_upload')

df_relatorio_curso, df_menos_5_dias_output = process_relatorio_curso(uploaded_relatorio_file)
df_novo_cadastro = process_formulario_cadastro(uploaded_formulario_file)


# --- Mescla das tabelas e seleção de colunas ---
st.header("Mesclagem das Tabelas")
PREPARO_ETL = pd.DataFrame()
if not df_relatorio_curso.empty and not df_novo_cadastro.empty:
    st.write("--- Mesclando tabelas e selecionando colunas ---")
    # Mescla as duas tabelas usando a coluna 'CPF' (numérico)
    # Utiliza um merge 'inner' para incluir apenas CPFs presentes em ambas as tabelas
    try:
        PREPARO_ETL = pd.merge(df_relatorio_curso, df_novo_cadastro, on='CPF', how='inner')

        # Seleciona as colunas desejadas, incluindo o CPF_Original
        colunas_desejadas = ['CPF_Original', 'CPF', 'data-inicio-curso', 'data-fim-curso', 'numero-cnh', 'categoria']
        PREPARO_ETL = PREPARO_ETL[colunas_desejadas]

        st.write("Prévia da tabela PREPARO_ETL (mesclada e com colunas selecionadas):")
        st.dataframe(PREPARO_ETL.head())

    except Exception as e:
        st.error(f"Erro ao mesclar as tabelas: {e}")
        PREPARO_ETL = pd.DataFrame() # Garante um DataFrame vazio em caso de erro

elif uploaded_relatorio_file is not None and uploaded_formulario_file is not None:
     st.warning("Uma ou ambas as tabelas carregadas resultaram vazias após o processamento. Verifique os arquivos de entrada.")


# --- Criação do DataFrame Final ---
st.header("Criação da Tabela Final")
df_final = pd.DataFrame()
if not PREPARO_ETL.empty:
    # Usa um formulário para agrupar os inputs e evitar re-execução a cada mudança
    with st.form(key="parametros_finais"):
        st.write("Informe os parâmetros para gerar a tabela final:")

        # Solicita o número inicial da sequência
        nu_seq_trans_inicio = st.number_input("Informe o número inicial da sequência para 'nu-seq-trans':", min_value=0, value=888888, step=1)

        # Solicita o tipo de atualização
        tipo_atualizacao_input = st.radio("Selecione o tipo de atualização: Sendo I para inclusão e S substituição do registro", ('I', 'S'), horizontal=True)

        # Solicita a carga horária
        carga_horaria_input = st.radio("Selecione a carga horária:", ('060', '018','040'), horizontal=True)

        # Botão para submeter o formulário e iniciar o processamento
        submitted = st.form_submit_button("Gerar Tabela Final")

    if submitted:
        # --- Início da montagem da tabela final para download ---
        # Criação do novo DataFrame
        df_final = pd.DataFrame()

        # Popula as colunas conforme os requisitos
        df_final['nu-seq-trans'] = range(nu_seq_trans_inicio, nu_seq_trans_inicio + len(PREPARO_ETL))
        df_final['cod-trans'] = '181'
        df_final['cod-mod-trans'] = '7' # Modified to '7'
        df_final['codusu'] = PREPARO_ETL['CPF'] # Continua usando o CPF numérico para esta coluna
        df_final['uf-or-trans'] = 'SA'
        df_final['uf-orig-transm'] = 'SA'
        df_final['uf-des-transm'] = 'BR'
        df_final['cond-trans'] = '0'
        df_final['tam-trans'] = '0152'# 4 digitos
        df_final['cod-ret-trans'] = '00'

        # Calcula o dia juliano
        hoje = datetime.date.today()
        dia_juliano_hoje = hoje.timetuple().tm_yday
        df_final['dia-juliano'] = dia_juliano_hoje

        df_final['tipo-chave'] = '2'
        df_final['numero-cnh'] = PREPARO_ETL['numero-cnh'].str.zfill(11)
        df_final['tipo-evento'] = 'C'
        df_final['tipo-atualizacao'] = tipo_atualizacao_input
        df_final['codigo-curso'] = '04'
        df_final['modalidade'] = '2'

        # Gera o número do certificado
        df_final['Numero Certificado'] = [f'escola{i:09d}' for i in range(1, len(PREPARO_ETL) + 1)]

        df_final['data-inicio-curso'] = PREPARO_ETL['data-inicio-curso']
        df_final['data-fim-curso'] = PREPARO_ETL['data-fim-curso']
        df_final['carga-horaria'] = carga_horaria_input
        df_final['cnpj-entidade-crede'] = '00394494000560'
        df_final['cpf-instrutor'] = '57437670097'
        df_final['municipio-curso'] = '9701'
        df_final['uf-curso'] = 'DF'

        # Calcula a data de validade (acrescenta 5 anos)
        df_final['data-inicio-curso_dt'] = pd.to_datetime(df_final['data-inicio-curso'], format='%Y%m%d', errors='coerce')
        df_final['data-validade'] = (df_final['data-inicio-curso_dt'] + pd.DateOffset(years=5)).dt.strftime('%Y%m%d').fillna('')
        df_final = df_final.drop(columns=['data-inicio-curso_dt']) # Remove a coluna temporária

        df_final['categoria'] = PREPARO_ETL['categoria'].str.ljust(4) # Garante 4 caracteres com espaços à direita
        df_final['observacoes-curso'] = '99                  ' # 99 seguido de 18 espaços para totalizar 20

        # --- Formatação das colunas para o CSV final ---
        df_final['nu-seq-trans'] = df_final['nu-seq-trans'].astype(str).str.zfill(6)
        df_final['cod-trans'] = df_final['cod-trans'].astype(str).str.zfill(3)
        df_final['cod-mod-trans'] = df_final['cod-mod-trans'].astype(str) # Ensure it's treated as a string, not a number
        df_final['codusu'] = df_final['codusu'].astype(str).str.zfill(11)
        df_final['uf-or-trans'] = df_final['uf-or-trans'].astype(str).str.ljust(2)
        df_final['uf-orig-transm'] = df_final['uf-orig-transm'].astype(str).str.ljust(2)
        df_final['uf-des-transm'] = df_final['uf-des-transm'].astype(str).str.ljust(2)
        df_final['cond-trans'] = df_final['cond-trans'].astype(str).str.zfill(1)
        df_final['tam-trans'] = df_final['tam-trans'].astype(str).str.zfill(4)
        df_final['cod-ret-trans'] = df_final['cod-ret-trans'].astype(str).str.zfill(2)
        df_final['dia-juliano'] = df_final['dia-juliano'].astype(str).str.zfill(3)
        df_final['tipo-chave'] = df_final['tipo-chave'].astype(str).str.zfill(1)
        df_final['numero-cnh'] = df_final['numero-cnh'].astype(str).str.zfill(10)
        df_final['tipo-evento'] = df_final['tipo-evento'].astype(str).str.ljust(1)
        df_final['tipo-atualizacao'] = df_final['tipo-atualizacao'].astype(str).str.ljust(1)
        df_final['codigo-curso'] = df_final['codigo-curso'].astype(str).str.zfill(2)
        df_final['modalidade'] = df_final['modalidade'].astype(str).str.zfill(1)
        df_final['Numero Certificado'] = df_final['Numero Certificado'].astype(str).str.ljust(15)
        df_final['data-inicio-curso'] = df_final['data-inicio-curso'].astype(str).str.ljust(8) # Datas já devem estar em YYYYMMDD ou vazio
        df_final['data-fim-curso'] = df_final['data-fim-curso'].astype(str).str.ljust(8) # Datas já devem estar em YYYYMMDD ou vazio
        df_final['carga-horaria'] = df_final['carga-horaria'].astype(str).str.zfill(3)
        df_final['cnpj-entidade-crede'] = df_final['cnpj-entidade-crede'].astype(str).str.zfill(14)
        df_final['cpf-instrutor'] = df_final['cpf-instrutor'].astype(str).str.zfill(11)
        df_final['municipio-curso'] = df_final['municipio-curso'].astype(str).str.zfill(5)
        df_final['uf-curso'] = df_final['uf-curso'].astype(str).str.ljust(2)
        df_final['data-validade'] = df_final['data-validade'].astype(str).str.ljust(8) # Data já deve estar em YYYYMMDD ou vazio
        df_final['categoria'] = df_final['categoria'].astype(str).str.ljust(4)
        df_final['observacoes-curso'] = df_final['observacoes-curso'].astype(str).str.ljust(20)

        # Explicitly convert to string for display in Streamlit just before displaying
        df_final_display = df_final.copy()
        df_final_display['cod-mod-trans'] = df_final_display['cod-mod-trans'].astype(str)


        st.success("Tabela final gerada com sucesso!")
        st.write("\nPrévia da tabela final:")
        st.dataframe(df_final_display.head()) # Display the modified copy

        # --- Opção para baixar o CSV final ---
        st.header("Download da Tabela Final")
        csv_final_content = df_final.to_csv(index=False, sep=',').encode('utf-8')
        st.download_button(
            label="Baixar PREPARO_ETL_FINAL.csv",
            data=csv_final_content,
            file_name='PREPARO_ETL_FINAL.csv',
            mime='text/csv',
            key='download_final_etl'
        )

        # --- Verificação de CPFs que começam com '0' ---
        st.header("Verificação de CPFs que começam com '0'")
        # Usa a coluna 'codusu' que já foi formatada com zeros à esquerda, se necessário
        cpfs_com_zero = df_final[df_final['codusu'].astype(str).str.startswith('0')]

        if not cpfs_com_zero.empty:
            st.write("Foram encontrados CPFs (numéricos) que começam com '0' na tabela final:")
            st.dataframe(cpfs_com_zero[['codusu']])
        else:
            st.write("Não foram encontrados CPFs (numéricos) que começam com '0' na tabela final.")


else:
    if uploaded_relatorio_file is not None and uploaded_formulario_file is not None:
        st.warning("Não foi possível criar o DataFrame final. Verifique os arquivos de entrada e as condições de mesclagem.")
    else:
        st.info("Carregue os arquivos CSV para iniciar o processamento.")
