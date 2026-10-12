# Verificação

Executado: 14 testes Python de dados. Log em evidencias/testes_python.txt.
Validam ausentes, NaN, faixas, rótulos, duplicados, reset temporal, lacunas,
limites, formato EI, separação sem leituras compartilhadas, preservação de saída,
classe única por janela e rejeição de janelas idênticas nos dois conjuntos.
Fixtures são sintéticas temporárias e não evidência de coleta real.

```powershell
python -m unittest discover -s testes -v
```

test_policy.cpp testa a política C++ realmente incluída pelo firmware. Não
executado: não foi localizado compilador C++ de host. Se disponível:

```powershell
g++ -std=c++11 testes/test_policy.cpp -o work/test_policy.exe
./work/test_policy.exe
```

Firmware não compilado; comunicação MQTT, leitura HC-SR04, inferência embarcada,
velocidade e parada físicas não testadas. Consulte roteiro_fisico.md.
