#Importação de bibliotecas
import simpy
from random import *
import matplotlib
import matplotlib.pyplot as plt
from scipy import stats
import numpy as np

#Variáveis da simulação
n_replicacoes = 16
dias_simulacao = 180
duracao_da_simulacao = dias_simulacao*24*60  #Converte a duracao para minutos
dias_aquecimento = 5
tempo_aquecimento = dias_aquecimento*24*60 #4320  #3 dias de aquecimento
capacidade_britagem = 4020.833 #ton/h (por silo). ref inicial = 4020.833
ajuste_downtime = 0  #Acrescenta minutos no tempo de parada e retira do tempo em operação
imprime_detalhes = False

#Capacidades dos recursos
capacidade_silo1 = 1250
capacidade_silo2 = 1250
num_trator_mina = 14
num_trator_estoque_mina = 1

#Dados dos caminhoes
quantidade_caminhoes = 30
capacidade_caminhao = 250

USO_estoque_de_mina = []
NS, NA, TS, TA, TF, USO_trator_mina, USO_trator_estoque_mina, USO_silo1_acesso, USO_silo2_acesso = [], [], [], [], [], [], [], [], []
NF_trator_mina, NF_trator_estoque_mina, NF_silo1_acesso, NF_silo2_acesso = [], [], [], []
TF_trator_mina, TF_trator_estoque_mina, TF_silo1_acesso, TF_silo2_acesso = [], [], [], []
NS_bar, NA_bar, TS_bar, TF_bar, TA_bar = [], [], [], [], []
NF_trator_mina_bar, NF_trator_estoque_mina_bar, NF_silo1_acesso_bar, NF_silo2_acesso_bar = [], [], [], []
TF_trator_mina_bar, TF_trator_estoque_mina_bar, TF_silo1_acesso_bar, TF_silo2_acesso_bar = [], [], [], []
USO_trator_mina_bar, USO_trator_estoque_mina_bar, USO_silo1_acesso_bar, USO_silo2_acesso_bar  = [], [], [], []
T = []
taxa_producao_bar, disponibilidade_britagem_bar, disponibilidade_mina_bar = [], [], []

momento_chegada, momento_saida, tempo_sistema, momento_entrada_fila = {}, {}, {}, {}
momento_saida_fila, tempo_fila, inicia_atendimento, finaliza_atendimento = {}, {}, {}, {}
duracao_atendimento, utilizacao = {}, {}
utilizacao["trator_mina"], utilizacao["trator_estoque_mina"], utilizacao["silo1_acesso"], utilizacao["silo2_acesso"] = 0, 0, 0,0

def processo_silos(env):
  global silo1, silo2
  while env.now <= duracao_da_simulacao:
    tempo_processamento_caminhao = 1/(capacidade_britagem/250/60)
    yield env.timeout(tempo_processamento_caminhao)
    if silo1.level > 0:
        silo1.get(250)
        if imprime_detalhes:                                                         #Retirando 1 carga do silo1
          print("{0:.2f}: Nivel do Silo 1 após processamento: {1:d}".format(env.now,silo1.level))
    if silo2.level > 0:
        silo2.get(250)
        if imprime_detalhes:                                                         #Retirando 1 carga do silo2
          print("{0:.2f}: Nivel do Silo 2 após processamento: {1:d}".format(env.now,silo2.level))

def distribuicoes (tipo):
  return {
      'carregamento_na_mina' : lognormvariate(1.4473,0.3823),
      'carregamento_no_estoque_mina' : lognormvariate(1.5634,0.3051),
      'descarregamento_no_silo1': weibullvariate(1.9334,1.4902),
      'descarregamento_no_silo2' : weibullvariate(1.9334,1.4902),
      'descarregamento_no_estoque_mina' : lognormvariate(0.1816,0.4691),
      'descarregamento_no_estoque_de_esteril' : lognormvariate(0.1704,0.5357),
      'decarregamento_na_pilha_de_esteril' : lognormvariate(0.1704,0.5357),
      'tempo_processamento_silo1' : 1/(capacidade_britagem/60),             #min/ton    multiplicar por 250 para obter min/caminhão
      'tempo_processamento_silo2' : 1/(capacidade_britagem/60),             #min/ton    multiplicar por 250 para obter min/caminhão
      'delay_mina_silo1' : lognormvariate(2.802,0.28619),
      'delay_estoque_mina_silo1' : lognormvariate(1.425,0.1872),
      'delay_mina_silo2' : lognormvariate(2.802,0.28619),
      'delay_estoque_mina_silo2' : lognormvariate(1.425,0.1872),
      'delay_silo1_mina' : lognormvariate(2.438,0.33727),                   #Delay de transporte saindo do silo1 para mina
      'delay_silo2_mina' : lognormvariate(2.438,0.33727),                   #Delay de transporte saindo do silo2 para mina
      'delay_estoque_de_mina_mina' : lognormvariate(2.3987,0.36667),        #Delay de transporte saindo do estoque de mina para mina
      'delay_esteril_mina' : lognormvariate(2.4234,0.38006),                #Delay de transporte saindo do estoque de esteril para mina
      'delay_silo1_estoque_mina' : lognormvariate(1.028,0.42235),           #Delay de transporte saindo do silo1 para estoque de mina
      'delay_silo2_estoque_mina' : lognormvariate(1.028,0.42235),           #Delay de transporte saindo do silo2 para estoque de mina
      'delay_mina_estoque_de_mina' : lognormvariate(2.6774,0.31966),        #Delay de transporte saindo da mina para estoque de mina
      'delay_mina_estoque_de_esteril' : lognormvariate(2.7661,0.27162),     #Delay de transporte saindo da mina para estoque de esteril
      'manutencao_no_silo1' : lognormvariate(5.3560,0.9942),                #Delay de manutenção no silo1
      'operacao_no_silo1' : lognormvariate(6.9813,0.3952),                  #Tempo de operação do silo1 MTBF
      'manutencao_no_silo2' : lognormvariate(5.4930,0.8612),                #Delay de manutenção no silo2
      'operacao_no_silo2' : lognormvariate(6.9348,0.5244),                  #Tempo de operação do silo2 MTBF
      'manutencao_na_mina' : lognormvariate(4.0793,1.1427),                 #Delay de manutenção na mina
      'operacao_na_mina' : lognormvariate(7.1993,0.0916)                    #Tempo de operação na mina MTBF
  }.get(tipo,0.0)

def carregamento(env, id_caminhao, caminhoes, origem, trator_mina, trator_estoque_mina, silo1_acesso, silo2_acesso):
  distribruicao = randint(0,100)                                                #Desvio probabilístico mina x est. de mina

  if (distribruicao <= 69.7) or (origem == "estoque_esteril"):   #79.4
    env.process(carrega_na_mina(env,id_caminhao,caminhoes,origem,trator_mina,trator_estoque_mina,silo1_acesso,silo2_acesso))
  else:
    env.process(carrega_no_estoque_de_mina(env,id_caminhao,caminhoes,origem,trator_mina,trator_estoque_mina,silo1_acesso,silo2_acesso))

