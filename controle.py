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
PROBABILIDADE_DE_LIBERACAO = 70
TEMPO_MEDIO_DE_PERMANENCIA = 80
TEMPO_DE_DETECCAO_DE_ALUNOS = 40
TEMPO_DE_DETECCAO_DE_INTRUSOS = 40
TEMPO_DE_SAIDA_DE_ALUNOS = 60
PROBABILIDADE_IR_AO_REFEITORIO = 40
PROBABILIDADE_DE_LIBERACAO_DO_REFEITORIO = 40
TEMPO_DE_IR_AO_REFEITORIO = 40
TEMPO_DO_REFEITORIO = 40


def preparar():
    global configuracao

    configuracao = None
    try:
        with open(ARQUIVO_DE_CONFIGURACAO, "r", encoding='utf-8') as arquivo:
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
        "alunos": None,
        "intrusos": None
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

    alunos = []

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

    return len(alunos) > 0, alunos


def reconhecer_intrusos(visitantes):
    global configuracao

    print("Realizando reconhecimento dos intrusos...")
    foto_visitantes = reconhecedor.load_image_file(visitantes["foto"])
    caracteristicas_dos_visitantes = reconhecedor.face_encodings(
        foto_visitantes)

    intrusos = []

    for intruso in configuracao["intrusos"]:

        fotos = intruso["fotos"]
        num_faces_reconhecidas = 0

        for foto in fotos:
            foto_intruso = reconhecedor.load_image_file(foto)
            caracteristicas_intruso = reconhecedor.face_encodings(foto_intruso)

            if len(caracteristicas_intruso) > 0:
                reconhecimentos = reconhecedor.compare_faces(
                    caracteristicas_dos_visitantes, caracteristicas_intruso[0])
                if True in reconhecimentos:
                    num_faces_reconhecidas += 1

        if num_faces_reconhecidas / len(fotos) >= 0.6:
            intrusos.append(intruso)

    return len(intrusos) > 0, intrusos


def reconhecer_visitantes(ambiente_de_simulacao):
    global alunos_reconhecidos

    while True:
        print(
            f"--Tentando reconhecer um aluno entre visitantes em {ambiente_de_simulacao.now}")

        visitantes = simular_visitas()
        ocorreram_reconhecimentos, alunos = reconhecer_alunos(visitantes)
        ocorreram_reconhecimentos_intruso, intrusos = reconhecer_intrusos(
            visitantes)

        if ocorreram_reconhecimentos:
            for aluno in alunos:
                aluno["tempo_para_liberacao"] = ambiente_de_simulacao.now + \
                    TEMPO_MEDIO_DE_PERMANENCIA
                aluno["na_instituicao"] = False
                aluno["no_refeitorio"] = False

                id_entrada = secrets.token_hex(nbytes=16).upper()
                alunos_reconhecidos[id_entrada] = aluno

                imprimir_dados_do_aluno(aluno)

        if ocorreram_reconhecimentos_intruso:
            for intruso in intrusos:
                imprimir_dados_do_intruso(intruso)

        yield ambiente_de_simulacao.timeout(TEMPO_DE_DETECCAO_DE_ALUNOS)


def imprimir_dados_do_aluno(aluno):
    print(colored.fg('black'), colored.bg(
        'blue'), f"aluno reconhecido em {ambiente_de_simulacao.now}", colored.attr('reset'))
    print(colored.fg('black'), colored.bg(
        'blue'), f"nome: {aluno['nome']}", colored.attr('reset'))
    print(colored.fg('black'), colored.bg(
        'blue'), f"curso: {aluno['curso']}", colored.attr('reset'))


def imprimir_dados_do_intruso(intruso):
    print(colored.fg('black'), colored.bg(
        'red'), f"intruso reconhecido em {ambiente_de_simulacao.now}", colored.attr('reset'))
    print(colored.fg('black'), colored.bg(
        'red'), f"nome: {intruso['nome']}", colored.attr('reset'))
    print(colored.fg('black'), colored.bg(
        'red'), f"curso: {intruso['curso']}", colored.attr('reset'))


