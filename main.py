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
        self.prox_byte_esperado = None

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
            conexao.prox_byte_esperado = num_msg  # O próximo byte esperado do SERVIDOR
            conexao.conectado = True

        case 4:  # MUSIC_RESPONSE
            if num_msg == conexao.prox_byte_esperado:
                conexao.prox_byte_esperado += len(payload)
                enviarMensagem(6)  # Envia ACK do pacote recebido
                return tipo, num_msg, num_conexao, payload
            else:
                # Pacote duplicado ou fora de ordem: reenvia ACK do que já tinha
                enviarMensagem(6)
                return tipo, num_msg, num_conexao, None

        case 5:  # MUSIC_RESPONSE_CONCLUDED
            if num_msg == conexao.prox_byte_esperado:
                conexao.prox_byte_esperado += len(payload)  # <- ESSENCIAL: contabiliza o payload
                enviarMensagem(6)  # agora sim, ACK com o valor correto e atualizado

                menu_str = payload.rstrip(b"\x00").decode("utf-8", errors="ignore")
                print("\nTransferência concluída com sucesso!")
                print(menu_str)
            else:
            # o ACK atual sem reprocessar/reimprimir nada
                enviarMensagem(6)

            return tipo, num_msg, num_conexao, payload

        case 10:  # INVALID_CONN
            print(f"[servidor] número de conexão inválido: {num_conexao}")
            conexao.conectado = False
            
        case 11:
            print("[servidor] identificador de música inválido.")
            
        case 12:
            print(f"[servidor] número de mensagem inválido. Esperado pelo servidor: {num_msg}")

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
    
    # Atualiza o num_msg apenas para pacotes que consomem bytes de sequência do cliente
    if tipo == 3:
        conexao.num_msg += 1  # MUSIC_SELECT tem 1 byte de payload


def receberMensagem():
    try:
        dados, endereço = meuSocket.recvfrom(1007)
    except socket.timeout:
        return None
    mensagem = desencapsular(dados)
    return mensagem

def baixar_musica(opcao):
    print(f"\nSolicitando música {opcao}...")
    enviarMensagem(3, int(opcao))
    
    buffer_musica = bytearray()
    
    while conexao.conectado:
        try:
            # Buffer ajustado para suportar cabeçalho + até 1000 bytes do payload
            dados, _ = meuSocket.recvfrom(2000)
        except socket.timeout:
            # Em caso de timeout de rede, reenvia o ACK atual solicitando o byte correto
            enviarMensagem(6)
            continue

        tipo, _, _, payload = desencapsular(dados)

        if tipo == 4 and payload:
            buffer_musica.extend(payload)
        elif tipo == 5:
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