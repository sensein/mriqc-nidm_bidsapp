# MRIQC-NIDM Converter

A BIDS App that converts MRIQC output to NIDM format.

## Repository Structure

```
.
├── README.md                 # This file
├── LICENSE                   # License file
├── mriqc-nidm.def           # Apptainer definition file
├── Dockerfile               # Docker definition file
├── run.py                   # Main conversion script
├── mriqc_dictionary_v1.csv  # MRIQC to NIDM mapping
└── mriqc_software_metadata.csv  # Software metadata for NIDM
```

## Installation

### Using Apptainer

1. Build the container:
```bash
apptainer build mriqc-nidm.sif mriqc-nidm.def
```

2. Run the container:
```bash
apptainer run mriqc-nidm.sif /path/to/mriqc/output /path/to/output participant
```

### Using Docker

1. Build the container:
```bash
docker build -t mriqc-nidm .
```

2. Run the container:
```bash
docker run -v /path/to/mriqc/output:/data -v /path/to/output:/out mriqc-nidm /data /out participant
```

## Usage

The app takes MRIQC output and converts it to NIDM format. Basic usage:

```bash
mriqc-nidm <mriqc_dir> <output_dir> participant [options]
```

### Options

- `--participant-label`: Process specific participants
- `-v, --verbose`: Enable verbose output
- `--version`: Show version information

## License

See the [LICENSE](LICENSE) file for details. 
