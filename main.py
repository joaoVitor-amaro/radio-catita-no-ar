"""
Grupo:
    João Vitor Amaro de Melo   
    Gabriel Cardoso Sales
"""
import socket
import struct
import random

# Configurações do servidor (Rádio Catita FM)
ip = "52.67.245.39"
porta = 50000
addr = (ip, porta)

meuSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
meuSocket.settimeout(2.0)


class Conexao:
    def __init__(self, num_msg, num_conexao):
        self.num_msg = num_msg
        self.num_conexao = num_conexao
        self.conectado = False
        self.prox_byte_esperado = None
        self.buffer_fora_de_ordem = {}
        self.dados_musica = bytearray()
        self.transferencia_concluida = False


def gerar_isn():
    inicio = 0
    fim = (1 << 24) - 1
    return random.randint(inicio, fim)


def processar_dados_recebidos(num_msg, payload):
    # Acumula o segmento esperado e drena o buffer se algum gap fechou
    conexao.dados_musica += payload
    conexao.prox_byte_esperado += len(payload)

    while conexao.prox_byte_esperado in conexao.buffer_fora_de_ordem:
        prox_payload = conexao.buffer_fora_de_ordem.pop(conexao.prox_byte_esperado)
        conexao.dados_musica += prox_payload
        conexao.prox_byte_esperado += len(prox_payload)


def desencapsular(dados):
    if len(dados) < 7:
        print("[erro] mensagem recebida menor que 7 bytes")
        return None, None, None, None

    cabecalho = dados[:7]
    payload = dados[7:]
    tipo, num_msg, num_conexao = struct.unpack("<BIH", cabecalho)

    match tipo:
        case 2:  # CONN_ACK
            menu_str = payload.rstrip(b"\x00").decode("utf-8", errors="ignore")
            print(menu_str)
            print("0 - Encerrar programa")
            conexao.num_conexao = num_conexao
            conexao.prox_byte_esperado = num_msg
            conexao.conectado = True

        case 4:  # MUSIC_RESPONSE
            if num_msg == conexao.prox_byte_esperado:
                processar_dados_recebidos(num_msg, payload)
            elif num_msg > conexao.prox_byte_esperado:
                if num_msg not in conexao.buffer_fora_de_ordem:
                    conexao.buffer_fora_de_ordem[num_msg] = payload
            # num_msg < prox_byte_esperado: duplicata, apenas reconfirma
            enviarMensagem(6)
            return tipo, num_msg, num_conexao, payload

        case 5:  # MUSIC_RESPONSE_CONCLUDED
            if num_msg == conexao.prox_byte_esperado:
                conexao.prox_byte_esperado += len(payload)
                menu_str = payload.rstrip(b"\x00").decode("utf-8", errors="ignore")
                print("\nTransferência concluída com sucesso!")
                print(menu_str)
                print("0 - Encerrar programa")
                conexao.transferencia_concluida = True

            enviarMensagem(6)
            return tipo, num_msg, num_conexao, payload

        case 8:
            print("[servidor] erro: mensagem enviada pelo cliente foi muito curta (< 7 bytes).")

        case 9:
            print("[servidor] erro: mensagem enviada pelo cliente foi muito longa (> 1007 bytes).")

        case 10:
            print(f"[servidor] número de conexão inválido: {num_conexao}")
            conexao.conectado = False

        case 11:
            print("[servidor] identificador de música inválido.")

        case 12:
            print(f"[servidor] número de mensagem inválido. Esperado pelo servidor: {num_msg}")
            conexao.num_msg = num_msg

    return tipo, num_msg, num_conexao, payload


def encapsular(tipo, payload=None):
    match tipo:
        case 1:  # CONN_REQ
            return struct.pack("<BIH", tipo, conexao.num_msg, 0)

        case 3:  # MUSIC_SELECT
            cabecalho = struct.pack("<BIH", tipo, conexao.num_msg, conexao.num_conexao)
            return cabecalho + struct.pack("<B", payload)

        case 6:  # ACK cumulativo
            return struct.pack("<BIH", tipo, conexao.prox_byte_esperado, conexao.num_conexao)

        case 7:  # CONN_FIN
            return struct.pack("<BIH", tipo, conexao.num_msg, conexao.num_conexao)

        case _:
            print(f"[erro interno] tipo desconhecido: {tipo}")
            return None


def enviarMensagem(tipo, payload=None):
    segmento = encapsular(tipo, payload)
    if segmento is None:
        return
    meuSocket.sendto(segmento, addr)

    if tipo == 3:
        conexao.num_msg += 1  # MUSIC_SELECT consome 1 byte de sequência


def receberMensagem():
    try:
        dados, _ = meuSocket.recvfrom(1007)
    except socket.timeout:
        return None
    return desencapsular(dados)


def baixar_musica(opcao):
    print(f"\nSolicitando música {opcao}...")

    msg_num_inicial = conexao.num_msg
    enviarMensagem(3, int(opcao))

    conexao.dados_musica = bytearray()
    conexao.buffer_fora_de_ordem = {}
    conexao.transferencia_concluida = False

    recebeu_algum_pacote = False

    while conexao.conectado:
        resultado = receberMensagem()

        if resultado is None:
            if not recebeu_algum_pacote:
                print("Timeout aguardando início do download. Retransmitindo solicitação...")
                conexao.num_msg = msg_num_inicial
                enviarMensagem(3, int(opcao))
            continue

        tipo, num_msg, num_conexao, payload = resultado

        if tipo == 4:
            recebeu_algum_pacote = True

        elif tipo == 5:
            if conexao.transferencia_concluida:
                nome_arquivo = f"musica_{opcao}.mp3"
                with open(nome_arquivo, "wb") as f:
                    f.write(conexao.dados_musica)
                print(f"Arquivo salvo como: {nome_arquivo}\n")
                break

        elif tipo in (8, 9, 10, 11, 12):
            break


def conectar():
    print("Conectando ao servidor...")
    tentativas = 0
    while tentativas < 5:
        enviarMensagem(1)  # CONN_REQ
        resposta = receberMensagem()
        if resposta is not None:
            return
        print("Timeout, tentando novamente...")
        tentativas += 1
    print("Não foi possível conectar após várias tentativas.")


def menu():
    return input("Digite a opção desejada: ")

conexao = Conexao(gerar_isn(), 0)

conectar()

while conexao.conectado:
    opcao = menu()

    if opcao == "0":
        print("Encerrando conexão...")
        enviarMensagem(7)  # CONN_FIN
        meuSocket.close()
        break

    elif opcao in ("1", "2", "3", "4"):
        baixar_musica(opcao)

    else:
        print("Opção inválida!\n")

if not conexao.conectado:
    print("Conexão encerrada pelo servidor.")
    meuSocket.close()