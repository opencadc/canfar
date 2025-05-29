# Download ALMA Data (Using Transfer Script)

**Alternative method**: Transfer a download script from your local computer and run it in a CANFAR session.

## 📋 Overview

There are two ways to download ALMA archive data in CANFAR:

1. **Direct web download** - Use Firefox in your Desktop session ([see tutorial](archive-download.md))
2. **Transfer script method** - Generate the script locally, transfer it to CANFAR, then run it (this tutorial)

## 🎯 When to Use This Method

**Best for**:
- Complex archive queries done on your local machine
- Situations where you already have download scripts prepared locally
- When you prefer using the archive interface on your own computer with better internet

## 📚 Prerequisites

1. **ALMA archive query experience** - Review this instructional video: [ALMA Archive Video Tutorials](https://almascience.nrao.edu/alma-data/archive/archive-video-tutorials)
2. **Download script generated** on your local computer from the ALMA archive
3. **CANFAR account** with Desktop session access

## 🚀 Step-by-Step Process

### Step 1: Generate Download Script (Local Computer)

1. Visit the [ALMA Science Archive](https://almascience.nrao.edu/aq/) on your local computer
2. Use the query interface to locate your desired datasets
3. Select datasets and generate a download script
4. Save the script file (usually named something like `script_request_XXXXX.sh`)

### Step 2: Transfer Script to CANFAR

Choose one of these [data transfer methods](../data-transfer-guide.md):

- **Web upload**: Use the [web file manager](../user-guide/web-file-manager.md)
- **sshfs**: Mount your CANFAR storage and copy files directly
- **VOSpace tools**: Use `vcp` command-line tool

**Example using sshfs**:
```bash
# On your local computer
cp script_request_12345.sh ~/canfar/arc/projects/yourproject/scripts/
```

### Step 3: Run Script in CANFAR Session

1. **Launch a Desktop session** - Follow the [Desktop launch guide](../user-guide/launch-desktop.md)
2. **Open a terminal** - Double-click the terminal icon
3. **Navigate to your script**:
   ```bash
   cd /arc/projects/yourproject/scripts/
   ```
4. **Make script executable**:
   ```bash
   chmod +x script_request_12345.sh
   ```
5. **Run the download**:
   ```bash
   ./script_request_12345.sh
   ```

### Step 4: Monitor Download Progress

The script will show download progress and save data to your current directory. Large downloads may take considerable time.

## 💡 Tips and Best Practices

- **Check disk space**: Ensure sufficient space in `/arc/projects/yourproject/` before starting large downloads
- **Use appropriate session**: Desktop sessions work well for moderate downloads; consider headless containers for very large batch downloads
- **Organize data**: Create subdirectories like `/arc/projects/yourproject/data/alma_2023/` for organization

## 🔗 Related Documentation

- **[Direct ALMA download tutorial](archive-download.md)** - Download directly in CANFAR sessions
- **[Complete data transfer guide](../data-transfer-guide.md)** - All methods for moving files to/from CANFAR
- **[Desktop session guide](../user-guide/launch-desktop.md)** - Setting up your interactive environment
