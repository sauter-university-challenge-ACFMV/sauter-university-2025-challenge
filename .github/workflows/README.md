
# Guia de CI/CD – Sauter University 2025

> Este guia explica como funciona o processo de CI/CD utilizando workflows YAML no GitHub Actions, seguindo o padrão do repositório e integrando boas práticas de automação, validação e deploy. O objetivo é garantir que qualquer pessoa do time consiga **entender, executar e evoluir** os pipelines de entrega contínua de forma segura e automatizada.

---

## 1) Visão geral

* **Plataforma:** GitHub Actions
* **Objetivo:** Automatizar validação, testes e deploy de aplicações, scripts ou infraestrutura.
* **Processo:**
  * **Validação:** Checagem automática de código, testes e padrões em cada Pull Request (PR).
  * **Deploy:** Aplicação dos artefatos aprovados no ambiente de destino (ex: dev, prod).
  * **Segurança:** Uso de segredos e autenticação federada (ex: WIF) para acesso seguro a recursos externos.

---

## 2) Estrutura do repositório

```
.github/
  workflows/
    ci.yml           # CI (validação, mypy, testes)
    cd.yml           # CD (deploy automatizado)
    iac-dev.yaml     # CI/CD da infraestrutura (Terraform)
```

---

## 3) Fluxo CI/CD detalhado

### 3.1 CI – Validação e Testes

- **Quando roda:**
  - Em todo Pull Request (PR) ou push para branches de feature.
- **O que faz:**
  - Valida se tá tipado (mypy) e  executa testes automatizados.


### 3.2 CD – Deploy Automatizado

- **Quando roda:**
  - Em merge para a branch principal (`main`) ou branch de release.
- **O que faz:**
  - Autentica no ambiente de destino cloud.
  - Executa deploy dos artefatos aprovados (aplicação, scripts, infraestrutura).

---

## 4) Boas práticas

- **Validação automática:** Nunca faça deploy sem passar pelo CI.
- **Segurança:** Use WIF e nunca exponha credenciais no repositório.
- **Logs:** Mantenha logs de deploy acessíveis para troubleshooting.
- **Idempotência:** Scripts e deploys devem ser seguros para múltiplas execuções.

---

## 5) Troubleshooting (erros comuns)

- **Falha de autenticação:** Verifique configurações do WIF e permissões da Service Account.
- **Erro de sintaxe:** Corrija o código conforme apontado pelo CI.
- **Deploy parcial:** Certifique-se de que todos os artefatos necessários estão incluídos no deploy.

---

## 6) Referências

- [GitHub Actions Docs](https://docs.github.com/actions)
  

---
*Atualizado por: Clauderson Branco Xavier.*
