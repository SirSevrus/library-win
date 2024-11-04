import argparse
import subprocess
import os
import sys

def modify_or_create_spec_file(target, arch, output_name, spec_path=None, force_name=False):
    """Modify or create a spec file with the specified architecture."""
    if spec_path and os.path.exists(spec_path):
        # Modify the existing spec file if architecture is not specified
        with open(spec_path, 'r') as file:
            lines = file.readlines()

        # Check if target_arch is already defined
        arch_found = False
        for i, line in enumerate(lines):
            if "target_arch=" in line:
                arch_found = True
                if arch:
                    lines[i] = f"target_arch='{arch}'  # Architecture target\n"
                break
        
        # If target_arch not found, append it if arch is specified
        if not arch_found and arch:
            lines.append(f"target_arch='{arch}'  # Architecture target\n")

        with open(spec_path, 'w') as file:
            file.writelines(lines)
        print(f"[INFO] Updated spec file at {spec_path} with architecture '{arch}'" if arch else f"[INFO] Using spec file at {spec_path}")
        return spec_path
    else:
        # Adjust output name based on force_name argument
        final_output_name = output_name if force_name else f"{output_name}_{arch}"

        # Create a new spec file if spec_path is not given
        spec_file = f"{final_output_name}.spec"
        spec_content = f"""
# -*- mode: python -*-
block_cipher = None

a = Analysis(
    ['{target}'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='{final_output_name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    target_arch='{arch}'
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='{final_output_name}'
)
"""
        with open(spec_file, 'w') as file:
            file.write(spec_content)
        print(f"[INFO] Created new spec file: {spec_file}")
        return spec_file

def build_executable(spec_file):
    """Build executable using PyInstaller and the specified spec file."""
    print(f"[+] Building executable using {spec_file}...")
    subprocess.run(["pyinstaller", spec_file])

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Build Python Executable with Architecture Support")
    parser.add_argument("target", nargs="?", help="Python script to build")
    parser.add_argument("--arch", choices=["x86", "x86_64"], help="Target architecture (x86 or x86_64)")
    parser.add_argument("--only-spec", action="store_true", help="Generate spec file only, without building executable")
    parser.add_argument("--both", action="store_true", help="Generate spec and build for both architectures")
    parser.add_argument("--output", help="Base name for output files (without extension)")
    parser.add_argument("--spec", help="Comma-separated list of paths to existing spec files to use for building")
    parser.add_argument("--force-name", action="store_true", help="Use the exact output name without adding architecture suffix")
    return parser.parse_args()

def main():
    args = parse_arguments()

    if args.spec:
        # Process each spec file if --spec is used
        spec_files = args.spec.split(',')
        for spec_path in spec_files:
            spec_file = modify_or_create_spec_file(args.target, args.arch, args.output, spec_path, args.force_name)
            if not args.only_spec:
                build_executable(spec_file)

    else:
        # Handle custom spec creation and building if --spec is not provided
        if args.both:
            # Build for both architectures
            for arch in ["x86", "x86_64"]:
                if not args.output:
                    print("[ERROR] --output is required when not using --spec.")
                    sys.exit(1)
                spec_file = modify_or_create_spec_file(args.target, arch, args.output, force_name=args.force_name)
                if not args.only_spec:
                    build_executable(spec_file)
        else:
            # Build for single architecture
            if not args.arch:
                print("[ERROR] --arch must be specified if --both is not used.")
                sys.exit(1)
            if not args.output:
                print("[ERROR] --output is required when not using --spec.")
                sys.exit(1)
            spec_file = modify_or_create_spec_file(args.target, args.arch, args.output, force_name=args.force_name)
            if not args.only_spec:
                build_executable(spec_file)

if __name__ == "__main__":
    main()
