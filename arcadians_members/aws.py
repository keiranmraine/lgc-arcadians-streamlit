import mimetypes
import os
import pathlib
import time
import uuid
from contextlib import contextmanager
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
CF_DIST = "https://dv0cgprb23go3.cloudfront.net"  # will become lams.members....
CF_ID = "E2HM969BWTU3KK"


def invalidation_obj():
    return {"Paths": {"Quantity": 1, "Items": ["/*"]}, "CallerReference": str(datetime.now().timestamp())}


@contextmanager
def cwd(path):
    oldpwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(oldpwd)


def dl_link(path):
    url = f"[Download]({CF_DIST}{path})"
    return url + "{ target=_blank }"


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


def sync():
    """
    There's a small possibility files may need deleting over time.
    """
    to_sync = "site"
    with cwd(to_sync):
        l_paths = pathlib.Path(".").rglob("*")
        l_set = {}
        for po in l_paths:
            if po.is_dir():
                continue
            l_set[str(po).replace("\\", "/")] = 1

        s3 = get_client("s3")
        # this block just puts all the s3 object keys into a dict
        s3_set = {}
        bkt_resp = s3.list_objects_v2(Bucket=BUCKET)
        while True:
            for f in bkt_resp["Contents"]:
                if f["Key"].startswith("files/"):
                    continue
                s3_set[f["Key"]] = 1
            if bkt_resp["IsTruncated"] is False:
                break
            else:
                bkt_resp = s3.list_objects_v2(Bucket=BUCKET, ContinuationToken=bkt_resp["NextContinuationToken"])

        # now compare the lists anything in s3 not local needs deleting (safe as we excluded `files/`)
        s3_deletes = [{"Key": k} for k in s3_set if k not in l_set]
        if s3_deletes:
            with st.spinner("Removing files no longer needed..."):
                resp = s3.delete_objects(Bucket=BUCKET, Delete={"Objects": s3_deletes})
            st.success("Files removed")

        # then load all the local site
        with st.spinner("Uploading refreshed site..."):
            for k in l_set:
                mtype = mimetypes.guess_type(k)[0]
                s3.upload_file(k, BUCKET, k, ExtraArgs={"ContentType": mtype})
        st.success("Site uploaded")

        ### needs a spinner
        with st.spinner("Updating web-caches...(this can take a while)"):
            cf = get_client("cloudfront")
            inval_resp = cf.create_invalidation(DistributionId=CF_ID, InvalidationBatch=invalidation_obj())
            status = ""
            chk_counter = 0
            while status != "Completed":
                if chk_counter > 120:
                    break
                if status == "":
                    time.sleep(5)
                get_i_resp = cf.get_invalidation(DistributionId=CF_ID, Id=inval_resp["Invalidation"]["Id"])
                status = get_i_resp["Invalidation"]["Status"]
                chk_counter += 1
        st.success(f"Site fully available, access the members section directly [here]({CF_DIST}).")


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
