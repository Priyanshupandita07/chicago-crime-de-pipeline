"""
Chicago Crime Analytics Pipeline
=================================
End-to-end Data Engineering pipeline:
BigQuery Public Data → PySpark → GCP Dataproc → BigQuery
Automated via Cloud Scheduler (midnight trigger)

Author: Priyanshu Pandita
GitHub: github.com/Priyanshupandita07
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, month, hour, isnull, count
from google.cloud import bigquery
from google.cloud.bigquery import LoadJobConfig, WriteDisposition
import logging

# ── LOGGING ───────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)

# ── CONFIG ────────────────────────────────────────────────────
PROJECT_ID = "project-72181980-533d-4978-aa7"
BQ_TABLE   = "de_practice.chicago_crime_clean"

# ── CLIENTS ───────────────────────────────────────────────────
client_bq = bigquery.Client(project=PROJECT_ID)
spark     = SparkSession.builder.appName("ChicagoCrimePipeline").getOrCreate()


# ── EXTRACT ───────────────────────────────────────────────────
def extract():
    """
    Extract 500,000 rows of Chicago crime data
    from BigQuery public dataset (2020 onwards).
    """
    logger.info("EXTRACT: Starting...")

    query = """
        SELECT
            unique_key,
            date,
            primary_type,
            description,
            location_description,
            arrest,
            domestic,
            year,
            latitude,
            longitude
        FROM `bigquery-public-data.chicago_crime.crime`
        WHERE date >= '2020-01-01'
        LIMIT 500000
    """

    pandas_df = client_bq.query(query, location="US").to_dataframe()
    df        = spark.createDataFrame(pandas_df)

    logger.info(f"EXTRACT: {df.count()} rows loaded ✅")
    logger.info(f"EXTRACT: Schema:")
    df.printSchema()

    # NULL check
    logger.info("EXTRACT: NULL counts:")
    df.select([
        count(when(isnull(c), c)).alias(c)
        for c in df.columns
    ]).show()

    return df


# ── TRANSFORM ─────────────────────────────────────────────────
def transform(df):
    """
    Clean and enrich Chicago crime data:
    - Drop rows with missing GPS coordinates
    - Fill missing location descriptions
    - Extract month and hour from datetime
    - Add is_night flag (8PM - 4AM)
    - Add is_arrested integer column
    """
    logger.info("TRANSFORM: Starting...")
    original_count = df.count()
    logger.info(f"TRANSFORM: {original_count} rows received")

    # Drop rows with null GPS coordinates
    df = df.dropna(subset=["latitude", "longitude"])
    logger.info(f"TRANSFORM: Dropped {original_count - df.count()} null coordinate rows ✅")

    # Fill null location_description
    df = df.fillna({"location_description": "UNKNOWN"})
    logger.info("TRANSFORM: Filled null location_description ✅")

    # Extract month and hour
    df = df.withColumn("month", month(col("date")))
    df = df.withColumn("hour", hour(col("date")))
    logger.info("TRANSFORM: month + hour extracted ✅")

    # Add is_night flag (8PM - 4AM)
    df = df.withColumn("is_night",
        when((col("hour") >= 20) | (col("hour") <= 4), True).otherwise(False))
    logger.info("TRANSFORM: is_night flag added ✅")

    # Convert arrest boolean to integer
    df = df.withColumn("is_arrested",
        when(col("arrest") == True, 1).otherwise(0))
    logger.info("TRANSFORM: is_arrested column added ✅")

    logger.info(f"TRANSFORM: {df.count()} clean rows ready ✅")
    return df


# ── LOAD ──────────────────────────────────────────────────────
def load(df):
    """
    Load clean DataFrame into BigQuery and verify
    with SQL analytics query.
    """
    logger.info("LOAD: Starting...")

    pandas_df  = df.toPandas()
    job_config = LoadJobConfig(
        write_disposition=WriteDisposition.WRITE_TRUNCATE
    )

    job = client_bq.load_table_from_dataframe(
        pandas_df,
        BQ_TABLE,
        job_config=job_config
    )
    job.result()
    logger.info(f"LOAD: {len(pandas_df)} rows written to {BQ_TABLE} ✅")

    # SQL analytics verification
    query = f"""
        SELECT
            primary_type,
            COUNT(*)                                          AS total_crimes,
            SUM(is_arrested)                                  AS total_arrests,
            ROUND(SUM(is_arrested) * 100.0 / COUNT(*), 2)    AS arrest_rate
        FROM `{PROJECT_ID}.{BQ_TABLE}`
        GROUP BY primary_type
        ORDER BY total_crimes DESC
        LIMIT 5
    """
    result = client_bq.query(query, location="asia-south1").to_dataframe()
    logger.info("LOAD: Verification complete ✅")

    print("\n📊 Top 5 Crime Types:")
    print(result.to_string(index=False))


# ── RUN PIPELINE ──────────────────────────────────────────────
def run_pipeline():
    logger.info("=" * 50)
    logger.info("CHICAGO CRIME PIPELINE — STARTED")
    logger.info("=" * 50)

    raw   = extract()
    clean = transform(raw)
    load(clean)

    logger.info("=" * 50)
    logger.info("CHICAGO CRIME PIPELINE — COMPLETED ✅")
    logger.info("=" * 50)


if __name__ == "__main__":
    run_pipeline()
