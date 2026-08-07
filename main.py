import socket
import struct
import random

# Configurações do servidor (Rádio Catita FM)
ip = "52.67.245.39"
porta = 50000
addr = (ip, porta)

# Criação do socket UDP
meuSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
meuSocket.settimeout(2.0)

class Conexao:
    def __init__(self, num_msg, num_conexao):
        self.num_msg = num_msg
        self.num_conexao = num_conexao
        self.conectado = False
        self.prox_byte_esperado = None

# Sorteia um ISN (número inicial de sequência)
def gerar_isn():
    inicio = 0
    fim = (1 << 24) - 1
    return random.randint(inicio, fim)

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
            conexao.num_conexao = num_conexao
            conexao.prox_byte_esperado = num_msg  # Próximo byte esperado do servidor
            conexao.conectado = True

        case 4:  # MUSIC_RESPONSE
            if num_msg == conexao.prox_byte_esperado:
                conexao.prox_byte_esperado += len(payload)
                enviarMensagem(6)  # ACK cumulativo
                return tipo, num_msg, num_conexao, payload
            else:
                # Pacote duplicado ou fora de ordem: reenvia o ACK do que já tem
                enviarMensagem(6)
                return tipo, num_msg, num_conexao, None

        case 5:  # MUSIC_RESPONSE_CONCLUDED
            if num_msg == conexao.prox_byte_esperado:
                conexao.prox_byte_esperado += len(payload)
                enviarMensagem(6)  # ACK cumulativo final

                menu_str = payload.rstrip(b"\x00").decode("utf-8", errors="ignore")
                print("\nTransferência concluída com sucesso!")
                print(menu_str)
                return tipo, num_msg, num_conexao, payload
            else:
                # Pacote fora de ordem
                enviarMensagem(6)
                return tipo, num_msg, num_conexao, None

        case 8:  # TOO_SHORT_ERR
            print("[servidor] erro: mensagem enviada pelo cliente foi muito curta (< 7 bytes).")

        case 9:  # TOO_LONG_ERR
            print("[servidor] erro: mensagem enviada pelo cliente foi muito longa (> 1007 bytes).")

        case 10:  # INVALID_CONN
            print(f"[servidor] número de conexão inválido: {num_conexao}")
            conexao.conectado = False
            
        case 11:  # INVALID_MUSIC
            print("[servidor] identificador de música inválido.")
            
        case 12:  # INVALID_MSG
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
    
    buffer_musica = bytearray()
    recebeu_algum_pacote = False
    
    while conexao.conectado:
        try:
            dados, _ = meuSocket.recvfrom(2000)
        except socket.timeout:
            if not recebeu_algum_pacote:
                print("Timeout aguardando início do download. Retransmitindo solicitação...")
                conexao.num_msg = msg_num_inicial
                enviarMensagem(3, int(opcao))
            else:
                enviarMensagem(6)
            continue

        tipo, _, _, payload = desencapsular(dados)

        if tipo == 4 and payload:
            recebeu_algum_pacote = True
            buffer_musica.extend(payload)
        elif tipo == 5 and payload is not None:
            nome_arquivo = f"musica_{opcao}.mp3"
            with open(nome_arquivo, "wb") as f:
                f.write(buffer_musica)
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
    opcao = input("Digite a opção desejada: ")
    return opcao

# Execução Principal
conexao = Conexao(gerar_isn(), 0)

conectar()

while conexao.conectado:
    opcao = menu()

    if opcao == "0":
        print("Encerrando conexão...")
        enviarMensagem(7)
        meuSocket.close()
        break

    elif opcao in ("1", "2", "3", "4"):
        baixar_musica(opcao)
    else:
        print("Opção inválida!\n")

if not conexao.conectado:
    print("Conexão encerrada pelo servidor.")
    meuSocket.close()