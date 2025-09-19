# Performance and Parallel Processing Guide

## Overview

The h2k2hpxml tool is optimized for high-performance batch processing of H2K files, featuring automatic parallel processing that can dramatically reduce processing time for large datasets.

## Parallel Processing Features

### Automatic Threading

When processing multiple H2K files (folder input), h2k2hpxml automatically utilizes parallel processing:

- **Thread Count**: `CPU cores - 1` threads
- **Example**: On a 24-core system, uses 23 threads
- **Minimum**: Always uses at least 1 thread
- **Automatic**: No configuration required

### How It Works

```python
# Internally uses Python's concurrent.futures
max_workers = max(1, os.cpu_count() - 1)
with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
    results = list(executor.map(process_file, h2k_files))
```

### Performance Benefits

| Files | Sequential Time | Parallel Time (24 cores) | Speedup |
|-------|----------------|--------------------------|---------|
| 10    | 10 minutes     | ~30 seconds             | 20x     |
| 100   | 100 minutes    | ~5 minutes              | 20x     |
| 1000  | 1000 minutes   | ~50 minutes             | 20x     |
| 6000+ | ~100 hours     | ~5 hours                | 20x     |

*Note: Actual speedup depends on file complexity and available CPU cores*

## Usage Examples

### Single File Processing

```bash
# Standard single file - no parallelization needed
h2k2hpxml input.h2k
```

### Folder Processing (Parallel)

```bash
# Process entire folder - automatic parallel processing
h2k2hpxml /path/to/h2k/files/

# With output directory
h2k2hpxml /path/to/h2k/files/ --output /path/to/output/

# Convert only (no simulation) - faster
h2k2hpxml /path/to/h2k/files/ --do-not-sim
```

## Optimization Tips

### 1. Hardware Optimization

**CPU Cores**
- More cores = better parallel performance
- Recommended: 8+ cores for large batch processing
- Cloud instances: Consider high-CPU instances for batch jobs

**Memory**
- Each thread needs ~500MB-1GB RAM
- For 24 threads: Ensure 16-24GB RAM available
- Monitor memory usage with `htop` or Task Manager

**Storage**
- Use SSD for input/output files
- Network storage may bottleneck performance
- Local processing is typically faster

### 2. Processing Optimization

**Convert-Only Mode**
```bash
# Skip simulation for faster conversion
h2k2hpxml /path/to/files/ --do-not-sim
```

**Skip Validation**
```bash
# Skip schema validation for speed (use with caution)
h2k2hpxml /path/to/files/ --skip-validation
```

**Selective Processing**
```bash
# Process specific file types
find /path -name "*.h2k" -mtime -7 | xargs -I {} h2k2hpxml {}
```

### 3. Batch Processing Strategies

**Chunking Large Datasets**
```bash
# Split 6000 files into chunks
mkdir chunk1 chunk2 chunk3
ls *.h2k | head -2000 | xargs -I {} mv {} chunk1/
ls *.h2k | head -2000 | xargs -I {} mv {} chunk2/
ls *.h2k | head -2000 | xargs -I {} mv {} chunk3/

# Process chunks in parallel
h2k2hpxml chunk1/ --output output1/ &
h2k2hpxml chunk2/ --output output2/ &
h2k2hpxml chunk3/ --output output3/ &
wait
```

**Using GNU Parallel**
```bash
# Process files with GNU parallel
find . -name "*.h2k" | parallel -j 20 h2k2hpxml {} --output {.}.xml
```

## Docker Performance

### Docker Optimization

```bash
# Increase Docker CPU limit
docker run --cpus="20" -v $(pwd):/data canmet/h2k-hpxml h2k2hpxml /data/

# Increase memory limit
docker run --memory="16g" -v $(pwd):/data canmet/h2k-hpxml h2k2hpxml /data/
```

### Docker Compose for Parallel Jobs

```yaml
version: '3.8'
services:
  converter1:
    image: canmet/h2k-hpxml
    volumes:
      - ./chunk1:/input:ro
      - ./output1:/output
    command: h2k2hpxml /input/ --output /output/
    
  converter2:
    image: canmet/h2k-hpxml
    volumes:
      - ./chunk2:/input:ro
      - ./output2:/output
    command: h2k2hpxml /input/ --output /output/
    
  converter3:
    image: canmet/h2k-hpxml
    volumes:
      - ./chunk3:/input:ro
      - ./output3:/output
    command: h2k2hpxml /input/ --output /output/
```

## Cloud Processing

