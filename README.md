# QuickPizza — k6

[English version](README.en.md)

Smoke de performance e contrato contra **https://quickpizza.grafana.com**, aplicação hospedada da Grafana para aprender k6. Um usuário virtual, três iterações, nove requisições. Não é um teste de stress.

## Execução

k6 **2.3.0** e Python **3.12+** (somente para validar o relatório). Não há dependências Python ou servidor local.

```bash
cp .env.example .env
set -a; source .env; set +a
mkdir -p results
k6 run tests/smoke.js
python ci_summary.py
```

No PowerShell, copie `.env.example` para `.env` e exporte os dois valores com `$env:BASE_URL` e `$env:DEMO_TOKEN` antes de executar os mesmos comandos k6/Python. k6 não carrega `.env` automaticamente. O token do exemplo é público, publicado nos exemplos oficiais; não é credencial privada. Não use tokens reais nesta demo.

O script aceita apenas a URL da demo. Aumentar carga ou trocar o alvo exige revisar código, autorização e orçamento. A configuração fixa impede transformar o smoke acidentalmente em carga alta.

## Cenários

| Operação | O que precisa acontecer |
| --- | --- |
| Vegetariana | HTTP 200, JSON, identidade e ingredientes válidos, todos vegetarianos, até 500 calorias por fatia |
| Restrições | Mesmas verificações de contrato, sem Pepperoni e sem Knife, até 500 calorias por fatia |
| Sem token | HTTP 401, erro de autenticação e ausência de pizza |

São 12 checks repetidos três vezes: **36 verificações**. As exclusões usam nomes exatos do catálogo: a implementação compara strings com distinção entre maiúsculas e minúsculas. A pausa de um segundo entre operações limita a frequência; não é espera para esconder instabilidade. Não há retries.

O POST de recomendação grava a pizza no histórico da própria demo, como nos exemplos oficiais. Não criamos contas nem avaliações, e não apagamos histórico compartilhado. Os nomes e IDs das pizzas são dinâmicos; verificamos propriedades, não uma resposta aleatória específica.

## Critério de bloqueio

- Todos os checks precisam passar; respostas inesperadas reprovam. O 401 é esperado apenas na operação sem token.
- Exatamente nove requisições e três iterações; execução interrompida não passa.
- Cada uma das três operações deve ficar abaixo de **3000 ms no máximo**.

Os 3000 ms são um orçamento didático escolhido para identificar travamentos evidentes em um smoke de demo, não SLA do serviço. Com três amostras por operação, não estimamos capacidade, p95 de produção ou ganho de performance. Infraestrutura pública, rede e cold starts podem afetar a medição. Uma falha exige conferir operação, checks e latência antes de atribuir defeito ao serviço; não aumente o limite só para obter verde.

## CI e resultados

[Actions](https://github.com/brunobaccari/k6-api-performance/actions) executa a mesma carga em pushes, PRs e execução manual, com uma run por vez. O exit code nativo do k6 é preservado. O gate adicional rejeita JSON ausente/inválido, contagens incompletas e thresholds reprovados.

O Summary mostra checks por operação, thresholds e média/máximo observados. O artifact `k6-results` contém `k6-summary.json` e `summary.md`, inclusive em falhas, por 30 dias. Relatórios e `.env` ficam fora do Git; corpos HTTP e tokens não são exportados.

Para verificar o gate sem fazer chamadas:

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

## Referências

- [QuickPizza e exemplos oficiais](https://github.com/grafana/quickpizza)
- [Implementação das restrições](https://github.com/grafana/quickpizza/blob/main/pkg/http/http.go)
- [Thresholds no k6](https://grafana.com/docs/k6/latest/using-k6/thresholds/)
- [Custom summary](https://grafana.com/docs/k6/latest/results-output/end-of-test/custom-summary/)

Referências verificadas em 06/10/2026. O antigo `test-api.k6.io` redirecionava para QuickPizza; esta suíte usa o alvo atual diretamente.
