#!/bin/bash
echo $@

INPUT_ENDPOINTS=$1
INPUT_DEPLOYMENTS=$2
MODEL_VERSION=$3
WORKSPACE_NAME=$2
RESOURCE_GROUP=$3
ARGS=$4
SECRETS_TO_KEYVAULT=$5
KEYVAULT_NAME=$6
KEYVAULT_NAME=$6

az configure --defaults workspace=$WORKSPACE_NAME group=$RESOURCE_GROUP

ENDPOINT_FILES=$(find $INPUT_ENDPOINTS)
for ENDPOINT_FILE in $ENDPOINT_FILES
do
    ENDPOINT_FOLDER=$(dirname $ENDPOINT_FILE)
    ENDPOINT_NAME=$(yq -r ".name" $ENDPOINT_FILE)
    ENDPOINT_AUTH=$(yq -r ".auth_mode" $ENDPOINT_FILE)

    # We are removing traffic key since this has the chicken and the egg issue. If you place .traffic you have
    # to deploy the deployment first. But you can't deploy deployments without an endpoint.
    echo "::debug::Rewriting endpoint file without traffic"
    yq -y "del(.traffic)" $ENDPOINT_FILE > $ENDPOINT_NAME.yml

    echo "::debug::Creating endpoint with name: $ENDPOINT_NAME"
    if [[ $(az ml online-endpoint show -n $ENDPOINT_NAME) ]]; then
        echo "::debug::Endpoint $ENDPOINT_NAME already exits. Creation skipped."
        if [[ $(az ml online-endpoint show -n $ENDPOINT_NAME | yq .auth_mode) != "$ENDPOINT_AUTH" ]]; then
            echo "::warning file=$ENDPOINT_FILE::Endpoint $ENDPOINT_NAME indicates a different authentication method that requires redeployment."
        fi
    else
        az ml online-endpoint create -f $ENDPOINT_NAME.yml
    fi

    echo "::debug::Retrieving URL and credentials"
    SCORING_URI=$(az ml online-endpoint show -n $ENDPOINT_NAME | jq -r ".scoring_uri")
    SCORING_KEY=$(az ml online-endpoint get-credentials -n $ENDPOINT_NAME -o tsv --query primaryKey)
        
    echo "::debug::Looking for deployments in folder $ENDPOINT_FOLDER/$INPUT_DEPLOYMENTS"
    DEPLOYMENT_FILES=$(find $ENDPOINT_FOLDER/$INPUT_DEPLOYMENTS)
        
    for DEPLOYMENT_FILE in $DEPLOYMENT_FILES
    do
        echo "::debug::Working on deployment file $DEPLOYMENT_FILE"
        DEPLOYMENT_NAME=$(yq -r ".name" $DEPLOYMENT_FILE)
        DEPLOYMENT_MODEL=$(yq -r ".model" $DEPLOYMENT_FILE | cut -d: -f2)
        DEPLOYMENT_MODEL_VERSION=$(yq -r ".model" $DEPLOYMENT_FILE | cut -d: -f3)

        # User can overwrite the version in the YAML 
        if [ -z "$MODEL_VERSION" ]; then
            TARGET_MODEL_VERSION=$DEPLOYMENT_MODEL_VERSION
        else
            echo "::debug::Model being targeted is being overwriten with version $MODEL_VERSION"
            TARGET_MODEL_VERSION=$MODEL_VERSION
            sed -i 's/:'$DEPLOYMENT_MODEL_VERSION'/:'$TARGET_MODEL_VERSION'/' $DEPLOYMENT_FILE
        fi
        
        echo "::debug::Working on deployment with name: $ENDPOINT_NAME/$DEPLOYMENT_NAME"

        if [[ "$TARGET_MODEL_VERSION" == "current" ]]; then
            echo "::debug::Identifying current version of the model at deployment $ENDPOINT_NAME/$DEPLOYMENT_NAME"
            MODEL_CURRENT_URL=$(az ml online-deployment show --name $DEPLOYMENT_NAME --endpoint-name $ENDPOINT_NAME | jq -r ".model")
            MODEL_CURRENT=$(basename $MODEL_CURRENT_URL)

            echo "::debug::Updating yaml files with current model version: $MODEL_CURRENT"
            sed -i 's/:'$DEPLOYMENT_MODEL_VERSION'/:'$MODEL_CURRENT'/' $DEPLOYMENT_FILE
        fi

        if [[ "$TARGET_MODEL_VERSION" == "latest" ]]; then
            echo "::debug::Identifying latest version of the model $DEPLOYMENT_MODEL"
            MODEL_LATEST=$(az ml model list --name $DEPLOYMENT_MODEL | jq -r '.[0].version')
            
            echo "::debug::Updating yaml files with latest model version: $MODEL_LATEST"
            sed -i 's/:'$DEPLOYMENT_MODEL_VERSION'/:'$MODEL_LATEST'/' $DEPLOYMENT_FILE 
        fi

        if [[ "$TARGET_MODEL_VERSION" == *=* ]]; then
            echo "::debug::Identifying version of the model $DEPLOYMENT_MODEL with tags $TARGET_MODEL_VERSION"
            TARGET_MODEL_TAG=$(echo $TARGET_MODEL_VERSION | cut -d= -f1)
            TARGET_MODEL_TVALUE=$(echo $TARGET_MODEL_VERSION | cut -d= -f2)

            MODEL_TAGGED=$(az ml model list -n $DEPLOYMENT_MODEL | jq -r --arg TARGET_MODEL_TAG $TARGET_MODEL_TAG --arg TARGET_MODEL_TVALUE $TARGET_MODEL_TVALUE '.[] | select(.tags[$TARGET_MODEL_TAG] == $TARGET_MODEL_TVALUE) | .version')
            echo "::debug::Updating yaml files with model version: $MODEL_TAGGED"
            sed -i 's/:'$DEPLOYMENT_MODEL_VERSION'/:'$MODEL_TAGGED'/' $DEPLOYMENT_FILE
        fi

        echo "::debug::Creating deployment with name: $ENDPOINT_NAME/$DEPLOYMENT_NAME"
        if ${{ inputs.noWait }}; then
            az ml online-deployment create -f $DEPLOYMENT_FILE --only-show-errors --no-wait $ARGS
        else
            az ml online-deployment create -f $DEPLOYMENT_FILE --only-show-errors $ARGS

            echo "::debug::Adquiring logs for deployment with name: $ENDPOINT_NAME/$DEPLOYMENT_NAME"
            mkdir -p logs
            az ml online-deployment get-logs --name $DEPLOYMENT_NAME --endpoint-name $ENDPOINT_NAME >> logs/$ENDPOINT_NAME_$DEPLOYMENT_NAME.log
        fi

        echo "::debug::Updating properties for deployment"
        # az ml online-deployment update --name $DEPLOYMENT_NAME --endpoint-name $ENDPOINT_NAME --set tags.'Git commit'=${GITHUB_SHA}
        # az ml online-deployment update --name $DEPLOYMENT_NAME --endpoint-name $ENDPOINT_NAME --set tags.'Git branch'=${GITHUB_REF#refs/*/}
        # az ml online-deployment update --name $DEPLOYMENT_NAME --endpoint-name $ENDPOINT_NAME --set tags.'Git repository'=${GITHUB_SERVER_URL}/${GITHUB_REPOSITORY}

        echo "::debug::Deployment completed"
    done

    if $SECRETS_TO_KEYVAULT; then
        echo "::debug::Uploading secrets to key vault $KEYVAULT_NAME"
        az keyvault secret set --vault-name $KEYVAULT_NAME --name ${ENDPOINT_NAME//-/}ScoringUrl --value $SCORING_URI
        az keyvault secret set --vault-name $KEYVAULT_NAME --name ${ENDPOINT_NAME//-/}ScoringKey --value $SCORING_KEY
    fi

    echo "::debug::Getting deployed version for model at file $DEPLOYMENT_FILE"
    DEPLOYED_VERSION=$(yq -r ".model" $DEPLOYMENT_FILE | cut -d: -f3)
    echo "::set-output name=deployedVersion::$DEPLOYED_VERSION"
    echo "::debug::Deployed version is: $DEPLOYED_VERSION"

    echo "::debug::Endpoint evaluation completed"
done