import face_recognition as reconhecedor
import colored
import secrets
import random
import simpy
import json

FOTOS_VISITANTES = [
    "faces/visitantes.jpg",
    "faces/visitantes2.jpg",
    "faces/visitantes3.jpg"
]
ARQUIVO_DE_CONFIGURACAO = "configuracao.json"

TOTAL_DE_LEITOS_DE_UTI = 10

PROBABILIDADE_DE_LIBERACAO = 30
PROBABILIDADE_DE_SER_EMERGENCIA = 10
PROBABILIDADE_DE_ENVIO_PARA_UTI = 10
PROBABILIDADE_DE_LIBERACAO_DA_UTI = 40

TEMPO_MEDIO_DE_PERMANENCIA = 80
TEMPO_MEDIO_DE_PERMANENCIA_EM_UTI = 60

TEMPO_DE_DETECCAO_DE_ALUNOS = 40
TEMPO_DE_SAIDA_DE_ALUNOS = 60
TEMPO_DE_DETECCAO_DE_EMERGENCIAS = 20
TEMPO_DE_DETECCAO_DE_ENVIO_PARA_UTI = 40
TEMPO_DE_DETECCAO_DE_LIBERACAO_DA_UTI = 100

# ler configuracoes e preparar estruturas de dados


def preparar():
    global configuracao

    configuracao = None
    try:
        with open(ARQUIVO_DE_CONFIGURACAO, "r") as arquivo:
            configuracao = json.load(arquivo)
            if configuracao:
                print("*---Carregado os aquivos de configuração!---*")
            arquivo.close()
    except Exception as e:
        print(f"--> erro ao fazer a leitura do: {str(e)}")

    global alunos_reconhecidos
    alunos_reconhecidos = {}


def simular_visitas():
    foto = random.choice(FOTOS_VISITANTES)
    print(f"--foto de visitantes: {foto}")

    visitantes = {
        "foto": foto,
        "alunos": None
    }

    return visitantes


def alunos_previamente_reconhecidos(aluno):
    global alunos_reconhecidos

    reconhecido_previamente = False
    for reconhecido in alunos_reconhecidos.values():
        if aluno["codigo"] == reconhecido["codigo"]:
            reconhecido_previamente = True

            break

    return reconhecido_previamente


def reconhecer_alunos(visitantes):
    global configuracao

    print("realizando reconhecimento dos alunos...")
    foto_visitantes = reconhecedor.load_image_file(visitantes["foto"])
    caracteristicas_dos_visitantes = reconhecedor.face_encodings(
        foto_visitantes)

    alunos = []
    for aluno in configuracao["alunos"]:
        if not alunos_previamente_reconhecidos(aluno):
            fotos = aluno["fotos"]
            total_de_reconhecimentos = 0

            for foto in fotos:
                foto = reconhecedor.load_image_file(foto)
                caracteristicas = reconhecedor.face_encodings(foto)[0]

                reconhecimentos = reconhecedor.compare_faces(
                    caracteristicas_dos_visitantes, caracteristicas)
                if True in reconhecimentos:
                    total_de_reconhecimentos += 1

            if total_de_reconhecimentos/len(fotos) >= 0.6:
                alunos.append(aluno)
        else:
            print("aluno reconhecido previamente")

    return (len(alunos) > 0), alunos


def imprimir_dados_do_aluno(aluno):
    print(colored.fg('black'), colored.bg(
        'blue'), f"aluno reconhecido em {ambiente_de_simulacao.now}", colored.attr('reset'))
    print(colored.fg('black'), colored.bg(
        'blue'), f"nome: {aluno['nome']}", colored.attr('reset'))
    print(colored.fg('black'), colored.bg(
        'blue'), f"curso: {aluno['curso']}", colored.attr('reset'))

# captura uma foto de visitantes e reconhece se tem pacientes
# entre eles


def reconhecer_visitantes(ambiente_de_simulacao):
    global alunos_reconhecidos

    while True:
        print(
            f"--Tentando reconhecer um aluno entre visitantes em {ambiente_de_simulacao.now}")

        visitantes = simular_visitas()
        ocorreram_reconhecimentos, alunos = reconhecer_alunos(visitantes)
        if ocorreram_reconhecimentos:
            for aluno in alunos:
                aluno["tempo_para_liberacao"] = ambiente_de_simulacao.now + \
                    TEMPO_MEDIO_DE_PERMANENCIA
                # aluno["em_emergencia"] = False
                aluno["na_instituicao"] = False

                id_entrada = secrets.token_hex(nbytes=16).upper()
                alunos_reconhecidos[id_entrada] = aluno

                imprimir_dados_do_aluno(aluno)

        yield ambiente_de_simulacao.timeout(TEMPO_DE_DETECCAO_DE_ALUNOS)


