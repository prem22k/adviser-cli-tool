#!/usr/bin/env bash

# Adviser-CLI Premium Single-Command Installer
# Zero-Infrastructure Local RAG Assistant

set -e

# ANSI Color Codes for Premium Presentation
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ASCII Header
echo -e "${CYAN}${BOLD}"
echo "    ___       __     _                     "
echo "   /   | ____/ /_  __(_)____ ___  _____     "
echo "  / /| |/ __  / | / / / ___/ _ \/ ___/     "
echo " / ___ / /_/ /| |/ / (__  )  __/ /         "
echo "/_/  |_\__,_/ |___/_/____/\___/_/          "
echo "                                           "
echo -e "${NC}"
echo -e "${BOLD}Starting premium zero-infrastructure local RAG assistant installation...${NC}\n"

# Step 1: Check Python Version
echo -e "${BLUE}[1/4] Checking Python environment...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed on your system. Please install it to proceed.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
MAJOR_VER=$(python3 -c 'import sys; print(sys.version_info.major)')
MINOR_VER=$(python3 -c 'import sys; print(sys.version_info.minor)')

if [ "$MAJOR_VER" -lt 3 ] || { [ "$MAJOR_VER" -eq 3 ] && [ "$MINOR_VER" -lt 10 ]; }; then
    echo -e "${RED}Error: Adviser requires Python 3.10 or higher. Found: $PYTHON_VERSION${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Found compatible Python $PYTHON_VERSION${NC}"

# Step 2: Establish Virtual Environment
echo -e "${BLUE}[2/4] Initializing Python virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Created virtual environment in ./venv${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists at ./venv${NC}"
fi

# Step 3: Install Package & Dependencies
echo -e "${BLUE}[3/4] Sourcing environment and installing dependencies...${NC}"
source venv/bin/activate

# Check if uv is available for 10x faster installation
if command -v uv &> /dev/null; then
    echo -e "${CYAN}→ Found 'uv' package manager. Installing with maximum speed...${NC}"
    uv pip install -e ".[dev]"
else
    echo -e "${YELLOW}→ 'uv' not found. Defaulting to standard pip...${NC}"
    pip install --upgrade pip
    pip install -e ".[dev]"
fi
echo -e "${GREEN}✓ Successfully installed Adviser-CLI and all dependencies${NC}"

# Step 4: Setup Wizard Invocations
echo -e "${BLUE}[4/4] Setup complete!${NC}"
echo -e "${GREEN}✓ System configured successfully!${NC}\n"

# Execute init automatically to get them started right away
if [ "$1" != "--non-interactive" ] && [ -z "$ADVISER_NON_INTERACTIVE" ]; then
    echo -e "${CYAN}${BOLD}Launching Adviser interactive Setup Wizard...${NC}"
    ./venv/bin/adviser init
else
    echo -e "${GREEN}✓ Setup complete. You can now run 'adviser init' to configure your active profile.${NC}"
fi
