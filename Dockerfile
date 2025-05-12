FROM nipreps/mriqc:latest

# Install additional required packages
RUN pip install --no-cache-dir \
    pandas \
    nidmresults \
    rdflib \
    pybids \
    pynidm

# Set working directory
WORKDIR /opt

# Copy the main script and required files
COPY run.py /opt/
COPY mriqc_dictionary_v1.csv /opt/
COPY mriqc_software_metadata.csv /opt/

# Make the script executable
RUN chmod +x /opt/run.py

# Set the entrypoint to our script
ENTRYPOINT ["/opt/run.py"] 