# 📑 Model Card — Previsão de Volume de Água (ENA)

## 1. Objetivo do Modelo
Prever o **volume de água armazenado em reservatórios**  
com base em séries históricas diárias disponibilizadas pelo ONS, permitindo consultas  
de previsão em um horizonte futuro definido.

---

## 2. Contexto de Uso
- **Aplicação:** endpoint `/v1/predictions/reservatorios/{id}?date=YYYY-MM-DD` na API do projeto.  
- **Restrições:** previsão feita por reservatório, sem uso de variáveis exógenas (ex.: clima).  

---

## 3. Dados de Treino
- Fontes:
 [ONS — ENA Diário por Reservatório](https://dados.ons.org.br/dataset/ena-diario-por-reservatorio) 
 [ONS - Reservatórios](https://dados.ons.org.br/dataset/reservatorio)
- Período disponível: **2000–2025** (variando por reservatório).  
- Frequência: **diária**.  
- Variável alvo: `vol_agua`  

---

## 4. Métrica de Avaliação
- **Primária:** MAE (Mean Absolute Error)  
- **Secundária:** RMSE, MAPE.  

## 5. Janela de Treino/Validação
- Treino: **2015–2024**  
- Validação/Teste: **2024-2025**  

---

## 6. Riscos e Limitações
- Reservatórios sem usina → dados energéticos frequentemente NaN(filtrados).  
- Sazonalidade complexa (clima, chuvas) não explicitamente modelada.  

---

## 7. Assunções
- Dados fornecidos pelo ONS são consistentes e auditáveis.  
- O modelo é avaliado apenas sobre o histórico já disponível (sem variáveis externas).  
- Todos os reservatórios considerados têm séries válidas (com variação > 1 valor).  
