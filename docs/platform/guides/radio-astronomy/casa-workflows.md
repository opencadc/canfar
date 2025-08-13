# CASA Desktop Workflows

Advanced CASA workflows and desktop integration for radio astronomy data analysis on the CANFAR Science Platform.

!!! abstract "🎯 What You'll Learn"
    - How to launch and work efficiently with CASA in desktop sessions
    - Advanced calibration, imaging, and self-calibration workflows
    - Integration patterns with DS9 and CARTA
    - Parallel strategies, memory management, and automation

## Overview

This guide covers sophisticated CASA workflows that leverage the desktop environment for complex analysis, visualization, and data processing tasks.

## Desktop CASA Setup

### Launching CASA Desktop

1. **Start Desktop Session**:
   - Go to [CANFAR Portal](https://www.canfar.net)
   - Click "Desktop" session
   - Choose `radio-astronomy/casa` container
   - Set resources: 4+ cores, 8+ GB RAM for large datasets

2. **Open CASA**:
   - Click desktop "Applications" menu
   - Navigate to "Science" → "CASA"
   - Or open terminal and type `casa`

!!! warning "Persistence Reminder"
    Save important results to `/arc/projects/` or `/arc/home/`. Temporary locations or session-local directories may not persist after session end.

### Desktop Environment Advantages

- **Multiple CASA sessions**: Run parallel analysis tasks
- **GUI tools**: Access plotms, casaviewer, casabrowser
- **File management**: Visual file browser with FITS preview
- **External tools**: Use ds9, CARTA, Python IDEs alongside CASA
- **Session persistence**: Keep analysis state across disconnections

## Advanced Analysis Workflows

### Multi-Dataset Calibration Pipeline

```python
# casa_calibration_pipeline.py
import os
import glob


def full_calibration_pipeline(raw_data_dir, output_dir):
    """Complete calibration pipeline for multiple datasets"""

    # Setup directories
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Find all measurement sets
    ms_list = glob.glob(f"{raw_data_dir}/*.ms")

    for ms in ms_list:
        print(f"Processing {ms}")

        # 1. Initial flagging
        flagdata(vis=ms, mode="manual", autocorr=True, flagbackup=True)

        # 2. Set flux scale
        setjy(vis=ms, field="3C48", standard="Perley-Butler-2017")  # Calibrator

        # 3. Bandpass calibration
        bp_table = f"{output_dir}/{os.path.basename(ms)}.B1"
        bandpass(vis=ms, caltable=bp_table, field="3C48", solint="inf", combine="scan")

        # 4. Phase calibration
        phase_table = f"{output_dir}/{os.path.basename(ms)}.G1"
        gaincal(
            vis=ms,
            caltable=phase_table,
            field="3C48",
            calmode="p",
            solint="int",
            gaintable=[bp_table],
        )

        # 5. Amplitude calibration
        amp_table = f"{output_dir}/{os.path.basename(ms)}.G2"
        gaincal(
            vis=ms,
            caltable=amp_table,
            field="3C48",
            calmode="ap",
            solint="inf",
            gaintable=[bp_table, phase_table],
        )

        # 6. Apply calibrations
        applycal(
            vis=ms,
            field="",  # All fields
            gaintable=[bp_table, phase_table, amp_table],
            gainfield=["3C48", "3C48", "3C48"],
        )

        # 7. Split calibrated data
        output_ms = f"{output_dir}/{os.path.basename(ms)}_calibrated.ms"
        split(vis=ms, outputvis=output_ms, datacolumn="corrected")

        print(f"Calibration complete: {output_ms}")


# Run pipeline
full_calibration_pipeline(
    "/arc/projects/survey/raw/", "/arc/projects/survey/calibrated/"
)
```

### Imaging Workflow with Quality Assessment

```python
# casa_imaging_workflow.py


def imaging_workflow_with_qa(ms_file, target_field, output_dir):
    """Comprehensive imaging with quality assessment"""

    import matplotlib.pyplot as plt
    import numpy as np

    base_name = f"{output_dir}/{target_field}"

    # 1. Initial dirty image for assessment
    tclean(
        vis=ms_file,
        imagename=f"{base_name}_dirty",
        field=target_field,
        imsize=[1024, 1024],
        cell=["2arcsec"],
        niter=0,  # Dirty image
        deconvolver="hogbom",
    )

    # 2. Analyze dirty image for parameters
    ia.open(f"{base_name}_dirty.image")
    stats = ia.statistics()
    peak = stats["max"][0]
    rms = stats["rms"][0]
    dynamic_range = peak / rms
    ia.close()

    print(f"Dirty image stats:")
    print(f"  Peak: {peak:.3e} Jy/beam")
    print(f"  RMS: {rms:.3e} Jy/beam")
    print(f"  Dynamic range: {dynamic_range:.1f}")

    # 3. Determine cleaning parameters
    threshold = 3 * rms  # 3-sigma threshold
    niter = min(10000, int(dynamic_range * 100))

    # 4. Clean image
    tclean(
        vis=ms_file,
        imagename=f"{base_name}_clean",
        field=target_field,
        imsize=[1024, 1024],
        cell=["2arcsec"],
        niter=niter,
        threshold=f"{threshold}Jy",
        deconvolver="multiscale",
        scales=[0, 6, 18],
        gain=0.1,
        cycleniter=1000,
        usemask="auto-multithresh",
        interactive=False,
    )

    # 5. Primary beam correction
    impbcor(
        imagename=f"{base_name}_clean.image",
        pbimage=f"{base_name}_clean.pb",
        outfile=f"{base_name}_clean.pbcor",
        overwrite=True,
    )

    # 6. Generate diagnostic plots
    create_qa_plots(f"{base_name}_clean", target_field)

    print(f"Imaging complete: {base_name}_clean.pbcor")


def create_qa_plots(image_base, field_name):
    """Create quality assessment plots"""

    # Import CASA plotting tools
    from casaplotms import plotms

    # 1. uv-coverage plot
    plotms(
        vis=f"{image_base}.ms",
        xaxis="uvdist",
        yaxis="amp",
        avgtime="60s",
        plotfile=f"{image_base}_uvcoverage.png",
        showgui=False,
    )

    # 2. Image histogram
    ia.open(f"{image_base}.image")
    pixels = ia.getchunk()
    ia.close()

    plt.figure(figsize=(10, 6))
    plt.hist(pixels.flatten(), bins=100, alpha=0.7)
    plt.xlabel("Intensity (Jy/beam)")
    plt.ylabel("Number of pixels")
    plt.title(f"Intensity Distribution - {field_name}")
    plt.yscale("log")
    plt.savefig(f"{image_base}_histogram.png")
    plt.close()

    print(f"QA plots saved: {image_base}_*.png")


# Example usage
imaging_workflow_with_qa("calibrated_data.ms", "M31", "/arc/projects/m31/images/")
```

### Self-Calibration Loop

```python
# casa_selfcal.py


def self_calibration_loop(
    ms_file, source_field, output_dir, nloops=3, gain_solint=["inf", "30s", "10s"]
):
    """Iterative self-calibration"""

    base_name = f"{output_dir}/{source_field}"

    # Initial image
    current_ms = ms_file

    for loop in range(nloops):
        print(f"\n=== Self-cal loop {loop + 1} ===")

        # 1. Image current data
        img_name = f"{base_name}_selfcal{loop}"
        tclean(
            vis=current_ms,
            imagename=img_name,
            field=source_field,
            imsize=[512, 512],
            cell=["1arcsec"],
            niter=5000,
            threshold="0.1mJy",
            deconvolver="hogbom",
            interactive=False,
        )

        # 2. Calculate gain solutions
        cal_table = f"{base_name}_selfcal{loop}.gcal"
        gaincal(
            vis=current_ms,
            caltable=cal_table,
            field=source_field,
            gaintype="G",
            calmode="p",  # Phase-only first loops
            solint=gain_solint[min(loop, len(gain_solint) - 1)],
            refant="auto",
        )

        # 3. Apply calibration
        applycal(vis=current_ms, field=source_field, gaintable=[cal_table])

        # 4. Split corrected data for next loop
        if loop < nloops - 1:
            next_ms = f"{base_name}_selfcal{loop+1}.ms"
            split(
                vis=current_ms,
                outputvis=next_ms,
                field=source_field,
                datacolumn="corrected",
            )
            current_ms = next_ms

        # 5. Assess improvement
        assess_selfcal_improvement(img_name, loop)


def assess_selfcal_improvement(image_name, loop):
    """Assess self-calibration improvement"""

    ia.open(f"{image_name}.image")
    stats = ia.statistics()
    peak = stats["max"][0]
    rms = stats["rms"][0]
    ia.close()

    print(f"Loop {loop + 1} results:")
    print(f"  Peak: {peak*1000:.2f} mJy/beam")
    print(f"  RMS: {rms*1000:.2f} mJy/beam")
    print(f"  S/N: {peak/rms:.1f}")


# Run self-calibration
self_calibration_loop("target_data.ms", "NGC1068", "/arc/projects/agn/selfcal/")
```

## Integration with External Tools

### CASA + DS9 Workflow

```python
# casa_ds9_integration.py


def casa_to_ds9_analysis(casa_image, region_file=None):
    """Export CASA image to DS9 for detailed analysis"""

    # 1. Export to FITS
    fits_name = casa_image.replace(".image", ".fits")
    exportfits(imagename=casa_image, fitsimage=fits_name, overwrite=True)

    # 2. Launch DS9 with image
    os.system(f"ds9 {fits_name} &")

    # 3. If region file provided, load it
    if region_file:
        print(f"Load region file {region_file} in DS9")
        print("File → Region → Load")

    # 4. Return to CASA for further analysis
    print(f"Image {fits_name} loaded in DS9")
    print("Create regions in DS9, save as .reg file")
    print("Use importuvfits() to load back to CASA if needed")


# Usage
casa_to_ds9_analysis("M31_clean.image", "spiral_arms.reg")
```

### CASA + CARTA Integration

```python
# casa_carta_workflow.py


def casa_carta_cube_analysis(cube_ms, output_cube):
    """Create spectral cube for CARTA analysis"""

    # 1. Create spectral cube
    tclean(
        vis=cube_ms,
        imagename=output_cube,
        imsize=[256, 256, 1, 100],  # spatial + spectral
        cell=["2arcsec"],
        niter=1000,
        deconvolver="hogbom",
        specmode="cube",
        start="1.4GHz",
        width="1MHz",
        nchan=100,
    )

    # 2. Export for CARTA
    fits_cube = f"{output_cube}.fits"
    exportfits(imagename=f"{output_cube}.image", fitsimage=fits_cube, overwrite=True)

    # 3. Launch CARTA
    print(f"Load {fits_cube} in CARTA for:")
    print("- Spectral profile analysis")
    print("- Moment map generation")
    print("- Region statistics")
    print("- 3D visualization")

    return fits_cube


# Create cube for analysis
cube_fits = casa_carta_cube_analysis("line_data.ms", "HI_cube")
```

## Parallel Processing Strategies

### Multi-Core CASA Operations

```python
# casa_parallel.py
import multiprocessing as mp
import os


def parallel_imaging(ms_list, output_dir, ncores=None):
    """Image multiple datasets in parallel"""

    if ncores is None:
        ncores = mp.cpu_count() - 1

    def image_single_ms(ms_file):
        """Image a single measurement set"""
        base_name = os.path.basename(ms_file).replace(".ms", "")

        tclean(
            vis=ms_file,
            imagename=f"{output_dir}/{base_name}",
            imsize=[512, 512],
            cell=["2arcsec"],
            niter=1000,
            deconvolver="hogbom",
        )

        return f"Completed: {base_name}"

    # Use multiprocessing
    with mp.Pool(ncores) as pool:
        results = pool.map(image_single_ms, ms_list)

    for result in results:
        print(result)


# Process multiple observations
ms_files = glob.glob("/arc/projects/survey/*.ms")
parallel_imaging(ms_files, "/arc/projects/survey/images/", ncores=4)
```

### Memory-Efficient Large Dataset Processing

```python
# casa_memory_efficient.py


def process_large_cube(input_cube, chunk_size=10):
    """Process large spectral cubes in chunks"""

    # Get cube dimensions
    ia.open(input_cube)
    shape = ia.shape()
    nchans = shape[3]
    ia.close()

    # Process in chunks
    for start_chan in range(0, nchans, chunk_size):
        end_chan = min(start_chan + chunk_size, nchans)

        print(f"Processing channels {start_chan}-{end_chan}")

        # Extract channel subset
        chunk_name = f"temp_chunk_{start_chan}_{end_chan}"
        imsubimage(
            imagename=input_cube,
            outfile=chunk_name,
            box="",
            chans=f"{start_chan}~{end_chan}",
        )

        # Process chunk (example: smooth)
        imsmooth(
            imagename=chunk_name,
            outfile=f"{chunk_name}_smooth",
            kernel="gauss",
            major="3arcsec",
            minor="3arcsec",
        )

        # Clean up temporary files
        os.system(f"rm -rf {chunk_name}")

        print(f"Chunk {start_chan}-{end_chan} complete")


# Process 1000-channel cube in 50-channel chunks
process_large_cube("large_HI_cube.image", chunk_size=50)
```

!!! tip "Performance Planning"
    Imaging and spectral cubes can be resource-intensive. Plan for sufficient RAM and use chunking or parallelization where possible.

## Automation and Scripting

### Batch Processing Script

```bash
#!/bin/bash
# casa_batch_processing.sh

# Set up environment
export OMP_NUM_THREADS=4
export CASA_ENGINE_LOG_LEVEL=WARN

# Define directories
RAW_DIR="/arc/projects/survey/raw"
CAL_DIR="/arc/projects/survey/calibrated"  
IMG_DIR="/arc/projects/survey/images"

# Create output directories
mkdir -p $CAL_DIR $IMG_DIR

# Process all measurement sets
for ms_file in $RAW_DIR/*.ms; do
    echo "Processing $(basename $ms_file)"
    
    # Run CASA calibration
    casa --nogui -c "execfile('calibration_pipeline.py'); \
                     full_calibration_pipeline('$ms_file', '$CAL_DIR')"
    
    # Run imaging
    casa --nogui -c "execfile('imaging_workflow.py'); \
                     imaging_workflow('$CAL_DIR/$(basename $ms_file .ms)_cal.ms', '$IMG_DIR')"
done

echo "Batch processing complete"
```

### Quality Assessment Dashboard

```python
# casa_qa_dashboard.py
import glob
import matplotlib.pyplot as plt
import numpy as np


def generate_qa_dashboard(image_dir, output_html):
    """Generate HTML quality assessment dashboard"""

    images = glob.glob(f"{image_dir}/*.image")

    html_content = """
    <html>
    <head><title>CASA Processing QA Dashboard</title></head>
    <body>
    <h1>Quality Assessment Dashboard</h1>
    <table border="1">
    <tr><th>Image</th><th>Peak (mJy)</th><th>RMS (mJy)</th><th>Dynamic Range</th></tr>
    """

    for image in images:
        # Get statistics
        ia.open(image)
        stats = ia.statistics()
        peak = stats["max"][0] * 1000  # Convert to mJy
        rms = stats["rms"][0] * 1000
        dynamic_range = peak / rms
        ia.close()

        # Add to HTML
        base_name = os.path.basename(image)
        html_content += f"""
        <tr>
        <td>{base_name}</td>
        <td>{peak:.2f}</td>
        <td>{rms:.2f}</td>
        <td>{dynamic_range:.1f}</td>
        </tr>
        """

    html_content += """
    </table>
    </body>
    </html>
    """

    with open(output_html, "w") as f:
        f.write(html_content)

    print(f"QA dashboard saved: {output_html}")


# Generate dashboard
generate_qa_dashboard(
    "/arc/projects/survey/images/", "/arc/projects/survey/qa_dashboard.html"
)
```

## Best Practices

### Resource Management

- **Memory allocation**: Reserve 2GB per core for imaging
- **Disk space**: Allow 5x input data size for intermediate files
- **Parallel processing**: Use n-1 cores to maintain system responsiveness
- **Cleanup**: Remove temporary files regularly

### Workflow Organization

```python
# Directory structure for complex projects
project_structure = {
    "raw/": "Original measurement sets",
    "calibrated/": "Calibrated data",
    "images/": "Final images",
    "scripts/": "Processing scripts",
    "logs/": "Processing logs",
    "qa/": "Quality assessment outputs",
    "docs/": "Analysis documentation",
}
```

### Error Handling

```python
def robust_casa_operation(operation_func, *args, max_retries=3, **kwargs):
    """Execute CASA operation with error handling"""

    for attempt in range(max_retries):
        try:
            result = operation_func(*args, **kwargs)
            return result
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                print("Retrying...")
                time.sleep(5)
            else:
                print("Operation failed after all retries")
                raise e


# Usage
robust_casa_operation(tclean, vis="data.ms", imagename="output", niter=1000)
```