def carrega_na_mina(env, id_caminhao, caminhoes, origem, trator_mina,trator_estoque_mina, silo1_acesso, silo2_acesso):
  global operando_mina, inicio_de_operacao_mina, operacao_mina, tempo_utilizacao_Recurso_trator_mina, material_carregado_na_mina, tempo_aquecimento
  global tempo_total_operando_mina, tempo_total_parada_mina
  if origem == "silo1":
    while True:
      retpdf = distribuicoes('delay_silo1_mina')
      if retpdf > 5:
        break
    yield env.timeout(retpdf)
  elif origem == "silo2":
    while True:
      retpdf = distribuicoes('delay_silo2_mina')
      if retpdf > 5:
        break
    yield env.timeout(retpdf)
  elif origem == "estoque_esteril":
    while True:
      retpdf = distribuicoes('delay_esteril_mina')
      if retpdf > 4:
        break
    yield env.timeout(retpdf)
  elif origem == "estoque_de_mina":
    while True:
      retpdf = distribuicoes('delay_estoque_de_mina_mina')
      if retpdf > 4:
        break
    yield env.timeout(retpdf)
  origem = "mina"

  momento_entrada_fila[id_caminhao] = env.now                                   #Entra na fila para carregamento
  request = trator_mina.request()                                               #Solicita um recurso trator para carregamento
  yield request                                                                 #Aguarda um recurso trator ser liberado

  if operando_mina == "":
    while True:
        operacao_mina = distribuicoes('operacao_na_mina')                       #Distribuição de operação entre falha na mina
        if operacao_mina > 14:
            break
    inicio_de_operacao_mina = env.now                                           #Tempo que começou a operar
    operando_mina = "Sim"
    tempo_total_operando_mina += operacao_mina
  elif operando_mina == "Sim":
      if env.now - inicio_de_operacao_mina >= operacao_mina:                    #Verifico se o tempo de operação entre falha foi atingido
        if imprime_detalhes:
          print("{0:.2f}: Aguarde! A mina está em manutenção!".format(env.now))
        tempo_parada = distribuicoes('manutencao_na_mina') + ajuste_downtime
        tempo_total_parada_mina+=tempo_parada
        yield env.timeout(tempo_parada)                                         #Delay de manutenção no silo2
        if imprime_detalhes:
          print("{0:.2f}: Manutenção na mina finalizada!".format(env.now))
        while True:
            operacao_mina = distribuicoes('operacao_na_mina') - ajuste_downtime
            if operacao_mina > 14:
                break
        tempo_total_operando_mina+=operacao_mina
        inicio_de_operacao_mina = env.now

  momento_saida_fila[id_caminhao] = env.now
  tempo_fila[id_caminhao] =  momento_saida_fila[id_caminhao] - momento_entrada_fila[id_caminhao]

  if env.now > tempo_aquecimento:
      TF_trator_mina.append(tempo_fila[id_caminhao])

  inicia_atendimento[id_caminhao] = env.now                                     #Carregamento vai começar

  if imprime_detalhes:
    print("{0:.2f}: {1:s} posicionado para carregar na mina!".format(env.now, id_caminhao))

  inicia_atendimento[id_caminhao] = env.now
  inicia_utilizacao_Recurso = env.now

  yield env.timeout(max(1,distribuicoes('carregamento_na_mina')))               #Delay para carregar caminhão na mina

  finaliza_atendimento[id_caminhao] = env.now                                   #Carregamento Finalizado
  duracao_atendimento[id_caminhao] = finaliza_atendimento[id_caminhao] - inicia_atendimento[id_caminhao]

  if env.now > tempo_aquecimento:
      TA.append(duracao_atendimento[id_caminhao])

  yield trator_mina.release(request)                                            #Libero recurso trator

  caminhao = int(id_caminhao.split()[-1])-1
  caminhoes[caminhao].put(250)                                                  #Inserindo a carga no caminhão
  material_carregado_na_mina += 250                                             #Computando a carga carregada na mina

  if env.now > tempo_aquecimento:
    tempo_utilizacao_Recurso_trator_mina += env.now - inicia_utilizacao_Recurso
    utilizacao["trator_mina"] = tempo_utilizacao_Recurso_trator_mina / (num_trator_mina * (env.now - tempo_aquecimento))

  if imprime_detalhes:
    print("{0:.2f}: {1:s} carregado e liberado na mina!".format(env.now, id_caminhao))
  coleta_dados_indicadores(env, id_caminhao)
  descarregamento(env,id_caminhao,caminhoes,origem,trator_mina,trator_estoque_mina,silo1_acesso,silo2_acesso)

