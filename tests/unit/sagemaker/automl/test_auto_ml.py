# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
from __future__ import absolute_import

import copy

import pytest
from mock import Mock, patch
from sagemaker import AutoML, AutoMLJob, AutoMLInput, CandidateEstimator, PipelineModel
from sagemaker.predictor import Predictor

MODEL_DATA = "s3://bucket/model.tar.gz"
MODEL_IMAGE = "mi"
ENTRY_POINT = "blah.py"

TIMESTAMP = "2017-11-06-14:14:15.671"
BUCKET_NAME = "mybucket"
INSTANCE_COUNT = 1
INSTANCE_TYPE = "ml.c5.2xlarge"
RESOURCE_POOLS = [{"InstanceType": INSTANCE_TYPE, "PoolSize": INSTANCE_COUNT}]
ROLE = "DummyRole"
TARGET_ATTRIBUTE_NAME = "target"
REGION = "us-west-2"
DEFAULT_S3_INPUT_DATA = "s3://{}/data".format(BUCKET_NAME)
DEFAULT_OUTPUT_PATH = "s3://{}/".format(BUCKET_NAME)
LOCAL_DATA_PATH = "file://data"
DEFAULT_MAX_CANDIDATES = None
DEFAULT_JOB_NAME = "automl-{}".format(TIMESTAMP)

JOB_NAME = "default-job-name"
JOB_NAME_2 = "banana-auto-ml-job"
JOB_NAME_3 = "descriptive-auto-ml-job"
VOLUME_KMS_KEY = "volume-kms-key-id-string"
OUTPUT_KMS_KEY = "output-kms-key-id-string"
OUTPUT_PATH = "s3://my_other_bucket/"
BASE_JOB_NAME = "banana"
PROBLEM_TYPE = "BinaryClassification"
BLACKLISTED_ALGORITHM = ["xgboost"]
LIST_TAGS_RESULT = {"Tags": [{"Key": "key1", "Value": "value1"}]}
MAX_CANDIDATES = 10
MAX_RUNTIME_PER_TRAINING_JOB = 3600
TOTAL_JOB_RUNTIME = 36000
TARGET_OBJECTIVE = "0.01"
JOB_OBJECTIVE = {"fake job objective"}
TAGS = [{"Name": "some-tag", "Value": "value-for-tag"}]
VPC_CONFIG = {"SecurityGroupIds": ["group"], "Subnets": ["subnet"]}
COMPRESSION_TYPE = "Gzip"
ENCRYPT_INTER_CONTAINER_TRAFFIC = False
GENERATE_CANDIDATE_DEFINITIONS_ONLY = False
BEST_CANDIDATE = {"best-candidate": "best-trial"}
BEST_CANDIDATE_2 = {"best-candidate": "best-trial-2"}
AUTO_ML_DESC = {"AutoMLJobName": JOB_NAME, "BestCandidate": BEST_CANDIDATE}
AUTO_ML_DESC_2 = {"AutoMLJobName": JOB_NAME_2, "BestCandidate": BEST_CANDIDATE_2}
AUTO_ML_DESC_3 = {
    "AutoMLJobArn": "automl_job_arn",
    "AutoMLJobConfig": {
        "CompletionCriteria": {
            "MaxAutoMLJobRuntimeInSeconds": 3000,
            "MaxCandidates": 28,
            "MaxRuntimePerTrainingJobInSeconds": 100,
        },
        "SecurityConfig": {"EnableInterContainerTrafficEncryption": True},
    },
    "AutoMLJobName": "mock_automl_job_name",
    "AutoMLJobObjective": {"MetricName": "Auto"},
    "AutoMLJobSecondaryStatus": "Completed",
    "AutoMLJobStatus": "Completed",
    "GenerateCandidateDefinitionsOnly": False,
    "InputDataConfig": [
        {
            "DataSource": {
                "S3DataSource": {"S3DataType": "S3Prefix", "S3Uri": "s3://input/prefix"}
            },
            "TargetAttributeName": "y",
        }
    ],
    "OutputDataConfig": {"KmsKeyId": "string", "S3OutputPath": "s3://output_prefix"},
    "ProblemType": "Auto",
    "RoleArn": "mock_role_arn",
}

