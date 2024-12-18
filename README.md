This is the back-end for the project Web Visualisation of Satellite Images.

This project could not have been made possible without project submission and guidance from Digital Lights.

https://lights.digital/

Here are the contact details of the rest of the team:

Bogdan Iordache - bogdanmihai453@gmail.com

Cristi Dobos - c.c.dobos@gmail.com

Sophie Schaaf - Sophie@langeveld.me

Sorana Stan - sorana.a.stan10@gmail.com

# Django Backend

## Overview

This project is a web application built with Django and Django Rest Framework. It provides an API for visualizing satellite images. Each image covers the country of Bulgaria, and are rendered usinging the True Color, Normalised Difference Vegetation Index, Normalised Difference Water Index and Normalised Difference Moisture Index, view. This is the readme for the backend only. The application is containerized using Docker, which simplifies the setup process and ensures that the application runs in the same environment regardless of where it's deployed.

## Setup for New Developers

### Prerequisites
- Docker
- Docker Compose

### Installation
1. Clone the repository
2. Navigate to the project directory
3. Build the Docker image:
    ```
    docker-compose build
    ```
4. Apply migrations:
    ```
    docker-compose run web python manage.py migrate
    ```
5. Run the server:
    ```
    docker-compose up
    ```

# The application is accessed at `http://localhost:8000`.

### Editing the Code
To edit the code, you can use any text editor or IDE you prefer. The application code is located in the `/app` directory in the Docker container, which is mapped to the root directory of your project on your host machine. This means that any changes you make to the code on your host machine will be reflected in the Docker container.

If you're using an IDE like PyCharm, you can open the project directory in your IDE and start editing the code. When you save your changes, they will be automatically applied in the Docker container.

### Running a different environment
The default application environment is used when starting up the Docker using the runserver command. However this will not start the creation of image objects, the rendering of algorithms or the tiling of the rendered data. To start the application with any of these functionalities perform the following steps:
1. Run the server:
    ```
    docker-compose up
    ```
2. Use the docker command line tool to view the help of the application functionality:
    ```
    python ./manage.py help start
    ```
3. Choose which functionalities you want to start  
    _For example only creation of images in the "image_data/testing/img/" folder:_
    ```
    python3 ./manage.py start -c -ci image_data/testing/img/
    ```

As default all the boolean options are set to false. Overriding the location of any input or output will automatically create this folder if it is not yet available. The default locations of input and output are:
|                  |                                   |
|------------------|-----------------------------------|
| Creation input   | ```image_data/original_images/``` |
| Creation output  | ```image_data/images/```          |
| Rendering output | ```image_data/output/```          |
| Tile output      | ```image_data/tiles/```           |
| Temp output      | ```image_data/temp/```            |

#### Overview of available options
```
-c                    Enables the creation of image objects
-ci CI                Overrides the location where to-be-created images are stored
-co CO                Overrides the location where created image band data will be stored
-cf                   Forces the application to recreate image band data
-r                    Enables the rendering of algorithms
-ro RO                Overrides the location where rendered algorithm output will be stored
-rf                   Forces the application to rerender the algorithm output
-t                    Enables the tiling of algorithm output
-to TO                Overrides the location where tiled images will be stored
-tmp TMP              Overrides the location where temporary images will be stored while tiling
```

## How It Works
The application provides a RESTful API for fetching rendered satellite image tiles. The main components are:

- `Image`:  A model representing a satellite image, containing information about it's rendered counterparts.
- `Tile`:  .png images that can be fetched by the user

The API provides the following endpoints:

- `/tiles/<image_id>/<algorithm_id>/<level_number>/<x_axis>/y_axis`: `GET` endpoints for the tiles. This is based on the specific active image, the specific algorithm to fetch the image for, and the coordinates of the tile withing that rendered image (z - level, x and y).