def carrega_no_estoque_de_mina(env, id_caminhao, caminhoes, origem, trator_mina, trator_estoque_mina, silo1_acesso, silo2_acesso):
  global estoque_de_mina, tempo_utilizacao_Recurso_trator_estoque_mina, material_carregado_estoque_mina, tempo_aquecimento

  if origem == "silo1":
    while True:
      retpdf = distribuicoes('delay_silo1_estoque_mina')
      if (retpdf>1) and (retpdf<7):
        break
    yield env.timeout(retpdf)                                                   #Delay de transporte saida do silo1 para estoque de mina
  elif origem == "silo2":
    while True:
      retpdf = distribuicoes('delay_silo2_estoque_mina')
      if (retpdf>1) and (retpdf<7):
        break
    yield env.timeout(retpdf)                                                   #Delay de transporte saida do silo2 para estoque de mina
  #elif origem == "estoque_esteril":
  #  while True:
  #    retpdf = distribuicoes('delay_esteril_estoque_mina')
      #if (retpdf>4):
  #    break
  #  yield env.timeout(retpdf)                #Delay de transporte saida do estoque de esteril para estoque de mina
  elif origem == "mina":
    while True:
      retpdf = distribuicoes('delay_mina_estoque_mina')
      if (retpdf>8):
        break
    yield env.timeout(retpdf)                                                   #Delay de transporte saida da mina para estoque de mina
  origem = "estoque_de_mina"

  momento_entrada_fila[id_caminhao] = env.now                                   #Entra na fila para carregamento
  request = trator_estoque_mina.request()                                       #Solicita um recurso trator para carregamento
  yield request                                                                 #Aguarda um recurso trator ser liberado
  momento_saida_fila[id_caminhao] = env.now
  tempo_fila[id_caminhao] = momento_saida_fila[id_caminhao] - momento_entrada_fila[id_caminhao]

  if env.now > tempo_aquecimento:
      TF_trator_estoque_mina.append(tempo_fila[id_caminhao])

  inicia_atendimento[id_caminhao] = env.now                                     #Carregamento vai começar
  inicia_utilizacao_Recurso = env.now

  if estoque_de_mina > 250:                                                     #Só é possível carregar se tiver estoque de uma carga na mina
    if imprime_detalhes:
      print("{0:.2f}: {1:s} posicionado para carregar no estoque de mina!".format(env.now, id_caminhao))

    yield env.timeout(max(1,distribuicoes('carregamento_no_estoque_mina')))            #Delay para carregar caminhão no estoque de mina

    finaliza_atendimento[id_caminhao] = env.now                                 #Carregamento Finalizado
    duracao_atendimento[id_caminhao] = finaliza_atendimento[id_caminhao] - inicia_atendimento[id_caminhao]

    if env.now > tempo_aquecimento:
        TA.append(duracao_atendimento[id_caminhao])

    yield trator_estoque_mina.release(request)                                  #Libero recurso trator

    caminhao = int(id_caminhao.split()[-1])-1
    caminhoes[caminhao].put(250)                                                #Inserindo a carga no caminhão
    estoque_de_mina -= 250                                                      #Retirando a carga do estoque de mina
    material_carregado_estoque_mina += 250                                      #Computando a carga carregada no estoque de mina
    #USO_estoque_de_mina.append(estoque_de_mina)

    if env.now > tempo_aquecimento:
      tempo_utilizacao_Recurso_trator_estoque_mina += env.now - inicia_utilizacao_Recurso
      utilizacao["trator_estoque_mina"] = tempo_utilizacao_Recurso_trator_estoque_mina / (num_trator_estoque_mina * (env.now - tempo_aquecimento))

    if imprime_detalhes:
      print("{0:.2f}: {1:s} carregado e liberado no estoque de mina!".format(env.now, id_caminhao))
      print("{0:.2f}: Estoque de mina atual: {1:d}".format(env.now, estoque_de_mina))
    coleta_dados_indicadores(env, id_caminhao)
    descarregamento(env,id_caminhao,caminhoes,origem,trator_mina,trator_estoque_mina,silo1_acesso,silo2_acesso)

  else:
    if imprime_detalhes:
      print("{0:.2f}: Estoque de mina intermediário zerado! Aguarde um carregamento ser liberado!".format(env.now))

    yield env.timeout(max(1,distribuicoes('tempo_processamento_estoque_de_mina')))     #Delay para formar uma carga no estoque de mina

    if imprime_detalhes:
      print("{0:.2f}: {1:s} posicionado para carregar no estoque de mina!".format(env.now, id_caminhao))

    yield env.timeout(max(1,distribuicoes('carregamento_no_estoque_mina')))            #Delay para carregar caminhão no estoque de mina

    finaliza_atendimento[id_caminhao] = env.now                                 #Carregamento Finalizado
    duracao_atendimento[id_caminhao] = finaliza_atendimento[id_caminhao] - inicia_atendimento[id_caminhao]

    if env.now > tempo_aquecimento:
        TA.append(duracao_atendimento[id_caminhao])

    yield trator_estoque_mina.release(request)                                  #Libero recurso trator

    if env.now > tempo_aquecimento:
      tempo_utilizacao_Recurso_trator_estoque_mina += env.now - inicia_utilizacao_Recurso
      utilizacao["trator_estoque_mina"] = tempo_utilizacao_Recurso_trator_estoque_mina / (num_trator_estoque_mina * (env.now - tempo_aquecimento))

    caminhao = int(id_caminhao.split()[-1])-1
    caminhoes[caminhao].put(250)                                                #Inserindo a carga no caminhão
    estoque_de_mina -= 250                                                      #Retirando a carga do estoque de mina
    material_carregado_no_estoque_de_mina += 250                                #Computando a carga carregada no estoque de mina

    if imprime_detalhes:
      print("{0:.2f}: {1:s} carregado e liberado no estoque de mina!".format(env.now, id_caminhao))
      print("{0:.2f}: Estoque de mina atual: {1:d}".format(env.now, estoque_de_mina))
    coleta_dados_indicadores(env, id_caminhao)
    descarregamento(env,id_caminhao,caminhoes,origem,trator_mina,trator_estoque_mina,silo1_acesso,silo2_acesso)

def descarregamento(env, id_caminhao, caminhoes, origem, trator_mina, trator_estoque_mina, silo1_acesso, silo2_acesso):
  distribruicao = randint(0,100)                                                #Desvio probabilístico silos x estoque de esteril x estoque intermediário

  if distribruicao <= 55.9:
    env.process(descarrega_nos_silos(env,id_caminhao,caminhoes,origem,trator_mina,trator_estoque_mina,silo1_acesso,silo2_acesso))
  elif distribruicao <= 81.2:
    env.process(descarrega_no_estoque_de_mina(env,id_caminhao,caminhoes,origem,trator_mina,trator_estoque_mina,silo1_acesso,silo2_acesso))
  else:
    env.process(decarrega_na_pilha_de_esteril(env,id_caminhao,caminhoes,origem,trator_mina,trator_estoque_mina,silo1_acesso,silo2_acesso))

