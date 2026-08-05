import socket
import struct
import random

#Endereço IP da melhor forma (do Servidor Catita)
ip = "52.67.245.39"
porta = 50000
addr = ip, porta

#Socket criado
meuSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

class Conexao:
    def __init__(self, num_msg, num_conexao):
        self.num_msg = num_msg
        self.num_conexao = num_conexao

#tentar algo com o struct
def gerar_isn():
    inicio = 0
    fim = (1 << 24) - 1
    return random.randint(inicio, fim)

def enumeradorDeMensagem(payload):
    quant_bytes = len(payload)
    conexao.num_msg += quant_bytes

def criarCabecalho(tipo):
    num_conexao = conexao.num_conexao 
    num_msg = conexao.num_msg

    cabecalho = struct.pack("BIH", tipo, num_msg, num_conexao)
    return cabecalho

def desencapsular (dados):

    mensagem = dados[:7]
    tipo, num_msg, num_conexao = struct.unpack("!BIH", mensagem)

    match tipo:
        case 2:
            print(dados[7:].decode("utf-8"))
        case _:
            print("Opção inválida")


def encapsular (tipo, payload=None):

    match tipo: 
        case 1:
            cabecalho = criarCabecalho(tipo)
            print(struct.unpack("BIH", cabecalho))
            dados = struct.pack("H", 0)
            segmento = cabecalho + dados
            enumeradorDeMensagem(dados)
            return segmento
        case 3: 
            cabecalho = criarCabecalho(tipo)
            segmento = cabecalho + struct.pack("B", payload)
            return segmento

def enviarMensagem(tipo, payload=None):
    segmento = encapsular(tipo, payload)
    meuSocket.sendto(segmento, addr)

def receberMensagem():
    dados, endereço = meuSocket.recvfrom(1007)
    mensagem = desencapsular(dados)
    return mensagem

#Vamos lidar com o user
def menu():
    opcao = input("Digite a opção desejada: ")
    return opcao

conexao = Conexao(gerar_isn(), 0)

while True:
    opcao = menu()

    if opcao == "0":
        print("Encerrando...")
        meuSocket.close()
        break

    elif opcao in ("1", "2", "3", "4"):
        print(f"Você escolheu a música {opcao}")
        enviarMensagem(int(opcao))
        receberMensagem()

    else:
        print("Opção inválida!\n")