# SC Procurement Delta Tracker (EC2 + S3)

This app checks South Carolina open solicitations, finds what is new compared to your saved baseline, writes a delta CSV, and saves baseline + delta files to Amazon S3.

---

## Required AWS targets for this deployment

This code is now configured to target:

- S3 bucket ARN: `arn:aws:s3:::sc-procurement`
- EC2 instance ID: `i-0e5fc9f790256a3e1`
- EC2 instance ARN: `arn:aws:ec2:us-east-1:000442375884:instance/i-0e5fc9f790256a3e1`

You can still override values with CLI flags or environment variables if needed.

## What this app does

On each run it will:

1. Open the SC solicitation search website.
2. Read every page of results.
3. Build records with these fields:
   - Solicitation Number
   - Solicitation Description
   - Purchasing Agency
   - Submission Ending Date/Time
   - Link to Solicitation
4. Compare today’s records against your baseline CSV.
5. Write:
   - a timestamped delta CSV (`delta_YYYYMMDDTHHMMSSZ.csv`)
   - a stable latest delta CSV (`delta_latest.csv`)
6. Update the baseline CSV for next run.
7. Upload baseline + delta files to S3 (when S3 bucket is configured).
- Safety guard: if scraping returns zero rows while a baseline already exists, the app stops instead of overwriting the baseline (use `--allow-empty-scrape` only if you intentionally want that behavior).

---

## Output files

Local files after a run:

- `outputs/delta_<UTC timestamp>.csv`
- `outputs/delta_latest.csv`
- `output/delta_<UTC timestamp>.csv` (compatibility copy)
- `output/delta_latest.csv` (compatibility copy)
- `data/baseline.csv`

S3 files after a run (example prefix `sc-procurement`):

- `s3://<your-bucket>/sc-procurement/delta_<UTC timestamp>.csv`
- `s3://<your-bucket>/sc-procurement/delta_latest.csv`
- `s3://<your-bucket>/sc-procurement/baseline.csv`

---

## Command reference

### Local run (no S3)

```bash
python scraper.py
```

### Run with S3 upload

```bash
python scraper.py --s3-bucket "arn:aws:s3:::sc-procurement" --s3-prefix "sc-procurement"
```

### Reset baseline to empty

```bash
python scraper.py --reset-baseline
```

### Build check

```bash
make build
```

---

# Full beginner deployment guide (foundation to execution)

This section assumes you are new to AWS and programming.

## Phase 1: Create your AWS account and basic setup

1. Go to <https://aws.amazon.com> and create an account.
2. Sign in to AWS Console.
3. In the top right, choose a region (for example `us-east-1`). Keep using the same region for all steps.
4. In the AWS search bar, open **IAM**.
5. Create an IAM user for yourself (for console/admin setup), or use your root account only for setup then stop using root.
6. Turn on MFA (multi-factor authentication) for account security.

---

## Phase 2: Create S3 bucket for files

1. In AWS Console, search for **S3**.
2. Click **Create bucket**.
3. Enter a globally unique bucket name, for example:
   - `my-company-sc-procurement-delta`
4. Keep “Block all public access” ON.
5. Click **Create bucket**.
6. Open bucket → optionally create a folder named `sc-procurement` (the app can also create keys automatically).

---

## Phase 3: Create EC2 server (Linux)

1. In AWS Console, search for **EC2**.
2. Click **Launch instance**.
3. Name it: `sc-procurement-runner`.
4. AMI: choose **Amazon Linux 2023**.
5. Instance type: `t3.micro` (free-tier eligible in many accounts).
6. Key pair:
   - Create key pair if you don’t have one.
   - Download `.pem` file and keep it safe.
7. Network settings:
   - Allow SSH (port 22) from your IP only.
8. Storage: 8–16 GB is enough.
9. Click **Launch instance**.
10. Confirm you are using the exact instance ID required:

```bash
aws ec2 describe-instances --instance-ids i-0e5fc9f790256a3e1 --region us-east-1
```

---

## Phase 4: Attach S3 permissions to EC2

Your EC2 needs permission to read/write files in S3.

1. In AWS Console, open **IAM** → **Roles** → **Create role**.
2. Trusted entity: **AWS service**.
3. Use case: **EC2**.
4. Click Next.
5. Add permission policy:
   - Easiest for start: `AmazonS3FullAccess` (broad).
   - Better production: create custom least-privilege policy for only your bucket.