def descarrega_nos_silos(env, id_caminhao, caminhoes, origem, trator_mina, trator_estoque_mina, silo1_acesso, silo2_acesso):
  tamFilaSilo1 = len(silo1_acesso.put_queue)                                    #Tamanho da fila para descarregar no silo1
  tamFilaSilo2 = len(silo2_acesso.put_queue)                                    #Tamanho da fila para descarregar no silo2

  global inicio_de_operacao_silo1, inicio_de_operacao_silo2, operacao_silo1, operacao_silo2, operando_silo1, operando_silo2, tempo_aquecimento
  global tempo_utilizacao_Recurso_silo1_acesso, tempo_utilizacao_Recurso_silo2_acesso, silo1, silo2, material_descarregado_no_silo1, material_descarregado_no_silo2
  global tempo_total_parada_britagem, tempo_total_operando_britagem

  if tamFilaSilo1 <= tamFilaSilo2:                                              #Verifico qual menor fila para descarregamento nos silos
    if origem == "mina":
      while True:
        retpdf = distribuicoes('delay_mina_silo1')
        if retpdf>8:
            break
      yield env.timeout(retpdf)                      #Delay de transporte saida da mina para silo1
    else:
      while True:
        retpdf = distribuicoes('delay_estoque_mina_silo1')
        if (retpdf>2) and (retpdf<7):
            break
      yield env.timeout(retpdf)              #Delay de transporte saida do estoque de mina para silo1

    momento_entrada_fila[id_caminhao] = env.now                                 #Entra na fila para descarregamento no silo1
    request = silo1_acesso.request()                                            #Solicita o recurso silo1 para descarregamento
    yield request                                                               #Aguarda o silo1 ser liberado

    if operando_silo1 == "":
      while True:
        operacao_silo1 = distribuicoes('operacao_no_silo1') - ajuste_downtime                     #Distribuição de operação entre falha do silo1
        if operacao_silo1>2:
            break
      tempo_total_operando_britagem+=operacao_silo1
      inicio_de_operacao_silo1 = env.now                                        #Tempo que começou a operar
      operando_silo1 = "Sim"
    elif operando_silo1 == "Sim":
      if env.now - inicio_de_operacao_silo1 >= operacao_silo1:                  #Verifico se o tempo de operação entre falha foi atingido
        if imprime_detalhes:
          print("{0:.2f}: Aguarde! O silo1 está em manutenção!".format(env.now))
        tempo_parada = max(0.1,distribuicoes('manutencao_no_silo1')+ajuste_downtime)
        tempo_total_parada_britagem+=tempo_parada
        yield env.timeout(tempo_parada)                 #Delay de manutenção no silo1
        if imprime_detalhes:
          print("{0:.2f}: Manutenção no silo1 finalizada!".format(env.now))
        while True:
          operacao_silo1 = distribuicoes('operacao_no_silo1') - ajuste_downtime
          if operacao_silo1>2:
            break
        tempo_total_operando_britagem+=operacao_silo1
        inicio_de_operacao_silo1 = env.now

    momento_saida_fila[id_caminhao] = env.now
    tempo_fila[id_caminhao] = momento_saida_fila[id_caminhao] - momento_entrada_fila[id_caminhao]

    if env.now > tempo_aquecimento:
      TF_silo1_acesso.append(tempo_fila[id_caminhao])

    inicia_atendimento[id_caminhao] = env.now                                   #Descarregamento vai começar
    inicia_utilizacao_Recurso = env.now

    if silo1.level < capacidade_silo1 and silo1.level + caminhoes[int(id_caminhao.split()[-1])].level <= capacidade_silo1: #Verifico o nível do silo para possibilitar a descarga
      if imprime_detalhes:
        print("{0:.2f}: {1:s} posicionado para descarregar no silo1".format(env.now, id_caminhao))

      yield env.timeout(max(1,distribuicoes('descarregamento_no_silo1')))              #Delay para descarregar caminhão no silo1

      finaliza_atendimento[id_caminhao] = env.now                               #Descarregamento finalizado
      duracao_atendimento[id_caminhao] = finaliza_atendimento[id_caminhao] - inicia_atendimento[id_caminhao]

      if env.now > tempo_aquecimento:
          TA.append(duracao_atendimento[id_caminhao])

      caminhao = int(id_caminhao.split()[-1])-1
      caminhoes[caminhao].get(250)                                              #Retirando a carga do caminhão
      silo1.put(250)                                                            #Inserindo a carga no silo1
      if env.now > tempo_aquecimento:
        material_descarregado_no_silo1 += 250                                     #Computando a carga descarregada no silo1

      yield silo1_acesso.release(request)                                       #Liberando recurso silo1

      if env.now > tempo_aquecimento:
        tempo_utilizacao_Recurso_silo1_acesso += env.now - inicia_utilizacao_Recurso
        utilizacao["silo1_acesso"] = tempo_utilizacao_Recurso_silo1_acesso / (1 * (env.now - tempo_aquecimento))

      if imprime_detalhes:
        print("{0:.2f}: {1:s} descarregado e liberado no silo1!".format(env.now, id_caminhao))
        print("{0:.2f}: Nivel do Silo 1 apos caminhao descarregar: {1:d}".format(env.now, silo1.level))

      origem = "silo1"
      coleta_dados_indicadores(env, id_caminhao)
      carregamento(env,id_caminhao,caminhoes,origem,trator_mina,trator_estoque_mina,silo1_acesso,silo2_acesso)

    else:
      if imprime_detalhes:
        print("{0:.2f}: Silo1 cheio! Aguarde processamento!".format(env.now))
      yield env.timeout(distribuicoes('tempo_processamento_silo1')*250)         #Delay para processar uma carga no silo1

      if imprime_detalhes:
        print("{0:.2f}: {1:s} posicionado para descarregar no silo1".format(env.now, id_caminhao))

      yield env.timeout(max(1,distribuicoes('descarregamento_no_silo1')))              #Delay para descarregar caminhão no silo1

      finaliza_atendimento[id_caminhao] = env.now                               #Descarregamento finalizado
      duracao_atendimento[id_caminhao] = finaliza_atendimento[id_caminhao] - inicia_atendimento[id_caminhao]

      if env.now > tempo_aquecimento:
          TA.append(duracao_atendimento[id_caminhao])

      caminhao = int(id_caminhao.split()[-1])-1
      caminhoes[caminhao].get(250)                                              #Retirando a carga do caminhão
      silo1.put(250)                                                            #Inserindo a carga no silo1
      if env.now > tempo_aquecimento:
        material_descarregado_no_silo1 += 250                                     #Computando a carga descarregada no silo1

      yield silo1_acesso.release(request)

      if env.now > tempo_aquecimento:
        tempo_utilizacao_Recurso_silo1_acesso += env.now - inicia_utilizacao_Recurso
        utilizacao["silo1_acesso"] = tempo_utilizacao_Recurso_silo1_acesso / (1 * (env.now - tempo_aquecimento))

      if imprime_detalhes:
        print("{0:.2f}: {1:s} descarregado e liberado no silo1!".format(env.now, id_caminhao))
        print("{0:.2f}: Nivel do Silo 1 apos caminhao descarregar: {1:d}".format(env.now, silo1.level))

      origem = "silo1"
      coleta_dados_indicadores(env, id_caminhao)
      carregamento(env,id_caminhao,caminhoes,origem,trator_mina,trator_estoque_mina,silo1_acesso,silo2_acesso)

  else:
    if origem == "mina":
      while True:
        retpdf = distribuicoes('delay_mina_silo2')
        if retpdf>8:
            break
      yield env.timeout(retpdf)                      #Delay de transporte saida da mina para silo2
    else:
      while True:
        retpdf = distribuicoes('delay_estoque_mina_silo2')
        if (retpdf>2) and (retpdf<7):
            break
      yield env.timeout(retpdf)              #Delay de transporte saida do estoque de mina para silo2





    momento_entrada_fila[id_caminhao] = env.now                                 #Entra na fila para descarregamento no silo2
    request = silo2_acesso.request()                                            #Solicita o recurso silo2 para descarregamento
    yield request                                                               #Aguarda o silo2 ser liberado

    if operando_silo2 == "":
      while True:
        operacao_silo2 = distribuicoes('operacao_no_silo2') - ajuste_downtime                     #Distribuição de operação entre falha do silo2
        if operacao_silo2>2:
            break
      tempo_total_operando_britagem+=operacao_silo2
      inicio_de_operacao_silo2 = env.now                                        #Tempo que começou a operar
      operando_silo2 = "Sim"
    elif operando_silo2 == "Sim":
      if env.now - inicio_de_operacao_silo2 >= operacao_silo2:                  #Verifico se o tempo de operação entre falha foi atingido
        if imprime_detalhes:
          print("{0:.2f}: Aguarde o silo2 está em manutenção!".format(env.now))
        tempo_parada = max(0.1,distribuicoes('manutencao_no_silo2')+ajuste_downtime)
        tempo_total_parada_britagem+=tempo_parada
        yield env.timeout(tempo_parada)                 #Delay de manutenção no silo2
        if imprime_detalhes:
          print("{0:.2f}: Manutenção no silo2 finalizada!".format(env.now))
        while True:
          operacao_silo2 = distribuicoes('operacao_no_silo2') - ajuste_downtime
          if operacao_silo2>2:
            break
        tempo_total_operando_britagem+=operacao_silo2
        inicio_de_operacao_silo2 = env.now

    momento_saida_fila[id_caminhao] = env.now
    tempo_fila[id_caminhao] = momento_saida_fila[id_caminhao] - momento_entrada_fila[id_caminhao]

    if env.now > tempo_aquecimento:
      TF_silo2_acesso.append(tempo_fila[id_caminhao])
      TF.append(tempo_fila[id_caminhao])

    inicia_atendimento[id_caminhao] = env.now                                   #Descarregamento vai começar
    inicia_utilizacao_Recurso = env.now

    if silo2.level < capacidade_silo2 and silo2.level + caminhoes[int(id_caminhao.split()[-1])].level <= capacidade_silo2: #Verifico o nível do silo para possibilitar a descarga
      if imprime_detalhes:
        print("{0:.2f}: {1:s} posicionado para descarregar no silo2".format(env.now, id_caminhao))

      yield env.timeout(max(1,distribuicoes('descarregamento_no_silo2')))              #Delay para descarregar caminhão no silo2

      finaliza_atendimento[id_caminhao] = env.now                               #Descarregamento finalizado
      duracao_atendimento[id_caminhao] = finaliza_atendimento[id_caminhao] - inicia_atendimento[id_caminhao]

      if env.now > tempo_aquecimento:
          TA.append(duracao_atendimento[id_caminhao])

      caminhao = int(id_caminhao.split()[-1])-1
      caminhoes[caminhao].get(250)                                              #Retirando a carga do caminhão
      silo2.put(250)                                                            #Inserindo a carga no silo2
      if env.now > tempo_aquecimento:
        material_descarregado_no_silo2 += 250                                     #Computando a carga descarregada no silo2

      yield silo2_acesso.release(request)                                       #Liberando recurso silo2

      if env.now > tempo_aquecimento:
        tempo_utilizacao_Recurso_silo2_acesso += env.now - inicia_utilizacao_Recurso
        utilizacao["silo2_acesso"] = tempo_utilizacao_Recurso_silo2_acesso / (1 * (env.now - tempo_aquecimento))

      if imprime_detalhes:
        print("{0:.2f}: {1:s} descarregado e liberado no silo2!".format(env.now, id_caminhao))
        print("{0:.2f}: Nivel do Silo 2 apos caminhao descarregar: {1:d}".format(env.now, silo2.level))

      origem = "silo2"
      coleta_dados_indicadores(env, id_caminhao)
      carregamento(env,id_caminhao,caminhoes,origem,trator_mina,trator_estoque_mina,silo1_acesso,silo2_acesso)

    else:
      if imprime_detalhes:
        print("{0:.2f}: Silo2 cheio! Aguarde processamento!".format(env.now))
      yield env.timeout(distribuicoes('tempo_processamento_silo2')*250)         #Delay para processar uma carga no silo2

      if imprime_detalhes:
        print("{0:.2f}: {1:s} posicionado para descarregar no silo2".format(env.now, id_caminhao))

      yield env.timeout(max(1,distribuicoes('descarregamento_no_silo2')))              #Delay para descarregar caminhão no silo2

      finaliza_atendimento[id_caminhao] = env.now                               #Descarregamento finalizado
      duracao_atendimento[id_caminhao] = finaliza_atendimento[id_caminhao] - inicia_atendimento[id_caminhao]

      if env.now > tempo_aquecimento:
          TA.append(duracao_atendimento[id_caminhao])

      caminhao = int(id_caminhao.split()[-1])-1
      caminhoes[caminhao].get(250)                                              #Retirando a carga do caminhão
      silo2.put(250)                                                            #Inserindo a carga no silo2
      if env.now > tempo_aquecimento:
        material_descarregado_no_silo2 += 250                                     #Computando a carga descarregada no silo2

      yield silo2_acesso.release(request)                                       #Liberando recurso silo2

      if env.now > tempo_aquecimento:
        tempo_utilizacao_Recurso_silo2_acesso += env.now - inicia_utilizacao_Recurso
        utilizacao["silo2_acesso"] = tempo_utilizacao_Recurso_silo2_acesso / (1 * (env.now - tempo_aquecimento))

      if imprime_detalhes:
        print("{0:.2f}: {1:s} descarregado e liberado no silo2!".format(env.now, id_caminhao))
        print("{0:.2f}: Nivel do Silo 2 apos caminhao descarregar: {1:d}".format(env.now, silo2.level))

      origem = "silo2"
      coleta_dados_indicadores(env, id_caminhao)
      carregamento(env,id_caminhao,caminhoes,origem,trator_mina,trator_estoque_mina,silo1_acesso,silo2_acesso)

