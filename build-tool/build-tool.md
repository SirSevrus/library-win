
# Build Script Documentation

This script automates the process of generating or modifying PyInstaller spec files and building executables with specified target architectures. The script allows flexible usage through various arguments, including support for different architectures, creating spec files only, using existing spec files, and customizing output names.

## Usage

### Basic Syntax
```bash
python build.py <target> [OPTIONS]
```

### Options

- **`target`** (required unless using `--spec`): The Python script to build into an executable.
- **`--arch`**: Specifies the target architecture (`x86` or `x86_64`).
- **`--only-spec`**: Generates the spec file without building the executable.
- **`--both`**: Generates spec files and builds executables for both `x86` and `x86_64` architectures.
- **`--output`**: Sets the base name for the output files (without extension).
- **`--spec`**: Comma-separated list of existing spec file paths to use for building executables.
- **`--force-name`**: Prevents the addition of architecture type in the output name, maintaining it exactly as specified.

## Example Usages

### Building for a Specific Architecture
Generate a spec file and build an executable for a specified architecture:
```bash
python build.py target.py --arch=x86_64 --output=myapp
```

### Generating a Spec File Only
Generate only the spec file without building the executable:
```bash
python build.py target.py --arch=x86 --only-spec --output=myapp
```

### Building for Both Architectures
Generate spec files and build executables for both `x86` and `x86_64`:
```bash
python build.py target.py --both --output=myapp
```

### Using Existing Spec Files
Use multiple spec files to build executables:
```bash
python build.py --spec=file1.spec,file2.spec
```

### Using Force Name
Prevents architecture suffix from being added to the output name:
```bash
python build.py target.py --arch=x86_64 --output=myapp --force-name
```

## Script Overview

### `modify_or_create_spec_file(target, arch, output_name, spec_path=None, force_name=False)`
This function either modifies an existing spec file to add or update the `target_arch` field or creates a new spec file based on the specified `target`, `arch`, and `output_name`.

**Parameters**:
- `target`: The Python script to include in the spec file.
- `arch`: The architecture to target (e.g., `x86`, `x86_64`).
- `output_name`: The base name for the output files.
- `spec_path`: Path to an existing spec file to modify (optional).
- `force_name`: Boolean indicating if architecture suffix should be omitted from the output name.

### `build_executable(spec_file)`
Runs PyInstaller with the provided spec file to generate an executable.

**Parameters**:
- `spec_file`: Path to the spec file used for building the executable.

### `parse_arguments()`
Parses command-line arguments and returns the parsed arguments.

### `main()`
Main function that processes arguments, modifies/creates spec files as needed, and builds executables based on the arguments.

## Additional Notes

- **Output Naming**: By default, the architecture (`_x86` or `_x86_64`) is appended to the output file name. Use `--force-name` to prevent this.
- **Spec File Usage**: When `--spec` is provided, the script processes each spec file in the comma-separated list and builds an executable for each.

---

This script is useful for automating the PyInstaller build process, especially when targeting multiple architectures or reusing custom spec files.
