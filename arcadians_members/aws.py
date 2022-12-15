import os
import uuid
from datetime import datetime
from mimetypes import guess_type
from typing import Any
from typing import Dict
from typing import List

import boto3
import streamlit as st


MODE = os.environ["DEPLOY_MODE"] if "DEPLOY_MODE" in os.environ else "develop"
DOMAIN_ROOT = f"lgc-arcadians-{MODE}"
BUCKET = "lgc-arcadians-members"


def flatten_dict(data: Dict[str, Any], prefix=None):
    new_data = {}
    for k, v in data.items():
        if type(v) is list:
            new_data[k] = ",".join(v)
        elif type(v) is dict:
            nested = flatten_dict(v, k)
            new_data = dict(new_data, **nested)
        elif prefix is not None:
            new_data[f"{prefix}_{k}"] = str(v)
        else:
            new_data[k] = str(v)
    return new_data


def to_attrs(data: Dict[str, Any]):
    flattened = flatten_dict(data)
    new_list = [{"Name": "Timestamp", "Value": datetime.utcnow().strftime("%Y-%m-%d/%H:%M:%S UTC"), "Replace": False}]
    for k, v in flattened.items():
        new_list.append({"Name": k, "Value": v, "Replace": False})
    return new_list


def get_client(purpose: str):
    return boto3.client(
        purpose,
        region_name="eu-west-1",
        aws_access_key_id=os.environ["LIMITED_ACCESS_KEY"],
        aws_secret_access_key=os.environ["LIMITED_SECRET_KEY"],
    )


def sdb_write(data_type: str, data_dict: List[Dict[str, Any]]):
    """
    data_type - notice or file
    """
    with st.spinner("Writing to SDB..."):
        client = get_client("sdb")
        response = client.list_domains(MaxNumberOfDomains=10)

        data_domain = f"{DOMAIN_ROOT}-{data_type}"

        if "DomainNames" not in response or data_domain not in response["DomainNames"]:
            response = client.create_domain(DomainName=data_domain)

        for item in data_dict:
            response = client.put_attributes(
                DomainName=data_domain, ItemName=str(uuid.uuid4()), Attributes=to_attrs(item)
            )
    st.success("Write complete")


def sdb_get_uniq(data_type: str, field: str) -> List[str]:
    client = get_client("sdb")
    response = client.list_domains(MaxNumberOfDomains=10)
    data_domain = f"{DOMAIN_ROOT}-{data_type}"
    if "DomainNames" not in response or data_domain not in response["DomainNames"]:
        return []
    more_data = True
    next_token = ""
    entries = {}
    while more_data:
        response = client.select(SelectExpression=f"select {field} from `{data_domain}`", NextToken=next_token)
        if "Items" not in response:
            break
        for item in response["Items"]:
            value = item["Attributes"][0]["Value"]
            entries[value] = 1

        if "NextToken" in response:
            next_token = response["NextToken"]
        else:
            more_data = False
    return sorted(entries.keys())


def s3_write(files: List[Dict[str, Any]]):
    client = get_client("s3")
    for upload in files:
        (type, encoding) = guess_type(upload["path"])
        with st.spinner(f"Uploading to S3...{upload['path']}"):
            client.put_object(Body=upload["file"], Bucket=BUCKET, Key=upload["path"], ContentType=f"{type}/{encoding}")
    st.success("All files uploaded")


def sdb_content(data_type: str) -> List[Dict[str, Any]]:
    client = get_client("sdb")
    response = client.list_domains(MaxNumberOfDomains=10)
    data_domain = f"{DOMAIN_ROOT}-{data_type}"
    if "DomainNames" not in response or data_domain not in response["DomainNames"]:
        return []
    more_data = True
    next_token = ""
    items = []
    while more_data:
        response = client.select(SelectExpression=f"select * from `{data_domain}`", NextToken=next_token)
        if "Items" not in response:
            break

        if "NextToken" in response:
            next_token = response["NextToken"]
        else:
            more_data = False

        for item in response["Items"]:
            item_map = {"Id": item["Name"]}
            for attr in item["Attributes"]:
                item_map[attr["Name"]] = attr["Value"]
            items.append(item_map)
    return items
