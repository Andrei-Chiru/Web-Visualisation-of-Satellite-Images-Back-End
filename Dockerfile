# Use an official Python runtime as a parent image
FROM python:3.11

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install GDAL dependencies
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y libgdal-dev gdal-bin
    
# Set GDAL environment variable
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# Copy requirements.txt and Install dependencies
COPY ./DLBackend/requirements.txt ./
RUN pip install --no-cache-dir -r ./requirements.txt

# Copy project
COPY . ./

# Define entrypoint
ENTRYPOINT [ "python", "./manage.py" ]
