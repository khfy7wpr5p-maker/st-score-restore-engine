from __future__ import annotations

import json
import unittest

from st_score_restore.http_api import ApiV1
from st_score_restore.job_api_types import JobApiConfig

CLIENT_KEY = "client-key-0123456789abcdef"
REVIEWER_KEY = "reviewer-key-0123456789abcdef"


class DummyService:
    def __init__(self):
        self.uploaded=[]

    def create_job(self, pages, *, idempotency_key, actor, restoration_config):
        self.uploaded=list(pages)
        return {"jobId":"job_1","state":"UPLOADED"}, False

    def review_job(self, job_id, decisions, *, reviewer_id, notes):
        return {"jobId":job_id,"state":"COMPLETED","reviewer":reviewer_id}

    def get_artifact(self, job_id, artifact_id, *, role, purpose, actor):
        return {"mediaType":"image/png","artifactId":artifact_id}, b"x"


def multipart_body(files):
    boundary="st-score-boundary-001"
    chunks=[]
    for filename, content_type, data in files:
        chunks.extend([
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode(),
            f"Content-Type: {content_type}\r\n\r\n".encode(),
            data,
            b"\r\n",
        ])
    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks),f"multipart/form-data; boundary={boundary}"


class HttpApiSecurityCompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.config=JobApiConfig(client_api_key=CLIENT_KEY,reviewer_api_key=REVIEWER_KEY)
        self.service=DummyService()
        self.api=ApiV1(self.service,self.config)

    def test_existing_multipart_shape_and_binary_bytes_remain_compatible(self):
        binary=b"\x89PNG\r\n\x00\xffbinary"
        body,content_type=multipart_body([("page-1.png","image/png",binary)])
        response=self.api.handle("POST","/api/v1/restoration-jobs",{
            "Authorization":f"Bearer {CLIENT_KEY}",
            "Content-Type":content_type,
            "Idempotency-Key":"compat-0001",
            "X-Actor-Id":"client-app",
        },body)
        self.assertEqual(202,response.status)
        self.assertEqual(binary,self.service.uploaded[0].data)
        self.assertEqual("page-1.png",self.service.uploaded[0].name)

    def test_json_without_content_type_remains_compatible(self):
        response=self.api.handle("POST","/api/v1/restoration-jobs/job_1/review",{
            "X-Api-Key":REVIEWER_KEY,
            "X-Actor-Id":"teacher-1",
        },json.dumps({"decisions":[]}).encode())
        self.assertEqual(200,response.status)

    def test_ambiguous_auth_method_and_query_are_rejected(self):
        response=self.api.handle("GET","/health",{},b"")
        self.assertEqual(200,response.status)
        response=self.api.handle("PUT","/health",{},b"")
        self.assertEqual(405,response.status)
        response=self.api.handle("GET","/api/v1/restoration-jobs/job_1/artifacts/sha256:"+"a"*64+"?purpose=review&purpose=original",{
            "X-Api-Key":REVIEWER_KEY,
        })
        self.assertEqual(400,response.status)
        self.assertEqual("ambiguous_query_parameter",json.loads(response.body)["error"]["code"])
        response=self.api.handle("GET","/api/v1/restoration-jobs/job_1",{
            "Authorization":f"Bearer {CLIENT_KEY}",
            "X-Api-Key":CLIENT_KEY,
        })
        self.assertEqual(400,response.status)
        self.assertEqual("ambiguous_authentication",json.loads(response.body)["error"]["code"])


if __name__ == "__main__":
    unittest.main()
