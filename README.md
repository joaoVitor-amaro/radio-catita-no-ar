# 📻 Rádio Catita no Ar

Projeto da disciplina **Redes de Computadores I** — Centro de Informática, UFPB (2026.1).

Implementação de um serviço de entrega confiável de mensagens na **camada de aplicação**, levemente baseado no TCP (com pipelining), rodando sobre **sockets UDP puros**. O cliente se conecta a um servidor remoto, consulta uma lista de músicas disponíveis e realiza o download de uma delas de forma confiável, mesmo diante de perda de ACKs e retransmissões.

## ✨ Funcionalidades

- Estabelecimento de "conexão" (handshake `CONN_REQ` / `CONN_ACK`) com número de sequência inicial sorteado, como no TCP.
- Seleção e download de músicas via `MUSIC_SELECT` / `MUSIC_RESPONSE`, com **pipelining** (janela fixa de 50 segmentos) e **ACKs cumulativos**.
- Tratamento de mensagens duplicadas e retransmissões causadas por perda proposital de ACKs pelo servidor.
- Tratamento das mensagens de erro do servidor (`TOO_SHORT_ERR`, `TOO_LONG_ERR`, `INVALID_CONN`, `INVALID_MUSIC`, `INVALID_MSG`).
- Encerramento de conexão via `CONN_FIN`.

## 🧰 Tecnologias

- **Python 3** 
- Biblioteca `socket`

## ▶️ Como executar

```bash
python cliente.py
```

O cliente se conecta automaticamente ao servidor em `52.67.245.39:50000`. Ao iniciar, será exibido o menu com as músicas disponíveis (IDs de 1 a 4); basta digitar o número desejado para iniciar o download, ou `0` para encerrar o programa.

> Ajuste o nome do script acima (`cliente.py`) conforme o arquivo principal do repositório.

## 📄 Protocolo

Resumo do formato das mensagens (cabeçalho de 7 bytes: 1 byte de tipo + 4 bytes de número de mensagem/ACK *little-endian* + 2 bytes de número de conexão *little-endian*):

| Tipo | Código | Direção |
|---|---|---|
| CONN_REQ | 0x01 | Cliente → Servidor |
| CONN_ACK | 0x02 | Servidor → Cliente |
| MUSIC_SELECT | 0x03 | Cliente → Servidor |
| MUSIC_RESPONSE | 0x04 | Servidor → Cliente |
| MUSIC_RESPONSE_CONCLUDED | 0x05 | Servidor → Cliente |
| ACK | 0x06 | Cliente → Servidor |
| CONN_FIN | 0x07 | Cliente → Servidor |
| TOO_SHORT_ERR | 0x08 | Servidor → Cliente |
| TOO_LONG_ERR | 0x09 | Servidor → Cliente |
| INVALID_CONN | 0x0A | Servidor → Cliente |
| INVALID_MUSIC | 0x0B | Servidor → Cliente |
| INVALID_MSG | 0x0C | Servidor → Cliente |

A especificação completa está no PDF do trabalho (`Especificacao_Trabalho_Redes`).

## 👥 Autores

- João Vitor Amaro de Melo
- Gabriel Sales

## 📚 Disciplina

Redes de Computadores I — Prof. Ewerton Monteiro — 2026.1
