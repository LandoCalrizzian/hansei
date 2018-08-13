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
# APP_READINESS_PROBE=/api/v1/status/
# GIT_URL=https://github.com/project-koku/koku.git
# GIT_BRANCH=master
####################################################################################################

# PARSE COMMAND LINE ARGS
APP_PARAMS=""
APP_PARAMS_ENV=""
DISABLE_READY_CHECK=0
PARAMS=""
while (( "$#" )); do
    case "$1" in
        -h|--help)
            usage
            exit 0
            ;;
        -n|--project-name)
            OPENSHIFT_PROJECT=$2
            shift 2
            ;;
        --token)
            OPENSHIFT_TOKEN=$2
            shift 2
            ;;
        -t|--host)
            OPENSHIFT_HOST=$2
            shift 2
            ;;
        -p|--port)
            OPENSHIFT_PORT=$2
            shift 2
            ;;
        -m|--template)
            OPENSHIFT_TEMPLATE_PATH=$2
            shift 2
            ;;
        --git-url)
            GIT_URL=$2
            shift 2
            ;;
        -b|--branch)
            GIT_BRANCH=$2
            shift 2
            ;;
        --app-name)
            APP_NAME=$2
            shift 2
            ;;
        --app-param)
            APP_PARAMS="${APP_PARAMS} --param $2"
            shift 2
            ;;
        --app-param-env)
            APP_PARAMS_ENV="${APP_PARAMS_ENV} --env $2"
            shift 2
            ;;
        --disable-ready-check)
            DISABLE_READY_CHECK=1
            shift 1
            ;;
        --) # end argument parsing
            shift
            break
            ;;
        -*|--*=) # unsupported flags
            echo "Error: Unsupported flag $1" >&2
            exit 1
            ;;
        *) # preserve positional arguments
            PARAM="$PARAMS $1"
            shift
            ;;
    esac
done

# set positional arguments in their proper place
eval set -- "$PARAMS"
if [[ -n ${OPENSHIFT_PORT} ]]; then
  OPENSHIFT_URL=https://${OPENSHIFT_HOST}:${OPENSHIFT_PORT}
else
  OPENSHIFT_URL=https://${OPENSHIFT_HOST}
fi

echo Logging into OpenShift server ${OPENSHIFT_URL}
oc login  ${OPENSHIFT_URL} --token=${OPENSHIFT_TOKEN}

oc project ${OPENSHIFT_PROJECT}

if [[ "$(oc project -q)" != "${OPENSHIFT_PROJECT}" ]]; then
  echo "EXITING. We are not on project ${OPENSHIFT_PROJECT}"
  exit 1
fi

#Is this a new deployment or an existing app? Decide based on whether the project is empty or not
#If BuildConfig exists, assume that the app is already deployed and we need a rebuild

BUILD_CONFIG=`oc get bc ${APP_NAME} 2>/dev/null | tail -1 | awk '{print $1}'`

# Delete the old app directory where we cloned the repo
if [[ -d $APP_NAME ]]; then
  rm -rf $APP_NAME/
fi

echo Cloning the $APP_NAME repo $GIT_URL
# Clone repo and checkout specific branch or revision for testing
git clone $GIT_URL $APP_NAME
git checkout -q $GIT_BRANCH

echo Moving to repo dir $APP_NAME
pushd $APP_NAME

if [ -z "$BUILD_CONFIG" ]; then

