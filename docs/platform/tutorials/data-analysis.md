# Data Analysis with Jupyter

Comprehensive guide to data analysis workflows using Jupyter notebooks on CANFAR.

## 🚀 Quick Start

### Launching Jupyter
1. Go to [CANFAR Portal](https://www.canfar.net)
2. Click "Launch" → "Notebook"
3. Choose your preferred container (Python, R, or multi-language)
4. Wait ~30 seconds for startup

[**→ Detailed Launch Guide**](../general/NewUser/LaunchNotebook.md){ .md-button }

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
# Load and examine data
from astropy.io import fits
from astropy.table import Table
import matplotlib.pyplot as plt

# Load FITS file from project storage
data = fits.open('/arc/projects/your-group/data/observation.fits')
catalog = Table.read('/arc/projects/your-group/data/catalog.csv')

# Basic analysis
print(f"Image shape: {data[0].data.shape}")
print(f"Catalog entries: {len(catalog)}")

# Create publication-quality plot
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# Display image
ax1.imshow(data[0].data, origin='lower', cmap='viridis')
ax1.set_title('Observation')

# Plot catalog data  
ax2.scatter(catalog['ra'], catalog['dec'], alpha=0.6)
ax2.set_xlabel('RA (deg)')
ax2.set_ylabel('Dec (deg)')
ax2.set_title('Source Catalog')

plt.tight_layout()
plt.savefig('/arc/projects/your-group/results/analysis_plot.png', dpi=300)
plt.show()
```

---

## 📊 R Environment

### Pre-installed Packages

```r
# Astronomy and data analysis
library(FITSio)          # FITS file handling
library(astro)           # Astronomy calculations  
library(celestial)       # Coordinate transformations

# Data science
library(tidyverse)       # Data manipulation and visualization
library(data.table)      # Fast data handling
library(ggplot2)         # Advanced plotting
library(plotly)          # Interactive plots
library(shiny)           # Web applications
```

### Sample R Workflow

```r
# Load astronomy data
library(FITSio)
library(tidyverse)

# Read FITS table
catalog <- readFITS("/arc/projects/your-group/data/catalog.fits")$col

# Convert to data frame and analyze
df <- as.data.frame(catalog)
summary(df)

# Create publication plot
p <- ggplot(df, aes(x = magnitude, y = color)) +
  geom_point(alpha = 0.6) +
  labs(title = "Color-Magnitude Diagram",
       x = "Magnitude", y = "Color Index") +
  theme_minimal()

# Save plot
ggsave("/arc/projects/your-group/results/cmd.png", p, 
       width = 8, height = 6, dpi = 300)
print(p)
```

---

## 🔬 Advanced Analysis Examples

### Time Series Analysis
```python
from astropy.timeseries import TimeSeries
from astropy.time import Time
import numpy as np

# Load time series data
ts = TimeSeries.read('/arc/projects/your-group/data/lightcurve.csv')

# Period analysis
from astropy.timeseries import LombScargle
frequency, power = LombScargle(ts['time'], ts['flux']).autopower()
best_period = 1 / frequency[np.argmax(power)]
print(f"Best period: {best_period:.3f} days")
```

### Image Processing
```python
from photutils import DAOStarFinder
from astropy.stats import sigma_clipped_stats

# Load image
image = fits.getdata('/arc/projects/your-group/data/field.fits')

# Find stars
mean, median, std = sigma_clipped_stats(image, sigma=3.0)
daofind = DAOStarFinder(fwhm=3.0, threshold=5.*std)
sources = daofind(image - median)

print(f"Found {len(sources)} sources")
```

### Database Queries
```python
from astroquery.simbad import Simbad
from astroquery.vizier import Vizier

# Query SIMBAD for object information
result = Simbad.query_object("M31")
print(result)

# Query Vizier catalogs
v = Vizier(columns=["*", "+_r"])
catalogs = v.query_region("M31", radius="30m")
```

---

## 📁 Data Management Best Practices

### File Organization
```
/arc/projects/your-group/
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_photometry_analysis.ipynb  
│   ├── 03_final_results.ipynb
│   └── utilities/
│       └── helper_functions.py
├── data/
│   ├── raw/              # Original data files
│   ├── processed/        # Cleaned/calibrated data
│   └── external/         # Reference catalogs, etc.
└── results/
    ├── figures/          # Publication plots
    ├── tables/           # Output catalogs
    └── reports/          # Summary documents
```

### Sharing Notebooks
```python
# At the top of shared notebooks, add:
import sys
sys.path.append('/arc/projects/your-group/notebooks/utilities')
from helper_functions import *

# This allows team members to use shared code
```

---

## 🔄 File Transfer

### Getting Data In
```python
# Download from archive within notebook
import requests
from astroquery.mast import Observations

# Query and download Hubble data
obs = Observations.query_criteria(obs_id="your-observation-id")
data_products = Observations.get_product_list(obs)
Observations.download_products(data_products, 
                             download_dir="/arc/projects/your-group/data/raw/")
```

### Moving Results Out
- **Small files**: Download directly from the notebook interface
- **Large datasets**: Use [file transfer tools](../general/General_tools/File_transfers.md)
- **Plots and tables**: Use the web file manager

[**→ Complete File Transfer Guide**](../general/General_tools/File_transfers.md){ .md-button }

---

## 🎯 Tips for Efficient Analysis

### Performance Optimization
```python
# Use chunked processing for large datasets
import dask.array as da

# Load large FITS file as dask array
large_image = da.from_array(fits.getdata('huge_image.fits'), chunks=(1024, 1024))

# Process in chunks
result = large_image.mean(axis=0).compute()
```

### Reproducible Science
```python
# Always set random seeds
np.random.seed(42)

# Document package versions
import pkg_resources
packages = ['astropy', 'numpy', 'matplotlib', 'scipy']
for package in packages:
    version = pkg_resources.get_distribution(package).version
    print(f"{package}: {version}")
```

### Collaboration
- Use clear notebook names and organization
- Add markdown cells explaining each analysis step
- Include contact information and dates
- Save key results to shared directories

---

## 🆘 Getting Help

### Common Issues
- **Kernel crashes**: Usually memory issues - try processing smaller chunks
- **Missing packages**: Contact support to request additional libraries
- **Slow performance**: Check if data is in `/arc/projects/` for faster access

### Resources
- **Python help**: [Astropy documentation](https://docs.astropy.org/)
- **R help**: [CRAN Astronomy Task View](https://cran.r-project.org/web/views/Astronomy.html)
- **CANFAR support**: [Slack channel](https://cadc.slack.com/archives/C01K60U5Q87)
- **General questions**: [support@canfar.net](mailto:support@canfar.net)
