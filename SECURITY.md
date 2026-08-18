# Security

Generated model programs are untrusted code. Do not run them directly on a host that contains credentials or writable research data. Use the supplied restricted Docker runner, keep networking disabled, mount only the submitted program into the writable working directory, and retain the CPU, memory, process, timeout, and capability restrictions. The input raster is evaluator data and must not be mounted into the model program's container.
