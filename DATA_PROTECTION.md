# Data Protection

## Security Measures Implemented

### 1. **Secure File Naming**
- Images are stored with hash-based filenames instead of predictable names
- Prevents unauthorized access through filename guessing
- Format: `{hash}.{ext}` (e.g., `a3f5b2c1d4e6f7g8.jpg`)

### 2. **File System Permissions**
- Directory permissions: `0700` (owner read/write/execute only)
- File permissions: `0600` (owner read/write only)
- Prevents unauthorized file system access

### 3. **Automatic Retention Policy**
- Images are automatically deleted after a configurable retention period
- Default: **90 days** (configurable via `IMAGE_RETENTION_DAYS` environment variable)
- Ensures personal data is not stored indefinitely

### 4. **Access Logging**
- All image access is logged with:
  - Attempt ID
  - Client IP address
  - Timestamp
- Provides audit trail for compliance

### 5. **Right to be Forgotten**
- Manual deletion endpoint available: `POST /delete_attempt_image/<attempt_id>`
- Allows immediate deletion of specific images upon request
- Deletion is logged for audit purposes

## Configuration

### Environment Variables

Add to your `.env` file:

```env
# Image retention period in days (default: 90)
IMAGE_RETENTION_DAYS=90

# Enable secure file naming (default: true)
SECURE_FILE_NAMING=true

# Enable access logging (default: true)
LOG_IMAGE_ACCESS=true
```

### Configuration File

Settings can also be configured in `backend/app/config/config.py`:

```python
IMAGE_RETENTION_DAYS = 90  # Days before automatic deletion
SECURE_FILE_NAMING = True   # Use hash-based filenames
LOG_IMAGE_ACCESS = True     # Log image access
```

## Automatic Cleanup

### Manual Execution

Run the cleanup script manually:

```bash
cd backend/app
python cleanup_old_images.py
```

### Scheduled Execution (Recommended)

Set up a cron job or scheduled task to run cleanup automatically:

**Linux/Mac (cron):**
```bash
# Run daily at 2 AM
0 2 * * * cd /path/to/qr-face-gate-system/backend/app && python cleanup_old_images.py >> /var/log/image-cleanup.log 2>&1
```

**Windows (Task Scheduler):**
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Daily at 2:00 AM
4. Action: Start a program
5. Program: `python`
6. Arguments: `C:\path\to\qr-face-gate-system\backend\app\cleanup_old_images.py`


## Data Storage Location

All failed attempt images are stored in:
```
backend/app/uploads/failed_attempts/
```