INFERENCE_CONTAINERS = [
    {
        "Environment": {"SAGEMAKER_PROGRAM": "sagemaker_serve"},
        "Image": "account.dkr.ecr.us-west-2.amazonaws.com/sagemaker-auto-ml-data-processing:1.0-cpu-py3",
        "ModelDataUrl": "s3://sagemaker-us-west-2-account/sagemaker-auto-ml-gamma/data-processing/output",
    },
    {
        "Environment": {"MAX_CONTENT_LENGTH": "20000000"},
        "Image": "account.dkr.ecr.us-west-2.amazonaws.com/sagemaker-auto-ml-training:1.0-cpu-py3",
        "ModelDataUrl": "s3://sagemaker-us-west-2-account/sagemaker-auto-ml-gamma/training/output",
    },
    {
        "Environment": {"INVERSE_LABEL_TRANSFORM": "1"},
        "Image": "account.dkr.ecr.us-west-2.amazonaws.com/sagemaker-auto-ml-transform:1.0-cpu-py3",
        "ModelDataUrl": "s3://sagemaker-us-west-2-account/sagemaker-auto-ml-gamma/transform/output",
    },
]

CLASSIFICATION_INFERENCE_CONTAINERS = [
    {
        "Environment": {"SAGEMAKER_PROGRAM": "sagemaker_serve"},
        "Image": "account.dkr.ecr.us-west-2.amazonaws.com/sagemaker-auto-ml-data-processing:1.0-cpu-py3",
        "ModelDataUrl": "s3://sagemaker-us-west-2-account/sagemaker-auto-ml-gamma/data-processing/output",
    },
    {
        "Environment": {
            "MAX_CONTENT_LENGTH": "20000000",
            "SAGEMAKER_INFERENCE_SUPPORTED": "probability,probabilities,predicted_label",
            "SAGEMAKER_INFERENCE_OUTPUT": "predicted_label",
        },
        "Image": "account.dkr.ecr.us-west-2.amazonaws.com/sagemaker-auto-ml-training:1.0-cpu-py3",
        "ModelDataUrl": "s3://sagemaker-us-west-2-account/sagemaker-auto-ml-gamma/training/output",
    },
    {
        "Environment": {
            "INVERSE_LABEL_TRANSFORM": "1",
            "SAGEMAKER_INFERENCE_SUPPORTED": "probability,probabilities,predicted_label,labels",
            "SAGEMAKER_INFERENCE_OUTPUT": "predicted_label",
            "SAGEMAKER_INFERENCE_INPUT": "predicted_label",
        },
        "Image": "account.dkr.ecr.us-west-2.amazonaws.com/sagemaker-auto-ml-transform:1.0-cpu-py3",
        "ModelDataUrl": "s3://sagemaker-us-west-2-account/sagemaker-auto-ml-gamma/transform/output",
    },
]

CANDIDATE_STEPS = [
    {
        "CandidateStepName": "training-job/sagemaker-auto-ml-gamma/data-processing",
        "CandidateStepType": "AWS::Sagemaker::TrainingJob",
    },
    {
        "CandidateStepName": "transform-job/sagemaker-auto-ml-gamma/transform",
        "CandidateStepType": "AWS::Sagemaker::TransformJob",
    },
    {
        "CandidateStepName": "training-job/sagemaker-auto-ml-gamma/training",
        "CandidateStepType": "AWS::Sagemaker::TrainingJob",
    },
]

CANDIDATE_DICT = {
    "CandidateName": "candidate_mock",
    "InferenceContainers": INFERENCE_CONTAINERS,
    "CandidateSteps": CANDIDATE_STEPS,
}

CLASSIFICATION_CANDIDATE_DICT = {
    "CandidateName": "candidate_mock",
    "InferenceContainers": CLASSIFICATION_INFERENCE_CONTAINERS,
    "CandidateSteps": CANDIDATE_STEPS,
}

TRAINING_JOB = {
    "AlgorithmSpecification": {
        "AlgorithmName": "string",
        "TrainingImage": "string",
        "TrainingInputMode": "string",
    },
    "CheckpointConfig": {"LocalPath": "string", "S3Uri": "string"},
    "EnableInterContainerTrafficEncryption": False,
    "EnableManagedSpotTraining": False,
    "EnableNetworkIsolation": False,
    "InputDataConfig": [
        {"DataSource": {"S3DataSource": {"S3DataType": "string", "S3Uri": "string"}}}
    ],
    "OutputDataConfig": {"KmsKeyId": "string", "S3OutputPath": "string"},
    "ResourceConfig": {},
    "RoleArn": "string",
    "StoppingCondition": {},
    "TrainingJobArn": "string",
    "TrainingJobName": "string",
    "TrainingJobStatus": "string",
    "VpcConfig": {},
}