### AWS EC2 Example

```bash
# Use compute-optimized instance (c5.12xlarge - 48 vCPUs)
# Will use 47 threads for processing

# Install and run
curl -LsSf https://astral.sh/uv/install.sh | sh
uv pip install git+https://github.com/canmet-energy/h2k-hpxml.git@refactor
h2k-deps --auto-install
h2k2hpxml /data/h2k_files/ --output /data/output/
```

### Azure Batch Processing

```yaml
# Azure Batch job configuration
pool:
  vmSize: Standard_F32s_v2  # 32 vCPUs
  maxTasksPerNode: 31       # Leave 1 CPU for system

task:
  commandLine: h2k2hpxml /mnt/batch/tasks/working/input/ --output /mnt/batch/tasks/output/
  resourceFiles:
    - blobSource: https://storage.blob.core.windows.net/h2k-files
      filePath: input/
```

## Monitoring Performance

### System Monitoring

```bash
# Monitor CPU usage
htop  # Linux/Mac
# or
top -H  # Show threads

# Monitor specific process
pidstat -t -p $(pgrep h2k2hpxml) 1

# Monitor I/O
iotop
```

### Application Monitoring

The tool logs thread count at startup:
```
INFO - Processing files with 23 threads...
```

Monitor progress via log files:
```bash
# Watch log output
tail -f processing.log

# Count completed files
ls output/*/*.xml | wc -l
```

### Performance Metrics

Check `processing_results.md` for:
- Failed conversions
- Processing errors
- Time per file (if logged)

## Benchmarking

### Simple Benchmark Script

```bash
#!/bin/bash
# benchmark.sh
echo "Starting benchmark at $(date)"
START=$(date +%s)

h2k2hpxml /path/to/test/files/ --output /tmp/benchmark/

END=$(date +%s)
DIFF=$(( $END - $START ))
FILES=$(ls /path/to/test/files/*.h2k | wc -l)

echo "Processed $FILES files in $DIFF seconds"
echo "Average: $(( $DIFF / $FILES )) seconds per file"
```

### Performance Testing

```python
# test_performance.py
import time
import os
from pathlib import Path

def benchmark_processing(input_dir, output_dir):
    start = time.time()
    
    # Count input files
    h2k_files = list(Path(input_dir).glob("*.h2k"))
    file_count = len(h2k_files)
    
    # Run conversion
    os.system(f"h2k2hpxml {input_dir} --output {output_dir}")
    
    # Calculate metrics
    elapsed = time.time() - start
    files_per_second = file_count / elapsed
    
    print(f"Performance Metrics:")
    print(f"  Files processed: {file_count}")
    print(f"  Total time: {elapsed:.2f} seconds")
    print(f"  Files/second: {files_per_second:.2f}")
    print(f"  Seconds/file: {elapsed/file_count:.2f}")
    
benchmark_processing("/path/to/files", "/path/to/output")
```

## Troubleshooting Performance Issues

### Slow Processing

1. **Check CPU usage**
   - If low: May be I/O bound
   - If single core maxed: Check thread count

2. **Check memory**
   - Swapping will severely impact performance
   - Reduce thread count if memory limited

3. **Check disk I/O**
   - Move to SSD if using HDD
   - Check network latency for network storage

### Thread Count Issues

```bash
# Override thread count (if needed)
# This would require code modification to support MAX_WORKERS env variable
export MAX_WORKERS=10
h2k2hpxml /path/to/files/
```

### Memory Issues

```bash
# Limit thread count to reduce memory usage
# Process in smaller batches
find . -name "*.h2k" | head -100 | xargs -I {} h2k2hpxml {}
```

## Best Practices

1. **Use folder processing** for multiple files (automatic parallelization)
2. **Ensure adequate RAM** (1GB per thread minimum)
3. **Use SSDs** for input/output files
4. **Monitor system resources** during processing
5. **Process overnight** for large batches
6. **Use `--do-not-sim`** if only conversion needed
7. **Split very large datasets** into manageable chunks
8. **Use cloud computing** for massive datasets (6000+ files)

## Performance Roadmap

Future improvements being considered:
- Configurable thread count via environment variable
- Progress bars for batch processing
- Estimated time remaining
- Performance profiling options
- Distributed processing support
- GPU acceleration for simulations

## See Also

- [Docker Guide](DOCKER.md) - For containerized processing
- [Installation Guide](INSTALLATION.md) - For optimal setup
- [Development Guide](DEVELOPMENT.md) - For performance contributions