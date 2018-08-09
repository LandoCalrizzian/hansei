#!/bin/sh
####################################################################################################
#
# DEFINE THE ENVIRONMENT VARIABLES BELOW
# HANSEI_SERVICE_ACCOUNT_TOKEN=
# OPENSHIFT_HOST=
# OPENSHIFT_PORT=8443
# OPENSHIFT_PROJECT=
# OPENSHIFT_APP_DOMAIN=
# OPENSHIFT_TEMPLATE_PATH=
# OPENSHIFT_PROJECT=
# APP_NAME=
# ARTIFACT_DIR=
####################################################################################################

# Create or empty the artifact directory
if [[ -z $ARTIFACT_DIR ]]; then
  echo "ERROR: ARTIFACT_DIR is not defined"
  exit 1
fi

echo "Storing artifacts in $ARTIFACT_DIR"
if [[ ! -d $ARTIFACT_DIR ]]; then
  echo "Creating artifact directory $ARTIFACT_DIR"
  mkdir $ARTIFACT_DIR
else
  echo "Cleaning artifact directory $ARTIFACT_DIR"
  rm -rf $ARTIFACT_DIR/*
fi

oc get all > $ARTIFACT_DIR/${APP_NAME}_oc_get_all.log
oc describe all > $ARTIFACT_DIR/${APP_NAME}_oc_describe_all.log

echo "Contents of $ARTIFACT_DIR:"
echo $(find $ARTIFACT_DIR -type f)