# no app found so create a new one
  echo "Create a new app"


  if [[ ! -f ${OPENSHIFT_TEMPLATE_PATH} ]]; then
    echo "${OPENSHIFT_TEMPLATE_PATH} does not exist"
    exit 1
  fi

  oc apply -f ${OPENSHIFT_TEMPLATE_PATH} -n ${OPENSHIFT_PROJECT}

  oc new-app --template $(basename ${OPENSHIFT_TEMPLATE_PATH} .yaml) ${APP_PARAMS_ENV} ${APP_PARAMS}

  echo "Find build id"
  BUILD_ID=`oc get builds | grep ${APP_NAME} | tail -1 | awk '{print $1}'`
  rc=1
  attempts=75
  count=0
  while [ $rc -ne 0 -a $count -lt $attempts ]; do
    BUILD_ID=`oc get builds | grep ${APP_NAME} | tail -1 | awk '{print $1}'`
    if [[ $BUILD_ID == "NAME"  || -z ${BUILD_ID// /} ]]; then
      if [ -z ${BUILD_ID// /} ]; then
        echo "DEBUG: Blank Build Id --> $(oc get builds)"
      fi
      count=$(($count+1))
      echo "Attempt $count/$attempts"
      sleep 5
    else 
      rc=0
      echo "Build Id is :" ${BUILD_ID}
    fi 
  done

  if [ $rc -ne 0 ]; then
    echo "Fail: Build could not be found after maximum attempts"
    exit 1
  fi 
else

  # Application already exists, just need to start a new build
  echo "App Exists. Triggering application build and deployment"
  BUILD_ID=`oc start-build ${BUILD_CONFIG} | awk '{print $2}' | sed -e 's/^"//' -e 's/"$//'`
fi

echo "Waiting for build ${BUILD_ID} to start"
rc=1
attempts=25
count=0
while [ $rc -ne 0 -a $count -lt $attempts ]; do
  status=`oc get build ${BUILD_ID} -o jsonpath='{.status.phase}'`
  if [[ $status == "Failed" || $status == "Error" || $status == "Canceled" ]]; then
    echo "Fail: Build completed with unsuccessful status: ${status}"
    exit 1
  fi
  if [ $status == "Complete" ]; then
    echo "Build completed successfully, will test deployment next"
    rc=0
  fi
  
  if [ $status == "Running" ]; then
    echo "Build started"
    rc=0
  fi
  
  if [ $status == "Pending" ]; then
    count=$(($count+1))
    echo "Attempt $count/$attempts"
    sleep 5
  fi
done

# stream the logs for the build that just started
oc logs -f bc/${APP_NAME}



echo "Checking build result status"
rc=1
count=0
attempts=100
while [ $rc -ne 0 -a $count -lt $attempts ]; do
  status=`oc get build ${BUILD_ID} -o jsonpath='{.status.phase}'`
  if [[ $status == "Failed" || $status == "Error" || $status == "Canceled" ]]; then
    echo "Fail: Build completed with unsuccessful status: ${status}"
    exit 1
  fi

  if [ $status == "Complete" ]; then
    echo "Build completed successfully, will test deployment next"
    rc=0
  else 
    count=$(($count+1))
    echo "Attempt $count/$attempts"
    sleep 5
  fi
done

if [ $rc -ne 0 ]; then
    echo "Fail: Build did not complete in a reasonable period of time"
    exit 1
fi

# scale up the test deployment
RC_ID=`oc get rc | tail -1 | awk '{print $1}'`

echo "Scaling up new deployment $RC_ID"
oc scale --replicas=1 rc $RC_ID


if [[ $DISABLE_READY_CHECK -eq 0 ]]; then
  echo "Checking for successful deployment at http://${APP_NAME}-${OPENSHIFT_PROJECT}.${OPENSHIFT_APP_DOMAIN}${APP_READINESS_PROBE}"
  set +e
  rc=1
  count=0
  attempts=100
  while [ $rc -ne 0 -a $count -lt $attempts ]; do
    CURL_RES=`curl -I --connect-timeout 2 http://${APP_NAME}-${OPENSHIFT_PROJECT}.${OPENSHIFT_APP_DOMAIN}${APP_READINESS_PROBE} 2> /dev/null | head -n 1 | cut -d$' ' -f2`
    if [[ $CURL_RES == "200" ]]; then
      rc=0
      echo "Successful test against http://${APP_NAME}-${OPENSHIFT_PROJECT}.${OPENSHIFT_APP_DOMAIN}${APP_READINESS_PROBE}"
      break
    fi
    count=$(($count+1))
    echo "Attempt $count/$attempts"
    sleep 5
  done
  set -e

  if [ $rc -ne 0 ]; then
      echo "Failed to access deployment, aborting roll out."
      exit 1
  fi
fi

# Leave the APP_NAME directory
popd
