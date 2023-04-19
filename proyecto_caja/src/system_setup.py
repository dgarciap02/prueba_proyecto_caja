
from enum import IntEnum
from os import getenv
import time
from element.logging_formatter import logger
import project_code as pc
import mlrequests as mlr
from pyplc import create_plc
import detectron2 as detectron
import sys
from element.element import Element
from bot_telegram import bot
from publisher import Publisher


def system_setup(tiempo_espera=40):
    logger.info('Esperando {} segundos a que'
                ' levanten todos los contenedores...'.format(tiempo_espera))
    time.sleep(tiempo_espera)
    logger.info('Iniciando sistema...')
    # telegram_bot = _load_telegram_bot()
    publisher = _load_publisher()
    plc = _load_plc()
    models = _load_element_models()
    algoritmos = _load_ml({'yolo': ml_models.YOLO})

    return publisher, plc, models, algoritmos


def _load_ml(models):
    # models = {'yolo_rois': ml_models.YOLO}
    yolo_url = getenv('YOLO_URL')
    yolo_weights = getenv('YOLO_WEIGHTS')
    detectron2_url = getenv('DETECTRON2_URL')
    detectron2_cfg = getenv('DETECTRON2_CFG')
    detectron2_weights = getenv('DETECTRON2_WEIGHTS')
    detectron2_names = getenv('DETECTRON2_NAMES')

    for model_name, model_type in models.items():
        if model_type == ml_models.YOLO:
            weights = yolo_weights
            models[model_name] = mlr.YoloAPIHandler(yolo_url)
            response = models[model_name].load_model(yolo_weights)
        elif model_type == ml_models.DETETRON2:
            weights = detectron2_weights
            models[model_name] = mlr.Detectron2APIHandler(detectron2_url)
            response = models[model_name].load_model(
                detectron2_url, detectron2_cfg,
                detectron2_weights, detectron2_names)
        else:
            logger.error('El modelo ML {}: no puede ser de tipo: {}.'
                         'Elige entre: {}'.format(
                            model_name, model_type, ml_models.names()))
            sys.exit(1)
        if not response['success']:
            logger.error('El modelo: {} no se ha cargado,'
                         ' por el motivo: {}'.format(model_name, response))
            sys.exit(1)
        logger.info('Se ha cargado el modelo: {} de tipo {}'
                    ' con los weights: {}'.format(
                        model_name, model_type, weights))
    return models


def _load_plc():
    plc = create_plc(getenv("PLC_CONNECTION_TYPE"), getenv("PATH_JSON_PLC"),
                     getenv("LOGLEVEL"))
    return plc


def _load_element_models():
    path_json_model = getenv("PATH_JSON_MODEL")
    models_json = pc.load_json(path_json_model)
    models = {}
    logger.info('Cargando modelos de element: {}'.format(models_json.keys()))
    for model_name in models_json.keys():
        models[model_name] = Element.from_file(path_json_model, model_name)
        models[model_name].load_cameras()
        logger.info("Modelo cargado: {}".format(model_name))

    return models


def _load_telegram_bot():
    telegram_bot = bot.Bot.from_json(getenv("PATH_JSON_BOT_TELEGRAM"))
    telegram_bot.awaiking()
    return telegram_bot


def _load_publisher():
    publisher = Publisher("http://django:8000", "admin", "admin")
    return publisher


class ml_models(IntEnum):
    YOLO = 1
    DETETRON2 = 2
