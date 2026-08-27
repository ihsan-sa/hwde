# ai-ee run image - the whole toolchain in one container (Linux/Docker port of the
# S0 Windows environment; see docker/README.md). Built by `ccbox build ai-ee-run`
# (iiks1's ccbox: image ccbox-<name>:latest, context = repo root) or by hand:
#   docker build -t ccbox-ai-ee-run:latest -f docker/Dockerfile .
#
# Base: the official KiCad image = kicad-cli 10.0.5 + bundled (system) python 3.13.5
# with the SWIG pcbnew module + symbol/footprint libs + libngspice. 10.0.3 (the
# Windows pin) has no published image; 10.0.x share one file format.
FROM kicad/kicad:10.0.5

ARG CLAUDE_CODE_VERSION=latest
ARG NODE_VERSION=24.20.0
ARG JRE_URL=https://github.com/adoptium/temurin25-binaries/releases/download/jdk-25.0.4.1%2B1/OpenJDK25U-jre_x64_linux_hotspot_25.0.4.1_1.tar.gz
ARG FREEROUTING_URL=https://github.com/freerouting/freerouting/releases/download/v2.2.4/freerouting-2.2.4.jar
ARG KRT_URL=https://github.com/drandyhaas/KiCadRoutingTools/releases/download/v0.19.0/KiCadRoutingTools-0.19.0.zip
ARG TZ=UTC
ENV TZ=$TZ DEBIAN_FRONTEND=noninteractive

USER root
# --- OS packages: ccbox parity (tmux, firewall tools, gh deps) + build deps + LaTeX for report_gen + xvfb for kicad-cli render
RUN apt-get update && apt-get install -y --no-install-recommends \
      less git procps sudo fzf man-db unzip zip gnupg2 iptables ipset iproute2 dnsutils aggregate jq nano vim \
      tmux curl wget ca-certificates build-essential ripgrep fd-find xz-utils \
      python3-venv python3-pip python3-numpy python3-shapely python3-scipy \
      texlive-latex-base texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended \
      xvfb xauth \
  && rm -rf /var/lib/apt/lists/*
# gh CLI (ccbox parity; only used when GH_TOKEN is provided)
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg -o /usr/share/keyrings/githubcli-archive-keyring.gpg \
  && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" > /etc/apt/sources.list.d/github-cli.list \
  && apt-get update && apt-get install -y --no-install-recommends gh && rm -rf /var/lib/apt/lists/*
# Node (official tarball, no distro repo) for Claude Code
RUN curl -fsSL "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-x64.tar.xz" | tar -xJ -C /usr/local --strip-components=1 \
  && node --version && npm --version
# Temurin 25 JRE (Freerouting 2.2.4 needs Java >= 25) + the jar + KiCadRoutingTools (Linux prebuilt rust core)
RUN mkdir -p /opt/jre /opt/freerouting /opt/krt \
  && curl -fsSL "$JRE_URL" | tar -xz -C /opt/jre --strip-components=1 \
  && /opt/jre/bin/java -version \
  && curl -fsSL -o /opt/freerouting/freerouting-2.2.4.jar "$FREEROUTING_URL" \
  && curl -fsSL -o /tmp/krt.zip "$KRT_URL" \
  && unzip -q /tmp/krt.zip -d /opt/krt/KiCadRoutingTools-0.19.0 && rm /tmp/krt.zip \
  && cp /opt/krt/KiCadRoutingTools-0.19.0/plugins/rust_router/grid_router-linux-x86_64.so \
        /opt/krt/KiCadRoutingTools-0.19.0/plugins/rust_router/grid_router.so \
  && printf 'KiCadRoutingTools v0.19.0 from %s\nrust core: grid_router-linux-x86_64.so copied to plugins/rust_router/grid_router.so (abi3-py39)\n' "$KRT_URL" > /opt/krt/PROVENANCE.txt
# --- the repo venv, baked: same Python minor as the pin (3.13), same lock (minus Windows-only wheels).
#     /workspace/.venv -> /opt/venv is linked at container start (ccbox-project-init).
COPY requirements.lock /tmp/requirements.lock
RUN python3 -m venv /opt/venv \
  && grep -v -E '^(pywin32|pywin32-ctypes)==' /tmp/requirements.lock > /tmp/requirements.linux.lock \
  && /opt/venv/bin/pip install --no-cache-dir -q -r /tmp/requirements.linux.lock \
  && /opt/venv/bin/python -c "import kipy, kiutils, skidl, shapely, numpy, gerbonara, easyeda2kicad, InSpice, scipy; print('venv ok')"
# --- ccbox conventions: user `node` (uid 1000 = the host user), /workspace, shared login volume at /home/node/.claude
RUN usermod -l node -d /home/node -m -s /bin/bash kicad && groupmod -n node kicad \
  && mkdir -p /usr/local/share/npm-global /commandhistory /workspace /home/node/.claude /etc/ccbox \
  && touch /commandhistory/.bash_history \
  && chown -R node:node /usr/local/share /commandhistory /workspace /home/node
ENV DEVCONTAINER=true \
    NODE_OPTIONS=--max-old-space-size=4096 \
    CLAUDE_CONFIG_DIR=/home/node/.claude \
    HISTFILE=/commandhistory/.bash_history \
    EDITOR=nano VISUAL=nano \
    NPM_CONFIG_PREFIX=/usr/local/share/npm-global \
    PATH=/opt/venv/bin:/usr/local/share/npm-global/bin:$PATH \
    # ai-ee toolchain pins (scripts/lib/env.py reads these; tools/ is unused in the container)
    AIEE_KICAD_CLI=/usr/bin/kicad-cli \
    AIEE_JAVA=/opt/jre/bin/java \
    AIEE_FREEROUTING_JAR=/opt/freerouting/freerouting-2.2.4.jar \
    AIEE_KRT_DIR=/opt/krt/KiCadRoutingTools-0.19.0/plugins \
    AIEE_NGSPICE_DLL=/usr/lib/x86_64-linux-gnu/libngspice.so.0 \
    KICAD10_SYMBOL_DIR=/usr/share/kicad/symbols \
    KICAD10_FOOTPRINT_DIR=/usr/share/kicad/footprints \
    KICAD10_TEMPLATE_DIR=/usr/share/kicad/template \
    KICAD10_3DMODEL_DIR=/usr/share/kicad/3dmodels
# ccbox's entrypoint + egress firewall + tmux conf come from the ccbox base image (iiks1 ccbox/)
COPY --from=ccbox:latest /usr/local/bin/entrypoint.sh /usr/local/bin/init-firewall.sh /usr/local/bin/
COPY --from=ccbox:latest --chown=node:node /home/node/.tmux.conf /home/node/.tmux.conf
COPY --chmod=755 docker/ccbox-project-init docker/ai-ee-loop /usr/local/bin/
RUN chmod +x /usr/local/bin/init-firewall.sh /usr/local/bin/entrypoint.sh \
  && echo "node ALL=(root) NOPASSWD: /usr/local/bin/init-firewall.sh" > /etc/sudoers.d/node-firewall && chmod 0440 /etc/sudoers.d/node-firewall
USER node
RUN npm install -g @anthropic-ai/claude-code@${CLAUDE_CODE_VERSION} && claude --version
WORKDIR /workspace
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