TRANSFORM_JOB = {
    "BatchStrategy": "string",
    "DataProcessing": {},
    "Environment": {"string": "string"},
    "FailureReason": "string",
    "LabelingJobArn": "string",
    "MaxConcurrentTransforms": 1,
    "MaxPayloadInMB": 2000,
    "ModelName": "string",
    "TransformInput": {"DataSource": {"S3DataSource": {"S3DataType": "string", "S3Uri": "string"}}},
    "TransformJobStatus": "string",
    "TransformJobArn": "string",
    "TransformJobName": "string",
    "TransformOutput": {},
    "TransformResources": {},
}


def describe_auto_ml_job_mock(job_name=None):
    if job_name is None or job_name == JOB_NAME:
        return AUTO_ML_DESC
    elif job_name == JOB_NAME_2:
        return AUTO_ML_DESC_2
    elif job_name == JOB_NAME_3:
        return AUTO_ML_DESC_3


@pytest.fixture()
def sagemaker_session():
    boto_mock = Mock(name="boto_session", region_name=REGION)
    sms = Mock(
        name="sagemaker_session",
        boto_session=boto_mock,
        boto_region_name=REGION,
        config=None,
        local_mode=False,
    )
    sms.default_bucket = Mock(name="default_bucket", return_value=BUCKET_NAME)
    sms.upload_data = Mock(name="upload_data", return_value=DEFAULT_S3_INPUT_DATA)
    sms.expand_role = Mock(name="expand_role", return_value=ROLE)
    sms.describe_auto_ml_job = Mock(
        name="describe_auto_ml_job", side_effect=describe_auto_ml_job_mock
    )
    sms.sagemaker_client.describe_training_job = Mock(
        name="describe_training_job", return_value=TRAINING_JOB
    )
    sms.sagemaker_client.describe_transform_job = Mock(
        name="describe_transform_job", return_value=TRANSFORM_JOB
    )
    sms.list_candidates = Mock(name="list_candidates", return_value={"Candidates": []})
    sms.sagemaker_client.list_tags = Mock(name="list_tags", return_value=LIST_TAGS_RESULT)
    return sms


@pytest.fixture()
def candidate_mock(sagemaker_session):
    candidate = Mock(
        name="candidate_mock",
        containers=INFERENCE_CONTAINERS,
        steps=CANDIDATE_STEPS,
        sagemaker_session=sagemaker_session,
    )
    return candidate


def test_auto_ml_default_channel_name(sagemaker_session):
    auto_ml = AutoML(
        role=ROLE, target_attribute_name=TARGET_ATTRIBUTE_NAME, sagemaker_session=sagemaker_session
    )
    inputs = DEFAULT_S3_INPUT_DATA
    AutoMLJob.start_new(auto_ml, inputs)
    sagemaker_session.auto_ml.assert_called_once()
    _, args = sagemaker_session.auto_ml.call_args
    assert args["input_config"] == [
        {
            "DataSource": {
                "S3DataSource": {"S3DataType": "S3Prefix", "S3Uri": DEFAULT_S3_INPUT_DATA}
            },
            "TargetAttributeName": TARGET_ATTRIBUTE_NAME,
        }
    ]


def test_auto_ml_invalid_input_data_format(sagemaker_session):
    auto_ml = AutoML(
        role=ROLE, target_attribute_name=TARGET_ATTRIBUTE_NAME, sagemaker_session=sagemaker_session
    )
    inputs = {}

    with pytest.raises(ValueError) as excinfo:
        AutoMLJob.start_new(auto_ml, inputs)

    expected_error_msg = "Cannot format input {}. Expecting a string or a list of strings."
    assert expected_error_msg.format(inputs) in str(excinfo.value)

    sagemaker_session.auto_ml.assert_not_called()


