const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

console.log('--- Setting up local Python Virtual Environment & Dependencies ---');

const isWindows = process.platform === 'win32';
const rootDir = path.resolve(__dirname, '..');

let cmd = '';
let args = [];

if (isWindows) {
  cmd = 'powershell.exe';
  args = ['-ExecutionPolicy', 'Bypass', '-File', path.join(rootDir, 'install.ps1'), '--non-interactive'];
} else {
  cmd = 'bash';
  args = [path.join(rootDir, 'install.sh'), '--non-interactive'];
  // Ensure the script is executable
  try {
    fs.chmodSync(path.join(rootDir, 'install.sh'), '755');
  } catch (err) {
    // Ignore permissions errors
  }
}

const child = spawn(cmd, args, {
  cwd: rootDir,
  stdio: 'inherit',
  shell: true
});

child.on('close', (code) => {
  if (code === 0) {
    console.log('✔ Python virtual environment installation completed successfully.');
  } else {
    console.error(`✖ Installation failed with exit code: ${code}`);
    process.exit(code);
  }
});
