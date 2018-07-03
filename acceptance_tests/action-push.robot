*** Settings ***
Documentation     Tests to verify functionality of ACTION=push
Library           Collections
Library           lib/CFStepHelm.py

*** Test Cases ***
Able to push to ChartMuseum repo
    &{env}=   Create dictionary
    Set to dictionary   ${env}  CHART_REF   mychartref
    Set to dictionary   ${env}  RELEASE_NAME   my-release
    Set to dictionary   ${env}  KUBE_CONTEXT   my-context
    Set to dictionary   ${env}  DRY_RUN   true
    Set to dictionary   ${env}  ACTION   push
    Set to dictionary   ${env}  CHART_REPO_URL  cm://my-cm-repo.com
    Run with env   ${env}
    Should have succeeded
    Output contains   helm push

Able to push to S3 repo
    &{env}=   Create dictionary
    Set to dictionary   ${env}  CHART_REF   mychartref
    Set to dictionary   ${env}  RELEASE_NAME   my-release
    Set to dictionary   ${env}  KUBE_CONTEXT   my-context
    Set to dictionary   ${env}  DRY_RUN   true
    Set to dictionary   ${env}  ACTION   push
    Set to dictionary   ${env}  CHART_REPO_URL  s3://my-s3-bucket
    Run with env   ${env}
    Should have succeeded
    Output contains   helm s3 push

Able to push to GCS repo
    &{env}=   Create dictionary
    Set to dictionary   ${env}  CHART_REF   mychartref
    Set to dictionary   ${env}  RELEASE_NAME   my-release
    Set to dictionary   ${env}  KUBE_CONTEXT   my-context
    Set to dictionary   ${env}  DRY_RUN   true
    Set to dictionary   ${env}  ACTION   push
    Set to dictionary   ${env}  CHART_REPO_URL  gs://my-gcs-bucket
    Run with env   ${env}
    Should have succeeded
    Output contains   helm gcs push