def test_auto_ml_only_one_of_problem_type_and_job_objective_provided(sagemaker_session):
    with pytest.raises(ValueError) as excinfo:
        AutoML(
            role=ROLE,
            target_attribute_name=TARGET_ATTRIBUTE_NAME,
            sagemaker_session=sagemaker_session,
            problem_type=PROBLEM_TYPE,
        )

    message = (
        "One of problem type and objective metric provided. Either both of them "
        "should be provided or none of them should be provided."
    )
    assert message in str(excinfo.value)


@patch("sagemaker.automl.automl.AutoMLJob.start_new")
def test_auto_ml_fit_set_logs_to_false(start_new, sagemaker_session, caplog):
    auto_ml = AutoML(
        role=ROLE, target_attribute_name=TARGET_ATTRIBUTE_NAME, sagemaker_session=sagemaker_session
    )
    inputs = DEFAULT_S3_INPUT_DATA
    auto_ml.fit(inputs, job_name=JOB_NAME, wait=False, logs=True)
    start_new.wait.assert_not_called()
    assert "Setting logs to False. logs is only meaningful when wait is True." in caplog.text


def test_auto_ml_additional_optional_params(sagemaker_session):
    auto_ml = AutoML(
        role=ROLE,
        target_attribute_name=TARGET_ATTRIBUTE_NAME,
        sagemaker_session=sagemaker_session,
        volume_kms_key=VOLUME_KMS_KEY,
        vpc_config=VPC_CONFIG,
        encrypt_inter_container_traffic=ENCRYPT_INTER_CONTAINER_TRAFFIC,
        compression_type=COMPRESSION_TYPE,
        output_kms_key=OUTPUT_KMS_KEY,
        output_path=OUTPUT_PATH,
        problem_type=PROBLEM_TYPE,
        max_candidates=MAX_CANDIDATES,
        max_runtime_per_training_job_in_seconds=MAX_RUNTIME_PER_TRAINING_JOB,
        total_job_runtime_in_seconds=TOTAL_JOB_RUNTIME,
        job_objective=JOB_OBJECTIVE,
        generate_candidate_definitions_only=GENERATE_CANDIDATE_DEFINITIONS_ONLY,
        tags=TAGS,
    )
    inputs = DEFAULT_S3_INPUT_DATA
    auto_ml.fit(inputs, job_name=JOB_NAME)
    sagemaker_session.auto_ml.assert_called_once()
    _, args = sagemaker_session.auto_ml.call_args

    assert args == {
        "input_config": [
            {
                "CompressionType": COMPRESSION_TYPE,
                "DataSource": {
                    "S3DataSource": {"S3DataType": "S3Prefix", "S3Uri": DEFAULT_S3_INPUT_DATA}
                },
                "TargetAttributeName": TARGET_ATTRIBUTE_NAME,
            }
        ],
        "output_config": {"S3OutputPath": OUTPUT_PATH, "KmsKeyId": OUTPUT_KMS_KEY},
        "auto_ml_job_config": {
            "CompletionCriteria": {
                "MaxAutoMLJobRuntimeInSeconds": TOTAL_JOB_RUNTIME,
                "MaxCandidates": MAX_CANDIDATES,
                "MaxRuntimePerTrainingJobInSeconds": MAX_RUNTIME_PER_TRAINING_JOB,
            },
            "SecurityConfig": {
                "VolumeKmsKeyId": VOLUME_KMS_KEY,
                "VpcConfig": VPC_CONFIG,
                "EnableInterContainerTrafficEncryption": ENCRYPT_INTER_CONTAINER_TRAFFIC,
            },
        },
        "job_name": JOB_NAME,
        "role": ROLE,
        "job_objective": JOB_OBJECTIVE,
        "problem_type": PROBLEM_TYPE,
        "generate_candidate_definitions_only": GENERATE_CANDIDATE_DEFINITIONS_ONLY,
        "tags": TAGS,
    }


