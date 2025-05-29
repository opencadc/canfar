# Data Analysis with Jupyter

Comprehensive guide to data analysis workflows using Jupyter notebooks on CANFAR.

## 🚀 Quick Start

### Launching Jupyter

1. Go to [CANFAR Portal](https://www.canfar.net)
2. Click "Launch" → "Notebook"
3. Choose your preferred container (Python, R, or multi-language)
4. Wait ~30 seconds for startup

[**→ Detailed Launch Guide**](../user-guide/launch-notebook.md){ .md-button }

---

## 🐍 Python Data Science Environment

### Pre-installed Libraries

The notebook containers come with a comprehensive astronomy and data science stack:

**Astronomy Libraries**:

```python
import astropy            # Core astronomy library
import astroquery         # Query astronomical databases  
import photutils          # Photometry tools
import specutils          # Spectroscopy tools
import reproject          # Image reprojection
import astroml            # Machine learning for astronomy
```

**Data Science Core**:

```python
import numpy as np        # Numerical computing
import pandas as pd       # Data manipulation
import matplotlib.pyplot as plt  # Plotting
import scipy              # Scientific computing
import scikit-learn       # Machine learning
import seaborn            # Statistical visualization
```

**Image Processing**:

```python
import skimage            # Image processing
import opencv             # Computer vision
import PIL                # Image manipulation
```

### Sample Analysis Workflow

```python
# Load and examine astronomical data
from astropy.io import fits
from astropy.wcs import WCS
import matplotlib.pyplot as plt

# Open FITS file
hdul = fits.open('/arc/projects/your-group/data/image.fits')
data = hdul[0].data
header = hdul[0].header

# Create WCS object for coordinate transformations
wcs = WCS(header)

# Display image with proper coordinates
plt.figure(figsize=(10, 8))
plt.subplot(projection=wcs)
plt.imshow(data, origin='lower', cmap='viridis')
plt.xlabel('RA')
plt.ylabel('Dec')
plt.title('Astronomical Image')
plt.colorbar(label='Flux')
plt.show()
```

---

## 📊 Common Analysis Tasks

### Time Series Analysis

```python
import pandas as pd
import numpy as np
from astropy.time import Time
import matplotlib.pyplot as plt

# Load time series data
data = pd.read_csv('/arc/projects/your-group/data/lightcurve.csv')

# Convert to astropy Time objects for proper handling
times = Time(data['mjd'], format='mjd')

# Plot time series
plt.figure(figsize=(12, 6))
plt.plot(times.datetime, data['magnitude'], 'o-')
plt.xlabel('Date')
plt.ylabel('Magnitude')
plt.title('Light Curve Analysis')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
```

### Image Processing

```python
from photutils import DAOStarFinder
from astropy.stats import sigma_clipped_stats

# Background subtraction and source detection
mean, median, std = sigma_clipped_stats(data, sigma=3.0)
daofind = DAOStarFinder(fwhm=3.0, threshold=5.*std)
sources = daofind(data - median)

# Display results
print(f'Found {len(sources)} sources')
plt.figure(figsize=(10, 8))
plt.imshow(data, origin='lower', cmap='gray', vmin=median-std, vmax=median+10*std)
plt.scatter(sources['xcentroid'], sources['ycentroid'], 
           s=50, facecolors='none', edgecolors='red')
plt.title('Detected Sources')
plt.show()
```

### Database Queries

```python
from astroquery.simbad import Simbad
from astroquery.vizier import Vizier

# Query SIMBAD for object information
result = Simbad.query_object("M31")
print(result['MAIN_ID', 'RA', 'DEC', 'OTYPE'])

# Query VizieR catalogs
v = Vizier(columns=['*'], row_limit=1000)
catalogs = v.query_region("M31", radius="30m", catalog="II/246")
for catalog in catalogs:
    print(f"Found {len(catalog)} sources")
```

---

## 💾 Data Management

### File Organization

Best practices for organizing your analysis:

```text
/arc/projects/your-group/
├── data/
│   ├── raw/              # Original data files
│   ├── processed/        # Cleaned/calibrated data
│   └── catalogs/         # Reference catalogs
├── notebooks/
│   ├── exploration/      # Initial data exploration
│   ├── analysis/         # Main analysis notebooks
│   └── results/          # Final results and plots
├── code/
│   ├── utils.py          # Utility functions
│   └── plotting.py       # Custom plotting functions
└── output/
    ├── plots/            # Generated figures
    └── tables/           # Output catalogs
```

### Sharing Notebooks

```python
# Always include this cell at the top of shared notebooks
import sys
sys.path.append('/arc/projects/your-group/code')

# Document your environment
import astropy
import numpy as np
print(f"Astropy version: {astropy.__version__}")
print(f"NumPy version: {np.__version__}")

# Set reproducible random seeds
np.random.seed(42)
```

---

## 🔄 Data Input/Output

### Getting Data In

```python
# Download directly from within notebook
import urllib.request
import os

# Create data directory if it doesn't exist
os.makedirs('/arc/projects/your-group/data', exist_ok=True)

# Download file
url = "https://example.com/data.fits"
local_path = "/arc/projects/your-group/data/data.fits"
urllib.request.urlretrieve(url, local_path)
```

### Moving Results Out

- **Small files**: Download directly from the notebook interface
- **Large results**: Use the [data transfer guide](../data-transfer-guide.md)
- **Sharing**: All files in `/arc/projects` are shared with your group

---

## ⚡ Performance Optimization

### Memory Management

```python
# Monitor memory usage
import psutil
import os

def check_memory():
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / 1024 / 1024
    print(f"Current memory usage: {memory_mb:.1f} MB")

# Use memory-efficient operations
# Instead of loading everything at once:
# data = fits.getdata('huge_file.fits')

# Use memory mapping:
with fits.open('huge_file.fits', memmap=True) as hdul:
    # Work with data in chunks
    data_chunk = hdul[0].data[0:1000, 0:1000]
```

### Parallel Processing

```python
from multiprocessing import Pool
import numpy as np

def process_chunk(data_chunk):
    # Your processing function here
    return np.mean(data_chunk)

# Split work across multiple cores
if __name__ == '__main__':
    data_chunks = np.array_split(large_array, 4)
    with Pool(4) as pool:
        results = pool.map(process_chunk, data_chunks)
```

---

## 🔬 Reproducible Science

### Version Control

```python
# Document your analysis environment
def log_environment():
    import sys
    import astropy, numpy, matplotlib
    
    print("=== Analysis Environment ===")
    print(f"Python: {sys.version}")
    print(f"Astropy: {astropy.__version__}")
    print(f"NumPy: {numpy.__version__}")
    print(f"Matplotlib: {matplotlib.__version__}")
    
    # Log analysis parameters
    print("=== Analysis Parameters ===")
    print(f"Filter: {filter_name}")
    print(f"Exposure time: {exp_time}")
    print(f"Date: {observation_date}")

log_environment()
```

### Saving Analysis State

```python
import pickle
import joblib

# Save complex objects
analysis_state = {
    'parameters': parameters,
    'results': results,
    'figures': fig_data
}

# Use pickle for Python objects
with open('/arc/projects/your-group/analysis_state.pkl', 'wb') as f:
    pickle.dump(analysis_state, f)

# Use joblib for NumPy arrays (more efficient)
joblib.dump(large_array, '/arc/projects/your-group/processed_data.joblib')
```

---

## 🤝 Collaboration

Best practices for team analysis:

- Use clear notebook names and organization
- Include markdown cells explaining your approach
- Save intermediate results that others can use
- Document data sources and processing steps
- Use version control for shared code

---

## 🆘 Common Issues

### Troubleshooting

- **Kernel crashes**: Usually memory issues - try processing smaller chunks
- **Slow performance**: Check if you're working in `/arc/projects` (fastest storage)
- **Missing packages**: Contact support to add packages to containers
- **Connection timeouts**: Refresh browser, sessions auto-save work

### Resources

- **Python help**: [Astropy documentation](https://docs.astropy.org/)
- **Jupyter tips**: [Jupyter documentation](https://jupyter.org/documentation)
- **CANFAR support**: [FAQ](../help/faq.md) or [Slack](https://cadc.slack.com/archives/C01K60U5Q87)
