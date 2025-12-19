FROM ubuntu:latest

# system dependencies
RUN apt-get update && apt-get install -y python3 \
    python3-venv python3-pip \
    wget unzip git build-essential cmake make \
    coinor-cbc libgl1-mesa-dev libffi-dev

# python dependencies
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip
RUN pip install pyomo minizinc minizinc[dzn] z3-solver \
    matplotlib numpy pandas python-sat pyomo[highs] highspy

RUN mkdir CDMO
WORKDIR /CDMO
COPY . /CDMO

# minizinc install
ARG MINIZINC_VERSION=2.8.4
RUN wget https://github.com/MiniZinc/MiniZincIDE/releases/download/${MINIZINC_VERSION}/MiniZincIDE-${MINIZINC_VERSION}-bundle-linux-x86_64.tgz && \
    tar -xvf MiniZincIDE-${MINIZINC_VERSION}-bundle-linux-x86_64.tgz && \
    rm MiniZincIDE-${MINIZINC_VERSION}-bundle-linux-x86_64.tgz
ENV PATH="${PATH}:/CDMO/MiniZincIDE-${MINIZINC_VERSION}-bundle-linux-x86_64/bin"


RUN chmod +x run_one_instance.sh run_all_instances.sh entry.sh
ENTRYPOINT ["/CDMO/entry.sh"]

CMD []