@patch("time.strftime", return_value=TIMESTAMP)
def test_auto_ml_default_fit(strftime, sagemaker_session):
    auto_ml = AutoML(
        role=ROLE, target_attribute_name=TARGET_ATTRIBUTE_NAME, sagemaker_session=sagemaker_session
    )
    inputs = DEFAULT_S3_INPUT_DATA
    auto_ml.fit(inputs)
    sagemaker_session.auto_ml.assert_called_once()
    _, args = sagemaker_session.auto_ml.call_args
    assert args == {
        "input_config": [
            {
                "DataSource": {
                    "S3DataSource": {"S3DataType": "S3Prefix", "S3Uri": DEFAULT_S3_INPUT_DATA}
                },
                "TargetAttributeName": TARGET_ATTRIBUTE_NAME,
            }
        ],
        "output_config": {"S3OutputPath": DEFAULT_OUTPUT_PATH},
        "auto_ml_job_config": {
            "CompletionCriteria": {"MaxCandidates": DEFAULT_MAX_CANDIDATES},
            "SecurityConfig": {
                "EnableInterContainerTrafficEncryption": ENCRYPT_INTER_CONTAINER_TRAFFIC
            },
        },
        "role": ROLE,
        "job_name": DEFAULT_JOB_NAME,
        "problem_type": None,
        "job_objective": None,
        "generate_candidate_definitions_only": GENERATE_CANDIDATE_DEFINITIONS_ONLY,
        "tags": None,
    }


def test_auto_ml_local_input(sagemaker_session):
    auto_ml = AutoML(
        role=ROLE, target_attribute_name=TARGET_ATTRIBUTE_NAME, sagemaker_session=sagemaker_session
    )
    inputs = DEFAULT_S3_INPUT_DATA
    auto_ml.fit(inputs)
    sagemaker_session.auto_ml.assert_called_once()
    _, args = sagemaker_session.auto_ml.call_args
    assert args["input_config"][0]["DataSource"]["S3DataSource"]["S3Uri"] == DEFAULT_S3_INPUT_DATA


def test_auto_ml_input(sagemaker_session):
    inputs = AutoMLInput(
        inputs=DEFAULT_S3_INPUT_DATA, target_attribute_name="target", compression="Gzip"
    )
    auto_ml = AutoML(
        role=ROLE, target_attribute_name=TARGET_ATTRIBUTE_NAME, sagemaker_session=sagemaker_session
    )
    auto_ml.fit(inputs)
    _, args = sagemaker_session.auto_ml.call_args
    assert args["input_config"] == [
        {
            "CompressionType": "Gzip",
            "DataSource": {
                "S3DataSource": {"S3DataType": "S3Prefix", "S3Uri": DEFAULT_S3_INPUT_DATA}
            },
            "TargetAttributeName": TARGET_ATTRIBUTE_NAME,
        }
    ]


def test_describe_auto_ml_job(sagemaker_session):
    auto_ml = AutoML(
        role=ROLE, target_attribute_name=TARGET_ATTRIBUTE_NAME, sagemaker_session=sagemaker_session
    )
    auto_ml.describe_auto_ml_job(job_name=JOB_NAME)
    sagemaker_session.describe_auto_ml_job.assert_called_once()
    sagemaker_session.describe_auto_ml_job.assert_called_with(JOB_NAME)


def test_list_candidates_default(sagemaker_session):
    auto_ml = AutoML(
        role=ROLE, target_attribute_name=TARGET_ATTRIBUTE_NAME, sagemaker_session=sagemaker_session
    )
    auto_ml.current_job_name = "current_job_name"
    auto_ml.list_candidates()
    sagemaker_session.list_candidates.assert_called_once()
    sagemaker_session.list_candidates.assert_called_with(job_name=auto_ml.current_job_name)


def test_list_candidates_with_optional_args(sagemaker_session):
    auto_ml = AutoML(
        role=ROLE, target_attribute_name=TARGET_ATTRIBUTE_NAME, sagemaker_session=sagemaker_session
    )
    auto_ml.list_candidates(
        job_name=JOB_NAME,
        status_equals="Completed",
        candidate_name="candidate-name",
        candidate_arn="candidate-arn",
        sort_order="Ascending",
        sort_by="Status",
        max_results=99,
    )
    sagemaker_session.list_candidates.assert_called_once()
    _, args = sagemaker_session.list_candidates.call_args
    assert args == {
        "job_name": JOB_NAME,
        "status_equals": "Completed",
        "candidate_name": "candidate-name",
        "candidate_arn": "candidate-arn",
        "sort_order": "Ascending",
        "sort_by": "Status",
        "max_results": 99,
    }


