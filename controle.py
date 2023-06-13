import face_recognition as reconhecedor
import colored
import secrets
import random
import simpy
import json

FOTOS_VISITANTES = [
    "faces/visitantes1.jpg",
    "faces/visitantes2.jpg",
    "faces/visitantes3.jpg"
]

ARQUIVO_DE_CONFIGURACAO = "configuracao.json"
TEMPO_MEDIO_DE_PERMANENCIA = 80
TEMPO_DE_DETECCAO_DE_ALUNOS = 40
TEMPO_DE_SAIDA_DE_ALUNOS = 60


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

    print("Realizando reconhecimento dos alunos...")
    foto_visitantes = reconhecedor.load_image_file(visitantes["foto"])
    caracteristicas_dos_visitantes = reconhecedor.face_encodings(
        foto_visitantes)
    # localizacoes_faces_desconhecidas = reconhecedor.face_locations(foto_visitantes)

    alunos = []
    # num_faces_desconhecidas = len(localizacoes_faces_desconhecidas)  # Inicializa com a quantidade de faces desconhecidas

    for aluno in configuracao["alunos"]:
        if not alunos_previamente_reconhecidos(aluno):
            fotos = aluno["fotos"]
            num_faces_reconhecidas = 0

            for foto in fotos:
                foto_aluno = reconhecedor.load_image_file(foto)
                caracteristicas_aluno = reconhecedor.face_encodings(foto_aluno)

                if len(caracteristicas_aluno) > 0:
                    reconhecimentos = reconhecedor.compare_faces(
                        caracteristicas_dos_visitantes, caracteristicas_aluno[0])
                    if True in reconhecimentos:
                        num_faces_reconhecidas += 1

            if num_faces_reconhecidas / len(fotos) >= 0.6:
                alunos.append(aluno)
                # num_faces_desconhecidas = len(localizacoes_faces_desconhecidas) - num_faces_reconhecidas

    # print("Quantidade de rostos não conhecidos:", num_faces_desconhecidas)

    return len(alunos) > 0, alunos


def barrar_intruso(visitantes, alunos):
    print("Detectando intrusos...")
    foto_visitantes = reconhecedor.load_image_file(visitantes["foto"])
    localizacoes_faces_desconhecidas = reconhecedor.face_locations(
        foto_visitantes)

    # Inicializa com a quantidade de faces desconhecidas
    num_faces_desconhecidas = len(localizacoes_faces_desconhecidas)

    num_faces_desconhecidas = len(
        localizacoes_faces_desconhecidas) - len(alunos)
    print(colored.fg('black'), colored.bg(
        'red'), f"Quantidade de pessoas barradas:  {num_faces_desconhecidas}", colored.attr('reset'))
    print(colored.fg('black'), colored.bg(
        'red'), f"Em: {ambiente_de_simulacao.now}", colored.attr('reset'))

    return num_faces_desconhecidas


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
                aluno["na_instituicao"] = False

                id_entrada = secrets.token_hex(nbytes=16).upper()
                alunos_reconhecidos[id_entrada] = aluno

                imprimir_dados_do_aluno(aluno)

        barrar_intruso(visitantes, alunos)

        yield ambiente_de_simulacao.timeout(TEMPO_DE_DETECCAO_DE_ALUNOS)


def imprimir_dados_do_aluno(aluno):
    print(colored.fg('black'), colored.bg(
        'blue'), f"aluno reconhecido em {ambiente_de_simulacao.now}", colored.attr('reset'))
    print(colored.fg('black'), colored.bg(
        'blue'), f"nome: {aluno['nome']}", colored.attr('reset'))
    print(colored.fg('black'), colored.bg(
        'blue'), f"curso: {aluno['curso']}", colored.attr('reset'))


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


def contar_alunos_na_instituicao():
    global alunos_reconhecidos

    alunos_na_instituicao = 0
    for aluno in alunos_reconhecidos.values():
        if aluno["na_instituicao"]:
            alunos_na_instituicao += 1

    return alunos_na_instituicao


if __name__ == "__main__":
    preparar()

    ambiente_de_simulacao = simpy.Environment()
    ambiente_de_simulacao.process(reconhecer_visitantes(ambiente_de_simulacao))
    ambiente_de_simulacao.process(saida_de_alunos(ambiente_de_simulacao))
    ambiente_de_simulacao.run(until=1000)
