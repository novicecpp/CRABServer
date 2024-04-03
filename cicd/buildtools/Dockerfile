FROM gitlab-registry.cern.ch/linuxsupport/alma9-base
SHELL ["/bin/bash", "-c"]

RUN yum install -y openssh bash-completion
RUN curl -LO https://dl.k8s.io/v1.28.3/kubernetes-client-linux-amd64.tar.gz \
    && tar zxvf kubernetes-client-linux-amd64.tar.gz \
    && cp kubernetes/client/bin/kubectl /usr/bin \
    && /usr/bin/kubectl completion bash > /usr/share/bash-completion/completions/kubectl \
    && rm -r kubernetes-client-linux-amd64.tar.gz kubernetes
