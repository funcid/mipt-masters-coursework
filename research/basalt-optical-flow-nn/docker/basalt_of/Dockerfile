# Basalt optical-flow teacher image:
#  - official Basalt 0.1.7 binaries (basalt_opt_flow, basalt_vio, …) for EuRoC/T3
#  - pair-track CLI (Pattern51 SE2 from Basalt open headers) for our sparse protocol
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates python3 python3-pip python3-numpy \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Official Basalt release into /root/.local
RUN curl -LsSf https://gitlab.com/VladyslavUsenko/basalt/-/raw/master/scripts/install.sh | sh \
    && ln -sf /root/.local/bin/* /usr/local/bin/ \
    && echo 'export PATH=/root/.local/bin:$PATH' >> /etc/profile.d/basalt.sh \
    && echo 'export LD_LIBRARY_PATH=/root/.local/lib:${LD_LIBRARY_PATH}' >> /etc/profile.d/basalt.sh

ENV PATH="/root/.local/bin:${PATH}"
ENV LD_LIBRARY_PATH="/root/.local/lib:${LD_LIBRARY_PATH}"

RUN pip3 install --no-cache-dir opencv-python-headless numpy

WORKDIR /opt/basalt_of
COPY se2_core.py track_pair.py /opt/basalt_of/

# Default: show installed Basalt tools
CMD ["bash", "-lc", "basalt_opt_flow --help | head -20; echo; python3 /opt/basalt_of/track_pair.py --help"]
