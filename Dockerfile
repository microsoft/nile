ARG PYTHON_VERSION=3.7
FROM python:${PYTHON_VERSION} AS build

# install dependencies
RUN pip install --upgrade pip
COPY requirements*.txt /app/
RUN for reqs in /app/requirements*.txt; do pip install --no-cache-dir -r $reqs; done

# copy build dependencies
COPY .pylintrc README.md setup.cfg setup.py version.txt /app/
COPY nile/ /app/nile
COPY tests/ /app/tests

WORKDIR /app
RUN echo "Running setup tools..." \
    && python setup.py \
        mypy \
        pylint \
        isort \
        flake8 \
        pytest \
        sdist \
        bdist_wheel \
    && export CI=True \
    && echo "Finished running setup tools..."

# executes code coverage upload to codecov.io
CMD ["/bin/bash", "-c", "bash <(curl -s https://codecov.io/bash)"]



FROM python:${PYTHON_VERSION}-stretch AS sample
RUN pip install --upgrade pip

# OpenCV Harr Cascade model for detecting cars
ADD https://raw.githubusercontent.com/nmiodice/vehicle_detection_haarcascades/master/cars.xml /samples/

# copy and install dependencies
COPY /samples/requirements.txt /samples/
RUN pip install --no-cache-dir -r /samples/requirements.txt

COPY --from=build /app/dist /dist
RUN pip install --no-cache-dir /dist/*.whl

COPY /samples /samples
# run samples to verify that they work as expected
WORKDIR /samples
RUN bash run_all_samples.sh
ENTRYPOINT ["bash", "run_all_samples.sh"]
