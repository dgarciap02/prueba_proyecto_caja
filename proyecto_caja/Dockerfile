# USE THIS DOCKERFILE ONLY IF YOU NEED MORE PACKAGES/PROGRAMS THAN THE ONES AVAILABLE IN siali/main-base.
# Dont forget to update main-base tag to the most recent number.
FROM siali/main-base:157
COPY requirements.txt .
RUN pip install --trusted-host pypi.python.org -r requirements.txt