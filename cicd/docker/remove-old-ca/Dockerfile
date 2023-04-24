FROM registry.cern.ch/cmscrab/crabtaskworker:v3.230221
COPY tls-ca-bundle_fix.pem /
USER root
RUN chown root:root /tls-ca-bundle_fix.pem \
    && chmod 444 /tls-ca-bundle_fix.pem \
    && ln -sf /tls-ca-bundle_fix.pem /etc/pki/tls/certs/ca-bundle.crt
USER crab3
