# 🚔 Chicago Crime Analytics Pipeline

An end-to-end **Data Engineering pipeline** built on Google Cloud Platform — processing 500,000 rows of real Chicago crime data through PySpark on Dataproc, automated via Cloud Scheduler.

---

## 🏗️ Architecture

```
BigQuery Public Data (chicago_crime)
        ↓  extract()
PySpark on GCP Dataproc
        ↓  transform()
Clean DataFrame (492,630 rows)
        ↓  load()
BigQuery (de_practice.chicago_crime_clean)
        ↓
Cloud Scheduler (midnight trigger)
```

---

## 📊 Dataset

- **Source:** BigQuery Public Data — `bigquery-public-data.chicago_crime.crime`
- **Extracted:** 500,000 rows (2020–2026)
- **Total dataset:** 8.5 million rows (2001–2026)

---

## 🔧 Transformations Applied

| Transform | Description |
|-----------|-------------|
| Null handling | Dropped 6,670 rows with missing GPS coordinates |
| fillna | Filled missing location descriptions with UNKNOWN |
| month | Extracted month from datetime column |
| hour | Extracted hour from datetime column |
| is_night | True if crime occurred between 8PM–4AM |
| is_arrested | Converted boolean arrest flag to integer |

---

## 📈 Key Insights

| Crime Type | Total Cases | Arrest Rate |
|---|---|---|
| 🥇 THEFT | 95,679 | 6.01% |
| BATTERY | 94,869 | 15.99% |
| CRIMINAL DAMAGE | 59,376 | 3.64% |
| ASSAULT | 48,225 | 10.66% |
| MOTOR VEHICLE THEFT | 40,872 | 2.99% |

- **THEFT** is the most common crime with only **6.01% arrest rate**
- **BATTERY** has the highest arrest rate at **15.99%**
- Only **25.06% overall arrest rate** across 8.5 million crimes

---

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3 | Pipeline orchestration |
| PySpark | Distributed data transformation |
| BigQuery | Data source + analytics warehouse |
| GCP Dataproc | Managed Spark cluster |
| Cloud Scheduler | Automated midnight pipeline trigger |
| google-cloud-bigquery | Python ↔ BigQuery connector |

---

## 🚀 How to Run

### Prerequisites
- Google Cloud account with BigQuery and Dataproc enabled
- Python 3.8+

```bash
pip install -r requirements.txt
```

### Deploy to Dataproc
```bash
# Upload pipeline to Cloud Storage
gsutil cp chicago_pipeline.py gs://your-bucket/scripts/

# Submit job to Dataproc
gcloud dataproc jobs submit pyspark \
    gs://your-bucket/scripts/chicago_pipeline.py \
    --cluster=your-cluster \
    --region=asia-south1
```

### Automate with Cloud Scheduler
```bash
gcloud scheduler jobs create http chicago-pipeline-schedule \
    --schedule="0 0 * * *" \
    --uri="https://dataproc.googleapis.com/v1/projects/YOUR_PROJECT/regions/asia-south1/jobs" \
    --message-body='{"placement":{"clusterName":"your-cluster"},"pysparkJob":{"mainPythonFileUri":"gs://your-bucket/scripts/chicago_pipeline.py"}}' \
    --time-zone="Asia/Kolkata"
```

---

## 📁 Project Structure

```
chicago-crime-de-pipeline/
├── chicago_pipeline.py  ← PySpark ETL pipeline
├── requirements.txt     ← Python dependencies
└── README.md            ← Project documentation
```

---

## 👤 Author

**Priyanshu Pandita**
- GitHub: [@Priyanshupandita07](https://github.com/Priyanshupandita07)
- LinkedIn: [priyanshu-pandita](https://linkedin.com/in/priyanshu-pandita)
