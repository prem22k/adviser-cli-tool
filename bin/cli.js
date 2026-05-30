#!/usr/bin/env node

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const rootDir = path.resolve(__dirname, '..');
const isWindows = process.platform === 'win32';

let adviserPath = '';
if (isWindows) {
  adviserPath = path.join(rootDir, 'venv', 'Scripts', 'adviser.exe');
  if (!fs.existsSync(adviserPath)) {
    // Fallback if Scripts folder has python scripts instead of compiled exe
    adviserPath = path.join(rootDir, 'venv', 'Scripts', 'adviser.py');
  }
} else {
  adviserPath = path.join(rootDir, 'venv', 'bin', 'adviser');
}

// Fallback to searching globally if venv setup wasn't complete
if (!fs.existsSync(adviserPath)) {
  console.error(`✖ Error: Adviser virtual environment executable not found at: ${adviserPath}`);
  console.error(`Please run 'npm install' or run './install.sh' in the package root.`);
  process.exit(1);
}

// Capture arguments passed to Node process and forward them
const args = process.argv.slice(2);

const child = spawn(adviserPath, args, {
  cwd: process.cwd(),
  stdio: 'inherit',
  shell: isWindows // Windows requires shell option for executable scripts
});

child.on('close', (code) => {
  process.exit(code);
});
