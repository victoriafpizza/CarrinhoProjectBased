# Evidências e limitações

Executados: inspeção arquivos, cópia byte a byte do CSV sintético fornecido,
validação completa, geração 42 amostras EI, 14 testes Python, hashes dos originais.
Studio observado na tela de login. Não há evidência de importação/treinamento.

Correções feitas somente nas novas versões: separação dos programas de duas
placas, fechamento do controle, watchdog/validação MQTT, proteção por confirmação
dos GPIOs/modelo, rótulo manual de coleta preservado, separação/purga do dataset.
O primeiro teste Python falhou por acesso ao diretório temporário do ambiente;
foi corrigido usando work/test_tmp e os 14 testes passaram depois.

Git: o acesso inicial falhou por restrição do ambiente. A concessão de escrita
na pasta pai resolveu a criação de CP2-TinyML e o Git. Commits separados apenas
com novos arquivos CP2-TinyML; nenhum push. A pasta preexistente CP2 permanece
não rastreada como estava. Documentação de treinamento não alega execução.

Pendências: login Studio, dados reais, GPIOs, versão exata da placa/core,
treinamento, métricas, ZIP real, compilação e hardware. Não há prints inventados.
