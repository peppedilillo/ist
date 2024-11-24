FROM redis:7.2-alpine

COPY ./run.sh /run.sh

USER root

RUN chmod +x /run.sh

USER redis

CMD ["/run.sh"]
