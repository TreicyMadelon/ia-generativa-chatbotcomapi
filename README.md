# Chatbot Literário com API Generativa

> Um experimento utilizando a API do Google Gemini para construção de um chatbot especializado no mercado literário brasileiro, com foco em confiabilidade, contexto e redução de alucinações.

## Sobre o projeto

Este projeto explora a construção de um chatbot especializado utilizando uma **API externa de IA generativa** para responder perguntas sobre o mercado editorial brasileiro.

O principal objetivo foi investigar como transformar um modelo de propósito geral em um assistente mais confiável para um domínio específico, reduzindo comportamentos indesejados e aumentando a consistência das respostas.

Mais do que consumir uma API de linguagem, o desafio consistiu em desenvolver uma camada de controle capaz de orientar o modelo durante toda a conversa.

---

## Objetivos

* Integrar uma API externa de IA generativa;
* Construir um chatbot especializado em literatura e mercado editorial brasileiro;
* Manter contexto entre múltiplas interações;
* Padronizar o formato das respostas;
* Reduzir alucinações e respostas inconsistentes.

---

## Stack

* Python
* Google Gemini API
* Logging
* Dataclasses
* Controle de contexto e histórico de conversas

---

## Arquitetura

O projeto utiliza a API do Google Gemini como mecanismo de geração de linguagem, enquanto a aplicação atua como uma camada intermediária responsável por controlar o comportamento do modelo.

Entre as responsabilidades implementadas estão:

* gerenciamento de histórico da conversa;
* enriquecimento de contexto;
* instruções sistêmicas (System Prompt);
* hooks de pré e pós-processamento;
* validação do fluxo conversacional;
* tratamento de exceções e respostas de fallback.

Essa abordagem reduz a dependência exclusiva do modelo e permite um comportamento mais previsível.

---

## O principal desafio

O maior desafio deste projeto foi lidar com um dos problemas inerentes aos modelos generativos: **as alucinações**.

Embora os modelos atuais possuam excelente capacidade de geração de texto, eles ainda podem produzir respostas incorretas, assumir informações como verdade ou responder com excesso de confiança sobre fatos inexistentes.

Em um chatbot especializado, esse comportamento compromete diretamente a credibilidade da aplicação.

Por esse motivo, grande parte do desenvolvimento foi dedicada não apenas à integração da API, mas à implementação de mecanismos para mitigar esse risco.

---

## Estratégias utilizadas

Para aumentar a confiabilidade das respostas, foram adotadas diversas abordagens diretamente no código da aplicação:

* uso de uma instrução sistêmica robusta para restringir o domínio de atuação;
* gerenciamento explícito do histórico da conversa;
* enriquecimento de contexto antes do envio das mensagens ao modelo;
* perguntas de afunilamento para solicitações ambíguas;
* controle de contexto pendente entre múltiplas interações;
* validações antes e depois das chamadas à API;
* padronização das respostas para recomendações literárias;
* tratamento de erros e respostas de fallback.

Essas estratégias não eliminam completamente a possibilidade de alucinação, mas reduzem significativamente sua ocorrência e tornam o comportamento do chatbot mais consistente.

---

## Aprendizados

O desenvolvimento evidenciou que integrar uma API de IA generativa é apenas uma parte da solução.

Na prática, aplicações que dependem de modelos de linguagem precisam de uma camada adicional de engenharia responsável por controlar contexto, validar entradas, restringir domínio e orientar o comportamento do modelo.

Quanto maior a especialização esperada da aplicação, maior tende a ser a importância dessa camada intermediária.

---

## Executando

1. Instale as dependências.

```bash
pip install google-generativeai
```

2. Configure a variável de ambiente:

```bash
GEMINI_API_KEY=<sua_chave>
```

3. Execute:

```bash
python chatbotcomapi.py
```

---

## Considerações finais

Este projeto serviu como um estudo sobre o desenvolvimento de aplicações baseadas em modelos generativos utilizando APIs externas.

Além da integração com o modelo, o foco esteve na criação de mecanismos que reduzissem respostas inconsistentes e aumentassem a previsibilidade da aplicação, demonstrando que a qualidade de um chatbot especializado depende tanto da engenharia ao redor do modelo quanto do próprio modelo de IA.