def descarrega_no_estoque_de_mina(env, id_caminhao, caminhoes, origem, trator_mina, trator_estoque_mina, silo1_acesso, silo2_acesso):
  global estoque_de_mina, material_descarregado_no_estoque_de_mina
  while True:
    retpdf = distribuicoes('delay_mina_estoque_de_mina')
    if retpdf>8:
        break
  yield env.timeout(retpdf)                #Delay de transporte saida da mina para estoque de mina

  momento_entrada_fila[id_caminhao] = env.now                                   #Entra na fila para descarregamento no estoque de mina

  if imprime_detalhes:
    print("{0:.2f}: {1:s} posicionado para descarregar no estoque de mina".format(env.now, id_caminhao))

  yield env.timeout(max(1,distribuicoes('descarregamento_no_estoque_mina')))           #Delay para descarregar caminhão no estoque de mina

  momento_saida_fila[id_caminhao] = env.now

  #if env.now > tempo_aquecimento:
    #TF.append(momento_saida_fila[id_caminhao]-momento_entrada_fila[id_caminhao])

  inicia_atendimento[id_caminhao] = env.now                                     #Descarregamento vai começar
  #inicia_utilizacao_Recurso = env.now

  finaliza_atendimento[id_caminhao] = env.now                                   #Descarregamento finalizado
  duracao_atendimento[id_caminhao] = finaliza_atendimento[id_caminhao] - inicia_atendimento[id_caminhao]

  #if env.now > tempo_aquecimento:
    #TA.append(duracao_atendimento[id_caminhao])

  caminhao = int(id_caminhao.split()[-1])-1
  estoque_de_mina += caminhoes[caminhao].level                                  #Inserindo a carga no estoque de mina
  USO_estoque_de_mina.append(estoque_de_mina)

  caminhao = int(id_caminhao.split()[-1])-1
  caminhoes[caminhao].get(250)                                                  #Retirando a carga do caminhão
  material_descarregado_no_estoque_de_mina += 250                               #Computando a carga descarregada no estoque de mina

  if imprime_detalhes:
    print("{0:.2f}: {1:s} descarregado e liberado no estoque de mina!".format(env.now, id_caminhao))
    print("{0:.2f}: Estoque de mina atual: {1:d}".format(env.now, estoque_de_mina))

  origem = "estoque_de_mina"
  coleta_dados_indicadores(env, id_caminhao)
  carregamento(env,id_caminhao,caminhoes,origem,trator_mina,trator_estoque_mina,silo1_acesso,silo2_acesso)

