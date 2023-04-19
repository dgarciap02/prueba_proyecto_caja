## Descripción

This a template for all Siali projects, from quality control to stock, count, measure, etc.

Entre proyectos, pueden cambiar algunas partes del programa:
* Los archivos de configuración en `cfgs/` sobre todo los del modelo que define Element
* En el docker compose, ajustar el número de cámaras, o el número de modelos (detectores, clasificadores...)
* El `main.py` es la base del sistema. En función de la comunicación con el plc, de si las vistas se refrescan en diferido o de golpe, logging, etc.
* Los pesos, que dependerán del proyecto
* Las imágenes de simulado, en `/files`, en función del producto a inspeccionar

El sistema incorpora un bot de Telegram, que avisa del inicio del sistema, o de paradas.

También incluimos un servicio que monitoriza las constantes del ordenador, que puede abrirse en el puerto `localhost:3050`. Puedes visitar el repositorio `siali/grafana-system-stats` para más información.

## Cómo hacerlo funcionar

Inserta unos pesos en la carpeta `weights/`. Puedes conseguir unos pesos de ejemplo en el NAS con la ruta ``

Ejecuta el comando `docker-compose -f docker-compose.yml -f docker-compose-system-stats.yml up`. Puedes comprobar el funcionamiento del programa en la terminal, y accediendo al puerto `localhost:8000`.


## Docker and requirements

We should use our image from `Siali/main-base:...`, but if you need to add some python modules to the image (in case you need it in your project code), you should use the requirements.txt file for writing down python packages required. Then you should create the docker image using Dockerfile.


### Estructura del proyecto

```bash
.
├── cfgs
│   ├── cfg_models.json
│   └── cfg_plc.json
├── deploy
│   └── README.md
├── docker-compose-simulated.yml
├── docker-compose.yml
├── Dockerfile
├── documentation
│   └── README.md
├── files
│   └── imgs
├── README.md
├── requirements.txt
├── src
│   ├── logger.py
│   ├── main.py
│   └── project_code.py
└── weights
    └── README.md
```
