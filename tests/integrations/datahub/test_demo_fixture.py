import json
from pathlib import Path

from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.ingestion.source.file import read_metadata_file


FIXTURE_PATH = (
    Path(__file__).resolve().parents[3] / "demo" / "nyc_taxi_metadata.json"
)


def test_nyc_taxi_fixture_deserializes_all_expected_proposals():
    fixture_records = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    proposals = list(read_metadata_file(FIXTURE_PATH))

    assert len(proposals) == 7
    assert all(isinstance(proposal, MetadataChangeProposalWrapper) for proposal in proposals)
    assert all(record["changeType"] == "UPSERT" for record in fixture_records)
    assert all(
        record["aspect"]["contentType"] == "application/json"
        for record in fixture_records
    )

    decoded_aspects = [
        json.loads(record["aspect"]["value"]) for record in fixture_records
    ]
    assert decoded_aspects == [
        {
            "name": "NYC Taxi Trips Raw",
            "description": "Demo asset with a planted stale freshness signal.",
            "customProperties": {
                "dic_scenario": "nyc_taxi_freshness",
                "dic_freshness_status": "stale",
                "dic_freshness_observed_at": "2026-07-24T09:00:00Z",
                "dic_quality_status": "passing",
                "dic_asset_type": "dataset",
                "dic_criticality": "high",
            },
        },
        {
            "name": "NYC Taxi Daily Metrics",
            "customProperties": {
                "dic_scenario": "nyc_taxi_freshness",
                "dic_quality_status": "passing",
                "dic_asset_type": "model",
                "dic_criticality": "high",
            },
        },
        {
            "name": "NYC Taxi Operations Dashboard",
            "customProperties": {
                "dic_scenario": "nyc_taxi_freshness",
                "dic_quality_status": "passing",
                "dic_asset_type": "dashboard",
                "dic_criticality": "critical",
            },
        },
        {
            "owners": [
                {
                    "owner": "urn:li:corpGroup:data-platform",
                    "type": "TECHNICAL_OWNER",
                    "source": {"type": "SERVICE"},
                }
            ],
            "lastModified": {"time": 0, "actor": "urn:li:corpuser:datahub"},
        },
        {
            "upstreams": [
                {
                    "dataset": "urn:li:dataset:(urn:li:dataPlatform:bigquery,dic_demo.nyc_taxi_trips_raw,PROD)",
                    "type": "TRANSFORMED",
                }
            ]
        },
        {
            "upstreams": [
                {
                    "dataset": "urn:li:dataset:(urn:li:dataPlatform:bigquery,dic_demo.nyc_taxi_daily_metrics,PROD)",
                    "type": "TRANSFORMED",
                }
            ]
        },
        {
            "name": "dic-incident-recorded",
            "description": "Approval-gated Data Incident Commander write-back proof",
            "colorHex": "#D97706",
        },
    ]