6. Name role: `ec2-sc-procurement-s3-role`.
7. Create role.
8. Go back to EC2 → your instance → **Actions** → **Security** → **Modify IAM role**.
9. Attach `ec2-sc-procurement-s3-role`.

---

## Phase 5: SSH into EC2 and install dependencies

From your local terminal:

```bash
chmod 400 /path/to/your-key.pem
ssh -i /path/to/your-key.pem ec2-user@<EC2_PUBLIC_DNS>
```

Now inside EC2:

```bash
sudo dnf update -y
sudo dnf install -y git python3 python3-pip
aws --version
python3 --version
```

If `aws --version` fails, install AWS CLI v2:

```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
aws --version
```

---

## Phase 6: Copy app code to EC2

On EC2:

```bash
sudo mkdir -p /opt/sc-procurement
sudo chown ec2-user:ec2-user /opt/sc-procurement
git clone <your-repo-url> /opt/sc-procurement
cd /opt/sc-procurement
```

(If this repo is private, configure GitHub token/SSH deploy key first.)

---

## Phase 7: Configure environment values

Create `.env` file:

```bash
cd /opt/sc-procurement
cp deploy/example.env .env
nano .env
```

Update values:

```env
S3_BUCKET=arn:aws:s3:::sc-procurement
S3_PREFIX=sc-procurement
EC2_INSTANCE_ID=i-0e5fc9f790256a3e1
EC2_INSTANCE_ARN=arn:aws:ec2:us-east-1:000442375884:instance/i-0e5fc9f790256a3e1
```

Save and exit.

---

## Phase 8: Run app manually first (important)

```bash
cd /opt/sc-procurement
python3 scraper.py --s3-bucket "$S3_BUCKET" --s3-prefix "$S3_PREFIX"
```

Expected results:

- terminal prints delta and baseline paths
- files created under `outputs/` and `output/`
- files uploaded to S3 prefix

Verify S3 files:

```bash
aws s3 ls "s3://$S3_BUCKET/$S3_PREFIX/"
```

---

## Phase 9: Set automatic daily schedule (systemd timer)

Install service/timer files:

```bash
cd /opt/sc-procurement
sudo cp deploy/sc-procurement.service /etc/systemd/system/
sudo cp deploy/sc-procurement.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now sc-procurement.timer
```

Check timer:

```bash
systemctl status sc-procurement.timer
systemctl list-timers | grep sc-procurement
```

Run one immediate test execution:

```bash
sudo systemctl start sc-procurement.service
sudo systemctl status sc-procurement.service
```

View logs:

```bash
journalctl -u sc-procurement.service -n 100 --no-pager
```

---

## Phase 10: Operating checklist (daily/weekly)

- Confirm timer is active:
  - `systemctl status sc-procurement.timer`
- Confirm recent successful run:
  - `journalctl -u sc-procurement.service -n 50 --no-pager`
- Confirm S3 has new delta:
  - `aws s3 ls s3://<bucket>/<prefix>/`
- Confirm baseline exists:
  - `aws s3 ls s3://<bucket>/<prefix>/baseline.csv`

---

## Troubleshooting guide

### Problem: `aws: command not found`
Install AWS CLI v2 (Phase 5).

### Problem: Access denied to S3
- Check EC2 instance has IAM role attached.
- Check role includes S3 permissions for your bucket.

### Problem: no baseline in S3 on first run
This is normal. First run creates and uploads baseline.

### Problem: no new solicitations
Normal if site has no new postings since baseline.

### Problem: service fails in systemd but works in terminal
- Verify `/opt/sc-procurement/.env` exists.
- Verify `S3_BUCKET` and `S3_PREFIX` are populated.
- Check logs: `journalctl -u sc-procurement.service -n 200 --no-pager`

---

## Security best practices (recommended)

- Do not store AWS access keys in code.
- Prefer EC2 IAM role authentication.
- Keep S3 bucket private (no public access).
- Restrict SSH to your office/home public IP.
- Enable MFA for AWS users.

---

## Native Codex run (local environment)

```bash
./run_codex.sh
```

Stable local download path:

- `/workspace/sc-procurement/output/delta_latest.csv`
- `/workspace/sc-procurement/outputs/delta_latest.csv`