def test_best_candidate_with_existing_best_candidate(sagemaker_session):
    auto_ml = AutoML(
        role=ROLE, target_attribute_name=TARGET_ATTRIBUTE_NAME, sagemaker_session=sagemaker_session
    )
    auto_ml._best_candidate = BEST_CANDIDATE
    best_candidate = auto_ml.best_candidate()
    sagemaker_session.describe_auto_ml_job.assert_not_called()
    assert best_candidate == BEST_CANDIDATE


def test_best_candidate_default_job_name(sagemaker_session):
    auto_ml = AutoML(
        role=ROLE, target_attribute_name=TARGET_ATTRIBUTE_NAME, sagemaker_session=sagemaker_session
    )
    auto_ml.current_job_name = JOB_NAME
    auto_ml._auto_ml_job_desc = AUTO_ML_DESC
    best_candidate = auto_ml.best_candidate()
    sagemaker_session.describe_auto_ml_job.assert_not_called()
    assert best_candidate == BEST_CANDIDATE


def test_best_candidate_job_no_desc(sagemaker_session):
    auto_ml = AutoML(
        role=ROLE, target_attribute_name=TARGET_ATTRIBUTE_NAME, sagemaker_session=sagemaker_session
    )
    auto_ml.current_job_name = JOB_NAME
    best_candidate = auto_ml.best_candidate()
    sagemaker_session.describe_auto_ml_job.assert_called_once()
    sagemaker_session.describe_auto_ml_job.assert_called_with(JOB_NAME)
    assert best_candidate == BEST_CANDIDATE


def test_best_candidate_no_desc_no_job_name(sagemaker_session):
    auto_ml = AutoML(
        role=ROLE, target_attribute_name=TARGET_ATTRIBUTE_NAME, sagemaker_session=sagemaker_session
    )
    best_candidate = auto_ml.best_candidate(job_name=JOB_NAME)
    sagemaker_session.describe_auto_ml_job.assert_called_once()
    sagemaker_session.describe_auto_ml_job.assert_called_with(JOB_NAME)
    assert best_candidate == BEST_CANDIDATE


def test_best_candidate_job_name_not_match(sagemaker_session):
    auto_ml = AutoML(
        role=ROLE, target_attribute_name=TARGET_ATTRIBUTE_NAME, sagemaker_session=sagemaker_session
    )
    auto_ml.current_job_name = JOB_NAME
    auto_ml._auto_ml_job_desc = AUTO_ML_DESC
    best_candidate = auto_ml.best_candidate(job_name=JOB_NAME_2)
    sagemaker_session.describe_auto_ml_job.assert_called_once()
    sagemaker_session.describe_auto_ml_job.assert_called_with(JOB_NAME_2)
    assert best_candidate == BEST_CANDIDATE_2


def test_deploy(sagemaker_session, candidate_mock):
    auto_ml = AutoML(
        role=ROLE, target_attribute_name=TARGET_ATTRIBUTE_NAME, sagemaker_session=sagemaker_session
    )
    mock_pipeline = Mock(name="pipeline_model")
    mock_pipeline.deploy = Mock(name="model_deploy")
    auto_ml.best_candidate = Mock(name="best_candidate", return_value=CANDIDATE_DICT)
    auto_ml.create_model = Mock(name="create_model", return_value=mock_pipeline)
    auto_ml.deploy(
        initial_instance_count=INSTANCE_COUNT,
        instance_type=INSTANCE_TYPE,
        sagemaker_session=sagemaker_session,
    )
    auto_ml.create_model.assert_called_once()
    mock_pipeline.deploy.assert_called_once()


