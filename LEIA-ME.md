# VaultVet — demonstração de 2026

Extraia esta pasta separadamente do seu programa real. Ela inclui o programa e um banco fictício pronto em data/vaultvet.db. Não copie esse banco por cima do seu banco real.

No terminal do VS Code, aberto nesta pasta:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python iniciar_demo.py
```

Se usar um ambiente virtual que já tenha as dependências, basta ativá-lo e executar python iniciar_demo.py.

A agenda contém de 5 a 10 atendimentos por dia de segunda a sábado, das 08:00 às 16:55 (dentro do expediente até 17:00), sem horários repetidos. São 313 dias e 2.367 atendimentos, média de 7,6/dia: 1.325 consultas, 382 retornos e 660 atendimentos de vacinação. Inclui 400 tutores, 589 pets, 728 doses, 260 arquivos de exames fictícios, pagamentos divididos, parcelas e pendências.

No início/agenda, selecione um dia de 2026. Nos clientes, abra os pets para ver consultas, retornos, vacinas e exames. No caixa, selecione 2026 e um mês ou todos os meses. No estoque, confira as oito vacinas, quantidades, vencimentos e custos. As consultas usam o mesmo controle de estoque do programa.

O ano inteiro está preenchido como uma simulação concluída, inclusive datas futuras. Não corresponde a atendimentos reais. Os exames são arquivos TXT claramente marcados como fictícios, sem valor clínico. Os tutores usam contatos vazios e emails no domínio inválido example.invalid.

O saldo atual de estoque é uma posição fictícia de demonstração, após reposições simuladas. O sistema não tem tabela de histórico de compras/reposições; portanto esse histórico não é apresentado. O vínculo de cada dose aplicada à consulta está registrado. O alerta de vencimento usa a data real do computador.

resumo.json contém os totais mensais. gerar_demo.py recria dados determinísticos se o banco não existir; ele recusa sobrescrever um banco existente. Para recomeçar, extraia outra cópia do ZIP.
