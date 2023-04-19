import requests
import json
import project_code as pc
class Publisher:
    def __init__(self, url, username, password) -> None:
        self.url = url
        self.session = requests.Session()
        response = self.session.post(
            url + '/login/', data={'username': username, 'password': password})
        print("Login... ", response.text)

        # save model
        sessionid = self.session.cookies.get_dict()['sessionid']
        csrftoken = self.session.cookies.get_dict()['csrftoken']
        self.headers_model = {
            'X-CSRFToken': csrftoken,
            'Content-Type': 'application/json',
            'Cookie': 'csrftoken={}; sessionid={}'.format(csrftoken, sessionid)
        }
        self.headers = {
            'X-CSRFToken': csrftoken,
            'Cookie': 'csrftoken={}; sessionid={}'.format(csrftoken, sessionid)
        }

    def upload(self, element_payload, imgs):
        # with open('/files/data.json') as f:
        #     payload = f.read()
        # files = {
        #     'ejemplo_image': ('image.jpeg', open('/files/imgs/image.jpeg', 'rb'), 'image/jpeg'),
        #     'image_dog': ('dog.jpg', open('/files/imgs/dog.jpg', 'rb'), 'image/jpg'),
        #     'data': payload
        # }

        # response = self.session.post(
        #     self.url + '/element/element/', data={}, files=files, headers=self.headers)
        # print(response)
        imgs["data"] = element_payload
        response = self.session.post(
            self.url + '/element/element/', data={}, files=imgs, headers=self.headers)
        with open("/files/response_post_element.html", "w") as f:
            f.write(response.text)

        return response

    def upload_model(self, json_path, model_name):
        """upload element model to BBDD

        Args:
            model (Element): Element model to upload.
        """
        with open(json_path) as json_file:
            model = json.load(json_file)[model_name]
        model = self.parse_model_dict(model)
        with open('/files/model.json', 'w') as fw:
            json.dump(model, fw)
        with open('/files/model.json') as fr:
            model_json = fr.read()
        response = self.session.post(
            self.url + '/element/model/', data=model_json, headers=self.headers_model)
        with open("/files/response_upload_model_{}.html".format(model_name), "w") as f:
            f.write(response.text)

    def get_current_model(self):
        response = self.session.get(
            self.url + '/element/model/current/', headers=self.headers_model)
        with open("/files/response_get_current_model.html", "w") as f:
            f.write(response.text)
        return response.json()

    def parse_model_dict(self, model):
        model["name"] = model["model"] # cambiar la clave model a name y borrarla del modelo. es para la bbdd
        from enum import IntEnum
        results = IntEnum("results", model["results"]) 
        del model["model"]
        model["current"] = True
        for anomaly_name in model["anomalies"].keys():
            model["anomalies"][anomaly_name]["ok"] = 2
            model["anomalies"][anomaly_name]["bias"] = results[model["anomalies"][anomaly_name]["bias"]] 
            model["anomalies"][anomaly_name]["view_name"] = model["anomalies"][anomaly_name]["view"]
            del model["anomalies"][anomaly_name]["view"]
            del model["anomalies"][anomaly_name]["views"]

        for roi_name in model["rois"].keys():
            model["rois"][roi_name]["ok"] = 2
            model["rois"][roi_name]["bias"] = results[model["rois"][roi_name]["bias"]] 
            model["rois"][roi_name]["view_name"] = model["rois"][roi_name]["view"]
            del model["rois"][roi_name]["view"]
        
        for part_name in model["parts"].keys():
            model["parts"][part_name] = {}
            model["parts"][part_name]["ok"] = 2
            model["parts"][part_name]["name"] = part_name
            print('PARTES...', model["parts"][part_name],'\n',part_name)
            # model["rois"][part_name]["bias"] = results[model["rois"][roi_name]["bias"]]
        return model
