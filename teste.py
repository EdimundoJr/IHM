import face_recognition
import os

pasta_imagens = 'faces'

imagens_conhecidas = []
nomes_conhecidos = []

for arquivo in os.listdir(pasta_imagens):
    imagem = face_recognition.load_image_file(os.path.join(pasta_imagens, arquivo))
    codificacao = face_recognition.face_encodings(imagem)
    if len(codificacao) > 0:
        imagens_conhecidas.append(codificacao[0])
        nomes_conhecidos.append(os.path.splitext(arquivo)[0])

imagem_desconhecida = face_recognition.load_image_file('teste/visitantes3.jpg')

localizacoes_faces_desconhecidas = face_recognition.face_locations(imagem_desconhecida)
num_faces_desconhecidas = len(localizacoes_faces_desconhecidas)

num_faces_reconhecidas = 0
for localizacao_face in localizacoes_faces_desconhecidas:
    codificacao_desconhecida = face_recognition.face_encodings(imagem_desconhecida, [localizacao_face])[0]
    resultados = face_recognition.compare_faces(imagens_conhecidas, codificacao_desconhecida)
    if True in resultados:
        num_faces_reconhecidas += 1

num_faces_desconhecidas = num_faces_desconhecidas - num_faces_reconhecidas
print(f"Número de rostos desconhecidos: {num_faces_desconhecidas}")
