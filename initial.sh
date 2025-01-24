#!/bin/bash

# Variables
RESOURCE_GROUP="Resource_Group_Name"
LOCATION="Region"
SERVICE_BUS_NAMESPACE="Service_bus_Namespace"
TOPIC_NAME="Service_Bus_Topic_Name"
SUBSCRIPTION_NAME="Service_Bus_Topic_Subscription_Name"


# Create a resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create a Service Bus namespace
az servicebus namespace create --resource-group $RESOURCE_GROUP --name $SERVICE_BUS_NAMESPACE --location $LOCATION

# Create a Service Bus topic
az servicebus topic create --resource-group $RESOURCE_GROUP --namespace-name $SERVICE_BUS_NAMESPACE --name $TOPIC_NAME

# Create a Service Bus subscription
az servicebus topic subscription create --resource-group $RESOURCE_GROUP --namespace-name $SERVICE_BUS_NAMESPACE --topic-name $TOPIC_NAME --name $SUBSCRIPTION_NAME
