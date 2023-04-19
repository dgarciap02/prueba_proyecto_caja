from element.element import Element
from element.anomaly import Anomaly
import json
from os import getenv
from element.logging_formatter import logger
import cv2
import copy

def load_model(publisher):
    model_interface = publisher.get_current_model()["name"]
    model = Element.from_file(getenv("PATH_JSON_MODEL"), model_interface)
    logger.info('Selecionado elemento: {}'.format(model))
    return model_interface, model



def load_models(json_path):
    models_json = load_json(json_path)
    models = {}
    for model_name in models_json.keys():
        print("CARGADNO MODELO " + model_name)
        models[model_name] = Element.from_file(json_path, model_name)
        models[model_name].load_cameras()

    return models


def upload_models(models, publisher, json_path):
    for model_name in models.keys():
        print("POSTEANDO MODELO " + model_name)
        publisher.upload_model(json_path, model_name)

def load_json(path):
    """Load json file.
    Args:
        path (str): string with the path to the json files.
                    e.g. "/data/model.json"
    Returns:
        dict: json parsed as python dictionary.
    """
    with open(path) as json_file:
        return json.load(json_file)

def post_element(element, publisher):
    # TODO: QUÉ HAY QUE MODIFICAR EN EL ELEMENTO.
    # - renombrar img a image en el diccionario (tanto en cada roi, como anomaly y view)
    # - quitar el atributo rois vista.
    # - cambiar los nulls de detection a {}
    # +- cambiar el nombre del atributo classification_confidence a confidence_classification (para anomalias y rois)
    # +- añadir bias a dict() rois y anomalies, no tienen bias cuando se hace dict en element.
    imgs = separate_imgs(element)
    element_dict = element2dict(element)
    with open('/files/element.json', 'w') as fw:
        json.dump(element_dict, fw)
    with open('/files/element.json') as fr:
        element_payload = fr.read()
    # print(element_payload)
    publisher.upload(element_payload, imgs)  

def separate_imgs(element):
    """Se guardan en disco las imágenes y se separan element
    en un diccionario para enviar a la bbdd..
    La clave es el nombre de la vista y el valor es la imagen en una
    tupla (nombre que queremos darle, path de la imagen, content type http)
    e.g. {"frontal_1": img1, "frontal_2": img2}
    Args:
        element (Element): Elemento del que queremos separar las imágenes
    returns:
        dict: diccionario con las imágenes separadas
    """
    imgs = {}
    imgs_path = "/files/imgs/"
    # separate imgs from views
    for dic in [element.views, element.rois, element.anomalies]:
        for name, obj in dic.items():
            filename = "{}.jpg".format(imgs_path + name)
            if obj.img is not None:
                cv2.imwrite(filename, obj.img) # guardar la imagen para cargarla como io.BufferedReader
                imgs[name] = (filename, open(filename, "rb"), 'image/jpeg')
            else:
                logger.info("{} no tiene imagen. Imagen: {}".format(name, obj.img))

    return imgs      

def element2dict(element):
    """parse element to a dictionary that elementdb accepts"""
    element_dict = element.as_dict()
    for view in element_dict["views"].keys():
        del element_dict["views"][view]["img"]
        del element_dict["views"][view]["rois"]
        del element_dict["views"][view]["anomalies"] # se ha quitado para elementDB
        element_dict["views"][view]["image"] = view
        # asignar a la imagen de la vista el nombre de la imagen guardada.
        # esto permite identificar que imagen corresponde a que vista.
    for roi_name, roi in element_dict["rois"].items():
        if roi["img"] is not None:
            element_dict["rois"][roi_name]["image"] = roi_name
        del element_dict["rois"][roi_name]["img"]
        del element_dict["rois"][roi_name]["results"]
        try:
            element_dict["rois"][roi_name]["detection"]["detections"] = element.rois[roi_name].detection.detections
        except:
            logger.warning("No se ha podido cargar la detección de la roi {}".format(roi_name))

    for anomaly_name, anomaly in element_dict["anomalies"].items():
        if anomaly["img"] is not None:
            element_dict["anomalies"][anomaly_name]["image"] = anomaly_name
        del element_dict["anomalies"][anomaly_name]["img"]
        del element_dict["anomalies"][anomaly_name]["results"]
        element_dict["anomalies"][anomaly_name]["detection"]["detections"] = element.anomalies[anomaly_name].detection.detections
    return element_dict    

def classify_rois(model, element):
    """Obtain the OK state of each roi:
    * If doesn't need classification, element.results.OK if has been detected (has detection)
    * The same case but the roi is an anomaly, element.results.OK
    * If classify, listen the model
    * If the confidence of the model is lower than threshold, fix bias
    Bias helps to tunning False positives and false negatives
    Args:
        model (object): an ML handler object (YOLO)
        element (object): Element type object
    Returns:
        element (object):
    """
    element.timer("classify rois")
    for name, roi in element.rois.items():
        if roi.detection is None:
            element.rois[name].ok = None
        elif roi.toclassify:
            clase, confidence = model.predict_class(roi.img)["data"][0]
            if '_ok' in clase.lower():
                element.rois[name].ok = element.results.OK
            if '_ko' in clase.lower():
                element.rois[name].ok = element.results.KO
            element.rois[name].confidence_classification = confidence
        elif type(roi) is Anomaly:
            element.rois[name].ok = element.results.KO
        else:
            element.rois[name].ok = element.results.OK
    for name, anomaly in element.anomalies.items():
        if anomaly.detection is None:
            element.anomalies[name].ok = None
        elif anomaly.toclassify:
            clase, confidence = model.predict_class(anomaly.img)["data"][0]
            if '_ok' in clase.lower():
                element.anomalies[name].ok = element.results.OK
            if '_ko' in clase.lower():
                element.anomalies[name].ok = element.results.KO
            element.anomalies[name].confidence_classification = confidence
        elif type(roi) is Anomaly:
            element.anomalies[name].ok = element.results.KO
        else:
            element.anomalies[name].ok = element.results.OK
        
    element.ok = element.__bool__()
    element.timer.stop()
    return element

def update_rois(new_element, detections):
    """check each detection and verify if the image
    can be related with any part of the element. If
    no one meets the requirements, it can be an anomaly,
    if its name is in the list
    Args:
        detections (Object): list of detection objects
    """
    new_element.timer("update rois")
    for detection in detections:
        for name, roi in new_element.rois.items():
            # if (roi.name == detection.name and roi.view.name == detection.view.name and not roi.detection):
            if roi == detection:
                new_element.rois[name].update(detection)
                break
            else:
                continue
        # TODO: update de anomalies a otr funcion privada
        for name, anomaly in new_element.anomalies_template.items():
            if anomaly == detection:
                new_anomaly = copy.deepcopy(anomaly)
                new_anomaly.update(detection)
                anomaly_name = "{}_{}".format(name, len(new_element.anomalies) + 1)
                new_element.anomalies[anomaly_name] = new_anomaly
    # self.rois.update(self.anomalies)  # TODO: garantizar que anomalies no pisa a rois
    new_element.timer.stop()