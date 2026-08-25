Sistema de Controle de Empréstimos de Ativos

Sistema desenvolvido em Python + MySQL para controlar o empréstimo e a devolução de ativos de tecnologia, como notebooks e celulares.

O projeto permite cadastrar equipamentos e colaboradores, registrar empréstimos e devoluções, gerar termos de responsabilidade automaticamente em Word e exportar relatórios para Excel.

Funcionalidades

O sistema possui as seguintes funcionalidades:

Cadastro de ativos
Cadastro automático de colaboradores durante o empréstimo
Registro de empréstimos
Registro de devoluções
Controle do status dos ativos
Listagem de ativos disponíveis
Listagem de todos os ativos
Listagem de empréstimos em aberto
Geração automática de termo de responsabilidade em .docx
Reemissão de termos de responsabilidade
Relatório de empréstimos em aberto
Relatório de ativos emprestados por departamento
Exportação de relatórios para Excel
Tecnologias utilizadas
Python
MySQL
MySQL Connector
docxtpl
openpyxl
Microsoft Word para o modelo do termo de responsabilidade
Estrutura do projeto
projeto/
│
├── main.py
├── conexao_mysql.py
├── relatorios.py
├── TERMO_RESPONSABILIDADE_MODELO.docx
│
└── termos/
    └── TERMO_login_serial.docx
main.py

Arquivo principal do sistema. Contém o menu e as funções responsáveis pelo cadastro de ativos, empréstimos, devoluções e geração dos termos.

conexao_mysql.py

Responsável pela conexão entre a aplicação Python e o banco de dados MySQL.

relatorios.py

Contém as funções responsáveis pela geração e exportação dos relatórios para Excel.

TERMO_RESPONSABILIDADE_MODELO.docx

Modelo utilizado pelo sistema para gerar automaticamente o termo de responsabilidade do colaborador.

termos/

Pasta criada automaticamente para armazenar os termos de responsabilidade gerados pelo sistema.

Banco de dados

O sistema utiliza três tabelas principais.

Colaboradores

Armazena os dados dos colaboradores:

login
nome
CPF
departamento
cargo
campus

O campo login é utilizado como chave primária.

Ativos

Armazena os equipamentos cadastrados:

serial_number
tipo
modelo
marca
at_status
itens_entregues
id_chamado

O campo serial_number é a chave primária do ativo.

O campo at_status permite controlar se o equipamento está, por exemplo:

disponivel
emprestado
Empréstimos

Relaciona colaboradores e ativos:

id
id_colaborador
id_ativo
data_saida
data_devolucao
condicao_saida
condicao_retorno
observacoes

id_colaborador referencia o login da tabela colaboradores.

id_ativo referencia o serial_number da tabela ativos.

Fluxo de empréstimo

Ao registrar um empréstimo, o sistema solicita o login do colaborador.

Se o colaborador já estiver cadastrado, seus dados são recuperados automaticamente. Caso contrário, o sistema solicita:

Nome
CPF
Departamento
Cargo
Campus

Em seguida, são apresentados os ativos disponíveis.

Após a escolha do equipamento, o sistema:

Registra o empréstimo no MySQL.
Altera o status do ativo para emprestado.
Gera automaticamente o termo de responsabilidade.
Salva o documento na pasta termos.

Exemplo:

termos/TERMO_teste01_teste001.docx
Termo de responsabilidade

O termo é gerado a partir de:

TERMO_RESPONSABILIDADE_MODELO.docx

O modelo utiliza campos como:

{{ nome }}
{{ cpf }}
{{ login }}
{{ departamento }}
{{ cargo }}
{{ campus }}
{{ modelo }}
{{ serial }}
{{ itens_entregues }}
{{ id_chamado }}

O Python substitui esses campos pelos dados armazenados no MySQL.

O termo contém dados do colaborador e do equipamento, incluindo nome, CPF, login, departamento, cargo, campus, modelo, serial/patrimônio, itens entregues e chamado GLPI, seguindo a estrutura do termo utilizado no projeto.

Relatórios

O sistema permite gerar relatórios dos empréstimos.

Empréstimos em aberto

Apresenta informações como:

ID empréstimo
Colaborador
Tipo
Marca
Modelo
Serial
Data saída
Dias em aberto
Chamado GLPI

O relatório pode ser exportado para:

relatorio_emprestimos_abertos.xlsx
Ativos por departamento

Apresenta a quantidade de ativos atualmente emprestados agrupados por departamento.

O relatório pode ser exportado para:

relatorio_departamentos.xlsx
Instalação

Instale as dependências necessárias:

pip install mysql-connector-python
pip install docxtpl
pip install openpyxl

Ou:

python -m pip install mysql-connector-python docxtpl openpyxl
Configuração do banco

Configure os dados de acesso ao MySQL no arquivo:

conexao_mysql.py

O projeto espera que get_connection() retorne uma conexão válida com o banco.

Executando o sistema: 
- Execute:

python main.py

O menu principal disponibiliza as operações do sistema:

1 - Cadastrar ativo
2 - Registrar empréstimo
3 - Registrar devolução
4 - Listar empréstimos em aberto
5 - Listar ativos disponíveis
6 - Listar todos os ativos
7 - Gerar termo de responsabilidade
8 - Relatórios
0 - Sair

Controle de status:
- Quando um ativo é cadastrado, seu status inicial é:

disponivel

Ao registrar um empréstimo:

disponivel -> emprestado

Ao registrar a devolução:

emprestado -> disponivel

Dessa forma, um equipamento emprestado não aparece na lista de ativos disponíveis para um novo empréstimo.

Objetivo: 
- O objetivo do projeto é centralizar e simplificar o controle de equipamentos disponibilizados aos colaboradores, mantendo o histórico dos empréstimos, informações dos ativos, condições de entrega e devolução, documentação de responsabilidade e relatórios administrativos.