@patch("sagemaker.automl.automl.CandidateEstimator")
def test_deploy_optional_args(candidate_estimator, sagemaker_session, candidate_mock):
    candidate_estimator.return_value = candidate_mock

    auto_ml = AutoML(
        role=ROLE, target_attribute_name=TARGET_ATTRIBUTE_NAME, sagemaker_session=sagemaker_session
    )
    mock_pipeline = Mock(name="pipeline_model")
    mock_pipeline.deploy = Mock(name="model_deploy")
    auto_ml.best_candidate = Mock(name="best_candidate", return_value=CANDIDATE_DICT)
    auto_ml.create_model = Mock(name="create_model", return_value=mock_pipeline)

    auto_ml.deploy(
        initial_instance_count=INSTANCE_COUNT,
        instance_type=INSTANCE_TYPE,
        candidate=CANDIDATE_DICT,
        sagemaker_session=sagemaker_session,
        name=JOB_NAME,
        endpoint_name=JOB_NAME,
        tags=TAGS,
        wait=False,
        vpc_config=VPC_CONFIG,
        enable_network_isolation=True,
        model_kms_key=OUTPUT_KMS_KEY,
        predictor_cls=Predictor,
        inference_response_keys=None,
    )

    auto_ml.create_model.assert_called_once()
    auto_ml.create_model.assert_called_with(
        name=JOB_NAME,
        sagemaker_session=sagemaker_session,
        candidate=CANDIDATE_DICT,
        inference_response_keys=None,
        vpc_config=VPC_CONFIG,
        enable_network_isolation=True,
        model_kms_key=OUTPUT_KMS_KEY,
        predictor_cls=Predictor,
    )

    mock_pipeline.deploy.assert_called_once()

    mock_pipeline.deploy.assert_called_with(
        initial_instance_count=INSTANCE_COUNT,
        instance_type=INSTANCE_TYPE,
        serializer=None,
        deserializer=None,
        endpoint_name=JOB_NAME,
        tags=TAGS,
        wait=False,
    )


def test_candidate_estimator_get_steps(sagemaker_session):
    candidate_estimator = CandidateEstimator(CANDIDATE_DICT, sagemaker_session=sagemaker_session)
    steps = candidate_estimator.get_steps()
    assert len(steps) == 3


def test_candidate_estimator_fit(sagemaker_session):
    candidate_estimator = CandidateEstimator(CANDIDATE_DICT, sagemaker_session=sagemaker_session)
    candidate_estimator._check_all_job_finished = Mock(
        name="_check_all_job_finished", return_value=True
    )
    inputs = DEFAULT_S3_INPUT_DATA
    candidate_estimator.fit(inputs)
    sagemaker_session.train.assert_called()
    sagemaker_session.transform.assert_called()


def test_validate_and_update_inference_response():
    cic = copy.copy(CLASSIFICATION_INFERENCE_CONTAINERS)

    AutoML.validate_and_update_inference_response(
        inference_containers=cic,
        inference_response_keys=["predicted_label", "labels", "probabilities", "probability"],
    )

    assert (
        cic[2]["Environment"]["SAGEMAKER_INFERENCE_OUTPUT"]
        == "predicted_label,labels,probabilities,probability"
    )
    assert (
        cic[2]["Environment"]["SAGEMAKER_INFERENCE_INPUT"]
        == "predicted_label,probabilities,probability"
    )
    assert (
        cic[1]["Environment"]["SAGEMAKER_INFERENCE_OUTPUT"]
        == "predicted_label,probabilities,probability"
    )


def test_validate_and_update_inference_response_wrong_input():
    cic = copy.copy(CLASSIFICATION_INFERENCE_CONTAINERS)

    with pytest.raises(ValueError) as excinfo:
        AutoML.validate_and_update_inference_response(
            inference_containers=cic,
            inference_response_keys=["wrong_key", "wrong_label", "probabilities", "probability"],
        )
    message = (
        "Requested inference output keys [wrong_key, wrong_label] are unsupported. "
        "The supported inference keys are [probability, probabilities, predicted_label, labels]"
    )
    assert message in str(excinfo.value)


def test_create_model(sagemaker_session):
    auto_ml = AutoML(
        role=ROLE, target_attribute_name=TARGET_ATTRIBUTE_NAME, sagemaker_session=sagemaker_session
    )

    pipeline_model = auto_ml.create_model(
        name=JOB_NAME,
        sagemaker_session=sagemaker_session,
        candidate=CLASSIFICATION_CANDIDATE_DICT,
        vpc_config=VPC_CONFIG,
        enable_network_isolation=True,
        model_kms_key=None,
        predictor_cls=None,
        inference_response_keys=None,
    )

    assert isinstance(pipeline_model, PipelineModel)


def test_attach(sagemaker_session):
    aml = AutoML.attach(auto_ml_job_name=JOB_NAME_3, sagemaker_session=sagemaker_session)
    assert aml.current_job_name == JOB_NAME_3
    assert aml.role == "mock_role_arn"
    assert aml.target_attribute_name == "y"
    assert aml.problem_type == "Auto"
    assert aml.output_path == "s3://output_prefix"
    assert aml.tags == LIST_TAGS_RESULT["Tags"]
