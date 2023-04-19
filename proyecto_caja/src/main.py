from element.element import Element
import mlrequests as mlr
import element.utils as utils
from os import getenv
import time
from element.logging_formatter import logger
import copy
import time
from rich import print
from rich.pretty import pprint
from bot_telegram import bot
import json
from publisher import Publisher
import project_code as pc


def main():

    logger.info('Iniciando sistema...')
    time.sleep(40)

    publisher = Publisher("http://django:8000", "admin", "admin")
    models = pc.load_models(getenv("PATH_JSON_MODEL"))
    pc.upload_models(models, publisher, getenv("PATH_JSON_MODEL"))    
    yolo_rois = mlr.YoloAPIHandler(getenv('URL_YOLO_ROIS'))
    yolo_rois.load_model(getenv('WEIGHTS_YOLO_ROIS'))
    yolo_defectos = mlr.YoloAPIHandler(getenv('URL_YOLO_DEFECTOS'))
    yolo_defectos.load_model(getenv('WEIGHTS_YOLO_DEFECTOS'))
    logger.info('Modelos ML cargados')


    # telegram_bot = bot.Bot.from_json(getenv("PATH_JSON_BOT_TELEGRAM"))
    # telegram_bot.awaiking()

    while True:
        new_element = copy.deepcopy(models["cajaA"])
        print('Elemento antes de nada', new_element.get_info())
        while new_element.views_sequence:
            if True:  # plc.new_element
                new_element.update_views()
                detections = utils.get_detections(yolo_rois, new_element)
                logger.info('Detecciones: {}'.format(detections))
                ocr_code = pc.yolo2ocr(detections)
                pc.update_rois(new_element, detections)
                new_element.apply_thresholds()
                logger.info('Lectura OCR: {}'.format(ocr_code))
                logger.info("El elemento esta: {}".format(new_element.ok))
            else:
                time.sleep(.05)
        new_element = pc.classify_rois(yolo_defectos, new_element)
        print('Elemento despues de classify', new_element.get_info())
        new_element.update_parts()
        logger.info("\n Elemento actualizado: {}".format(new_element.get_info()))
        logger.info("El elemento esta: {}".format(new_element.ok))
        new_element.save_images("/Element_class/example/files/results")
        new_element.check_time()

        # save element as json
        data_post_element = new_element.as_dict()
        # telegram_bot.heartbeat()
        # with open('/app/results/element_asdict.json', 'w') as f:
  	    #     json.dump(data_post_element, f)
        pc.post_element(new_element, publisher)
        
        logger.info("Esperando 2 segundos para la siguiente iteración")
        time.sleep(2)
        
if __name__ == '__main__':
    main() 