def entrada_de_alunos(ambiente_de_simulacao):
    global alunos_reconhecidos

    while True:
        print(
            f"--Registrando entrada de alunos em: {ambiente_de_simulacao.now}")

        if len(alunos_reconhecidos):
            for id_entrada, aluno in list(alunos_reconhecidos.items()):
                if not aluno["na_instituicao"]:
                    aluno["na_instituicao"] = True
                    print(colored.fg('white'), colored.bg(
                        'green'), f"Entrada de aluno {aluno['nome']} na instituição  em {ambiente_de_simulacao.now}", colored.attr('reset'))

        yield ambiente_de_simulacao.timeout(TEMPO_DE_DETECCAO_DE_ALUNOS)


def saida_de_alunos(ambiente_de_simulacao):
    global alunos_reconhecidos

    while True:
        print(
            f"--Alunos saindo em: {ambiente_de_simulacao.now}")

        if len(alunos_reconhecidos):
            for id_entrada, aluno in list(alunos_reconhecidos.items()):
                if aluno["na_instituicao"] and not aluno["no_refeitorio"] and ambiente_de_simulacao.now >= aluno["tempo_para_liberacao"]:
                    aluno_liberado = (random.randint(
                        1, 100)) <= PROBABILIDADE_DE_LIBERACAO
                    if aluno_liberado:
                        alunos_reconhecidos.pop(id_entrada)
                        print(colored.fg('white'), colored.bg('green'),
                              f"saida de aluno {aluno['nome']} da instiuição em {ambiente_de_simulacao.now}", colored.attr('reset'))

        yield ambiente_de_simulacao.timeout(TEMPO_DE_SAIDA_DE_ALUNOS)



def aluno_no_refeitorio(ambiente_de_simulacao):
    global alunos_reconhecidos

    while True:
        print(
            f"tentando identificar aluno no refeitório em {ambiente_de_simulacao.now}")

        for aluno in alunos_reconhecidos.values():
                if aluno["na_instituicao"] and not aluno["no_refeitorio"]:
                    enviar_pro_refeitorio = (random.randint(
                        1, 100)) <= PROBABILIDADE_IR_AO_REFEITORIO
                    if enviar_pro_refeitorio:
                        aluno["tempo_para_liberacao_da_uti"] = ambiente_de_simulacao.now + \
                            TEMPO_DO_REFEITORIO
                        aluno["no_refeitorio"] = True
                        print(colored.fg('black'), colored.bg(
                            'yellow'), f"aluno {aluno['nome']} foi para o refeitório {ambiente_de_simulacao.now}", colored.attr('reset'))

        yield ambiente_de_simulacao.timeout(TEMPO_DE_IR_AO_REFEITORIO)




def aluno_saida_refeitorio(ambiente_de_simulacao):
    global alunos_reconhecidos

    while True:
        print(
            f"tentando identificar saida de aluno do refeitório em {ambiente_de_simulacao.now}")

        if len(alunos_reconhecidos):
            for aluno in alunos_reconhecidos.values():
                if aluno["no_refeitorio"] and ambiente_de_simulacao.now:
                    aluno_liberado = (random.randint(
                        1, 100)) <= PROBABILIDADE_DE_LIBERACAO_DO_REFEITORIO
                    if aluno_liberado:
                        aluno["no_refeitorio"] = False
                        print(colored.fg('black'), colored.bg(
                            'yellow'), f"aluno {aluno['nome']} saindo do refeitório em {ambiente_de_simulacao.now}", colored.attr('reset'))

        yield ambiente_de_simulacao.timeout(TEMPO_DO_REFEITORIO)


def alunos_refeitorio():
    global alunos_reconhecidos

    alunos_no_refeitorio = 0
    for aluno in alunos_reconhecidos.values():
        if aluno["no_refeitorio"]:
            alunos_no_refeitorio += 1

    return alunos_no_refeitorio


if __name__ == "__main__":
    preparar()

    ambiente_de_simulacao = simpy.Environment()
    ambiente_de_simulacao.process(reconhecer_visitantes(ambiente_de_simulacao))
    ambiente_de_simulacao.process(entrada_de_alunos(ambiente_de_simulacao))
    ambiente_de_simulacao.process(saida_de_alunos(ambiente_de_simulacao))
    ambiente_de_simulacao.process(aluno_no_refeitorio(ambiente_de_simulacao))
    ambiente_de_simulacao.process(aluno_saida_refeitorio(ambiente_de_simulacao))

    ambiente_de_simulacao.run(until=1000)