# identifica pacientes que podem ser liberados
# nao pode liberar quem estah em uti
def saida_de_alunos(ambiente_de_simulacao):
    global alunos_reconhecidos

    while True:
        print(
            f"--Alunos saindo em: {ambiente_de_simulacao.now}")

        if len(alunos_reconhecidos):
            for id_entrada, aluno in list(alunos_reconhecidos.items()):
                if not aluno["na_instituicao"] and ambiente_de_simulacao.now >= aluno["tempo_para_liberacao"]:
                    aluno_liberado = (random.randint(
                        1, 100)) <= PROBABILIDADE_DE_LIBERACAO
                    if aluno_liberado:
                        alunos_reconhecidos.pop(id_entrada)
                        print(colored.fg('white'), colored.bg('green'),
                              f"saida de aluno {aluno['nome']} em {ambiente_de_simulacao.now}", colored.attr('reset'))

        yield ambiente_de_simulacao.timeout(TEMPO_DE_SAIDA_DE_ALUNOS)

# elege entre os pacientes aqueles q estao em situacao critica


# def identificar_emergencia(ambiente_de_simulacao):
#     global alunos_reconhecidos

#     while True:
#         print(
#             f"tentando identificar uma emergência em {ambiente_de_simulacao.now}")

#         if len(alunos_reconhecidos):
#             for id_entrada, paciente in list(alunos_reconhecidos.items()):
#                 if not paciente["em_emergencia"]:
#                     emergencia_reconhecida = (random.randint(
#                         1, 100) <= PROBABILIDADE_DE_SER_EMERGENCIA)
#                     if emergencia_reconhecida:
#                         alunos_reconhecidos[id_entrada]["em_emergencia"] = True
#                         print(colored.fg('white'), colored.bg('blue'),
#                               f"paciente {paciente['nome']} em situação de emergência em {ambiente_de_simulacao.now}", colored.attr('reset'))

#         yield ambiente_de_simulacao.timeout(TEMPO_DE_DETECCAO_DE_EMERGENCIAS)


def contar_alunos_na_instituicao():
    global alunos_reconhecidos

    alunos_na_instituicao = 0
    for aluno in alunos_reconhecidos.values():
        if aluno["na_instituicao"]:
            alunos_na_instituicao += 1

    return alunos_na_instituicao

# se paciente estiver em situacao de emergencia, identifica se
# ele precisa ser transferido para a uti
# nao pode enviar paciente se a capacidade maxima for extrapolada


# def reservar_uti(ambiente_de_simulacao):
#     global alunos_reconhecidos

#     while True:
#         print(
#             f"tentando identificar uma transferência para a UTI em {ambiente_de_simulacao.now}")

#         if len(alunos_reconhecidos) and contar_alunos_na_instituicao() >= TOTAL_DE_LEITOS_DE_UTI:
#             print(
#                 f"capacidade maxima de uti ultrapassada em {ambiente_de_simulacao.now}")
#         else:
#             for paciente in alunos_reconhecidos.values():
#                 if paciente["em_emergencia"] and not paciente["na_instituicao"]:
#                     enviar_para_uti = (random.randint(
#                         1, 100)) <= PROBABILIDADE_DE_ENVIO_PARA_UTI
#                     if enviar_para_uti:
#                         paciente["tempo_para_liberacao_da_uti"] = ambiente_de_simulacao.now + \
#                             TEMPO_MEDIO_DE_PERMANENCIA_EM_UTI
#                         paciente["na_instituicao"] = True
#                         print(colored.fg('white'), colored.bg(
#                             'red'), f"paciente {paciente['nome']} enviado para a uti em {ambiente_de_simulacao.now}", colored.attr('reset'))

#         yield ambiente_de_simulacao.timeout(TEMPO_DE_DETECCAO_DE_ENVIO_PARA_UTI)

# libera um paciente que ocupa um leito de uti


# def liberar_leito_da_uti(ambiente_de_simulacao):
#     global alunos_reconhecidos

#     while True:
#         print(
#             f"tentando identificar uma liberação de UTI em {ambiente_de_simulacao.now}")

#         if len(alunos_reconhecidos):
#             for paciente in alunos_reconhecidos.values():
#                 if paciente["na_instituicao"] and ambiente_de_simulacao.now >= paciente["tempo_para_liberacao_da_uti"]:
#                     paciente_liberado = (random.randint(
#                         1, 100)) <= PROBABILIDADE_DE_LIBERACAO_DA_UTI
#                     if paciente_liberado:
#                         paciente["na_instituicao"] = False
#                         print(colored.fg('white'), colored.bg(
#                             'green'), f"paciente {paciente['nome']} liberado da uti em {ambiente_de_simulacao.now}", colored.attr('reset'))

#         yield ambiente_de_simulacao.timeout(TEMPO_DE_DETECCAO_DE_LIBERACAO_DA_UTI)


if __name__ == "__main__":
    preparar()

    ambiente_de_simulacao = simpy.Environment()
    ambiente_de_simulacao.process(reconhecer_visitantes(ambiente_de_simulacao))
    ambiente_de_simulacao.process(saida_de_alunos(ambiente_de_simulacao))
    # ambiente_de_simulacao.process(
    #     identificar_emergencia(ambiente_de_simulacao))
    # ambiente_de_simulacao.process(reservar_uti(ambiente_de_simulacao))
    # ambiente_de_simulacao.process(liberar_leito_da_uti(ambiente_de_simulacao))
    ambiente_de_simulacao.run(until=1000)
