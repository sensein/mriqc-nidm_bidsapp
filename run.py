#!/usr/bin/env python3
"""
MRIQC to NIDM converter BIDS App
This app takes MRIQC output and converts the QC metrics into NIDM format.
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime
import tempfile
from typing import Dict, List, Optional
import pandas as pd
from bids import BIDSLayout

def setup_logging(output_dir: Path, verbose: bool = False) -> logging.Logger:
    """Set up logging configuration."""
    log_dir = output_dir / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    log_file = log_dir / f'mriqc-nidm-{timestamp}.log'
    
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger('mriqc-nidm')

def remove_keys(my_dict: Dict, keys_to_remove: List[str]) -> Dict:
    """Removes multiple keys from a dictionary."""
    for key in keys_to_remove:
        my_dict.pop(key, None)
    return my_dict

def extract_metadata(data: Dict) -> Dict[str, str]:
    """Extract metadata from the bids_meta field."""
    metadata = {}
    if 'bids_meta' in data:
        bids_meta = data['bids_meta']
        metadata['subject_id'] = bids_meta.get('subject', '')
        metadata['modality'] = bids_meta.get('modality', '')
        metadata['datatype'] = bids_meta.get('datatype', '')
        metadata['suffix'] = bids_meta.get('suffix', '')
    return metadata

def generate_source_url(json_file: str) -> str:
    """Generate source URL from the input JSON file path."""
    path = Path(json_file)
    parent_dir = path.parent.parent
    subject_id = path.parts[-3]  # sub-0051456
    html_file = f"{subject_id}_{path.stem}.html"
    source_url = str(parent_dir / html_file)
    return source_url

def convert_json_to_csv(json_file: Path, csv_file: Path, logger: logging.Logger) -> bool:
    """Convert MRIQC JSON file to CSV format."""
    try:
        # Read the JSON file
        with open(json_file, 'r') as f:
            data = json.load(f)

        # Extract metadata
        metadata = extract_metadata(data)
        
        # Delete unwanted items
        keys_to_drop = [
            'bids_meta', 'provenance', 'qi_1', 'qi_2',
            'size_x', 'size_y', 'size_z',
            'spacing_x', 'spacing_y', 'spacing_z'
        ]
        updated_data = remove_keys(data, keys_to_drop)

        # Add required fields
        updated_data.update({
            'subject_id': metadata.get('subject_id', ''),
            'ses': '',  # Empty if not provided
            'task': '',  # Empty if not provided
            'run': '',   # Empty if not provided
            'source_url': generate_source_url(str(json_file))
        })

        # Convert to DataFrame
        df = pd.DataFrame(updated_data, index=[0])

        # Reorder columns
        cols = df.columns.tolist()
        cols.remove('subject_id')
        cols.remove('ses')
        cols.remove('task')
        cols.remove('run')
        cols.remove('source_url')
        
        new_cols = ['subject_id', 'ses', 'task', 'run'] + cols + ['source_url']
        df = df[new_cols]

        # Write CSV
        df.to_csv(csv_file, index=False)
        logger.info(f"Successfully converted {json_file} to {csv_file}")
        return True

    except Exception as e:
        logger.error(f"Error converting {json_file} to CSV: {str(e)}")
        return False

def process_subject(mriqc_dir: Path, output_dir: Path, subject_id: str, logger: logging.Logger) -> bool:
    """Process MRIQC output for a single subject."""
    try:
        subject_dir = mriqc_dir / f"sub-{subject_id}"
        if not subject_dir.exists():
            logger.error(f"Subject directory not found: {subject_dir}")
            return False
            
        # Process anatomical data
        anat_dir = subject_dir / "anat"
        if anat_dir.exists():
            for json_file in anat_dir.glob("*.json"):
                # Create output directories
                nidm_dir = output_dir / f"sub-{subject_id}" / "nidm"
                nidm_dir.mkdir(parents=True, exist_ok=True)
                
                # Convert JSON to CSV
                csv_file = nidm_dir / f"{json_file.stem}.csv"
                if not convert_json_to_csv(json_file, csv_file, logger):
                    continue
                
                # Convert CSV to NIDM
                ttl_file = nidm_dir / f"{json_file.stem}.ttl"
                cmd = f"csv2nidm -csv {csv_file} -csv_map /opt/mriqc-nidm/mriqc_dictionary_v1.csv -no_concepts -derivative /opt/mriqc-nidm/mriqc_software_metadata.csv -out {ttl_file}"
                
                if os.system(cmd) != 0:
                    logger.error(f"Failed to convert {csv_file} to NIDM")
                    continue
                    
                logger.info(f"Created NIDM file: {ttl_file}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error processing subject {subject_id}: {str(e)}")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='MRIQC to NIDM converter BIDS App')
    
    # Required arguments
    parser.add_argument('mriqc_dir', help='The directory containing MRIQC output')
    parser.add_argument('output_dir', help='The directory where NIDM files should be stored')
    parser.add_argument('analysis_level', choices=['participant'], help='Processing level')
    
    # Optional arguments
    parser.add_argument('--participant-label', help='The label(s) of the participant(s) to analyze')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('--version', action='version', version='MRIQC-NIDM BIDS-App v0.1.0')
    
    args = parser.parse_args()
    
    # Convert input args to Path objects
    mriqc_dir = Path(args.mriqc_dir)
    output_dir = Path(args.output_dir)
    
    # Set up logging
    logger = setup_logging(output_dir, args.verbose)
    logger.info("Starting MRIQC to NIDM conversion")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process specific subjects or all subjects
    if args.participant_label:
        subjects = args.participant_label.split()
    else:
        # Get all subject directories in MRIQC output
        subjects = [d.name[4:] for d in mriqc_dir.glob('sub-*')]
    
    if not subjects:
        logger.error("No subjects found to process")
        return 1
    
    # Process each subject
    success = True
    for subject_id in subjects:
        logger.info(f"Processing subject: {subject_id}")
        if not process_subject(mriqc_dir, output_dir, subject_id, logger):
            success = False
    
    if success:
        logger.info("MRIQC to NIDM conversion completed successfully")
        return 0
    else:
        logger.error("Some subjects failed to process")
        return 1

if __name__ == "__main__":
    sys.exit(main())