def decarrega_na_pilha_de_esteril(env, id_caminhao, caminhoes, origem, trator_mina, trator_estoque_mina, silo1_acesso, silo2_acesso):
  global material_descarregado_no_estoque_de_esteril
  while True:
    retpdf = distribuicoes('delay_mina_estoque_de_esteril')
    if retpdf>10:
        break
  yield env.timeout(retpdf)             #Delay de transporte saida da mina para estoque de esteril

  momento_entrada_fila[id_caminhao] = env.now                                   #Entra na fila para descarregamento na pilha de esteril

  if imprime_detalhes:
    print("{0:.2f}: {1:s} posicionado para descarregar na pilha de esteril".format(env.now, id_caminhao))

  yield env.timeout(max(1,distribuicoes('descarregamento_no_estoque_de_esteril')))     #Delay para descarregar caminhão na pilha de esteril

  momento_saida_fila[id_caminhao] = env.now

  #if env.now > tempo_aquecimento:
    #TF.append(momento_saida_fila[id_caminhao]-momento_entrada_fila[id_caminhao])

  inicia_atendimento[id_caminhao] = env.now                                     #Descarregamento vai começar
  #inicia_utilizacao_Recurso = env.now

  finaliza_atendimento[id_caminhao] = env.now                                   #Descarregamento finalizado
  duracao_atendimento[id_caminhao] = finaliza_atendimento[id_caminhao] - inicia_atendimento[id_caminhao]

  #if env.now > tempo_aquecimento:
    #TA.append(duracao_atendimento[id_caminhao])

  caminhao = int(id_caminhao.split()[-1])-1
  caminhoes[caminhao].get(250)                                                  #Retirando a carga do caminhão
  material_descarregado_no_estoque_de_esteril += 250                            #Computando a carga descarregada na pilha de esteril

  if imprime_detalhes:
    print("{0:.2f}: {1:s} descarregado e liberado na pilha de esteril!".format(env.now, id_caminhao))

  origem = "estoque_esteril"
  coleta_dados_indicadores(env, id_caminhao)
  carregamento(env,id_caminhao,caminhoes,origem,trator_mina,trator_estoque_mina,silo1_acesso,silo2_acesso)

def gera_caminhoes(env, entidade, caminhoes, origem, trator_mina, trator_estoque_mina, silo1_acesso, silo2_acesso):
  global conta_chegada
  yield env.timeout(0)
  for conta_chegada in range (0,quantidade_caminhoes+1):
      id_caminhao = entidade + " " + str(conta_chegada+1)
      momento_chegada[id_caminhao] = env.now
      if imprime_detalhes:
          print("{0:.2f}: Gera {1:s}".format(env.now, id_caminhao))
      carregamento(env,id_caminhao,caminhoes,origem,trator_mina,trator_estoque_mina,silo1_acesso,silo2_acesso)

def coleta_dados_indicadores(env, nome):
    global trator_mina
    global trator_estoque_mina
    global silo1_acesso
    global silo2_acesso
    global conta_chegada
    global tempo_aquecimento

    # Coleta dados para estatísticas
    momento_saida[nome] = env.now
    tempo_sistema[nome] = momento_saida[nome] - momento_chegada[nome]
    if env.now > tempo_aquecimento:
        NS.append(conta_chegada)
        NA.append(trator_mina.count + trator_estoque_mina.count + silo1_acesso.count + silo2_acesso.count)
        NF_trator_mina.append(len(trator_mina.queue))
        NF_trator_estoque_mina.append(len(trator_estoque_mina.queue))
        NF_silo1_acesso.append(len(silo1_acesso.queue))
        NF_silo2_acesso.append(len(silo2_acesso.queue))
        TS.append(tempo_sistema[nome])
        USO_trator_mina.append(utilizacao['trator_mina'])
        USO_trator_estoque_mina.append(utilizacao['trator_estoque_mina'])
        USO_silo1_acesso.append(utilizacao['silo1_acesso'])
        USO_silo2_acesso.append(utilizacao['silo2_acesso'])
        T.append(env.now)

