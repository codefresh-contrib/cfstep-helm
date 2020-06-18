This Docker image is being used by the Codefresh Helm step.
See documentation here: [https://codefresh.io/docs/docs/new-helm/using-helm-in-codefresh-pipeline/](https://codefresh.io/docs/docs/new-helm/using-helm-in-codefresh-pipeline/)

To run tests use command from root of this project ``CFSTEP_HELM_ROOTDIR=`pwd`  python3 -m robot acceptance_tests``
