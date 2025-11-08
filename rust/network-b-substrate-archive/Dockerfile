# Network B Node - Institutional-Grade Docker Build
# Multi-stage build for optimized production binary

# Builder stage - Rust 1.91 for polkadot-stable2412
FROM rust:1.91-bullseye AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    clang \
    libclang-dev \
    cmake \
    protobuf-compiler \
    pkg-config \
    libssl-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Copy workspace files
COPY Cargo.toml Cargo.lock ./
COPY runtime ./runtime
COPY pallets ./pallets
COPY node ./node

# Build in release mode
RUN cargo build --release -p network-b-node

# Runtime stage - minimal image with just the binary
FROM debian:bullseye-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libssl1.1 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy binary from builder
COPY --from=builder /build/target/release/network-b-node /usr/local/bin/

# Create data directory
RUN mkdir -p /data

# Expose ports
# 30333: P2P
# 9933: RPC
# 9944: WebSocket
EXPOSE 30333 9933 9944

# Set data directory as volume
VOLUME ["/data"]

# Set entrypoint
ENTRYPOINT ["network-b-node"]

# Default command - run in dev mode
CMD ["--dev", "--tmp", "--rpc-external", "--rpc-cors", "all"]
