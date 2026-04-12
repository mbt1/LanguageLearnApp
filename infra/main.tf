locals {
  name_prefix   = "ll-test-${var.run_id}"
  image_prefix  = "ghcr.io/${var.image_owner}/languagelearn"
}

# ── VPC (ephemeral, torn down after tests) ───────────────────────────────────
resource "aws_vpc" "test" {
  cidr_block           = "10.0.0.0/24"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = { Name = "${local.name_prefix}-vpc" }
}

resource "aws_internet_gateway" "test" {
  vpc_id = aws_vpc.test.id

  tags = { Name = "${local.name_prefix}-igw" }
}

resource "aws_subnet" "test" {
  vpc_id                  = aws_vpc.test.id
  cidr_block              = "10.0.0.0/24"
  map_public_ip_on_launch = true

  tags = { Name = "${local.name_prefix}-subnet" }
}

resource "aws_route_table" "test" {
  vpc_id = aws_vpc.test.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.test.id
  }

  tags = { Name = "${local.name_prefix}-rt" }
}

resource "aws_route_table_association" "test" {
  subnet_id      = aws_subnet.test.id
  route_table_id = aws_route_table.test.id
}

# ── Security group ────────────────────────────────────────────────────────────
resource "aws_security_group" "test" {
  name        = "${local.name_prefix}-sg"
  description = "Test environment: HTTP inbound, all outbound"
  vpc_id      = aws_vpc.test.id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${local.name_prefix}-sg" }
}

# ── AMI: latest Amazon Linux 2023 x86_64 ─────────────────────────────────────
data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
}

# ── EC2 instance ──────────────────────────────────────────────────────────────
resource "aws_instance" "test" {
  ami                         = data.aws_ami.al2023.id
  instance_type               = var.instance_type
  subnet_id                   = aws_subnet.test.id
  vpc_security_group_ids      = [aws_security_group.test.id]
  associate_public_ip_address = true

  # No SSH key — access is not needed; the pipeline tests via HTTP only.

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
  }

  user_data = <<-EOF
    #!/bin/bash
    set -e
    dnf update -y
    dnf install -y docker
    systemctl enable --now docker

    # Docker Compose plugin
    mkdir -p /usr/local/lib/docker/cli-plugins
    curl -fsSL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64" \
      -o /usr/local/lib/docker/cli-plugins/docker-compose
    chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

    # Write .env for compose (test values only — not production secrets)
    cat > /opt/compose.env <<'ENVEOF'
    POSTGRES_DB=languagelearn
    POSTGRES_USER=languagelearn
    POSTGRES_PASSWORD=test-only-not-secret
    DATABASE_URL=postgresql://languagelearn:test-only-not-secret@db:5432/languagelearn
    JWT_SECRET=test-only-not-secret
    WEBAUTHN_RP_ID=localhost
    WEBAUTHN_RP_NAME=LanguageLearn
    WEBAUTHN_RP_ORIGIN=http://localhost
    DOMAIN=localhost
    SERVER_IMAGE=${local.image_prefix}/server:${var.image_sha}
    CADDY_IMAGE=${local.image_prefix}/caddy:${var.image_sha}
    BACKUP_IMAGE=${local.image_prefix}/backup:${var.image_sha}
    ENVEOF

    # Pull and start
    cd /opt
    curl -fsSL https://raw.githubusercontent.com/${var.image_owner}/languagelearn/main/docker-compose.yml \
      -o docker-compose.yml
    docker compose --env-file compose.env up -d

    # Signal readiness
    timeout 120 bash -c 'until curl -sf http://localhost/v1/health; do sleep 3; done'
    touch /tmp/ready
  EOF

  tags = { Name = local.name_prefix }
}