def computa_estatisticas(replicacao):
    print()
    comprimento_linha = 100
    print("="*comprimento_linha)
    print("Indicadores de Desempenho da Replicacao {0:d}".format(replicacao), end="\n")
    print("="*comprimento_linha)

    NS_i, NA_i, TS_i, TF_i, TA_i = np.mean(NS), np.mean(NA), np.mean(TS), np.mean(TF), np.mean(TA)
    TF_trator_mina_i, TF_trator_estoque_mina_i, TF_silo1_acesso_i, TF_silo2_acesso_i = np.mean(TF_trator_mina), np.mean(TF_trator_estoque_mina), np.mean(TF_silo1_acesso), np.mean(TF_silo2_acesso)
    NF_trator_mina_i, NF_trator_estoque_mina_i, NF_silo1_acesso_i, NF_silo2_acesso_i = np.mean(NF_trator_mina), np.mean(NF_trator_estoque_mina), np.mean(NF_silo1_acesso), np.mean(NF_silo2_acesso)
    USO_trator_mina_i = np.mean(USO_trator_mina) if len(USO_trator_mina) > 0 else 0
    USO_trator_estoque_mina_i = np.mean(USO_trator_estoque_mina) if len(USO_trator_estoque_mina) > 0 else 0
    USO_silo1_acesso_i = np.mean(USO_silo1_acesso) if len(USO_silo1_acesso) > 0 else 0
    USO_silo2_acesso_i = np.mean(USO_silo2_acesso) if len(USO_silo2_acesso) > 0 else 0

    print('NS: {0:.2f} caminhões'.format(NS_i))
    print('NF Carregamento na Mina: {0:.2f} caminhões'.format(NF_trator_mina_i))
    print('NF Carregamento no Estoque da Mina: {0:.2f} caminhões'.format(NF_trator_estoque_mina_i))
    print('NF Acesso Silo 1: {0:.2f} caminhões'.format(NF_silo1_acesso_i))
    print('NF Acesso Silo 2: {0:.2f} caminhões'.format(NF_silo2_acesso_i))
    print('NA: {0:.2f} caminhões'.format(NA_i))
    print('TS: {0:.2f} minutos'.format(TS_i))
    print('TF Carregamento Mina: {0:.2f} minutos'.format(TF_trator_mina_i))
    print('TF Carregamento Estoque: {0:.2f} minutos'.format(TF_trator_estoque_mina_i))
    print('TF Acesso Silo 1: {0:.2f} minutos'.format(TF_silo1_acesso_i))
    print('TF Acesso Silo 2: {0:.2f} minutos'.format(TF_silo2_acesso_i))
    print('TA: {0:.2f} minutos'.format(TA_i))
    print('USO trator mina:{0:.2f}%'.format(USO_trator_mina_i*100))
    print('USO trator estoque mina:{0:.2f}%'.format(USO_trator_estoque_mina_i*100))
    print('USO acesso silo 1:{0:.2f}%'.format(USO_silo1_acesso_i*100))
    print('USO acesso silo 2:{0:.2f}%'.format(USO_silo2_acesso_i*100))
    print("="*comprimento_linha, end="\n")
    NS_bar.append(NS_i), NA_bar.append(NA_i), TS_bar.append(TS_i), TF_bar.append(TF_i)
    NF_trator_mina_bar.append(NF_trator_mina_i), NF_trator_estoque_mina_bar.append(NF_trator_estoque_mina_i)
    NF_silo1_acesso_bar.append(NF_silo1_acesso_i), NF_silo2_acesso_bar.append(NF_silo2_acesso_i)
    TF_trator_mina_bar.append(TF_trator_mina_i), TF_trator_estoque_mina_bar.append(TF_trator_estoque_mina_i)
    TF_silo1_acesso_bar.append(TF_silo1_acesso_i), TF_silo2_acesso_bar.append(TF_silo2_acesso_i)
    TA_bar.append(TA_i), USO_trator_mina_bar.append(USO_trator_mina_i), USO_trator_estoque_mina_bar.append(USO_trator_estoque_mina_i)
    USO_silo1_acesso_bar.append(USO_silo1_acesso_i), USO_silo2_acesso_bar.append(USO_silo2_acesso_i)
    taxa_producao_diaria = (material_descarregado_no_silo1+material_descarregado_no_silo2)/(dias_simulacao-dias_aquecimento)/1000
    disp_britagem = 100*tempo_total_operando_mina/(tempo_total_parada_mina+tempo_total_operando_mina)
    disp_mina = 100*tempo_total_operando_britagem/(tempo_total_parada_britagem+tempo_total_operando_britagem)
    taxa_producao_bar.append(taxa_producao_diaria)
    disponibilidade_britagem_bar.append(disp_britagem)
    disponibilidade_mina_bar.append(disp_mina)

def calc_ic(lista):
    if len(lista) <= 1:
        return 0
    else:
        confidence = 0.95
        n = len(lista)
        # mean_se: Erro Padrão da Média
        mean_se = stats.sem(lista)
        h = mean_se * stats.t.ppf((1 + confidence) / 2., n-1)
        # Intervalo de confiança: mean, +_h
        return h

def publica_estatisticas():
    global material_carregado_na_mina, material_carregado_estoque_mina, material_descarregado_no_estoque_de_esteril, material_descarregado_no_estoque_de_mina
    global material_descarregado_no_silo1, material_descarregado_no_silo2
    global tempo_total_parada_britagem, tempo_total_operando_britagem, tempo_total_parada_mina, tempo_total_operando_mina

    print()
    comprimento_linha = 100
    print("="*comprimento_linha)
    print("Indicadores de Desempenho do Sistema", end="\n")
    print("="*comprimento_linha)

    print('NS: {0:.2f} \u00B1 {1:.2f} caminhões (IC 95%)'.format(np.mean(NS_bar), calc_ic(NS_bar)))
    print('NF: {0:.2f} \u00B1 {1:.2f} caminhões (IC 95%)'.format(np.mean(NF_trator_mina_bar), calc_ic(NF_trator_mina_bar)))
    print('NF: {0:.2f} \u00B1 {1:.2f} caminhões (IC 95%)'.format(np.mean(NF_trator_estoque_mina_bar), calc_ic(NF_trator_estoque_mina_bar)))
    print('NF: {0:.2f} \u00B1 {1:.2f} caminhões (IC 95%)'.format(np.mean(NF_silo1_acesso_bar), calc_ic(NF_silo1_acesso_bar)))
    print('NF: {0:.2f} \u00B1 {1:.2f} caminhões (IC 95%)'.format(np.mean(NF_silo2_acesso_bar), calc_ic(NF_silo2_acesso_bar)))
    print('NA: {0:.2f} \u00B1 {1:.2f} caminhões (IC 95%)'.format(np.mean(NA_bar), calc_ic(NA_bar)))
    print('TS: {0:.2f} \u00B1 {1:.2f} minutos (IC 95%)'.format(np.mean(TS_bar), calc_ic(TS_bar)))
    print('TF: {0:.2f} \u00B1 {1:.2f} minutos (IC 95%)'.format(np.mean(TF_trator_mina_bar), calc_ic(TF_trator_mina_bar)))
    print('TF: {0:.2f} \u00B1 {1:.2f} minutos (IC 95%)'.format(np.mean(TF_trator_estoque_mina_bar), calc_ic(TF_trator_estoque_mina_bar)))
    print('TF: {0:.2f} \u00B1 {1:.2f} minutos (IC 95%)'.format(np.mean(TF_silo1_acesso_bar), calc_ic(TF_silo1_acesso_bar)))
    print('TF: {0:.2f} \u00B1 {1:.2f} minutos (IC 95%)'.format(np.mean(TF_silo2_acesso_bar), calc_ic(TF_silo2_acesso_bar)))
    print('TA: {0:.2f} \u00B1 {1:.2f} minutos (IC 95%)'.format(np.mean(TA_bar), calc_ic(TA_bar)))
    print('USO Tratores da Mina:{0:.2f}% \u00B1 {1:.2f}%  (IC 95%)'.format(np.mean(USO_trator_mina_bar)*100, calc_ic(USO_trator_mina_bar)*100))
    print('USO Tratores do Estoque da Mina:{0:.2f}% \u00B1 {1:.2f}%  (IC 95%)'.format(np.mean(USO_trator_estoque_mina_bar)*100, calc_ic(USO_trator_estoque_mina_bar)*100))
    print('USO Acesso Silo 1:{0:.2f}% \u00B1 {1:.2f}%  (IC 95%)'.format(np.mean(USO_silo1_acesso_bar)*100, calc_ic(USO_silo1_acesso_bar)*100))
    print('USO Acesso Silo 2:{0:.2f}% \u00B1 {1:.2f}%  (IC 95%)'.format(np.mean(USO_silo2_acesso_bar)*100, calc_ic(USO_silo2_acesso_bar)*100))
    print("="*comprimento_linha, end="\n")

    print("="*comprimento_linha)
    print("Dados da Produção da mina", end="\n")
    print("="*comprimento_linha)
    print('Material carregado na mina: {0:.2f}'.format(material_carregado_na_mina))
    print('Material carregado no estoque intermediário da mina: {0:.2f}'.format(material_carregado_estoque_mina))
    print('Total de material carregado: {0:.2f}'.format(material_carregado_na_mina+material_carregado_estoque_mina))
    print('Material descarregado no estoque de esteril: {0:.2f}'.format(material_descarregado_no_estoque_de_esteril))
    print('Material descarregado no estoque de mina: {0:.2f}'.format(material_descarregado_no_estoque_de_mina))
    print('Material descarregado no Silo1: {0:.2f}'.format(material_descarregado_no_silo1))
    print('Material descarregado no Silo2: {0:.2f}'.format(material_descarregado_no_silo2))
    print('Total de material descarregado: {0:.2f}'.format(material_descarregado_no_estoque_de_esteril+material_descarregado_no_estoque_de_mina+material_descarregado_no_silo1+material_descarregado_no_silo2))
    print('Volume Final no Estoque_de_mina: {0:.2f}'.format(estoque_de_mina))
    print('Produção média diária da Britagem: {0:.2f} kt/dia \u00B1 {1:.2f} kt/dia  (IC 95%)'.format(np.mean(taxa_producao_bar), calc_ic(taxa_producao_bar)))
    print("="*comprimento_linha, end="\n")
    print('% Tempo de Britagem disponível para carregamento: {0:.2f} % \u00B1 {1:.2f}%'.format(np.mean(disponibilidade_britagem_bar),calc_ic(disponibilidade_britagem_bar)))
    print('% Tempo de Mina disponível para carregamento: {0:.2f} % \u00B1 {1:.2f}%'.format(np.mean(disponibilidade_mina_bar),calc_ic(disponibilidade_mina_bar)))
    print("="*comprimento_linha, end="\n")

    ###################################################################
    # Gera gráfico de Warm-up
    ###################################################################
    if n_replicacoes == 1:
        plt.clf()
        matplotlib.rcParams['figure.figsize'] = (8.0, 6.0)
        matplotlib.style.use('ggplot')
        # cria os dados
        xi = T
        y1 = USO_trator_mina
        y2 = USO_trator_estoque_mina
        y3 = USO_silo1_acesso
        y4 = USO_silo2_acesso
        # usa a função plot
        plt.title('Indicador de Desempenho: \n\n' + "Utilização média dos recursos")
        plt.plot(xi, y1, marker='o', linestyle='-', color='red', label='Dados')
        plt.plot(xi, y2, marker='o', linestyle='-', color='green', label='Dados')
        plt.plot(xi, y3, marker='o', linestyle='-', color='blue', label='Dados')
        plt.plot(xi, y4, marker='o', linestyle='-', color='yellow', label='Dados')
        plt.ylim(0.0,1.0)
        plt.xlim(0.0,duracao_da_simulacao)
        plt.xlabel('Tempo (horas)')
        plt.ylabel('Valor')
        plt.show()
    #else:
        plt.clf()
        matplotlib.rcParams['figure.figsize'] = (8.0, 6.0)
        matplotlib.style.use('ggplot')
        # cria os dados
        #xi = range(0,len(USO_estoque_de_mina))
        xi = np.arange(0, dias_simulacao, dias_simulacao/len(USO_estoque_de_mina))
        y1 = USO_estoque_de_mina
        # usa a função plot
        plt.title('Evolução do estoque na simulação')
        plt.plot(xi, y1, marker='o', linestyle='-', color='red', label='Dados')
        #plt.ylim(950000,1050000)
        plt.ylim(0,1600000)
        #plt.xlim(0.0,duracao_da_simulacao)
        plt.xlabel('Tempo (dias)')
        plt.ylabel('ton')
        plt.show()

