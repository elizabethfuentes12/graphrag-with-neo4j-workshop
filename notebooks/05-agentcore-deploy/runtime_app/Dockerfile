FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim
WORKDIR /app

# AWS_REGION and AWS_DEFAULT_REGION are both set, and to the same value.
# botocore reads only AWS_DEFAULT_REGION, so a container carrying just
# AWS_REGION builds a client that falls back to whatever region the task role
# resolves to. `workshop.aws_region` documents the whole trap. The launch step
# passes both again as container environment variables, which overrides these
# when the deploy targets a region other than us-east-1.
ENV UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_NO_PROGRESS=1 \
    PYTHONUNBUFFERED=1 \
    AWS_REGION=us-east-1 \
    AWS_DEFAULT_REGION=us-east-1

COPY agent_requirements.txt agent_requirements.txt
RUN uv pip install -r agent_requirements.txt

RUN useradd -m -u 1000 bedrock_agentcore
USER bedrock_agentcore

EXPOSE 8080

# `workshop/` and `reservation_command.py` are not in this directory in git.
# 5.1_deploy.ipynb stages both here immediately before the build, because both
# live elsewhere in the repository and Docker cannot reach outside the build
# context. They arrive as plain directories on the import path rather than as
# an installed wheel, which keeps one copy of each in version control. See the
# staging step in the notebook.
COPY --chown=bedrock_agentcore:bedrock_agentcore . .

CMD ["opentelemetry-instrument", "python", "-m", "booking_agent"]
