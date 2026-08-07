import socket
import struct
import random

#Endereço IP da melhor forma (do Servidor Catita)
ip = "52.67.245.39"
porta = 50000
addr = ip, porta

#Socket criado
meuSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
meuSocket.settimeout(2.0)

class Conexao:
    def __init__(self, num_msg, num_conexao):
        self.num_msg = num_msg
        self.num_conexao = num_conexao
        self.conectado = False

#tentar algo com o struct
def gerar_isn():
    inicio = 0
    fim = (1 << 24) - 1
    return random.randint(inicio, fim)

def enumeradorDeMensagem(tamanho_payload):
    conexao.num_msg += tamanho_payload

def criarCabecalho(tipo):
    num_conexao = conexao.num_conexao 
    num_msg = conexao.num_msg
    cabecalho = struct.pack("<BIH", tipo, num_msg, num_conexao)
    return cabecalho

def desencapsular (dados):

    if len(dados) < 7:
        print("[erro] mensagem recebida menor que o cabeçalho mínimo (7 bytes)")
        return None
 
    cabecalho = dados[:7]
    payload = dados[7:]
    tipo, num_msg, num_conexao = struct.unpack("<BIH", cabecalho)
 
    match tipo:
        case 2:  # CONN_ACK
            menu_str = payload.rstrip(b"\x00").decode("utf-8")
            print(menu_str)
 
            # Salva o número de conexão definido pelo servidor. Sem isso,
            conexao.num_conexao = num_conexao
            conexao.conectado = True
 
        case 5:  # MUSIC_RESPONSE_CONCLUDED
            menu_str = payload.rstrip(b"\x00").decode("utf-8")
            print("\nTransferência concluída!\n")
            print(menu_str)
 
        case 8:  # TOO_SHORT_ERR
            print("[servidor] a última mensagem enviada foi curta demais.")
 
        case 9:  # TOO_LONG_ERR
            print("[servidor] a última mensagem enviada foi longa demais.")
 
        case 10:  # INVALID_CONN
            print(f"[servidor] número de conexão inválido: {num_conexao}")
            conexao.conectado = False
 
        case 11:  # INVALID_MUSIC
            print("[servidor] identificador de música inválido (use 1 a 4).")
 
        case 12:  # INVALID_MSG
            print(f"[servidor] número de mensagem inválido. Esperado: {num_msg}")
 
        case _:
            print(f"[erro] tipo de mensagem não tratado ainda: {tipo}")
 
    return tipo, num_msg, num_conexao, payload
 



def encapsular (tipo, payload=None):
        match tipo:
            case 1:  # CONN_REQ sem payload, só os 7 bytes de cabeçalho
                cabecalho = criarCabecalho(tipo)
                return cabecalho
            case 3:  # MUSIC_SELECT payload de 1 byte com o id da música
                cabecalho = criarCabecalho(tipo)
                segmento = cabecalho + struct.pack("<B", payload)
                return segmento
            case 7:  # CONN_FIN sem payload
                cabecalho = criarCabecalho(tipo)
                return cabecalho
            case _:
                print(f"[erro interno] tentativa de montar tipo desconhecido: {tipo}")
                return None


def enviarMensagem(tipo, payload=None):
    segmento = encapsular(tipo, payload)
    if segmento is None:
        return
    meuSocket.sendto(segmento, addr)
    tamanho_payload = len(segmento) - 7 
    enumeradorDeMensagem(tamanho_payload)

def receberMensagem():
    try:
        dados, endereço = meuSocket.recvfrom(1007)
    except socket.timeout:
        return None
    mensagem = desencapsular(dados)
    return mensagem

def conectar():
    print("Conectando ao servidor...")
    tentativas = 0
    while tentativas < 5:
        enviarMensagem(1)          # CONN_REQ
        resposta = receberMensagem()
        if resposta is not None:
            return
        print("Timeout, tentando novamente...")
        tentativas += 1
    print("Não foi possível conectar após várias tentativas.")


def menu():
    opcao = input("Digite a opção desejada: ")
    return opcao

conexao = Conexao(gerar_isn(), 0)

conectar()

while conexao.conectado:
    opcao = menu()

    if opcao == "0":
        print("Encerrando...")
        enviarMensagem(7)
        meuSocket.close()
        break

    elif opcao in ("1", "2", "3", "4"):
        print(f"Você escolheu a música {opcao}")
        enviarMensagem(3, int(opcao))
        receberMensagem()
    else:
        print("Opção inválida!\n")

if not conexao.conectado:
    print("Conexão encerrada pelo servidor.")
    meuSocket.close()