for i in range (1, n_replicacoes+1):
  if n_replicacoes==1:
    seed(10)
  tempo_total_parada_britagem = 0
  tempo_total_operando_britagem = 0
  tempo_total_parada_mina = 0
  tempo_total_operando_mina = 0
  conta_chegada = 0                                                             #Conta o número de caminhões no sistema
  origem = ""                                                                   #Identifica a origem para delay's de transporte
  estoque_de_mina = 1000000                                                     #Registra o nível de estoque de mina
  chegada_anterior_silo1 = 0                                                    #Registra as descargas no silo1 p/ gerar processamento do silo 1
  chegada_anterior_silo2 = 0                                                    #Registra as descargas no silo2 p/ gerar processamento do silo 2
  inicio_de_operacao_silo1 = 0                                                  #Registra o inicio da operação do silo1
  inicio_de_operacao_silo2 = 0                                                  #Registra o inicio da operação do silo2
  operando_silo1 = ""                                                           #Registra se o silo1 está operando
  operando_silo2 = ""                                                           #Registra se o silo2 está operando
  operacao_silo1 = 0                                                            #Registra o tempo que o silo1 irá operar
  operacao_silo2 = 0                                                            #Registra o tempo que o silo2 irá operar
  inicio_de_operacao_mina = 0                                                   #Registra o inicio da operação na mina
  operando_mina = ""                                                            #Registra se a mina está operando
  operacao_mina = 0                                                             #Registra o tempo que a mina irá operar
  tempo_utilizacao_Recurso_trator_mina = 0
  tempo_utilizacao_Recurso_trator_estoque_mina = 0
  tempo_utilizacao_Recurso_silo2_acesso = 0
  tempo_utilizacao_Recurso_silo1_acesso = 0
  material_carregado_na_mina = 0
  material_carregado_estoque_mina = 0
  material_descarregado_no_estoque_de_esteril = 0
  material_descarregado_no_estoque_de_mina = 0
  material_descarregado_no_silo1 = 0
  material_descarregado_no_silo2 = 0

  env = simpy.Environment()
  trator_mina = simpy.Resource(env, capacity = num_trator_mina)                 #Recurso para carregamento na minha
  trator_estoque_mina = simpy.Resource(env, capacity = num_trator_estoque_mina) #Recurso para carregamento no estoque de mina
  silo1_acesso = simpy.Resource(env, capacity = 1)                              #Recurso Silo 1 (para solicitar e liberar recurso)
  silo2_acesso = simpy.Resource(env, capacity = 1)                              #Recurso Silo 2 (para solicitar e liberar recurso)
  silo1 = simpy.Container(env, capacidade_silo1, init=0)                        #Container Silo 1 (para inserir e remover carga)
  silo2 = simpy.Container(env, capacidade_silo2, init=0)                        #Container Silo 2 (para inserir e remover carga)
  caminhoes = [simpy.Container(env, capacidade_caminhao, init=0) for _ in range(100)] #Vetor de caminhões
  env.process(processo_silos(env))
  env.process(gera_caminhoes(env,"Caminhao",caminhoes,origem,trator_mina,trator_estoque_mina,silo1_acesso,silo2_acesso))
  env.run(duracao_da_simulacao)
  computa_estatisticas(i)
  publica_estatisticas()
