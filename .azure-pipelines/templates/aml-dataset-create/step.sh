#!/bin/bash
echo $@

DATASET_FILE_PATH=$1
WORKSPACE_NAME=$2
RESOURCE_GROUP=$3
INITIALIZE=$4
INITIALIZE_WITH_DATA_PATH=$5
STORAGE_ACCOUNT=$6

echo "##[debug]Looking for datasets definition at '$DATASET_FILE_PATH'"
DATASETS_FILES=$(find $DATASET_FILE_PATH;)

for DATASET_FILE in $DATASETS_FILES
do
    echo "##[debug]Working with dataset '$DATASET_FILE'"

    LOCAL_FOLDER=$(dirname $DATASET_FILE)
    DATASET_NAME=$(yq -r ".name" $DATASET_FILE)
    DATASET_TYPE=$(yq -r ".type" $DATASET_FILE)
    REMOTE_FILE=$(yq -r ".path" $DATASET_FILE)
    CONTAINER_NAME=$(dirname $REMOTE_FILE | cut -d/ -f4)

    if [[ "$DATASET_TYPE" == "uri_folder" ]]; then
        # IF dataset type is uri_folder, it's already a folder. Don't need dirname.
        REMOTE_FOLDER=$(echo $REMOTE_FILE | cut -d/ -f6-)
    else
        REMOTE_FOLDER=$(dirname $REMOTE_FILE | cut -d/ -f6-)
    fi

    echo "##[debug]DATASET_NAME=$DATASET_NAME"
    echo "##[debug]DATASET_TYPE=$DATASET_TYPE"
    echo "##[debug]REMOTE_FILE=$REMOTE_FILE"
    echo "##[debug]REMOTE_FOLDER=$REMOTE_FOLDER"
    echo "##[debug]CONTAINER_NAME=$CONTAINER_NAME"
    echo "##[debug]LOCAL_FOLDER=$LOCAL_FOLDER"

    if [[ $(az ml data list --name $DATASET_NAME --workspace-name $WORKSPACE_NAME --resource-group $RESOURCE_GROUP) ]]; then
        echo "##[debug]Dataset $DATASET_NAME already in target workspace."
    else
        echo "##[debug]Dataset $DATASET_NAME is missing. Creating from file $DATASET_FILE."
        az ml data create --file $DATASET_FILE --resource-group $RESOURCE_GROUP --workspace-name $WORKSPACE_NAME
        
        if $INITIALIZE; then
            # Data uploaded manually as AzureFileCopy@4 not supported in Linux
            echo "##[debug]Uploading data for $DATASET_NAME in container $CONTAINER_NAME ($STORAGE_ACCOUNT)"
            echo "##[debug]Source: $LOCAL_FOLDER/$INITIALIZE_WITH_DATA_PATH"
            echo "##[debug]Destination: $REMOTE_FOLDER"

            if test -d "$LOCAL_FOLDER/$INITIALIZE_WITH_DATA_PATH"; then
                az storage blob upload-batch -d $CONTAINER_NAME --auth-mode login --overwrite --account-name $STORAGE_ACCOUNT --source "$LOCAL_FOLDER/$INITIALIZE_WITH_DATA_PATH" --destination-path $REMOTE_FOLDER
            else
                echo "##vso[task.logissue type=error]Folder $LOCAL_FOLDER/$INITIALIZE_WITH_DATA_PATH not found."
                exit 1
            fi
        fi
    fi
done
