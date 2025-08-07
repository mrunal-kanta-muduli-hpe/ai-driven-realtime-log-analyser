# Sample Data Directory

This directory is for sample log files used for testing and demonstration.

## Usage

Place your log files here for analysis:

```bash
# Example: Copy your log files
cp /path/to/your/logfile.log sample-data/

# Run analysis
python main.py --log-file sample-data/logfile.log
```

## Supported Formats

- JSON formatted logs
- Plain text logs with timestamps
- Common log formats (Apache, Nginx, etc.)

## File Size Recommendations

- Keep sample files under 100MB for GitHub compatibility
- For larger files, use Git LFS or external storage
- Use compressed formats (.gz) for large datasets

## Demo Files

For demonstration purposes, you can generate sample logs using the demo script:

```bash
./demo.sh
```

This will create sample log files automatically for testing the AI log analyzer.
