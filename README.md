# Controle de Empréstimos de Ativos

Aplicação de desktop em Python para controlar ativos, empréstimos e devoluções em um banco MySQL. A interface gráfica permite cadastrar e consultar equipamentos, registrar movimentações, gerar termos em Word e exportar relatórios em Excel.

O projeto surgiu da necessidade de centralizar o controle de equipamentos e localizar seus termos de entrega e devolução sem procurar documento por documento em pastas compartilhadas.

## Funcionalidades

- Cadastro, consulta, edição e exclusão de ativos.
- Serial, patrimônio, tipo, marca, modelo e itens entregues são exibidos e salvos em maiúsculas; nome, departamento e cargo de novos colaboradores são salvos com as iniciais maiúsculas. As mesmas regras valem na interface e no menu de texto.
- Seleção da empresa responsável (`Arklok` ou `Vivo`). O patrimônio pode ser informado apenas para ativos da Arklok; esses campos servem ao controle interno e não aparecem nos termos.
- Cadastro de colaboradores durante o registro de um empréstimo, com reaproveitamento dos dados existentes.
- Registro de empréstimos e devoluções, com atualização do status do ativo e geração de termos DOCX.
- Reemissão de termos de responsabilidade, consulta de empréstimos em aberto e exportação de relatórios por empréstimo ou departamento.

## Requisitos e instalação

- Python com Tkinter (incluído na instalação usual do Python para Windows).
- MySQL com o banco `controle_emprestimos` e as tabelas `colaboradores`, `ativos` e `emprestimos` já criadas. O projeto não inclui um script completo de criação inicial dessas tabelas.
- Os modelos `TERMO_RESPONSABILIDADE_MODELO.docx` e `TERMO_DEVOLUCAO_MODELO.docx` na raiz do projeto.

Na pasta do projeto, crie um ambiente virtual e instale as dependências:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install mysql-connector-python python-dotenv docxtpl openpyxl
```

Crie um arquivo `.env` na raiz com os dados de acesso ao seu MySQL:

```dotenv
DB_HOST=localhost
DB_PORT=3306
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
DB_NAME=controle_emprestimos
```

Mantenha o `.env` fora dos commits para não publicar credenciais.

### Atualização de um banco existente

Se o banco ainda não tiver as colunas `empresa` e `patrimonio` na tabela `ativos`, faça um backup e execute **uma única vez** `migracao_empresa_patrimonio.sql`. O script adiciona as duas colunas e uma restrição de unicidade para o patrimônio. Ativos existentes continuam cadastrados, inicialmente sem empresa definida. Não execute a migração outra vez se as colunas já existirem.

A tabela `emprestimos` também precisa conter a coluna `chamado_devolucao`, utilizada pelo registro de devoluções.

## Execução

Abra a interface gráfica com:

```powershell
python main.py
```

Para usar o menu de texto:

```powershell
python main.py --cli
```

### Programa para Windows (.exe)

O executável abre a mesma interface gráfica sem precisar iniciar pelo PyCharm ou instalar Python no computador onde será usado. Baixe **ControleEmprestimos-Windows** na seção *Artifacts* da [execução mais recente de Aplicativo Windows](https://github.com/luccamukics/controle-de-emprestimos-de-ativos/actions/workflows/build-windows.yml) e extraia **a pasta inteira** em um local onde você possa salvar arquivos, como Documentos. Abra `ControleEmprestimos.exe` dentro dela.

Na primeira execução, copie `.env.exemplo` para `.env` na mesma pasta do executável e preencha as credenciais do MySQL. O banco deve estar acessível desse computador; `DB_HOST=localhost` funciona apenas se o MySQL estiver nele. Os dois modelos DOCX precisam permanecer ao lado do `.exe`. Termos e planilhas serão criados nessa mesma pasta, em `termos_empréstimos/`, `termos_devolucao/` e `Planilha de Controle/`. O pacote publicado não inclui senha, dados do banco ou documentos gerados.

Para gerar o pacote no seu próprio Windows, execute `powershell -ExecutionPolicy Bypass -File .\build_windows.ps1` na raiz do repositório, com Python instalado. O resultado estará em `dist\ControleEmprestimos\`. Distribua essa pasta inteira; o `.exe` sozinho depende dos arquivos que a acompanham.

Na aba **Ativos**, as colunas Colaborador e Setor mostram quem está com cada ativo emprestado e seu departamento cadastrado; ativos sem empréstimo em aberto ficam com essas células vazias. O botão **Exportar Excel** salva a lista exibida (inclusive o filtro «Somente disponíveis») em `Planilha de Controle/relatorio_ativos.xlsx`. Selecione um equipamento para editá-lo ou excluí-lo. A edição permite alterar todos os dados, inclusive o número de série; empréstimos anteriores passam a referenciar o novo serial. Um ativo com empréstimo em aberto só pode ser excluído depois da devolução. Se houver empréstimos já encerrados, a confirmação de exclusão informa quantos registros históricos também serão apagados do banco. Os termos DOCX gerados anteriormente permanecem nas pastas.

A escrita automática é aplicada aos novos cadastros e aos ativos editados. Registros antigos não são alterados em massa: ao editar um ativo com serial em minúsculas, seus empréstimos continuam vinculados depois da atualização. As opções de Empresa e Status mantêm os valores internos necessários ao funcionamento do programa; o chamado GLPI continua numérico. Os novos termos usam os dados salvos com a formatação aplicada; documentos já gerados não são reescritos.

Na aba **Empréstimos**, registre empréstimos ou devoluções e consulte as operações em aberto. A criação de um termo ocorre depois da gravação no banco: se o documento falhar, confira o aviso na interface e o modelo DOCX antes de tentar gerar o termo novamente.

Na aba **Relatórios**, consulte os empréstimos em aberto e os ativos emprestados por departamento e exporte as planilhas.

## Arquivos e pastas

| Caminho | Finalidade |
| --- | --- |
| `main.py` | Entrada da interface gráfica e do menu de texto. |
| `interface_grafica.py` | Janelas e formulários Tkinter. |
| `conexao_mysql.py` | Conexão MySQL configurada pelo `.env`. |
| `modulos/servicos.py` | Operações compartilhadas de banco e validações. |
| `modulos/ativos.py`, `modulos/emprestimos.py` | Opções do menu de texto. |
| `modulos/termos.py` | Geração dos documentos a partir dos modelos Word. |
| `modulos/relatorios.py` | Consultas e exportação das planilhas. |
| `migracao_empresa_patrimonio.sql` | Atualização de bancos anteriores. |
| `termos_empréstimos/` | Termos de responsabilidade gerados. |
| `termos_devolucao/` | Termos de devolução gerados. |
| `Planilha de Controle/` | Relatórios Excel exportados. |

As pastas de saída são criadas conforme os documentos e relatórios são gerados. Os arquivos resultantes contêm dados operacionais; revise-os antes de adicioná-los ao Git.

## Dados usados

- **Ativos:** empresa, número de série (chave primária), patrimônio, tipo, marca, modelo, status, itens entregues e chamado.
- **Colaboradores:** login (chave primária), nome, CPF, departamento, cargo e campus.
- **Empréstimos:** identificador, colaborador, ativo, datas de saída e devolução, condições, observações e chamado de devolução.

Ao emprestar um ativo, seu status muda de `disponivel` para `emprestado`. Ao registrar a devolução, volta para `disponivel`.
