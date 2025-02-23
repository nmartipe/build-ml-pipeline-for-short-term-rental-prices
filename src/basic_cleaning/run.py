#!/usr/bin/env python
"""
Download from W&B the raw dataset and apply some basic data cleaning, exporting the result to a new artifact
"""
import argparse
import logging
import wandb
import pandas as pd
import numpy as np
import os


logging.basicConfig(level=logging.INFO, format="%(asctime)-15s %(message)s")
logger = logging.getLogger()


def go(args):

    run = wandb.init(job_type="basic_cleaning")
    run.config.update(args)

    # Download input artifact. 
    logger.info("Downloading input artifact")
    artifact_local_path = run.use_artifact(args.input_artifact).file()
    df = pd.read_csv(artifact_local_path)

    logger.info("Dropping outliers")
    idx = df['price'].between(args.min_price, args.max_price)
    df = df[idx].copy()

    logger.info("Converting last_review to seconds")
    df['last_review'] = pd.to_datetime(df['last_review'], errors='coerce')
    df['last_review'] = df['last_review'].apply(lambda x: x.timestamp() if not pd.isnull(x) else np.nan)

    logger.info("Removing null values from 'name' and 'host_name' columns")
    df = df.dropna(subset=['name', 'host_name'])

    logger.info("Imputing null values in 'last_review' and 'reviews_per_month' columns with the mean of each group defined by 'neighbourhood_group'")
    df['last_review'] = df.groupby('neighbourhood_group')['last_review'].transform(lambda x: x.fillna(x.mean()))
    df['reviews_per_month'] = df.groupby('neighbourhood_group')['reviews_per_month'].transform(lambda x: x.fillna(x.mean()))

    #Drop rows in the dataset that are not in the proper geolocation
    idx = df['longitude'].between(-74.25, -73.50) & df['latitude'].between(40.5, 41.2)
    df = df[idx].copy()
    
    # Dataframe to csv
    filename = "clean_sample.csv"
    df.to_csv(filename, index=False)

    # Upload to W&B
    artifact = wandb.Artifact(
        name=args.output_artifact,
        type=args.output_type,
        description=args.output_description,
    )
    artifact.add_file(filename)

    logger.info("Logging artifact")
    run.log_artifact(artifact)

    os.remove(filename)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="A very basic data cleaning")


    parser.add_argument(
        "--input_artifact", 
        type=str,
        help="Name and version of W&B input artifact",
        required=True
    )

    parser.add_argument(
        "--output_artifact", 
        type=str,
        help="Name and version of W&B output artifact",
        required=True
    )

    parser.add_argument(
        "--output_type", 
        type=str,
        help="Type of the output",
        required=True
    )

    parser.add_argument(
        "--output_description", 
        type=str,
        help="Description of the output artifact",
        required=True
    )

    parser.add_argument(
        "--min_price", 
        type=float,
        help="Value of min_price",
        required=True
    )

    parser.add_argument(
        "--max_price", 
        type=float,
        help="Value of max_price",
        required=True
    )


    args = parser.parse_args()

    go(args)
